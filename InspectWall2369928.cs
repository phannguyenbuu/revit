using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWall2369928
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Check element 2369928 directly
            var elem = doc.GetElement(new ElementId(2369928L));
            
            // Also check all elements in active selection
            var selIds = uidoc.Selection.GetElementIds();
            var selList = selIds.Select(id => {
                var e = doc.GetElement(id);
                return new { id = id.Value, name = e?.Name, cat = e?.Category?.Name, type = e?.GetType().Name };
            }).ToList();

            // Find all walls at X ~ 550, Y in [5000..8500] across all levels
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var lc = w.Location as LocationCurve;
                    if (lc == null) return false;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    double midX = (p0.X + p1.X) * 0.5;
                    double midY = (p0.Y + p1.Y) * 0.5;
                    return Math.Abs(midX - 550.0) < 300.0 && midY >= 5000.0 && midY <= 8500.0;
                })
                .Select(w => {
                    var lc = (LocationCurve)w.Location;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    var bb = w.get_BoundingBox(null);
                    var bLvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
                    var tLvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId())?.Name ?? "Unconnected";
                    var h = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2MM;
                    var bOff = w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() * FT2MM;
                    var tOff = w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * FT2MM;
                    var inserts = w.FindInserts(true, true, true, true).Select(id => {
                        var ie = doc.GetElement(id);
                        return $"{ie?.Name} ({ie?.Category?.Name}, ID {id.Value})";
                    }).ToList();

                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        baseLevel = bLvl,
                        baseOffset = bOff,
                        topLevel = tLvl,
                        topOffset = tOff,
                        height = h,
                        p0 = $"({p0.X:F0}, {p0.Y:F0}, {p0.Z:F0})",
                        p1 = $"({p1.X:F0}, {p1.Y:F0}, {p1.Z:F0})",
                        minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2MM : 0,
                        inserts
                    };
                })
                .OrderBy(w => w.minZ)
                .ToList();

            // Find all windows hosted on any of these walls or nearby
            var windows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(wi => {
                    var bb = wi.get_BoundingBox(null);
                    if (bb == null) return false;
                    double midX = (bb.Min.X + bb.Max.X) * 0.5 * FT2MM;
                    double midY = (bb.Min.Y + bb.Max.Y) * 0.5 * FT2MM;
                    return Math.Abs(midX - 550.0) < 500.0 && midY >= 5000.0 && midY <= 8500.0;
                })
                .Select(wi => {
                    var bb = wi.get_BoundingBox(null);
                    return new {
                        id = wi.Id.Value,
                        name = wi.Name,
                        sym = wi.Symbol.Name,
                        host = $"{wi.Host?.Name} (ID {wi.Host?.Id.Value})",
                        minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2MM : 0
                    };
                })
                .OrderBy(w => w.minZ)
                .ToList();

            return new {
                elem2369928 = elem != null ? new { id = elem.Id.Value, name = elem.Name, type = elem.GetType().Name, cat = elem.Category?.Name } : null,
                selection = selList,
                wallsCount = walls.Count,
                walls,
                windowsCount = windows.Count,
                windows
            };
        }
    }
}
