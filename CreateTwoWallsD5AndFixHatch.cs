using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class TwoWallsWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var m in msgs)
            {
                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class CreateTwoWallsD5AndFixHatch
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // ---------------------------------------------------------------
            // 1. DELETE OLD DUPLICATE WALLS IF ANY
            // ---------------------------------------------------------------
            long[] oldDupIds = new long[] { 2361324L, 2361325L, 2361326L, 2361327L };
            using (var txDel = new Transaction(doc, "Delete Duplicate Old Walls"))
            {
                txDel.Start();
                var toDel = oldDupIds.Select(id => new ElementId(id))
                                     .Where(id => doc.GetElement(id) != null)
                                     .ToList();
                if (toDel.Count > 0)
                {
                    doc.Delete(toDel);
                }
                txDel.Commit();
            }

            // ---------------------------------------------------------------
            // 2. CHANGE HATCH OF TƯỜNG 100 TO ANSI31
            // ---------------------------------------------------------------
            var allFillPatterns = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .ToList();

            FillPatternElement fpeAnsi31 = allFillPatterns.FirstOrDefault(p => p.Name.Equals("ANSI31", StringComparison.OrdinalIgnoreCase)
                                                                           || p.Name.Equals("ANSI 31", StringComparison.OrdinalIgnoreCase))
                                       ?? allFillPatterns.FirstOrDefault(p => p.Name.Equals("Diagonal up 1.5mm", StringComparison.OrdinalIgnoreCase))
                                       ?? allFillPatterns.FirstOrDefault(p => p.Name.Equals("Diagonal up", StringComparison.OrdinalIgnoreCase));

            if (fpeAnsi31 == null)
            {
                using (var txPat = new Transaction(doc, "Create ANSI31 Pattern"))
                {
                    txPat.Start();
                    // 45 degrees, 1.5mm line spacing
                    var fp = new FillPattern("ANSI31", FillPatternTarget.Drafting, FillPatternHostOrientation.ToHost, Math.PI / 4.0, 1.5 / 304.8);
                    fpeAnsi31 = FillPatternElement.Create(doc, fp);
                    txPat.Commit();
                }
            }

            // Find wall types for 100mm
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();

            var wt100 = wallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi")
                     ?? wallTypes.FirstOrDefault(w => w.Name == "gach100");
            var wt200 = wallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi")
                     ?? wallTypes.FirstOrDefault(w => w.Name == "gach200");

            if (wt100 == null) return new { error = "Wall type gach100_xay moi not found" };
            if (wt200 == null) return new { error = "Wall type gach200_xay moi not found" };

            // Create or update dedicated Material for gach100 with ANSI31 hatch
            using (var txMat = new Transaction(doc, "Set ANSI31 Hatch for Tuong 100"))
            {
                txMat.Start();

                var allMats = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .ToList();

                var matGach100 = allMats.FirstOrDefault(m => m.Name == "Vật liệu Gạch 100 - ANSI31");
                if (matGach100 == null)
                {
                    var baseMat = allMats.FirstOrDefault(m => m.Name.Contains("HOAN THIEN", StringComparison.OrdinalIgnoreCase))
                               ?? allMats.FirstOrDefault();
                    if (baseMat != null)
                    {
                        matGach100 = baseMat.Duplicate("Vật liệu Gạch 100 - ANSI31") as Material;
                    }
                }

                if (matGach100 != null && fpeAnsi31 != null)
                {
                    matGach100.CutForegroundPatternId = fpeAnsi31.Id;
                    matGach100.CutForegroundPatternColor = new Color(80, 80, 80); // Dark gray clean hatch line
                }

                // Assign to wt100 CompoundStructure
                if (matGach100 != null)
                {
                    var cs = wt100.GetCompoundStructure();
                    if (cs != null)
                    {
                        int layerCount = cs.LayerCount;
                        for (int i = 0; i < layerCount; i++)
                        {
                            cs.SetMaterialId(i, matGach100.Id);
                        }
                        wt100.SetCompoundStructure(cs);
                    }
                }

                // Also update Coarse Scale Fill Pattern on wt100
                if (fpeAnsi31 != null)
                {
                    var pCoarse = wt100.LookupParameter("Coarse Scale Fill Pattern");
                    if (pCoarse != null && !pCoarse.IsReadOnly)
                    {
                        pCoarse.Set(fpeAnsi31.Id);
                    }
                }

                txMat.Commit();
            }

            // ---------------------------------------------------------------
            // 3. LEVELS & SYMBOLS FOR 2 WALLS AND DOOR D5
            // ---------------------------------------------------------------
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // Door Symbol D5_800x2200
            var allDoorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol symD5 = allDoorSymbols.FirstOrDefault(s => s.Name == "D5_800x2200")
                              ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 1671711);

            if (symD5 == null)
            {
                var baseSym = allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("EROWINDOW", StringComparison.OrdinalIgnoreCase))
                           ?? allDoorSymbols.FirstOrDefault();
                if (baseSym != null)
                {
                    using (var txSym = new Transaction(doc, "Prepare D5"))
                    {
                        txSym.Start();
                        symD5 = baseSym.Duplicate("D5_800x2200") as FamilySymbol;
                        symD5.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.Set(0.800 * M2FT);
                        symD5.get_Parameter(BuiltInParameter.DOOR_HEIGHT)?.Set(2.200 * M2FT);
                        symD5.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.Set("D5");
                        if (!symD5.IsActive) symD5.Activate();
                        txSym.Commit();
                    }
                }
            }
            if (symD5 != null && !symD5.IsActive)
            {
                using (var txAct = new Transaction(doc, "Activate D5"))
                {
                    txAct.Start();
                    symD5.Activate();
                    txAct.Commit();
                }
            }

            // ---------------------------------------------------------------
            // 4. CREATE THE 2 WALLS AND DOOR D5
            // ---------------------------------------------------------------
            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            Wall wallDoc = null;
            Wall wallNgang = null;
            FamilyInstance doorInst = null;
            var createdWalls = new List<object>();
            var selIds = new List<ElementId>();

            using (var txWall = new Transaction(doc, "Create 2 Walls and Door D5"))
            {
                txWall.Start();
                var opt = txWall.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new TwoWallsWarningSwallower());
                txWall.SetFailureHandlingOptions(opt);

                // Wall 1: Tường dọc 200mm dọc X = 34.550m từ Y = 0.100m đến Y = 5.400m
                var p1Start = new XYZ(34.550 * M2FT, 0.100 * M2FT, lvlTang1.Elevation);
                var p1End = new XYZ(34.550 * M2FT, 5.400 * M2FT, lvlTang1.Elevation);
                var line1 = Line.CreateBound(p1Start, p1End);
                wallDoc = Wall.Create(doc, line1, wt200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    wallDoc.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    wallDoc.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }
                selIds.Add(wallDoc.Id);
                createdWalls.Add(new
                {
                    name = "Tường dọc ngăn WC Khuyết tật",
                    id = wallDoc.Id.Value,
                    type = wt200.Name,
                    start = new { x = 34.550, y = 0.100 },
                    end = new { x = 34.550, y = 5.400 },
                    lengthM = line1.Length * FT2M
                });

                // Wall 2: Vách ngang 100mm chứa cửa D5 dọc Y = 3.450m từ X = 34.550m đến X = 37.100m
                var p2Start = new XYZ(34.550 * M2FT, 3.450 * M2FT, lvlTang1.Elevation);
                var p2End = new XYZ(37.100 * M2FT, 3.450 * M2FT, lvlTang1.Elevation);
                var line2 = Line.CreateBound(p2Start, p2End);
                wallNgang = Wall.Create(doc, line2, wt100.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    wallNgang.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    wallNgang.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }
                selIds.Add(wallNgang.Id);
                createdWalls.Add(new
                {
                    name = "Vách ngang cửa D5",
                    id = wallNgang.Id.Value,
                    type = wt100.Name,
                    start = new { x = 34.550, y = 3.450 },
                    end = new { x = 37.100, y = 3.450 },
                    lengthM = line2.Length * FT2M
                });

                doc.Regenerate();

                // Place Door D5 on Wall 2 at X = 35.150m, Y = 3.450m
                if (wallNgang != null && symD5 != null)
                {
                    var doorPt = new XYZ(35.150 * M2FT, 3.450 * M2FT, lvlTang1.Elevation);
                    doorInst = doc.Create.NewFamilyInstance(doorPt, symD5, wallNgang, lvlTang1, StructuralType.NonStructural);

                    doorInst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("D5");

                    // Door swing: swings south into WC Khuyết tật (-Y direction)
                    // Hinge at West (left, X = 34.750)
                    var facing = doorInst.FacingOrientation;
                    if (facing.Y > 0)
                    {
                        doorInst.flipFacing();
                    }

                    var hand = doorInst.HandOrientation;
                    if (hand.X > 0)
                    {
                        doorInst.flipHand();
                    }

                    selIds.Add(doorInst.Id);
                }

                txWall.Commit();
            }

            // ---------------------------------------------------------------
            // 5. HIGHLIGHT & EXPORT VERIFICATION IMAGES
            // ---------------------------------------------------------------
            try
            {
                uidoc.Selection.SetElementIds(selIds);
            }
            catch { }

            // Focus view on WC Khuyet Tat
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(32.5 * M2FT, 0.0 * M2FT, 0.0);
                XYZ pMax = new XYZ(38.5 * M2FT, 6.2 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            string outImgPath = "C:\\\\Users\\\\nguyenbuu.DESKTOP-TOEFTR1\\\\.gemini\\\\antigravity\\\\brain\\\\16005848-1987-4ccc-a037-b18d9e878697\\\\revit_2walls_d5_ansi31_result.png";
            if (File.Exists(outImgPath)) { try { File.Delete(outImgPath); } catch { } }

            try
            {
                var expOpt = new ImageExportOptions
                {
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2500
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                hatchUpdated = new
                {
                    patternName = fpeAnsi31?.Name,
                    wallType = wt100.Name
                },
                createdWalls = createdWalls,
                door = doorInst != null ? new
                {
                    id = doorInst.Id.Value,
                    mark = "D5",
                    x = 35.150,
                    y = 3.450,
                    widthMm = 800,
                    heightMm = 2200
                } : null,
                exportImage = outImgPath
            };
        }
    }
}
