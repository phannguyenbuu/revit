using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectViewTexts
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            long viewIdVal = 0;
            if (args.TryGetProperty("viewId", out var vProp))
            {
                viewIdVal = vProp.GetInt64();
            }

            View? targetView = null;
            if (viewIdVal > 0)
            {
                targetView = doc.GetElement(new ElementId(viewIdVal)) as View;
            }
            else
            {
                targetView = uiapp.ActiveUIDocument?.ActiveView;
            }

            var collector = targetView != null 
                ? new FilteredElementCollector(doc, targetView.Id)
                : new FilteredElementCollector(doc);

            var texts = collector
                .OfClass(typeof(TextNote))
                .Cast<TextNote>()
                .Take(50)
                .Select(t => new {
                    id = t.Id.Value,
                    text = t.Text,
                    typeName = doc.GetElement(t.GetTypeId())?.Name,
                    typeId = t.GetTypeId().Value,
                    x = t.Coord.X * 304.8,
                    y = t.Coord.Y * 304.8,
                    viewName = doc.GetElement(t.OwnerViewId)?.Name
                })
                .ToList();

            return new { 
                targetView = targetView?.Name, 
                targetViewId = targetView?.Id.Value, 
                count = texts.Count, 
                texts 
            };
        }
    }
}
