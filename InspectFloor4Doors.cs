using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloor4Doors
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            var view = doc.GetElement(new ElementId(2409349L)) as View;
            if (view == null) return new { error = "no view" };

            var doors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WherePasses(new ElementLevelFilter(view.GenLevel.Id))
                .Cast<FamilyInstance>()
                .Select(d => {
                    var lp = d.Location as LocationPoint;
                    var pt = lp?.Point ?? XYZ.Zero;
                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        symbol = d.Symbol.Name,
                        x = pt.X * 304.8,
                        y = pt.Y * 304.8
                    };
                })
                .OrderBy(d => d.y)
                .ThenBy(d => d.x)
                .ToList();

            return new { count = doors.Count, doors };
        }
    }
}
