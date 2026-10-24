using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAxis1Cols
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => {
                    var lp = c.Location as LocationPoint;
                    if (lp == null) return false;
                    return Math.Abs(lp.Point.X * FT2MM - 550.0) < 300.0;
                })
                .Select(c => {
                    var lp = (LocationPoint)c.Location;
                    var bb = c.get_BoundingBox(null);
                    var bLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId())?.Name;
                    var tLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsElementId())?.Name;
                    var tOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2MM;

                    return new {
                        id = c.Id.Value,
                        name = c.Name,
                        pt = $"({lp.Point.X * FT2MM:F0}, {lp.Point.Y * FT2MM:F0}, {lp.Point.Z * FT2MM:F0})",
                        baseLevel = bLvl,
                        topLevel = tLvl,
                        topOffset = tOff,
                        minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2MM : 0
                    };
                })
                .OrderBy(c => c.minZ)
                .ThenBy(c => c.pt)
                .ToList();

            return new { count = cols.Count, cols };
        }
    }
}
