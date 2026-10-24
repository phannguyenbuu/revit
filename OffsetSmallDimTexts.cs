using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class OffsetSmallDimTexts
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        private class MovedText
        {
            public double X { get; set; }
            public double Y { get; set; }
            public bool IsUp { get; set; }
            public int Level { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Find all horizontal dimensions in the view
            var hDims = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .Where(d => {
                    var c = d.Curve;
                    if (c == null) return false;
                    XYZ dir = XYZ.BasisX;
                    if (c.IsBound) dir = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize();
                    else if (c is Line l) dir = l.Direction;
                    return Math.Abs(Math.Abs(dir.X) - 1.0) < 0.1;
                })
                .ToList();

            var results = new List<object>();

            using (var tx = new Transaction(doc, "Offset Small Dim Texts Up and Down"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);
                tx.Start();

                foreach (var dim in hDims)
                {
                    if (dim.Segments == null || dim.Segments.Size <= 1) continue;

                    // Dimension Y line
                    double dimY = 0;
                    if (dim.Curve is Line l) dimY = l.Origin.Y * FT_TO_MM;
                    else if (dim.Curve != null && dim.Curve.IsBound) dimY = dim.Curve.GetEndPoint(0).Y * FT_TO_MM;

                    // Reset all text positions first for clean calculation
                    foreach (DimensionSegment s in dim.Segments)
                    {
                        try { s.ResetTextPosition(); } catch { }
                    }

                    var movedHistory = new List<MovedText>();
                    int adjustedThisDim = 0;

                    foreach (DimensionSegment seg in dim.Segments)
                    {
                        double valMm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 0) : 0;
                        if (valMm > 250) continue; // Only small values: 100, 200 (or <= 250)

                        if (!seg.IsTextPositionAdjustable()) continue;

                        var origPos = seg.TextPosition;
                        if (origPos == null) continue;

                        double origX = origPos.X * FT_TO_MM;

                        // Check recent moved texts within 800mm
                        var nearby = movedHistory
                            .Where(m => Math.Abs(m.X - origX) < 800.0)
                            .OrderByDescending(m => m.X)
                            .ToList();

                        bool goUp = true;
                        int level = 1;

                        if (nearby.Count > 0)
                        {
                            var last = nearby.First();
                            goUp = !last.IsUp; // Alternate up and down!

                            // If there is already another one on the same side nearby within 450mm, increase level
                            var sameSideNearby = nearby.Where(m => m.IsUp == goUp && Math.Abs(m.X - origX) < 450.0).ToList();
                            if (sameSideNearby.Count > 0)
                            {
                                level = sameSideNearby.Max(m => m.Level) + 1;
                            }
                        }

                        // Determine offset in mm
                        // Level 1: 500mm, Level 2: 800mm, Level 3: 1100mm
                        double baseOffset = (level == 1) ? 500.0 : (level == 2 ? 800.0 : 1100.0);
                        double offsetMm = goUp ? baseOffset : -baseOffset;

                        XYZ newPos = new XYZ(origPos.X, (dimY + offsetMm) * MM_TO_FT, origPos.Z);
                        try
                        {
                            seg.TextPosition = newPos;
                            movedHistory.Add(new MovedText {
                                X = origX,
                                Y = dimY + offsetMm,
                                IsUp = goUp,
                                Level = level
                            });
                            adjustedThisDim++;
                        }
                        catch { }
                    }

                    results.Add(new {
                        dimId = dim.Id.Value,
                        y = Math.Round(dimY, 0),
                        totalSegs = dim.Segments.Size,
                        adjustedCount = adjustedThisDim
                    });
                }

                tx.Commit();
            }

            // Export verification images
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

            // 1. Zoom Band AB
            if (uiview != null)
            {
                XYZ p1 = new XYZ(-1000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                XYZ p2 = new XYZ(39000.0 * MM_TO_FT, 6000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }
            string imgAB = Path.Combine(outDir, "revit_zoom_band_ab_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgAB,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 2. Zoom Band CD with Stairs
            if (uiview != null)
            {
                XYZ p3 = new XYZ(-1000.0 * MM_TO_FT, 7000.0 * MM_TO_FT, 0);
                XYZ p4 = new XYZ(39000.0 * MM_TO_FT, 15000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p3, p4);
            }
            string imgCD = Path.Combine(outDir, "revit_zoom_band_cd_stairs_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgCD,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 3. Zoom South Facade Detail (-1200)
            if (uiview != null)
            {
                XYZ p5 = new XYZ(-1000.0 * MM_TO_FT, -3500.0 * MM_TO_FT, 0);
                XYZ p6 = new XYZ(39000.0 * MM_TO_FT, 2000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p5, p6);
            }
            string imgSouth = Path.Combine(outDir, "revit_zoom_south_facade_refined_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgSouth,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 4. Zoom North Facade Detail (16000)
            if (uiview != null)
            {
                XYZ p7 = new XYZ(-1000.0 * MM_TO_FT, 12500.0 * MM_TO_FT, 0);
                XYZ p8 = new XYZ(39000.0 * MM_TO_FT, 18500.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p7, p8);
            }
            string imgNorth = Path.Combine(outDir, "revit_zoom_north_facade_refined_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgNorth,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 5. Full floor plan overview
            if (uiview != null)
            {
                XYZ p9 = new XYZ(-12000.0 * MM_TO_FT, -6000.0 * MM_TO_FT, 0);
                XYZ p10 = new XYZ(46000.0 * MM_TO_FT, 21000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p9, p10);
            }
            string imgFull = Path.Combine(outDir, "revit_full_tang1_all_horizontal_and_exterior_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgFull,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            });

            return new {
                success = true,
                results,
                images = new { imgAB, imgCD, imgSouth, imgNorth, imgFull }
            };
        }
    }
}
