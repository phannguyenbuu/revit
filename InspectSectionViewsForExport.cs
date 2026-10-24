using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSectionViewsForExport
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            var views = new List<View>();

            foreach (var id in selIds)
            {
                var v = doc.GetElement(id) as View;
                if (v != null && !v.IsTemplate) views.Add(v);
            }

            // Natural sort: 1-1, 2-2, 3-3, 4-4, 5-5
            views = views.OrderBy(v => v.Name).ToList();

            var viewInfos = new List<object>();
            foreach (var v in views)
            {
                var crop = v.CropBox;
                double widthMm = 0, heightMm = 0;
                if (crop != null)
                {
                    widthMm = (crop.Max.X - crop.Min.X) * 304.8;
                    heightMm = (crop.Max.Y - crop.Min.Y) * 304.8;
                }

                viewInfos.Add(new
                {
                    id = v.Id.Value,
                    name = v.Name,
                    viewType = v.ViewType.ToString(),
                    scale = v.Scale,
                    cropActive = v.CropBoxActive,
                    cropWidthMm = widthMm,
                    cropHeightMm = heightMm
                });
            }

            return new
            {
                count = views.Count,
                views = viewInfos
            };
        }
    }
}
