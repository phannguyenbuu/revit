using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListAllProjectWalls
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w =>
                {
                    string baseLvl = w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsValueString() ?? "None";
                    string topLvl = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsValueString() ?? "Unconnected";
                    double h = (w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() ?? 0) * 304.8;
                    double baseOffset = (w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() ?? 0) * 304.8;
                    double topOffset = (w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() ?? 0) * 304.8;

                    string cStr = "";
                    if (w.Location is LocationCurve lc)
                    {
                        var p0 = lc.Curve.GetEndPoint(0) * 304.8;
                        var p1 = lc.Curve.GetEndPoint(1) * 304.8;
                        cStr = $"[{p0.X:F0}, {p0.Y:F0}, {p0.Z:F0}] -> [{p1.X:F0}, {p1.Y:F0}, {p1.Z:F0}]";
                    }

                    return new
                    {
                        id = w.Id.Value,
                        name = w.Name,
                        baseLvl = baseLvl,
                        topLvl = topLvl,
                        h = h,
                        baseOffset = baseOffset,
                        topOffset = topOffset,
                        curve = cStr
                    };
                })
                .ToList();

            return new { count = walls.Count, walls = walls };
        }
    }
}
