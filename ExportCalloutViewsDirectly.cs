using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCalloutViewsDirectly
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var calloutIds = new List<(long id, string filename)>
            {
                (2409290L, "callout_view_thang1.png"),
                (2409302L, "callout_view_sanh_mat_tien.png"),
                (2409314L, "callout_view_thang2_and_wc.png"),
                (2409326L, "callout_view_tam_cap_and_wc_khuyet_tat.png")
            };

            var exported = new List<object>();

            foreach (var item in calloutIds)
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
                    exported.Add(new { id = item.id, name = v.Name, filePath });
                }
                catch (Exception ex)
                {
                    exported.Add(new { id = item.id, name = v.Name, error = ex.Message });
                }
            }

            return new { success = true, exported };
        }
    }
}
