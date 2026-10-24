using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoors
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(d => {
                    var lvl = doc.GetElement(d.LevelId) as Level;
                    var sym = d.Symbol;
                    var lp = d.Location as LocationPoint;
                    var pWidth = sym.get_Parameter(BuiltInParameter.DOOR_WIDTH) ?? sym.LookupParameter("Width") ?? sym.LookupParameter("Rộng");
                    var pHeight = sym.get_Parameter(BuiltInParameter.DOOR_HEIGHT) ?? sym.LookupParameter("Height") ?? sym.LookupParameter("Cao");
                    double wMm = pWidth != null ? pWidth.AsDouble() * FT2M * 1000 : 0;
                    double hMm = pHeight != null ? pHeight.AsDouble() * FT2M * 1000 : 0;

                    return new {
                        id = d.Id.Value,
                        level = lvl?.Name ?? "Unknown",
                        family = sym.FamilyName,
                        symbolName = sym.Name,
                        symbolId = sym.Id.Value,
                        width = Math.Round(wMm, 1),
                        height = Math.Round(hMm, 1),
                        x = lp != null ? Math.Round(lp.Point.X * FT2M * 1000, 1) : 0,
                        y = lp != null ? Math.Round(lp.Point.Y * FT2M * 1000, 1) : 0
                    };
                })
                .ToList();

            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => new {
                    id = s.Id.Value,
                    family = s.FamilyName,
                    name = s.Name
                })
                .ToList();

            return new { count = doors.Count, doors, doorSymbols };
        }
    }
}
