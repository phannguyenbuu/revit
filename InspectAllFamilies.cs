using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllFamilies
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Wall types
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .Select(w => new
                {
                    id = w.Id.Value,
                    name = w.Name,
                    kind = w.Kind.ToString(),
                    widthMm = w.Width * 304.8
                })
                .ToList();

            // 2. Door symbols
            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Select(d => new
                {
                    id = d.Id.Value,
                    familyName = d.FamilyName,
                    name = d.Name
                })
                .ToList();

            // 3. Window symbols
            var windowSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Select(w => new
                {
                    id = w.Id.Value,
                    familyName = w.FamilyName,
                    name = w.Name
                })
                .ToList();

            // 4. Floor types
            var floorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(f => new
                {
                    id = f.Id.Value,
                    name = f.Name
                })
                .ToList();

            // 5. Grids
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g =>
                {
                    var curve = g.Curve;
                    var p0 = curve.GetEndPoint(0);
                    var p1 = curve.GetEndPoint(1);
                    return new
                    {
                        id = g.Id.Value,
                        name = g.Name,
                        start = new { x = p0.X * 0.3048, y = p0.Y * 0.3048 },
                        end = new { x = p1.X * 0.3048, y = p1.Y * 0.3048 }
                    };
                })
                .ToList();

            // 6. Generic Models / Plumbing / Furniture
            var otherSymbols = new FilteredElementCollector(doc)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory>
                {
                    BuiltInCategory.OST_PlumbingFixtures,
                    BuiltInCategory.OST_Furniture,
                    BuiltInCategory.OST_GenericModel,
                    BuiltInCategory.OST_Stairs
                }))
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Select(s => new
                {
                    id = s.Id.Value,
                    category = s.Category?.Name,
                    familyName = s.FamilyName,
                    name = s.Name
                })
                .ToList();

            return new
            {
                wallTypes,
                doorSymbols,
                windowSymbols,
                floorTypes,
                grids,
                otherSymbols
            };
        }
    }
}
