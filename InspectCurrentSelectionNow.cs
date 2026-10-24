using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCurrentSelectionNow
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            var items = new List<object>();

            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem == null) continue;

                var type = doc.GetElement(elem.GetTypeId());
                var markParam = elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString();
                var typeMarkParam = type?.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString();

                var pLevel = elem.get_Parameter(BuiltInParameter.LEVEL_PARAM) 
                          ?? elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM);
                var levelName = pLevel != null ? doc.GetElement(pLevel.AsElementId())?.Name : "unknown";

                XYZ locPt = XYZ.Zero;
                if (elem.Location is LocationPoint lp) locPt = lp.Point;

                var segList = new List<object>();
                object? dimInfo = null;
                if (elem is Dimension dim)
                {
                    if (dim.Segments != null && dim.Segments.Size > 0)
                    {
                        foreach (DimensionSegment seg in dim.Segments)
                        {
                            segList.Add(new {
                                value = seg.Value.HasValue ? Math.Round(seg.Value.Value * 304.8, 1) : 0,
                                text = seg.ValueString,
                                textPos = seg.TextPosition != null ? new { x = Math.Round(seg.TextPosition.X * 304.8, 1), y = Math.Round(seg.TextPosition.Y * 304.8, 1) } : null
                            });
                        }
                    }
                    var c = dim.Curve;
                    dimInfo = new {
                        ownerViewId = dim.OwnerViewId.Value,
                        ownerViewName = doc.GetElement(dim.OwnerViewId)?.Name,
                        numSegments = dim.Segments?.Size ?? 0,
                        curveStart = c != null && c.IsBound ? new { x = Math.Round(c.GetEndPoint(0).X * 304.8, 1), y = Math.Round(c.GetEndPoint(0).Y * 304.8, 1) } : null,
                        curveEnd = c != null && c.IsBound ? new { x = Math.Round(c.GetEndPoint(1).X * 304.8, 1), y = Math.Round(c.GetEndPoint(1).Y * 304.8, 1) } : null,
                        segments = segList
                    };
                }

                items.Add(new
                {
                    id = elem.Id.Value,
                    category = elem.Category?.Name,
                    name = elem.Name,
                    typeName = type?.Name,
                    familyName = (elem as FamilyInstance)?.Symbol?.FamilyName,
                    mark = markParam,
                    typeMark = typeMarkParam,
                    level = levelName,
                    levelId = pLevel?.AsElementId()?.Value,
                    location = new { x = locPt.X * 304.8, y = locPt.Y * 304.8, z = locPt.Z * 304.8 },
                    dimInfo
                });
            }

            return new
            {
                success = true,
                count = selIds.Count,
                items,
                activeViewId = uidoc.ActiveView?.Id.Value,
                activeViewName = uidoc.ActiveView?.Name
            };
        }
    }
}
