using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportAllCleanCalloutViews
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var callouts = new List<(long id, string filename)>
            {
                (2409290L, "clean_callout_thang1.png"),
                (2409338L, "clean_callout_thang2.png"),
                (2409302L, "clean_callout_sanh_chinh.png"),
                (2409314L, "clean_callout_wc_nam_nu.png"),
                (2409326L, "clean_callout_tam_cap_wc_khuyet_tat.png")
            };

            var list = new List<object>();

            foreach (var item in callouts)
            {
                var v = doc.GetElement(new ElementId(item.id)) as View;
                if (v == null) continue;

                string filePath = Path.Combine(outDir, item.filename);

                var opt = new ImageExportOptions {
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
                    list.Add(new { id = item.id, name = v.Name, filePath });
                }
                catch (Exception ex)
                {
                    list.Add(new { id = item.id, error = ex.Message });
                }
            }

            return new { success = true, list };
        }
    }
}
