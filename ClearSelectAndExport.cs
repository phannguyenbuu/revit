using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ClearSelectAndExport
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            uidoc.Selection.SetElementIds(new List<ElementId>());

            string outPathNoCad = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\d1_pure_revit_unselected.png";
            if (File.Exists(outPathNoCad)) File.Delete(outPathNoCad);

            var cadLinks = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .Where(i => !i.IsHidden(view))
                .Select(i => i.Id)
                .ToList();

            using (var t = new Transaction(doc, "Temp Hide CAD"))
            {
                t.Start();
                if (cadLinks.Count > 0) view.HideElements(cadLinks);
                doc.Regenerate();

                var opt = new ImageExportOptions
                {
                    FilePath = outPathNoCad,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2500
                };
                doc.ExportImage(opt);
                t.RollBack();
            }

            return new { success = true, image = outPathNoCad };
        }
    }
}
