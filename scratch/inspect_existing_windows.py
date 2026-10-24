import urllib.request, json

code = """
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExistingWindowsDetails
    {
        private const double FT2M = 0.3048;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var windows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(w => {
                    var pt = (w.Location as LocationPoint)?.Point;
                    var host = w.Host as Wall;
                    var mark = w.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString();
                    var sill = w.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.AsDouble() * FT2M;
                    return new {
                        id = w.Id.Value,
                        symbol = w.Symbol.Name,
                        family = w.Symbol.FamilyName,
                        mark = mark,
                        sillHeightM = sill != null ? Math.Round(sill.Value, 3) : 0.0,
                        hostWallId = host?.Id.Value,
                        pt = pt != null ? new { x = Math.Round(pt.X * FT2M, 3), y = Math.Round(pt.Y * FT2M, 3), z = Math.Round(pt.Z * FT2M, 3) } : null
                    };
                })
                .ToList();

            return new { count = windows.Count, windows = windows };
        }
    }
}
"""

print("Inspecting existing windows details")
