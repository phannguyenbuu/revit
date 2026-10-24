using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAxis11Elements
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find elements near X = 37000..37500 (Axis 11)
            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => {
                    var lp = c.Location as LocationPoint;
                    if (lp == null) return false;
                    double x = lp.Point.X * FT2M * 1000;
                    return x > 35000;
                })
                .Select(c => {
                    var bLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId()) as Level;
                    var tLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsElementId()) as Level;
                    var lp = c.Location as LocationPoint;
                    return new {
                        id = c.Id.Value,
                        name = c.Name,
                        baseLevel = bLvl?.Name,
                        baseLevelId = bLvl?.Id.Value,
                        topLevel = tLvl?.Name,
                        topLevelId = tLvl?.Id.Value,
                        topElevM = (tLvl?.Elevation ?? 0) * FT2M,
                        x = Math.Round(lp.Point.X * FT2M * 1000, 1),
                        y = Math.Round(lp.Point.Y * FT2M * 1000, 1)
                    };
                })
                .ToList();

            // Find walls near Axis 11
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var lc = w.Location as LocationCurve;
                    if (lc == null) return false;
                    double x0 = lc.Curve.GetEndPoint(0).X * FT2M * 1000;
                    double x1 = lc.Curve.GetEndPoint(1).X * FT2M * 1000;
                    return Math.Max(x0, x1) > 35000;
                })
                .Select(w => {
                    var bLvl = doc.GetElement(w.LevelId) as Level;
                    var tLvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId()) as Level;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        baseLevel = bLvl?.Name,
                        topLevel = tLvl?.Name,
                        topElevM = (tLvl?.Elevation ?? 0) * FT2M
                    };
                })
                .ToList();

            return new { cols, walls };
        }
    }
}
