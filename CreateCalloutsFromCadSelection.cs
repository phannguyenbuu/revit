using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateCalloutsFromCadSelection
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

        private class CadPolylineItem
        {
            public string handle { get; set; }
            public string name { get; set; }
            public string short_name { get; set; }
            public BBoxRvt bbox_rvt_mm { get; set; }
        }

        private class BBoxRvt
        {
            public List<double> min { get; set; }
            public List<double> max { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No active ViewPlan" };

            string jsonPath = @"D:\Dropbox\_Documents\RevitAI\scratch\cad_callout_polylines.json";
            if (!File.Exists(jsonPath)) return new { error = "File not found: " + jsonPath };

            string jsonText = File.ReadAllText(jsonPath);
            var cadItems = JsonSerializer.Deserialize<List<CadPolylineItem>>(jsonText);
            if (cadItems == null || cadItems.Count == 0) return new { error = "No items in JSON" };

            // Find FloorPlan ViewFamilyType
            var floorPlanVft = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .FirstOrDefault(vft => vft.ViewFamily == ViewFamily.FloorPlan);

            if (floorPlanVft == null) return new { error = "No FloorPlan VFT" };

            // Rename callout 1 if it exists
            var callout1 = doc.GetElement(new ElementId(2409290L)) as View;

            var createdCallouts = new List<object>();

            using (var tx = new Transaction(doc, "Create Callouts from AutoCAD Selection"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(opts);
                tx.Start();

                if (callout1 != null)
                {
                    try
                    {
                        callout1.Name = "MẶT BẰNG CHI TIẾT CẦU THANG 1";
                        callout1.Scale = 50;
                    }
                    catch { }
                }

                foreach (var item in cadItems)
                {
                    double minX = item.bbox_rvt_mm.min[0] * MM_TO_FT;
                    double minY = item.bbox_rvt_mm.min[1] * MM_TO_FT;
                    double maxX = item.bbox_rvt_mm.max[0] * MM_TO_FT;
                    double maxY = item.bbox_rvt_mm.max[1] * MM_TO_FT;

                    XYZ p1 = new XYZ(minX, minY, 0);
                    XYZ p2 = new XYZ(maxX, maxY, 0);

                    try
                    {
                        var calloutView = ViewSection.CreateCallout(doc, view.Id, floorPlanVft.Id, p1, p2);
                        if (calloutView != null)
                        {
                            // Unique name
                            string desiredName = item.name;
                            string actualName = desiredName;
                            int suffix = 1;
                            while (new FilteredElementCollector(doc).OfClass(typeof(View)).Cast<View>().Any(v => v.Name.Equals(actualName, StringComparison.OrdinalIgnoreCase)))
                            {
                                actualName = $"{desiredName} ({suffix++})";
                            }

                            try { calloutView.Name = actualName; } catch { }
                            try { calloutView.Scale = 50; } catch { }

                            createdCallouts.Add(new {
                                id = calloutView.Id.Value,
                                name = calloutView.Name,
                                scale = calloutView.Scale,
                                handle = item.handle,
                                role = item.short_name,
                                bbox_mm = item.bbox_rvt_mm
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        createdCallouts.Add(new {
                            handle = item.handle,
                            error = ex.Message
                        });
                    }
                }

                tx.Commit();
            }

            // Export images
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

            // 1. Zoom West Entrance (Sảnh Mặt Tiền)
            if (uiview != null)
            {
                XYZ z1 = new XYZ(-8000.0 * MM_TO_FT, 1000.0 * MM_TO_FT, 0);
                XYZ z2 = new XYZ(3000.0 * MM_TO_FT, 13000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(z1, z2);
            }
            string imgSanhMatTien = Path.Combine(outDir, "revit_callout_sanh_mat_tien.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgSanhMatTien,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 2. Zoom East Toilets & Stair 2 (2 Toilet & Thang 2)
            if (uiview != null)
            {
                XYZ z3 = new XYZ(30000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                XYZ z4 = new XYZ(40000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(z3, z4);
            }
            string imgHaiToilet = Path.Combine(outDir, "revit_callout_hai_toilet_and_thang2.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgHaiToilet,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 3. Full floor plan overview with all callouts
            if (uiview != null)
            {
                XYZ z5 = new XYZ(-12000.0 * MM_TO_FT, -6000.0 * MM_TO_FT, 0);
                XYZ z6 = new XYZ(46000.0 * MM_TO_FT, 21000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(z5, z6);
            }
            string imgFullCallouts = Path.Combine(outDir, "revit_full_tang1_all_callouts.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgFullCallouts,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            });

            return new {
                success = true,
                createdCallouts,
                images = new { imgSanhMatTien, imgHaiToilet, imgFullCallouts }
            };
        }
    }
}
