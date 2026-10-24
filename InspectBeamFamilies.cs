using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBeamFamilies
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beamSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => new {
                    id = s.Id.Value,
                    name = s.Name,
                    family = s.FamilyName,
                    b = s.LookupParameter("b")?.AsDouble() * 304.8 ?? (s.LookupParameter("Width")?.AsDouble() * 304.8 ?? 0),
                    h = s.LookupParameter("h")?.AsDouble() * 304.8 ?? (s.LookupParameter("Height")?.AsDouble() * 304.8 ?? 0)
                })
                .ToList();

            var existingBeams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(b => {
                    var l = doc.GetElement(b.LevelId) as Level;
                    return new {
                        id = b.Id.Value,
                        name = b.Name,
                        level = l?.Name
                    };
                })
                .ToList();

            return new { beamSymbols, existingBeamsCount = existingBeams.Count, existingBeams };
        }
    }
}
