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
    public class WallAWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failureMessages = failuresAccessor.GetFailureMessages();
            foreach (var msg in failureMessages)
            {
                if (msg.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(msg);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class CreateWallAWithDoors
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Get 200mm wall type
            var wallType200 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach200_xay moi" || w.Name == "gach200" || w.Name == "Tường 200");

            if (wallType200 == null)
                return new { error = "Wall type gach200_xay moi not found" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Prepare Door Symbols: D2 (1400x2200, 2-canh) and D4 (1000x2200, 1-canh)
            var allDoorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            // Find base symbol for D2 (2-canh)
            var baseD2 = allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("CỬA 2 CÁNH EROWINDOW", StringComparison.OrdinalIgnoreCase))
                      ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 1659089)
                      ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("2 CANH", StringComparison.OrdinalIgnoreCase));

            // Find base symbol for D4 (1-canh)
            var baseD4 = allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("CỬA 1 CÁNH EROWINDOW", StringComparison.OrdinalIgnoreCase))
                      ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 1671711)
                      ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 2075619)
                      ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("1 CANH", StringComparison.OrdinalIgnoreCase));

            FamilySymbol symD2 = null;
            FamilySymbol symD4 = null;

            using (var txPrep = new Transaction(doc, "AI Copilot: Prepare Door Types D2 & D4"))
            {
                txPrep.Start();
                var opt = txPrep.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WallAWarningSwallower());
                txPrep.SetFailureHandlingOptions(opt);

                // D2: 1400x2200mm
                symD2 = allDoorSymbols.FirstOrDefault(s => s.Name == "D2_1400x2200");
                if (symD2 == null && baseD2 != null)
                {
                    symD2 = baseD2.Duplicate("D2_1400x2200") as FamilySymbol;
                    var pW = symD2.get_Parameter(BuiltInParameter.DOOR_WIDTH);
                    var pH = symD2.get_Parameter(BuiltInParameter.DOOR_HEIGHT);
                    pW?.Set(1.400 * M2FT);
                    pH?.Set(2.200 * M2FT);
                }
                else if (symD2 == null)
                {
                    symD2 = baseD2;
                }

                // D4: 1000x2200mm
                symD4 = allDoorSymbols.FirstOrDefault(s => s.Name == "D4_1000x2200");
                if (symD4 == null && baseD4 != null)
                {
                    symD4 = baseD4.Duplicate("D4_1000x2200") as FamilySymbol;
                    var pW = symD4.get_Parameter(BuiltInParameter.DOOR_WIDTH);
                    var pH = symD4.get_Parameter(BuiltInParameter.DOOR_HEIGHT);
                    pW?.Set(1.000 * M2FT);
                    pH?.Set(2.200 * M2FT);
                }
                else if (symD4 == null)
                {
                    symD4 = baseD4;
                }

                if (symD2 != null && !symD2.IsActive) symD2.Activate();
                if (symD4 != null && !symD4.IsActive) symD4.Activate();

                txPrep.Commit();
            }

            if (symD2 == null || symD4 == null)
                return new { error = "Could not prepare D2 and D4 door symbols" };

            // 4. Create Wall on Grid A (Y = 5.400m) from Trục 1 (X = 0.550m) to Trục 10 (X = 33.350m)
            double yFt = 5.400 * M2FT;
            double xStartFt = 0.550 * M2FT;
            double xEndFt = 33.350 * M2FT;
            double zFt = lvlTang1.Elevation;

            XYZ pStart = new XYZ(xStartFt, yFt, zFt);
            XYZ pEnd = new XYZ(xEndFt, yFt, zFt);
            Line wallLine = Line.CreateBound(pStart, pEnd);

            Wall wallA = null;
            var createdDoors = new List<object>();

            using (var tx = new Transaction(doc, "AI Copilot: Create Wall A and 7 Doors"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WallAWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

                // Create Wall
                wallA = Wall.Create(doc, wallLine, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    wallA.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    wallA.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }
                doc.Regenerate();

                // 5. Door specifications:
                // 4 doors D2 (1400mm): X = 2.450, 6.650, 9.450, 13.850
                // 3 doors D4 (1000mm): X = 16.050, 23.150, 30.550
                var doorSpecs = new[]
                {
                    new { Type = "D2", Mark = "D2-1", CenterX = 2.450, Symbol = symD2 },
                    new { Type = "D2", Mark = "D2-2", CenterX = 6.650, Symbol = symD2 },
                    new { Type = "D2", Mark = "D2-3", CenterX = 9.450, Symbol = symD2 },
                    new { Type = "D2", Mark = "D2-4", CenterX = 13.850, Symbol = symD2 },
                    new { Type = "D4", Mark = "D4-1", CenterX = 16.050, Symbol = symD4 },
                    new { Type = "D4", Mark = "D4-2", CenterX = 23.150, Symbol = symD4 },
                    new { Type = "D4", Mark = "D4-3", CenterX = 30.550, Symbol = symD4 },
                };

                foreach (var ds in doorSpecs)
                {
                    XYZ doorPt = new XYZ(ds.CenterX * M2FT, yFt, zFt);
                    var doorInst = doc.Create.NewFamilyInstance(doorPt, ds.Symbol, wallA, lvlTang1, StructuralType.NonStructural);

                    // Set Mark
                    var pMark = doorInst.get_Parameter(BuiltInParameter.DOOR_NUMBER);
                    pMark?.Set(ds.Mark);

                    // Sill height = 0
                    var pSill = doorInst.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                    pSill?.Set(0.0);

                    // Ensure door faces North (+Y, into the room)
                    if (doorInst.FacingOrientation.Y < 0)
                    {
                        doorInst.flipFacing();
                    }

                    createdDoors.Add(new
                    {
                        id = doorInst.Id.Value,
                        type = ds.Type,
                        mark = ds.Mark,
                        symbol = ds.Symbol.Name,
                        family = ds.Symbol.FamilyName,
                        centerX = ds.CenterX,
                        y = 5.400
                    });
                }

                tx.Commit();
            }

            // 6. Export verification image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wall_a_doors_result.png";
            try
            {
                var activeView = uidoc.ActiveView;
                var expOpt = new ImageExportOptions
                {
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560,
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                wall = new
                {
                    id = wallA?.Id.Value,
                    lengthM = wallLine.Length * FT2M,
                    start = new { x = pStart.X * FT2M, y = pStart.Y * FT2M },
                    end = new { x = pEnd.X * FT2M, y = pEnd.Y * FT2M }
                },
                doorsCount = createdDoors.Count,
                doors = createdDoors,
                exportImage = outImgPath
            };
        }
    }
}
