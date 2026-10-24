using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ViewCuaThuyLuc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            // Find door 2363716
            var elem = doc.GetElement(new ElementId(2363716L));
            if (elem == null)
            {
                elem = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .FirstOrDefault(d => d.Symbol != null && d.Symbol.Family.Name.Contains("thuy luc"));
            }

            if (elem == null) return new { error = "No cua thuy luc instance found" };

            var bb = elem.get_BoundingBox(view);

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
            if (uiview != null && bb != null)
            {
                uiview.ZoomAndCenterRectangle(bb.Min - new XYZ(3, 3, 0), bb.Max + new XYZ(3, 3, 0));
            }

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\cua_thuy_luc_sample.png";
            if (File.Exists(outPath)) File.Delete(outPath);
            var opt = new ImageExportOptions
            {
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 1500
            };
            doc.ExportImage(opt);

            return new { success = true, id = elem.Id.Value, name = elem.Name, image = outPath };
        }
    }
}
