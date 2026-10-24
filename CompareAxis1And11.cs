using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CompareAxis1And11
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active doc" };

            // Find all walls near front facade (y < 2000 mm)
            var frontWalls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var lc = w.Location as LocationCurve;
                    if (lc == null) return false;
                    var p0 = lc.Curve.GetEndPoint(0);
                    var p1 = lc.Curve.GetEndPoint(1);
                    double y0 = p0.Y * FT2M * 1000;
                    double y1 = p1.Y * FT2M * 1000;
                    return (y0 < 2000 || y1 < 2000);
                })
                .Select(w => {
                    var lc = (LocationCurve)w.Location;
                    var p0 = lc.Curve.GetEndPoint(0);
                    var p1 = lc.Curve.GetEndPoint(1);
                    var pBase = w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
                    var pTop = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                    var pBaseOff = w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                    var pTopOff = w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                    var pHeight = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    var baseLvl = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) as Level : null;
                    var topLvl = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) as Level : null;

                    return new {
                        id = w.Id.Value,
                        wallType = w.WallType.Name,
                        baseLvl = baseLvl?.Name,
                        baseOffset = Math.Round((pBaseOff?.AsDouble() ?? 0) * FT2M * 1000, 1),
                        topLvl = topLvl?.Name,
                        topOffset = Math.Round((pTopOff?.AsDouble() ?? 0) * FT2M * 1000, 1),
                        height = Math.Round((pHeight?.AsDouble() ?? 0) * FT2M * 1000, 1),
                        p0 = new { x = Math.Round(p0.X * FT2M * 1000, 1), y = Math.Round(p0.Y * FT2M * 1000, 1), z = Math.Round(p0.Z * FT2M * 1000, 1) },
                        p1 = new { x = Math.Round(p1.X * FT2M * 1000, 1), y = Math.Round(p1.Y * FT2M * 1000, 1), z = Math.Round(p1.Z * FT2M * 1000, 1) }
                    };
                })
                .OrderBy(w => w.p0.x)
                .ToList();

            // Find all columns near front facade (y < 2000 mm)
            var frontCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => {
                    var lp = c.Location as LocationPoint;
                    if (lp == null) return false;
                    return (lp.Point.Y * FT2M * 1000 < 2000);
                })
                .Select(c => {
                    var lp = (LocationPoint)c.Location;
                    var pBase = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    var pBaseOff = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                    var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                    var baseLvl = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) as Level : null;
                    var topLvl = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) as Level : null;

                    return new {
                        id = c.Id.Value,
                        name = c.Name,
                        baseLvl = baseLvl?.Name,
                        baseOffset = Math.Round((pBaseOff?.AsDouble() ?? 0) * FT2M * 1000, 1),
                        topLvl = topLvl?.Name,
                        topOffset = Math.Round((pTopOff?.AsDouble() ?? 0) * FT2M * 1000, 1),
                        pos = new { x = Math.Round(lp.Point.X * FT2M * 1000, 1), y = Math.Round(lp.Point.Y * FT2M * 1000, 1), z = Math.Round(lp.Point.Z * FT2M * 1000, 1) }
                    };
                })
                .OrderBy(c => c.pos.x)
                .ToList();

            return new {
                frontWalls,
                frontCols
            };
        }
    }
}
