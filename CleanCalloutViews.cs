using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CleanCalloutViews
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var calloutIds = new List<long> { 2409290L, 2409338L, 2409302L, 2409314L, 2409326L };

            using (var tx = new Transaction(doc, "Clean Callout Views Display"))
            {
                tx.Start();
                foreach (var id in calloutIds)
                {
                    var v = doc.GetElement(new ElementId(id)) as View;
                    if (v == null) continue;

                    v.CropBoxActive = true;
                    v.CropBoxVisible = false;

                    // Hide elevation and section markers
                    try { v.SetCategoryHidden(new ElementId(BuiltInCategory.OST_ElevationMarks), true); } catch { }
                    try { v.SetCategoryHidden(new ElementId(BuiltInCategory.OST_Sections), true); } catch { }
                    try { v.SetCategoryHidden(new ElementId(BuiltInCategory.OST_Callouts), true); } catch { }
                }
                tx.Commit();
            }

            // Export Stair 2 clean view
            var vStair2 = doc.GetElement(new ElementId(2409338L)) as View;
            string imgStair2Clean = Path.Combine(outDir, "view_detail_thang2_clean.png");
            if (vStair2 != null)
            {
                var opt = new ImageExportOptions {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = imgStair2Clean,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2000,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { vStair2.Id });
                try { doc.ExportImage(opt); } catch { }
            }

            // Export Sảnh Chính clean view
            var vSanh = doc.GetElement(new ElementId(2409302L)) as View;
            string imgSanhClean = Path.Combine(outDir, "view_detail_sanh_chinh_clean.png");
            if (vSanh != null)
            {
                var opt = new ImageExportOptions {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = imgSanhClean,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2000,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { vSanh.Id });
                try { doc.ExportImage(opt); } catch { }
            }

            return new { success = true, imgStair2Clean, imgSanhClean };
        }
    }
}
