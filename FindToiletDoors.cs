using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindToiletDoors
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Select(d => {
                    var pt = (d.Location as LocationPoint)?.Point;
                    return new {
                        id = d.Id.Value,
                        family = d.Symbol.FamilyName,
                        symbol = d.Symbol.Name,
                        x = pt != null ? pt.X * 304.8 : 0,
                        y = pt != null ? pt.Y * 304.8 : 0,
                        z = pt != null ? pt.Z * 304.8 : 0,
                        level = d.LevelId.Value
                    };
                })
                .Where(d => (d.x >= 19000 && d.x <= 38000) && (d.y >= 0 && d.y <= 14000))
                .ToList();

            return doors;
        }
    }
}
