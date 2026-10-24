using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportD1PureRevit
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            // Zoom closely to door D1: X in [-1, 2.5], Y in [4.5, 8.5] in meters
            // In feet: X in [-3.28, 8.2], Y in [14.7, 27.9]
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
            if (uiview != null)
            {
                var minPt = new XYZ(-1.0 * 3.28084, 4.5 * 3.28084, 0.0);
                var maxPt = new XYZ(2.5 * 3.28084, 8.5 * 3.28084, 0.0);
                uiview.ZoomAndCenterRectangle(minPt, maxPt);
            }

            uidoc.Selection.SetElementIds(new System.Collections.Generic.List<ElementId>());

            string outPathNoCad = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\d1_pure_revit.png";
            string outPathWithCad = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\d1_with_cad.png";

            // First export with CAD
            ExportView(doc, outPathWithCad);

            // Hide CAD links temporarily in transaction and export
            var cadLinks = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .Where(i => !i.IsHidden(view))
                .Select(i => i.Id)
                .ToList();

            using (var t = new Transaction(doc, "Temp Hide CAD for Export"))
            {
                t.Start();
                if (cadLinks.Count > 0)
                {
                    view.HideElements(cadLinks);
                }
                doc.Regenerate();

                ExportView(doc, outPathNoCad);

                // Rollback so we don't permanently hide CAD
                t.RollBack();
            }

            return new
            {
                success = true,
                withCad = outPathWithCad,
                noCad = outPathNoCad
            };
        }

        private static void ExportView(Document doc, string filePath)
        {
            if (File.Exists(filePath)) File.Delete(filePath);
            var opt = new ImageExportOptions
            {
                FilePath = filePath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2500
            };
            doc.ExportImage(opt);
        }
    }
}
