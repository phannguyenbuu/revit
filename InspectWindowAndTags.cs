using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowAndTags
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2413190L)) as FamilyInstance;
            if (win == null) return new { error = "Window 2413190 not found" };

            var host = win.Host as Wall;
            var hostId = host?.Id.Value;
            var hostLevel = host?.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId()?.Value;

            // Check loaded Window Tag families
            var winTagSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_WindowTags)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => new { id = s.Id.Value, name = s.Name, family = s.FamilyName })
                .ToList();

            // Check existing tags on windows in view 695 or view 312
            var existingWinTags = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_WindowTags)
                .WhereElementIsNotElementType()
                .Cast<IndependentTag>()
                .Take(10)
                .Select(t => {
                    var taggedId = t.GetTaggedElementIds().FirstOrDefault()?.HostElementId?.Value;
                    return new {
                        id = t.Id.Value,
                        viewId = t.OwnerViewId.Value,
                        taggedId,
                        tagText = t.TagText
                    };
                })
                .ToList();

            // Check walls at X ~ 37150, Y ~ 6602 on Tang 3 and Tang 4
            var allWalls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            var candidateWalls = new List<object>();
            foreach (var w in allWalls)
            {
                var bb = w.get_BoundingBox(null);
                if (bb != null)
                {
                    double x1 = bb.Min.X * FT_TO_MM, x2 = bb.Max.X * FT_TO_MM;
                    double y1 = bb.Min.Y * FT_TO_MM, y2 = bb.Max.Y * FT_TO_MM;
                    if (37150 >= x1 - 500 && 37150 <= x2 + 500 && 6602 >= y1 - 500 && 6602 <= y2 + 500)
                    {
                        var lvlParam = w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId();
                        var lvl = lvlParam != null ? doc.GetElement(lvlParam)?.Name : "unknown";
                        candidateWalls.Add(new
                        {
                            id = w.Id.Value,
                            level = lvl,
                            levelId = lvlParam?.Value,
                            name = w.Name,
                            curve = w.Location is LocationCurve lc ? $"{lc.Curve.GetEndPoint(0) * FT_TO_MM} -> {lc.Curve.GetEndPoint(1) * FT_TO_MM}" : "none"
                        });
                    }
                }
            }

            return new
            {
                success = true,
                winId = win.Id.Value,
                mark = win.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                typeMark = win.Symbol?.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                hostId,
                hostLevel,
                winTagSymbols,
                existingWinTags,
                candidateWalls
            };
        }
    }
}
