using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindDoorsOnAxisC
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Grid C: Y = 7800
            // Grid 9: X = 29650
            // Grid 10: X = 33350

            var allDoors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .ToList();

            var candidateDoors = new List<object>();

            foreach (var d in allDoors)
            {
                var lp = d.Location as LocationPoint;
                if (lp == null) continue;

                double x = lp.Point.X * FT_TO_MM;
                double y = lp.Point.Y * FT_TO_MM;
                double z = lp.Point.Z * FT_TO_MM;

                var level = doc.GetElement(d.LevelId) as Level;
                string levelName = level?.Name ?? "N/A";

                var sym = d.Symbol;
                string famName = sym?.FamilyName ?? "";
                string typeName = sym?.Name ?? "";
                string mark = d.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString() ?? "";

                // Check distance to Axis C (Y = 7800) and between Grid 9 & 10 (X between 28500 and 34500)
                double distToC = Math.Abs(y - 7800.0);
                bool between9and10 = (x >= 28500.0 && x <= 34500.0);

                // Let's also check if near Axis C within +/- 1500mm
                if (between9and10 && distToC <= 1500.0)
                {
                    candidateDoors.Add(new
                    {
                        id = d.Id.Value,
                        level = levelName,
                        levelId = d.LevelId.Value,
                        x = Math.Round(x, 1),
                        y = Math.Round(y, 1),
                        z = Math.Round(z, 1),
                        distToAxisC = Math.Round(distToC, 1),
                        familyName = famName,
                        typeName = typeName,
                        mark = mark,
                        hostWallId = d.Host?.Id.Value ?? 0,
                        hostWallName = d.Host?.Name ?? ""
                    });
                }
            }

            // Also check available D7 symbols in project
            var d7Symbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Where(s => s.FamilyName.Contains("D7", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("D7", StringComparison.OrdinalIgnoreCase))
                .Select(s => new {
                    id = s.Id.Value,
                    familyName = s.FamilyName,
                    name = s.Name,
                    isActive = s.IsActive
                })
                .ToList();

            return new
            {
                totalDoorsChecked = allDoors.Count,
                matchedDoorsCount = candidateDoors.Count,
                matchedDoors = candidateDoors,
                d7Symbols
            };
        }
    }
}
