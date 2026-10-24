using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class OptimizeAndExportCallouts
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var callouts = new List<(long id, string filename, string cleanTitle)>
            {
                (2409290L, "view_detail_thang1.png", "Cầu Thang 1"),
                (2409338L, "view_detail_thang2.png", "Cầu Thang 2"),
                (2409302L, "view_detail_sanh_chinh.png", "Sảnh Chính Mặt Tiền"),
                (2409314L, "view_detail_wc_nam_nu.png", "Khu Vệ Sinh Nam Nữ"),
                (2409326L, "view_detail_tam_cap_wc_khuyet_tat.png", "Tam Cấp & WC Khuyết Tật")
            };

            using (var tx = new Transaction(doc, "Enable Annotation Crop on Callouts"))
            {
                tx.Start();
                foreach (var item in callouts)
                {
                    var v = doc.GetElement(new ElementId(item.id)) as View;
                    if (v == null) continue;

                    v.CropBoxActive = true;
                    v.CropBoxVisible = false; // Hide crop box boundary lines on callout view for clean print

                    // Enable Annotation Crop
                    var pAnnoCrop = v.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE);
                    if (pAnnoCrop != null && !pAnnoCrop.IsReadOnly)
                    {
                        pAnnoCrop.Set(1);
                    }
                }
                tx.Commit();
            }

            var results = new List<object>();

            foreach (var item in callouts)
            {
                var v = doc.GetElement(new ElementId(item.id)) as View;
                if (v == null) continue;

                string filePath = Path.Combine(outDir, item.filename);

                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = filePath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { v.Id });

                try
                {
                    doc.ExportImage(opt);
                    results.Add(new { id = item.id, name = v.Name, filePath });
                }
                catch (Exception ex)
                {
                    results.Add(new { id = item.id, error = ex.Message });
                }
            }

            return new { success = true, results };
        }
    }
}
