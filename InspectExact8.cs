using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExact8
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active doc" };

            long[] ids = new long[] { 2379835L, 2379828L, 2379825L, 2379826L, 2379827L, 2361336L, 2379829L, 2379830L };
            var list = new List<object>();

            foreach (var id in ids)
            {
                var elem = doc.GetElement(new ElementId(id));
                if (elem == null)
                {
                    list.Add(new { id, found = false });
                    continue;
                }
                var pBase = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM) ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
                var pTop = elem.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM) ?? elem.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                var pBaseOff = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM) ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                var pTopOff = elem.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM) ?? elem.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                var pHeight = elem.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);

                var baseLvl = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) as Level : null;
                var topLvl = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) as Level : null;

                XYZ p0 = null, p1 = null;
                if (elem.Location is LocationCurve lc)
                {
                    p0 = lc.Curve.GetEndPoint(0);
                    p1 = lc.Curve.GetEndPoint(1);
                }
                else if (elem.Location is LocationPoint lp)
                {
                    p0 = lp.Point;
                }

                list.Add(new
                {
                    id,
                    found = true,
                    name = elem.Name,
                    category = elem.Category?.Name,
                    baseLvl = baseLvl?.Name,
                    baseElev = baseLvl != null ? Math.Round(baseLvl.Elevation * FT2M, 3) : 0,
                    baseOffset = Math.Round((pBaseOff?.AsDouble() ?? 0) * FT2M * 1000, 1),
                    topLvl = topLvl?.Name,
                    topElev = topLvl != null ? Math.Round(topLvl.Elevation * FT2M, 3) : 0,
                    topOffset = Math.Round((pTopOff?.AsDouble() ?? 0) * FT2M * 1000, 1),
                    height = Math.Round((pHeight?.AsDouble() ?? 0) * FT2M * 1000, 1),
                    p0 = p0 != null ? new { x = Math.Round(p0.X * FT2M * 1000, 1), y = Math.Round(p0.Y * FT2M * 1000, 1), z = Math.Round(p0.Z * FT2M * 1000, 1) } : null,
                    p1 = p1 != null ? new { x = Math.Round(p1.X * FT2M * 1000, 1), y = Math.Round(p1.Y * FT2M * 1000, 1), z = Math.Round(p1.Z * FT2M * 1000, 1) } : null
                });
            }
            return list;
        }
    }
}
