using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSelectedViewsForDwgExport
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

            // Sort views by name
            views = views.OrderBy(v => v.Name).ToList();

            var viewInfos = new List<object>();
            foreach (var v in views)
            {
                var sheetNumParam = v.get_Parameter(BuiltInParameter.VIEWPORT_SHEET_NUMBER);
                string sheetNum = sheetNumParam?.AsString() ?? "";

                // Get crop box or outline
                BoundingBoxXYZ crop = v.CropBox;
                double widthMm = 0, heightMm = 0;
                if (crop != null)
                {
                    widthMm = (crop.Max.X - crop.Min.X) * 304.8;
                    heightMm = (crop.Max.Y - crop.Min.Y) * 304.8;
                }

                // Check model elements bounding box in this view
                var collector = new FilteredElementCollector(doc, v.Id)
                    .WhereElementIsNotElementType();
                
                XYZ minPt = null, maxPt = null;
                int elemCount = 0;
                foreach (var el in collector)
                {
                    elemCount++;
                    var bb = el.get_BoundingBox(v);
                    if (bb != null)
                    {
                        if (minPt == null)
                        {
                            minPt = new XYZ(bb.Min.X, bb.Min.Y, bb.Min.Z);
                            maxPt = new XYZ(bb.Max.X, bb.Max.Y, bb.Max.Z);
                        }
                        else
                        {
                            minPt = new XYZ(Math.Min(minPt.X, bb.Min.X), Math.Min(minPt.Y, bb.Min.Y), Math.Min(minPt.Z, bb.Min.Z));
                            maxPt = new XYZ(Math.Max(maxPt.X, bb.Max.X), Math.Max(maxPt.Y, bb.Max.Y), Math.Max(maxPt.Z, bb.Max.Z));
                        }
                    }
                }

                viewInfos.Add(new
                {
                    id = v.Id.Value,
                    name = v.Name,
                    viewType = v.ViewType.ToString(),
                    scale = v.Scale,
                    cropActive = v.CropBoxActive,
                    cropVisible = v.CropBoxVisible,
                    cropWidthMm = widthMm,
                    cropHeightMm = heightMm,
                    sheetNumber = sheetNum,
                    canBeAddedToSheet = string.IsNullOrEmpty(sheetNum),
                    elementCount = elemCount,
                    modelMin = minPt != null ? new { x = minPt.X * 304.8, y = minPt.Y * 304.8 } : null,
                    modelMax = maxPt != null ? new { x = maxPt.X * 304.8, y = maxPt.Y * 304.8 } : null,
                    modelWidthMm = (minPt != null && maxPt != null) ? (maxPt.X - minPt.X) * 304.8 : 0,
                    modelHeightMm = (minPt != null && maxPt != null) ? (maxPt.Y - minPt.Y) * 304.8 : 0
                });
            }

            return new
            {
                success = true,
                selectedViewCount = views.Count,
                views = viewInfos
            };
        }
    }
}
