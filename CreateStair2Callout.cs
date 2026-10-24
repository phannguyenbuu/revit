using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateStair2Callout
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

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No active ViewPlan" };

            // Find FloorPlan ViewFamilyType
            var floorPlanVft = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .FirstOrDefault(vft => vft.ViewFamily == ViewFamily.FloorPlan);

            if (floorPlanVft == null) return new { error = "No FloorPlan VFT" };

            // Polyline 4C7E37 coordinates from AutoCAD selection:
            // X: 28784.245 to 33999.992 mm
            // Y: 7131.311 to 15617.656 mm
            double minX = 28784.245 * MM_TO_FT;
            double minY = 7131.311 * MM_TO_FT;
            double maxX = 33999.992 * MM_TO_FT;
            double maxY = 15617.656 * MM_TO_FT;

            XYZ p1 = new XYZ(minX, minY, 0);
            XYZ p2 = new XYZ(maxX, maxY, 0);

            long createdId = -1;
            string createdName = "";

            using (var tx = new Transaction(doc, "Create Callout Cau Thang 2"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(opts);
                tx.Start();

                // Rename previous callout 2409314 if needed to WC Nam & Nu
                var prevWcCallout = doc.GetElement(new ElementId(2409314L)) as View;
                if (prevWcCallout != null)
                {
                    try { prevWcCallout.Name = "MẶT BẰNG CHI TIẾT KHU VỆ SINH (WC NAM & NỮ)"; } catch { }
                }

                // Delete any existing view with exact name "MẶT BẰNG CHI TIẾT CẦU THANG 2"
                string desiredName = "MẶT BẰNG CHI TIẾT CẦU THANG 2";
                var oldView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View))
                    .Cast<View>()
                    .FirstOrDefault(v => v.Name.Equals(desiredName, StringComparison.OrdinalIgnoreCase));

                if (oldView != null && oldView.Id.Value != 2127444L) // protect original project sheet/view
                {
                    try { doc.Delete(oldView.Id); } catch { }
                }

                var calloutView = ViewSection.CreateCallout(doc, view.Id, floorPlanVft.Id, p1, p2);
                if (calloutView != null)
                {
                    createdId = calloutView.Id.Value;
                    string actualName = desiredName;
                    int suffix = 1;
                    while (new FilteredElementCollector(doc).OfClass(typeof(View)).Cast<View>().Any(v => v.Name.Equals(actualName, StringComparison.OrdinalIgnoreCase)))
                    {
                        actualName = $"{desiredName} ({suffix++})";
                    }
                    try { calloutView.Name = actualName; } catch { }
                    try { calloutView.Scale = 50; } catch { }
                    createdName = calloutView.Name;
                }

                tx.Commit();
            }

            // Export images
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

            // 1. Zoom Stair 2 callout area
            if (uiview != null)
            {
                XYZ z1 = new XYZ(26000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0);
                XYZ z2 = new XYZ(36000.0 * MM_TO_FT, 17500.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(z1, z2);
            }
            string imgThang2 = Path.Combine(outDir, "revit_callout_thang2_close.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgThang2,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 2. Zoom entire East group (Thang 2, WC, Tam cap)
            if (uiview != null)
            {
                XYZ z3 = new XYZ(26000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                XYZ z4 = new XYZ(40000.0 * MM_TO_FT, 17500.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(z3, z4);
            }
            string imgEastGroup = Path.Combine(outDir, "revit_callout_east_group_all.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgEastGroup,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 3. Full floor plan overview
            if (uiview != null)
            {
                XYZ z5 = new XYZ(-12000.0 * MM_TO_FT, -6000.0 * MM_TO_FT, 0);
                XYZ z6 = new XYZ(46000.0 * MM_TO_FT, 21000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(z5, z6);
            }
            string imgFull = Path.Combine(outDir, "revit_full_tang1_all_callouts_final.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgFull,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            });

            // 4. Export callout view of Stair 2 directly
            string imgStair2View = Path.Combine(outDir, "callout_view_thang2_actual.png");
            if (createdId > 0)
            {
                var opt = new ImageExportOptions {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = imgStair2View,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { new ElementId(createdId) });
                try { doc.ExportImage(opt); } catch { }
            }

            return new {
                success = true,
                createdId,
                createdName,
                images = new { imgThang2, imgEastGroup, imgFull, imgStair2View }
            };
        }
    }
}
