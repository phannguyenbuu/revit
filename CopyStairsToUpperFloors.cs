using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CopyStairsToUpperFloors
    {
        private const double M2FT = 3.2808398950131235;
        private static double M(double meters) => meters / 0.3048;
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Gather all levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            var level1 = levels.FirstOrDefault(l => l.Id.Value == 311) ?? levels.FirstOrDefault(l => Math.Abs(ToM(l.Elevation) - 0.0) < 0.1);
            var level2 = levels.FirstOrDefault(l => l.Id.Value == 694) ?? levels.FirstOrDefault(l => Math.Abs(ToM(l.Elevation) - 3.6) < 0.1);
            var level3 = levels.FirstOrDefault(l => l.Id.Value == 1727584) ?? levels.FirstOrDefault(l => Math.Abs(ToM(l.Elevation) - 7.2) < 0.1);
            var level4 = levels.FirstOrDefault(l => l.Id.Value == 2360634) ?? levels.FirstOrDefault(l => Math.Abs(ToM(l.Elevation) - 10.8) < 0.1);
            var levelTum = levels.FirstOrDefault(l => l.Id.Value == 2360635) ?? levels.FirstOrDefault(l => Math.Abs(ToM(l.Elevation) - 14.4) < 0.1);

            if (level1 == null || level2 == null || level3 == null || level4 == null || levelTum == null)
            {
                return new {
                    error = "Could not find all required levels (Tầng 1, 2, 3, 4, Tum)",
                    levels = levels.Select(l => new { id = l.Id.Value, name = l.Name, elev = ToM(l.Elevation) }).ToList()
                };
            }

            // 2. Identify base stairs at Tầng 1 (Z min near 0)
            var allStairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .ToList();

            Stairs stair1_Bay23 = null;
            Stairs stair2_Bay910 = null;
            var upperStairIdsToDelete = new List<ElementId>();

            foreach (var s in allStairs)
            {
                var bb = s.get_BoundingBox(null);
                if (bb == null) continue;

                double minZ = ToM(bb.Min.Z);
                double minX = ToM(bb.Min.X);

                if (minZ < 1.0) // Ground floor stairs
                {
                    if (minX < 15.0 && stair1_Bay23 == null)
                    {
                        stair1_Bay23 = s;
                    }
                    else if (minX >= 15.0 && stair2_Bay910 == null)
                    {
                        stair2_Bay910 = s;
                    }
                }
                else
                {
                    // Existing upper stairs from previous tests
                    upperStairIdsToDelete.Add(s.Id);
                }
            }

            if (stair1_Bay23 == null || stair2_Bay910 == null)
            {
                return new {
                    error = "Could not locate both base stairs at Tầng 1",
                    foundBay23 = stair1_Bay23 != null,
                    foundBay910 = stair2_Bay910 != null,
                    totalStairs = allStairs.Count
                };
            }

            // 3. Delete existing upper test stairs
            if (upperStairIdsToDelete.Count > 0)
            {
                using (Transaction t = new Transaction(doc, "Delete Existing Upper Stairs"))
                {
                    t.Start();
                    doc.Delete(upperStairIdsToDelete);
                    t.Commit();
                }
            }

            // 4. Define copy configurations for Tầng 2, Tầng 3, Tầng 4
            var floorsConfig = new[]
            {
                new { FloorName = "Tầng 2", DeltaZ_m = 3.6, BaseLevel = level2, TopLevel = level3, Comment = "STAIR_TANG2" },
                new { FloorName = "Tầng 3", DeltaZ_m = 7.2, BaseLevel = level3, TopLevel = level4, Comment = "STAIR_TANG3" },
                new { FloorName = "Tầng 4", DeltaZ_m = 10.8, BaseLevel = level4, TopLevel = levelTum, Comment = "STAIR_TANG4" }
            };

            var copiedResults = new List<object>();

            using (Transaction t = new Transaction(doc, "Copy Stairs to Upper Floors"))
            {
                var prep = new StairFailurePreprocessor();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                foreach (var cfg in floorsConfig)
                {
                    XYZ shift = new XYZ(0, 0, M(cfg.DeltaZ_m));

                    // Copy Stair 1 (Bay 2-3)
                    var c1 = ElementTransformUtils.CopyElement(doc, stair1_Bay23.Id, shift);
                    Stairs newS1 = null;
                    if (c1 != null && c1.Count > 0)
                    {
                        newS1 = doc.GetElement(c1.First()) as Stairs;
                        if (newS1 != null)
                        {
                            newS1.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)?.Set(cfg.BaseLevel.Id);
                            newS1.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)?.Set(cfg.TopLevel.Id);
                            newS1.get_Parameter(BuiltInParameter.STAIRS_BASE_OFFSET)?.Set(0.0);
                            newS1.get_Parameter(BuiltInParameter.STAIRS_TOP_OFFSET)?.Set(0.0);
                            newS1.LookupParameter("Comments")?.Set(cfg.Comment + "_BAY_2_3");
                        }
                    }

                    // Copy Stair 2 (Bay 9-10)
                    var c2 = ElementTransformUtils.CopyElement(doc, stair2_Bay910.Id, shift);
                    Stairs newS2 = null;
                    if (c2 != null && c2.Count > 0)
                    {
                        newS2 = doc.GetElement(c2.First()) as Stairs;
                        if (newS2 != null)
                        {
                            newS2.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)?.Set(cfg.BaseLevel.Id);
                            newS2.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)?.Set(cfg.TopLevel.Id);
                            newS2.get_Parameter(BuiltInParameter.STAIRS_BASE_OFFSET)?.Set(0.0);
                            newS2.get_Parameter(BuiltInParameter.STAIRS_TOP_OFFSET)?.Set(0.0);
                            newS2.LookupParameter("Comments")?.Set(cfg.Comment + "_BAY_9_10");
                        }
                    }

                    var bb1 = newS1?.get_BoundingBox(null);
                    var bb2 = newS2?.get_BoundingBox(null);

                    copiedResults.Add(new
                    {
                        floor = cfg.FloorName,
                        baseLevel = cfg.BaseLevel.Name,
                        topLevel = cfg.TopLevel.Name,
                        stairBay23 = new
                        {
                            id = newS1?.Id.Value,
                            minZ = bb1 != null ? Math.Round(ToM(bb1.Min.Z), 2) : 0,
                            maxZ = bb1 != null ? Math.Round(ToM(bb1.Max.Z), 2) : 0,
                            runsCount = newS1?.GetStairsRuns()?.Count ?? 0,
                            landingsCount = newS1?.GetStairsLandings()?.Count ?? 0
                        },
                        stairBay910 = new
                        {
                            id = newS2?.Id.Value,
                            minZ = bb2 != null ? Math.Round(ToM(bb2.Min.Z), 2) : 0,
                            maxZ = bb2 != null ? Math.Round(ToM(bb2.Max.Z), 2) : 0,
                            runsCount = newS2?.GetStairsRuns()?.Count ?? 0,
                            landingsCount = newS2?.GetStairsLandings()?.Count ?? 0
                        }
                    });
                }

                doc.Regenerate();
                t.Commit();
            }

            // 5. Ensure visibility and export images
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var exportedFiles = new List<string>();

            // 5a. 3D View Export
            var view3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name == "{3D}")
                ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

            if (view3d != null)
            {
                uidoc.ActiveView = view3d;
                var catStairs = new ElementId(BuiltInCategory.OST_Stairs);
                using (Transaction tv = new Transaction(doc, "Ensure 3D Stairs Visible"))
                {
                    tv.Start();
                    if (view3d.CanCategoryBeHidden(catStairs) && view3d.GetCategoryHidden(catStairs))
                    {
                        view3d.SetCategoryHidden(catStairs, false);
                    }
                    tv.Commit();
                }

                string img3dPath = Path.Combine(outDir, "revit_3d_all_stairs.jpg");
                try
                {
                    if (File.Exists(img3dPath)) File.Delete(img3dPath);
                    var opt3d = new ImageExportOptions
                    {
                        FilePath = img3dPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(opt3d);
                    exportedFiles.Add(img3dPath);
                }
                catch { }
            }

            // 5b. Export Floor Plans showing stairs (Tầng 2, 3, 4)
            var floorPlans = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                .ToList();

            var plansToExport = new[]
            {
                new { LevelName = "TẦNG 2", FileName = "plan_tang2_with_stairs.png" },
                new { LevelName = "TẦNG 3", FileName = "plan_tang3_with_stairs.png" },
                new { LevelName = "TẦNG 4", FileName = "plan_tang4_with_stairs.png" }
            };

            foreach (var item in plansToExport)
            {
                var vp = floorPlans.FirstOrDefault(p => p.Name.IndexOf(item.LevelName, StringComparison.OrdinalIgnoreCase) >= 0);
                if (vp != null)
                {
                    uidoc.ActiveView = vp;
                    string fpPath = Path.Combine(outDir, item.FileName);
                    try
                    {
                        if (File.Exists(fpPath)) File.Delete(fpPath);
                        var optFp = new ImageExportOptions
                        {
                            FilePath = fpPath,
                            FitDirection = FitDirectionType.Horizontal,
                            HLRandWFViewsFileType = ImageFileType.PNG,
                            ImageResolution = ImageResolution.DPI_300,
                            ExportRange = ExportRange.VisibleRegionOfCurrentView,
                            ZoomType = ZoomFitType.FitToPage,
                            PixelSize = 3000
                        };
                        doc.ExportImage(optFp);
                        exportedFiles.Add(fpPath);
                    }
                    catch { }
                }
            }

            // 6. Save document
            bool saved = false;
            try
            {
                doc.Save();
                saved = true;
            }
            catch { }

            return new
            {
                status = "SUCCESS",
                totalStairsNow = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Stairs).WhereElementIsNotElementType().GetElementCount(),
                copiedResults,
                exportedFiles,
                docSaved = saved
            };
        }
    }
}
