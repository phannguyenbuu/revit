using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDoor2364731
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var elem = doc.GetElement(new ElementId(2364731L));
            if (elem == null) return new { error = "Element 2364731 not found" };
            var fi = elem as FamilyInstance;
            var lp = fi?.Location as LocationPoint;
            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            var lc = wall?.Location as LocationCurve;
            return new
            {
                doorId = elem.Id.Value,
                doorName = elem.Name,
                doorCategory = elem.Category?.Name,
                symbolName = fi?.Symbol?.Name,
                familyName = fi?.Symbol?.Family?.Name,
                hostId = fi?.Host?.Id?.Value,
                hostName = fi?.Host?.Name,
                pt = lp != null ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null,
                wallLength = wall != null ? wall.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)?.AsDouble() * 0.3048 : 0,
                wallCurves = lc != null ? (lc.Curve.GetEndPoint(0).ToString() + " to " + lc.Curve.GetEndPoint(1).ToString()) : "none"
            };
        }
    }
}
