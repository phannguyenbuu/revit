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
    public static class CopyStairToBay910
    {
        private const double M2FT = 3.2808398950131235;
        private static double M(double meters) => meters / 0.3048;
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find source stair at bay 2-3
            var sourceStair = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .FirstOrDefault(s => s.Id.Value == 2368346)
                ?? new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Stairs)
                    .WhereElementIsNotElementType()
                    .Cast<Stairs>()
                    .FirstOrDefault();

            if (sourceStair == null)
                return new { error = "Source stair not found" };

            // Check if any stair already exists at bay 9-10 (X > 25m)
            var existing910 = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .FirstOrDefault(s => {
                    var bb = s.get_BoundingBox(null);
                    return bb != null && ToM(bb.Min.X) > 20.0;
                });

            if (existing910 != null)
            {
                using (Transaction t = new Transaction(doc, "Delete Existing Bay 9-10 Stair"))
                {
                    t.Start();
                    doc.Delete(existing910.Id);
                    t.Commit();
                }
            }

            double deltaX_m = 25.300;
            XYZ translation = new XYZ(M(deltaX_m), 0, 0);

            ElementId newStairsId = ElementId.InvalidElementId;
            string methodUsed = "";
            string copyError = null;

            // Method A: Try ElementTransformUtils.CopyElement
            try
            {
                using (Transaction t = new Transaction(doc, "Copy Stair to Bay 9-10"))
                {
                    var prep = new StairFailurePreprocessor();
                    var opt = t.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(prep);
                    t.SetFailureHandlingOptions(opt);

                    t.Start();
                    var copiedIds = ElementTransformUtils.CopyElement(doc, sourceStair.Id, translation);
                    if (copiedIds != null && copiedIds.Count > 0)
                    {
                        newStairsId = copiedIds.First();
                        methodUsed = "ElementTransformUtils.CopyElement";
                    }
                    t.Commit();
                }
            }
            catch (Exception ex)
            {
                copyError = ex.Message;
            }

            // Method B: If CopyElement didn't produce a valid stair, recreate via StairsEditScope
            if (newStairsId == ElementId.InvalidElementId || doc.GetElement(newStairsId) == null)
            {
                var prep = new StairFailurePreprocessor();
                try
                {
                    ElementId baseLevelId = sourceStair.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL)?.AsElementId();
                    ElementId topLevelId = sourceStair.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL)?.AsElementId();

                    Level baseLevel = (baseLevelId != null && baseLevelId != ElementId.InvalidElementId ? doc.GetElement(baseLevelId) as Level : null)
                        ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 1") || l.Name.Contains("TANG 1"));
                    Level topLevel = (topLevelId != null && topLevelId != ElementId.InvalidElementId ? doc.GetElement(topLevelId) as Level : null)
                        ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 2") || l.Name.Contains("TANG 2"));

                    StairsEditScope scope = new StairsEditScope(doc, "Create Stair Bay 9-10");
                    newStairsId = scope.Start(baseLevel.Id, topLevel.Id);

                    using (Transaction t = new Transaction(doc, "Add Runs and Landing 9-10"))
                    {
                        t.Start();
                        Stairs stairs = doc.GetElement(newStairsId) as Stairs;
                        stairs.ChangeTypeId(sourceStair.GetTypeId());
                        stairs.DesiredRisersNumber = 21;
                        stairs.ActualTreadDepth = M(0.300);
                        stairs.LookupParameter("Comments")?.Set("CAD_CONVERTED_BAY_9_10");

                        // Run 1: Center X = 5.1125 + 25.300 = 30.4125, Y from 10.100 to 13.100
                        XYZ pt1Start = new XYZ(M(30.4125), M(10.100), 0);
                        XYZ pt1End = new XYZ(M(30.4125), M(13.100), 0);
                        Line line1 = Line.CreateBound(pt1Start, pt1End);
                        StairsRun run1 = StairsRun.CreateStraightRun(doc, newStairsId, line1, StairsRunJustification.Center);
                        run1.ActualRunWidth = M(1.325);

                        double landingElev = run1.TopElevation;

                        // Run 2: Center X = 7.2875 + 25.300 = 32.5875, Y from 13.100 down to 10.100
                        XYZ pt2Start = new XYZ(M(32.5875), M(13.100), landingElev);
                        XYZ pt2End = new XYZ(M(32.5875), M(10.100), landingElev);
                        Line line2 = Line.CreateBound(pt2Start, pt2End);
                        StairsRun run2 = StairsRun.CreateStraightRun(doc, newStairsId, line2, StairsRunJustification.Center);
                        run2.ActualRunWidth = M(1.325);
                        run2.EndsWithRiser = false;

                        // Landing: X from 29.750 to 33.250, Y from 13.100 to 14.800
                        CurveLoop landingLoop = new CurveLoop();
                        XYZ p1 = new XYZ(M(29.750), M(13.100), landingElev);
                        XYZ p2 = new XYZ(M(29.750), M(14.800), landingElev);
                        XYZ p3 = new XYZ(M(33.250), M(14.800), landingElev);
                        XYZ p4 = new XYZ(M(33.250), M(13.100), landingElev);
                        landingLoop.Append(Line.CreateBound(p1, p2));
                        landingLoop.Append(Line.CreateBound(p2, p3));
                        landingLoop.Append(Line.CreateBound(p3, p4));
                        landingLoop.Append(Line.CreateBound(p4, p1));

                        StairsLanding landing = StairsLanding.CreateSketchedLanding(doc, newStairsId, landingLoop, landingElev);

                        t.Commit();
                    }

                    scope.Commit(prep);
                    methodUsed = "StairsEditScope (Fallback)";
                }
                catch (Exception ex)
                {
                    return new { error = "Both copy and recreate failed: " + ex.Message, copyError };
                }
            }

            // Verify newly created stair
            var finalStair = doc.GetElement(newStairsId) as Stairs;
            var runsCount = finalStair?.GetStairsRuns()?.Count ?? 0;
            var landingsCount = finalStair?.GetStairsLandings()?.Count ?? 0;

            // Also check railings hosted on the stair
            var railings = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StairsRailing)
                .WhereElementIsNotElementType()
                .Cast<Railing>()
                .Where(r => r.HostId == newStairsId)
                .Select(r => new { id = r.Id.Value, name = r.Name })
                .ToList();

            // Export verification images
            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"));

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang1_with_both_stairs.png");
            string stair910ImgPath = Path.Combine(folder, "stair_bay_9_10.png");

            if (plan != null)
            {
                uidoc.ActiveView = plan;
                uidoc.Selection.SetElementIds(new List<ElementId> { newStairsId });

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == plan.Id);

                // Bay 9-10 close-up: X in [29.0, 34.0], Y in [9.5, 15.6]
                uiview?.ZoomAndCenterRectangle(new XYZ((29.0 - 0.5) * M2FT, 9.5 * M2FT, 0.0), new XYZ((34.0 + 0.5) * M2FT, 15.6 * M2FT, 0.0));
                try
                {
                    if (File.Exists(stair910ImgPath)) File.Delete(stair910ImgPath);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = stair910ImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt);
                }
                catch { }

                // Full floor plan showing BOTH stairs (2-3 and 9-10)
                uidoc.Selection.SetElementIds(new List<ElementId>());
                uiview?.ZoomAndCenterRectangle(new XYZ(-5.0 * M2FT, -3.0 * M2FT, 0.0), new XYZ(42.0 * M2FT, 17.0 * M2FT, 0.0));
                try
                {
                    if (File.Exists(planImgPath)) File.Delete(planImgPath);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = planImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3500
                    };
                    doc.ExportImage(expOpt);
                }
                catch { }
            }

            return new {
                success = true,
                methodUsed,
                sourceStairsId = sourceStair.Id.Value,
                newStairsId = newStairsId.Value,
                actualRisers = finalStair?.ActualRisersNumber,
                runsCount,
                landingsCount,
                railingsCount = railings.Count,
                stair910Image = stair910ImgPath,
                fullPlanImage = planImgPath
            };
        }
    }
}
