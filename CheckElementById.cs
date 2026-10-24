using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckElementById
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            long idVal = 2369928L;
            if (args.TryGetProperty("id", out var pId)) idVal = pId.GetInt64();

            var e = doc.GetElement(new ElementId(idVal));
            if (e == null) return new { found = false, id = idVal };

            return new {
                found = true,
                id = e.Id.Value,
                name = e.Name,
                category = e.Category?.Name,
                type = e.GetType().Name
            };
        }
    }
}
