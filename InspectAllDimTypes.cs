using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllDimTypes
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                .Select(dt => {
                    var pBg = dt.get_Parameter(BuiltInParameter.TEXT_BACKGROUND);
                    int bgVal = pBg != null ? pBg.AsInteger() : -1;
                    return new {
                        id = dt.Id.Value,
                        name = dt.Name,
                        textBackground = bgVal,
                        bgDesc = bgVal == 0 ? "Opaque" : (bgVal == 1 ? "Transparent" : "Unknown")
                    };
                })
                .ToList();

            return new { count = dimTypes.Count, dimTypes };
        }
    }
}
