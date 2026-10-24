using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorsInRevit
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find all Door symbols (types)
            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s =>
                {
                    double w = 0, h = 0;
                    var pW = s.get_Parameter(BuiltInParameter.DOOR_WIDTH);
                    var pH = s.get_Parameter(BuiltInParameter.DOOR_HEIGHT);
                    if (pW != null) w = pW.AsDouble() * 304.8;
                    if (pH != null) h = pH.AsDouble() * 304.8;

                    return new
                    {
                        id = s.Id.Value,
                        familyName = s.FamilyName,
                        typeName = s.Name,
                        widthMm = Math.Round(w, 1),
                        heightMm = Math.Round(h, 1)
                    };
                })
                .OrderBy(s => s.familyName).ThenBy(s => s.typeName)
                .ToList();

            // Find any existing door instances
            var existingInstances = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(i =>
                {
                    var lp = i.Location as LocationPoint;
                    var pt = lp?.Point;
                    return new
                    {
                        id = i.Id.Value,
                        name = i.Name,
                        symbol = i.Symbol.Name,
                        family = i.Symbol.FamilyName,
                        x = pt != null ? Math.Round(pt.X * 0.3048, 3) : 0,
                        y = pt != null ? Math.Round(pt.Y * 0.3048, 3) : 0,
                        hostId = i.Host?.Id.Value
                    };
                })
                .ToList();

            // Find wall types
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .Where(wt => wt.Kind == WallKind.Basic)
                .Select(wt => new
                {
                    id = wt.Id.Value,
                    name = wt.Name,
                    widthMm = Math.Round(wt.Width * 304.8, 1)
                })
                .ToList();

            return new
            {
                doorSymbols = doorSymbols,
                existingInstances = existingInstances,
                wallTypes = wallTypes
            };
        }
    }
}
