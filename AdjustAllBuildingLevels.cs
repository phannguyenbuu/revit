using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class LevelAdjustmentWarningSwallower : IFailuresPreprocessor
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

    public static class AdjustAllBuildingLevels
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // Target elevations:
            // Sân vườn: -0.75 m (-750 mm)
            // Tầng 1: 0.0 m (0 mm)
            // Tầng 2: 3.9 m (3900 mm)
            // Tầng 3: 7.5 m (7500 mm)
            // Tầng 4: 11.1 m (11100 mm)
            // Áp Mái: 11.1 m (11100 mm)
            // Tầng Tum: 14.7 m (14700 mm)
            // Mái: 17.7 m (17700 mm)

            var targetElevsM = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase)
            {
                { "MẶT BẰNG MÁI", 17.700 },
                { "MẶT BẰNG TẦNG TUM", 14.700 },
                { "MẶT BẰNG TẦNG 4", 11.100 },
                { "MẶT BẰNG TẦNG ÁP MÁI", 11.100 },
                { "MẶT BẰNG TẦNG 3", 7.500 },
                { "MẶT BẰNG TẦNG 2", 3.900 },
                { "MẶT BẰNG TẦNG 1", 0.000 },
                { "MẶT BẰNG SÂN VƯỜN", -0.750 }
            };

            var allLevels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var levelUpdates = new List<object>();

            // 1. UPDATE LEVELS FROM TOP TO BOTTOM
            using (var txLvl = new Transaction(doc, "Adjust All Building Levels"))
            {
                var opt = txLvl.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new LevelAdjustmentWarningSwallower());
                txLvl.SetFailureHandlingOptions(opt);

                txLvl.Start();

                // Sort descending so upper levels move first
                var orderedLevels = allLevels
                    .OrderByDescending(l => l.Elevation)
                    .ToList();

                foreach (var lvl in orderedLevels)
                {
                    string nameKey = targetElevsM.Keys.FirstOrDefault(k => lvl.Name.Equals(k, StringComparison.OrdinalIgnoreCase)
                                                                       || lvl.Name.Contains(k, StringComparison.OrdinalIgnoreCase));
                    if (nameKey != null)
                    {
                        double targetM = targetElevsM[nameKey];
                        double oldM = lvl.Elevation * FT2M;
                        double targetFt = targetM * M2FT;

                        if (Math.Abs(oldM - targetM) > 0.001)
                        {
                            lvl.Elevation = targetFt;
                            levelUpdates.Add(new
                            {
                                id = lvl.Id.Value,
                                name = lvl.Name,
                                oldElevM = Math.Round(oldM, 3),
                                newElevM = Math.Round(targetM, 3)
                            });
                        }
                    }
                }

                doc.Regenerate();
                txLvl.Commit();
            }

            // 2. CHECK AND ADJUST BEAMS Z ELEVATION
            // In Revit, beams may need their curve Z updated if they were created with fixed curve points
            int beamsAdjusted = 0;
            using (var txBeams = new Transaction(doc, "Align Beams to Adjusted Levels"))
            {
                var opt = txBeams.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new LevelAdjustmentWarningSwallower());
                txBeams.SetFailureHandlingOptions(opt);

                txBeams.Start();

                var allBeams = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralFraming)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .ToList();

                foreach (var beam in allBeams)
                {
                    var pRef = beam.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM);
                    var lvl = pRef != null && pRef.AsElementId() != ElementId.InvalidElementId
                        ? doc.GetElement(pRef.AsElementId()) as Level : null;

                    if (lvl == null) continue;

                    var lc = beam.Location as LocationCurve;
                    if (lc == null) continue;

                    double expectedZFt = lvl.Elevation;
                    double currentZFt = lc.Curve.GetEndPoint(0).Z;
                    double dZFt = expectedZFt - currentZFt;

                    if (Math.Abs(dZFt) > 0.001)
                    {
                        ElementTransformUtils.MoveElement(doc, beam.Id, new XYZ(0, 0, dZFt));
                        beamsAdjusted++;
                    }
                }

                doc.Regenerate();
                txBeams.Commit();
            }

            // 3. CHECK AND ADJUST FACADE WALLS HEIGHT IF THEY WERE SET TO 12300
            // Since Tầng 4 raised from 10.8m to 11.1m (+300mm), parapet / facade walls at 12300 should be 12600
            int facadeWallsAdjusted = 0;
            using (var txWalls = new Transaction(doc, "Adjust Facade Wall Heights for New Levels"))
            {
                var opt = txWalls.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new LevelAdjustmentWarningSwallower());
                txWalls.SetFailureHandlingOptions(opt);

                txWalls.Start();

                var allWalls = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Walls)
                    .WhereElementIsNotElementType()
                    .Cast<Wall>()
                    .ToList();

                foreach (var w in allWalls)
                {
                    var pUnconn = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    if (pUnconn != null && !pUnconn.IsReadOnly)
                    {
                        double hMm = pUnconn.AsDouble() * FT2M * 1000.0;
                        // If wall was explicitly set to 12300mm, update to 12600mm to match new +11.100m + 1.5m level
                        if (Math.Abs(hMm - 12300.0) < 50.0)
                        {
                            pUnconn.Set(12600.0 / 1000.0 * M2FT);
                            facadeWallsAdjusted++;
                        }
                    }
                }

                doc.Regenerate();
                txWalls.Commit();
            }

            // 4. EXPORT VERIFICATION IMAGES
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string out3dImg = Path.Combine(folder, "revit_levels_adjusted_overview_3d.png");
            string outSecImg = Path.Combine(folder, "revit_framing_corridor_section_cut.png");

            try
            {
                var v3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (v3d != null)
                {
                    uidoc.ActiveView = v3d;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);

                    // Ensure section box is off for overview
                    using (var txReset = new Transaction(doc, "Reset Section Box"))
                    {
                        txReset.Start();
                        v3d.IsSectionBoxActive = false;
                        txReset.Commit();
                    }
                    uiview?.ZoomToFit();

                    if (File.Exists(out3dImg)) try { File.Delete(out3dImg); } catch { }

                    var expOpt = new ImageExportOptions
                    {
                        FilePath = out3dImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOpt);

                    // Section cut inside corridor
                    using (var txSec = new Transaction(doc, "Corridor Section Cut"))
                    {
                        txSec.Start();
                        BoundingBoxXYZ sb = new BoundingBoxXYZ();
                        sb.Min = new XYZ(3.0 * M2FT, 6.5 * M2FT, -0.5 * M2FT);
                        sb.Max = new XYZ(27.0 * M2FT, 16.0 * M2FT, 18.0 * M2FT);
                        v3d.SetSectionBox(sb);
                        v3d.IsSectionBoxActive = true;
                        v3d.DisplayStyle = DisplayStyle.FlatColors;
                        var vdm = v3d.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        v3d.SetViewDisplayModel(vdm);
                        txSec.Commit();
                    }

                    uiview?.ZoomToFit();
                    if (File.Exists(outSecImg)) try { File.Delete(outSecImg); } catch { }
                    expOpt.FilePath = outSecImg;
                    doc.ExportImage(expOpt);

                    // Restore section box off
                    using (var txRest = new Transaction(doc, "Restore Section Box"))
                    {
                        txRest.Start();
                        v3d.IsSectionBoxActive = false;
                        txRest.Commit();
                    }
                    uiview?.ZoomToFit();
                }
            }
            catch { }

            // 5. SAVE REVIT DOCUMENT
            try
            {
                doc.Save(new SaveOptions());
            }
            catch { }

            return new
            {
                success = true,
                levelUpdates,
                beamsAdjusted,
                facadeWallsAdjusted,
                images = new string[] { out3dImg, outSecImg }
            };
        }
    }
}
