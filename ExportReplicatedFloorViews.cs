using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportReplicatedFloorViews
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var viewsToExport = new List<(long id, string filename)>
            {
                (312L, "plan_tang_1_overview.png"),
                (695L, "plan_tang_2_overview.png"),
                (1727632L, "plan_tang_3_overview.png"),
                (2409349L, "plan_tang_4_overview.png"),
                (2411549L, "callout_thang1_tang2.png"),
                (2411573L, "callout_wc_tang2.png")
            };

            var exported = new List<object>();

            foreach (var item in viewsToExport)
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
                    PixelSize = 3000,
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
