using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpSelection
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };
            
            var selIds = uidoc.Selection.GetElementIds();
            var list = new List<object>();
            foreach (var id in selIds)
            {
                var el = doc.GetElement(id);
                list.Add(new {
                    id = id.Value,
                    typeName = el?.GetType().FullName,
                    name = el?.Name,
                    category = el?.Category?.Name
                });
            }
            return new { count = selIds.Count, elements = list };
        }
    }
}
