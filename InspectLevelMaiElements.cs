using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectLevelMaiElements
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var lvlMai = doc.GetElement(new ElementId(1209118L)) as Level;
            var lvlTum = doc.GetElement(new ElementId(2360635L)) as Level;

            var elemsOnMai = new FilteredElementCollector(doc)
                .WherePasses(new ElementLevelFilter(lvlMai.Id))
                .WhereElementIsNotElementType()
                .Select(e => new { id = e.Id.Value, cat = e.Category?.Name, name = e.Name })
                .ToList();

            var elemsOnTum = new FilteredElementCollector(doc)
                .WherePasses(new ElementLevelFilter(lvlTum.Id))
                .WhereElementIsNotElementType()
                .Select(e => new { id = e.Id.Value, cat = e.Category?.Name, name = e.Name })
                .ToList();

            // Floors in document
            var allFloors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Select(f => {
                    var l = doc.GetElement(f.LevelId) as Level;
                    return new {
                        id = f.Id.Value,
                        level = l?.Name,
                        elevM = (l?.Elevation ?? 0) * FT2M,
                        areaM2 = Math.Round(f.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2)
                    };
                }).ToList();

            return new
            {
                lvlMai = new { name = lvlMai?.Name, elevM = (lvlMai?.Elevation ?? 0) * FT2M, elemCount = elemsOnMai.Count, elems = elemsOnMai },
                lvlTum = new { name = lvlTum?.Name, elevM = (lvlTum?.Elevation ?? 0) * FT2M, elemCount = elemsOnTum.Count, elems = elemsOnTum },
                allFloors
            };
        }
    }
}
