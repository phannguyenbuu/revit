using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveSelection
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var selIds = uidoc.Selection.GetElementIds().Select(id => id.Value).ToList();
            var selElems = selIds.Select(id => {
                var el = doc.GetElement(new ElementId(id));
                return new { id, name = el?.Name, cat = el?.Category?.Name, type = el?.GetType().Name };
            }).ToList();

            var view = uidoc.ActiveView;
            return new {
                activeView = new { id = view?.Id.Value, name = view?.Name, type = view?.ViewType.ToString() },
                selectedCount = selIds.Count,
                selectedElements = selElems
            };
        }
    }
}
