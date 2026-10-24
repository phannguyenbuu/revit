using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckElem112070
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var elem = doc.GetElement(new ElementId(112070L));
            if (elem != null)
            {
                return new
                {
                    found = true,
                    name = elem.Name,
                    category = elem.Category?.Name ?? "NoCat",
                    className = elem.GetType().Name
                };
            }
            return new { found = false };
        }
    }
}
