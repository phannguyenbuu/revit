using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class K2WarningSwallower : IFailuresPreprocessor
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

    public static class CreateWindowK2AndStack
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        private static Solid CreateBoxSolid(double minXMm, double maxXMm, double minYMm, double maxYMm, double minZMm, double maxZMm)
        {
            double minX = minXMm * MM2FT;
            double maxX = maxXMm * MM2FT;
            double minY = minYMm * MM2FT;
            double maxY = maxYMm * MM2FT;
            double minZ = minZMm * MM2FT;
            double maxZ = maxZMm * MM2FT;

            XYZ p0 = new XYZ(minX, minY, minZ);
            XYZ p1 = new XYZ(maxX, minY, minZ);
            XYZ p2 = new XYZ(maxX, minY, maxZ);
            XYZ p3 = new XYZ(minX, minY, maxZ);

            CurveLoop loop = new CurveLoop();
            loop.Append(Line.CreateBound(p0, p1));
            loop.Append(Line.CreateBound(p1, p2));
            loop.Append(Line.CreateBound(p2, p3));
            loop.Append(Line.CreateBound(p3, p0));

            double depth = maxY - minY;
            return GeometryCreationUtilities.CreateExtrusionGeometry(new List<CurveLoop> { loop }, XYZ.BasisY, depth);
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var app = uiapp.Application;
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active Revit doc" };

                List<string> logs = new List<string>();

                // -------------------------------------------------------------------------
                // 1. Create Window_K2.rfa
                // -------------------------------------------------------------------------
                string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
                if (!File.Exists(templatePath))
                {
                    return new { error = "Template not found: " + templatePath };
                }

                string famPath = @"D:\Dropbox\_Documents\RevitAI\Window_K2.rfa";
                if (File.Exists(famPath))
                {
                    try { File.Delete(famPath); } catch { }
                }

                Document famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Failed to create family document" };

                using (Transaction tx = new Transaction(famDoc, "Create Window_K2 Geometry"))
                {
                    tx.Start();

                    // Set category to OST_Windows
                    var winCat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows);
                    famDoc.OwnerFamily.FamilyCategory = winCat;
                    logs.Add("Family category set to Windows");

                    var glassSubCat = winCat.SubCategories.Cast<Category>().FirstOrDefault(c => c.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase));
                    var frameSubCat = winCat.SubCategories.Cast<Category>().FirstOrDefault(c => c.Name.Equals("Frame/Mullion", StringComparison.OrdinalIgnoreCase));

                    // 1. Glass Solid: X[-328.75, 328.75] Y[20.0, 30.0] Z[112.5, 1688.0]
                    Solid glassSolid = CreateBoxSolid(-328.75, 328.75, 20.0, 30.0, 112.5, 1688.0);
                    FreeFormElement glassFfe = FreeFormElement.Create(famDoc, glassSolid);
                    if (glassSubCat != null) glassFfe.Subcategory = glassSubCat;
                    logs.Add($"Glass FreeFormElement created (Volume={glassSolid.Volume:F4} ft3)");

                    // 2. Frame Solids (8 boxes from 3ds Max mesh):
                    var frameBoxes = new List<(double minX, double maxX, double minY, double maxY, double minZ, double maxZ, string name)>
                    {
                        (-396.0, 396.0, -50.0, 50.0, 1746.0, 1800.0, "Outer Top"),
                        (-396.0, 396.0, -50.0, 50.0, 0.0, 54.5, "Outer Bottom"),
                        (-450.0, -396.0, -50.0, 50.0, 0.0, 1800.0, "Outer Left Jamb"),
                        (396.0, 450.0, -50.0, 50.0, 0.0, 1800.0, "Outer Right Jamb"),
                        (-328.75, 328.75, 0.0, 50.0, 1688.0, 1746.0, "Inner Sash Top"),
                        (-328.75, 328.75, 0.0, 50.0, 54.5, 112.5, "Inner Sash Bottom"),
                        (-396.0, -328.75, 0.0, 50.0, 54.5, 1746.0, "Inner Sash Left"),
                        (328.75, 396.0, 0.0, 50.0, 54.5, 1746.0, "Inner Sash Right")
                    };

                    int frameCount = 0;
                    foreach (var fb in frameBoxes)
                    {
                        Solid fbSolid = CreateBoxSolid(fb.minX, fb.maxX, fb.minY, fb.maxY, fb.minZ, fb.maxZ);
                        FreeFormElement fbFfe = FreeFormElement.Create(famDoc, fbSolid);
                        if (frameSubCat != null) fbFfe.Subcategory = frameSubCat;
                        frameCount++;
                    }
                    logs.Add($"Created {frameCount} Frame FreeFormElements with subcategory Frame/Mullion");

                    tx.Commit();
                }

                famDoc.SaveAs(famPath);
                famDoc.Close(false);
                logs.Add($"Saved family to: {famPath}");

                // -------------------------------------------------------------------------
                // 2. Load Window_K2.rfa into active project doc
                // -------------------------------------------------------------------------
                Family famK2 = null;
                using (Transaction tx = new Transaction(doc, "Load Window_K2"))
                {
                    tx.Start();
                    doc.LoadFamily(famPath, new SimpleFamilyLoadOptions(), out famK2);
                    tx.Commit();
                }

                if (famK2 == null)
                {
                    // Check if already in doc
                    famK2 = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name == "Window_K2");
                }

                if (famK2 == null) return new { error = "Could not find loaded Window_K2 family" };

                FamilySymbol symK2 = null;
                foreach (ElementId sid in famK2.GetFamilySymbolIds())
                {
                    symK2 = doc.GetElement(sid) as FamilySymbol;
                    if (symK2 != null) break;
                }
                if (symK2 == null) return new { error = "No symbol found for Window_K2" };

                using (Transaction tx = new Transaction(doc, "Activate Window_K2 Symbol"))
                {
                    tx.Start();
                    if (!symK2.IsActive) symK2.Activate();
                    tx.Commit();
                }
                logs.Add($"Activated symbol: {symK2.Name}");

                // -------------------------------------------------------------------------
                // 3. Find Levels and WallTypes in project
                // -------------------------------------------------------------------------
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase) || l.Name.Contains("TRET", StringComparison.OrdinalIgnoreCase))
                            ?? levels.OrderBy(l => l.Elevation).First();
                var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
                var lvlTang3 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 3", StringComparison.OrdinalIgnoreCase));
                var lvlTang4 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 4", StringComparison.OrdinalIgnoreCase));

                var wt200 = new FilteredElementCollector(doc)
                    .OfClass(typeof(WallType))
                    .Cast<WallType>()
                    .FirstOrDefault(w => w.Name == "gach200_xay moi")
                    ?? new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().FirstOrDefault(w => w.Name.Contains("200"));

                if (wt200 == null) return new { error = "WallType 200mm not found" };

                // -------------------------------------------------------------------------
                // 4. Adjust existing walls on Truc 1 (X = 0.55m) to clear bay Y: [12.09375, 12.99375]
                // -------------------------------------------------------------------------
                double bayYMinM = 12.09375;
                double bayYMaxM = 12.99375;
                double truc1XM = 0.55;

                var createdCornerWalls = new List<long>();

                using (Transaction tx = new Transaction(doc, "Clear Truc 1 Bay and Add Corner Walls"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new K2WarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    // Find existing walls along X = 0.55 that extend through the bay
                    var truc1Walls = new FilteredElementCollector(doc)
                        .OfClass(typeof(Wall))
                        .Cast<Wall>()
                        .Where(w =>
                        {
                            var lc = (w.Location as LocationCurve)?.Curve;
                            if (lc == null) return false;
                            double p0x = Math.Round(lc.GetEndPoint(0).X * FT2M, 2);
                            double p1x = Math.Round(lc.GetEndPoint(1).X * FT2M, 2);
                            if (Math.Abs(p0x - truc1XM) > 0.05 || Math.Abs(p1x - truc1XM) > 0.05) return false;

                            double minY = Math.Min(lc.GetEndPoint(0).Y * FT2M, lc.GetEndPoint(1).Y * FT2M);
                            double maxY = Math.Max(lc.GetEndPoint(0).Y * FT2M, lc.GetEndPoint(1).Y * FT2M);
                            return minY < bayYMinM && maxY > bayYMaxM;
                        })
                        .ToList();

                    foreach (var wall in truc1Walls)
                    {
                        var lc = wall.Location as LocationCurve;
                        var curve = lc?.Curve;
                        if (curve == null) continue;

                        XYZ ep0 = curve.GetEndPoint(0);
                        XYZ ep1 = curve.GetEndPoint(1);

                        // Determine which end is near 0 and which is near 13.2
                        XYZ startPt = ep0.Y < ep1.Y ? ep0 : ep1;
                        XYZ endPt = ep0.Y < ep1.Y ? ep1 : ep0;

                        // Trim main wall to end at bayYMinM (12.09375m)
                        XYZ trimmedEndPt = new XYZ(startPt.X, bayYMinM * M2FT, startPt.Z);
                        lc.Curve = Line.CreateBound(startPt, trimmedEndPt);
                        logs.Add($"Trimmed wall {wall.Id.Value} to end at Y={bayYMinM}m");

                        // Create corner segment from bayYMaxM (12.99375m) to endPt (13.20m)
                        XYZ cornerStart = new XYZ(endPt.X, bayYMaxM * M2FT, endPt.Z);
                        if (endPt.Y > cornerStart.Y + 0.01)
                        {
                            Line cornerLine = Line.CreateBound(cornerStart, endPt);
                            Wall cornerWall = Wall.Create(doc, cornerLine, wall.WallType.Id, wall.LevelId, 3.60 * M2FT, 0.0, false, false);

                            // Copy height/top constraint from original wall
                            var topParam = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                            if (topParam != null && topParam.AsElementId() != ElementId.InvalidElementId)
                            {
                                cornerWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(topParam.AsElementId());
                                cornerWall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() ?? 0.0);
                            }
                            createdCornerWalls.Add(cornerWall.Id.Value);
                            logs.Add($"Created corner wall {cornerWall.Id.Value} from Y={bayYMaxM}m to Y={endPt.Y * FT2M:F3}m");
                        }
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------------------
                // 5. Draw 4 Stacked Walls in Revit
                // -------------------------------------------------------------------------
                var createdStackWalls = new List<long>();

                // Geometry: X = 0.55m, Y from 12.09375m to 12.99375m
                // Block 1: Z[0.0, 1.50m] (Height 1.50m, Offset 0.0m)
                // Block 2: Z[3.30m, 5.10m] (Height 1.80m, Offset 3.30m)
                // Block 3: Z[6.90m, 8.70m] (Height 1.80m, Offset 6.90m)
                // Block 4: Z[10.50m, 11.35m] (Height 0.85m, Offset 10.50m)

                var wallBlocks = new List<(double offsetM, double heightM, string name)>
                {
                    (0.00,  1.50, "Wall Block 1 (Z: 0.0 to 1.5m)"),
                    (3.30,  1.80, "Wall Block 2 (Z: 3.3 to 5.1m)"),
                    (6.90,  1.80, "Wall Block 3 (Z: 6.9 to 8.7m)"),
                    (10.50, 0.85, "Wall Block 4 (Z: 10.5 to 11.35m)")
                };

                using (Transaction tx = new Transaction(doc, "Draw 4 Stacked Walls 200mm"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new K2WarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    XYZ wp1 = new XYZ(truc1XM * M2FT, bayYMinM * M2FT, lvlTang1.Elevation);
                    XYZ wp2 = new XYZ(truc1XM * M2FT, bayYMaxM * M2FT, lvlTang1.Elevation);
                    Line wallLine = Line.CreateBound(wp1, wp2);

                    foreach (var wb in wallBlocks)
                    {
                        double baseOffsetFt = wb.offsetM * M2FT;
                        double heightFt = wb.heightM * M2FT;

                        Wall w = Wall.Create(doc, wallLine, wt200.Id, lvlTang1.Id, heightFt, baseOffsetFt, false, false);
                        // Ensure unconnected height
                        w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(ElementId.InvalidElementId);
                        w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.Set(heightFt);
                        w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.Set(baseOffsetFt);

                        createdStackWalls.Add(w.Id.Value);
                        logs.Add($"Created {wb.name}: Id={w.Id.Value}");
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------------------
                // 6. Place 3 Window_K2 Instances
                // -------------------------------------------------------------------------
                var createdWindowIds = new List<long>();
                double bayCenterYM = (bayYMinM + bayYMaxM) / 2.0; // 12.54375m

                // Window elevations:
                // Window 1: Base Z = 1.50m (top = 3.30m)
                // Window 2: Base Z = 5.10m (top = 6.90m)
                // Window 3: Base Z = 8.70m (top = 10.50m)
                var windowPlacements = new List<(double zM, string name)>
                {
                    (1.50, "Window K2 #1 (Z: 1.5 to 3.3m)"),
                    (5.10, "Window K2 #2 (Z: 5.1 to 6.9m)"),
                    (8.70, "Window K2 #3 (Z: 8.7 to 10.5m)")
                };

                using (Transaction tx = new Transaction(doc, "Place 3 Window_K2 Instances"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new K2WarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    foreach (var wp in windowPlacements)
                    {
                        XYZ loc = new XYZ(truc1XM * M2FT, bayCenterYM * M2FT, lvlTang1.Elevation + wp.zM * M2FT);
                        FamilyInstance inst = doc.Create.NewFamilyInstance(loc, symK2, lvlTang1, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);

                        // Rotate 90 degrees around Z axis through loc to align window width with Truc 1 (along Y)
                        Line rotAxis = Line.CreateBound(loc, new XYZ(loc.X, loc.Y, loc.Z + 10.0));
                        ElementTransformUtils.RotateElement(doc, inst.Id, rotAxis, Math.PI / 2.0);

                        // Set Mark to K2
                        inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("K2");

                        createdWindowIds.Add(inst.Id.Value);
                        logs.Add($"Placed {wp.name}: Id={inst.Id.Value} at Z={wp.zM}m");
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------------------
                // 7. Highlight and Export Visual Verification
                // -------------------------------------------------------------------------
                var allNewIds = createdStackWalls.Concat(createdWindowIds).Concat(createdCornerWalls).Select(id => new ElementId(id)).ToList();
                try
                {
                    uidoc.Selection.SetElementIds(allNewIds);
                }
                catch { }

                // Find 3D View
                var view3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                string out3DImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_stack_3d.jpg";
                string outCloseupImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_closeup.jpg";

                if (File.Exists(out3DImg)) try { File.Delete(out3DImg); } catch { }
                if (File.Exists(outCloseupImg)) try { File.Delete(outCloseupImg); } catch { }

                if (view3D != null)
                {
                    try
                    {
                        var expOpt = new ImageExportOptions
                        {
                            FilePath = out3DImg,
                            FitDirection = FitDirectionType.Horizontal,
                            HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                            ImageResolution = ImageResolution.DPI_300,
                            ExportRange = ExportRange.VisibleRegionOfCurrentView,
                            ZoomType = ZoomFitType.FitToPage,
                            PixelSize = 3000
                        };
                        doc.ExportImage(expOpt);
                    }
                    catch (Exception ex)
                    {
                        logs.Add("Export 3D image warning: " + ex.Message);
                    }
                }

                // Clear selection
                try { uidoc.Selection.SetElementIds(new List<ElementId>()); } catch { }

                return new
                {
                    success = true,
                    familyPath = famPath,
                    family = famK2.Name,
                    symbol = symK2.Name,
                    createdStackWalls,
                    createdWindowIds,
                    createdCornerWalls,
                    logs,
                    out3DImg
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
