using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectEntranceArea
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Find doors and walls near X in [36000, 38000], Y in [5000, 8500]
            var doors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(d => {
                    var lp = d.Location as LocationPoint;
                    if (lp == null) return false;
                    double x = lp.Point.X * 304.8;
                    double y = lp.Point.Y * 304.8;
                    return x >= 36000 && x <= 38000 && y >= 4500 && y <= 8500;
                })
                .Select(d => {
                    var lp = d.Location as LocationPoint;
                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        symbol = d.Symbol.Name,
                        family = d.Symbol.FamilyName,
                        x = lp.Point.X * 304.8,
                        y = lp.Point.Y * 304.8
                    };
                })
                .ToList();

            // Check floor types
            var floorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => new { id = ft.Id.Value, name = ft.Name })
                .ToList();

            // Check stairs types
            var stairTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(Autodesk.Revit.DB.Architecture.StairsType))
                .Cast<Autodesk.Revit.DB.Architecture.StairsType>()
                .Select(st => new { id = st.Id.Value, name = st.Name })
                .ToList();

            return new {
                doors = doors,
                floorTypes = floorTypes,
                stairTypes = stairTypes
            };
        }
    }
}
