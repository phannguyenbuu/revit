using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCadLinkAndCoordinates
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Check CAD Links or Imports
            var cadLinks = new List<object>();
            foreach (var elem in new FilteredElementCollector(doc).OfClass(typeof(ImportInstance)).Cast<ImportInstance>())
            {
                var tr = elem.GetTransform();
                var bb = elem.get_BoundingBox(null);
                cadLinks.Add(new
                {
                    id = elem.Id.Value,
                    isLinked = elem.IsLinked,
                    name = elem.Category?.Name,
                    origin = $"[{tr.Origin.X * 304.8:F1}, {tr.Origin.Y * 304.8:F1}, {tr.Origin.Z * 304.8:F1}]",
                    basisX = $"[{tr.BasisX.X:F3}, {tr.BasisX.Y:F3}, {tr.BasisX.Z:F3}]",
                    basisY = $"[{tr.BasisY.X:F3}, {tr.BasisY.Y:F3}, {tr.BasisY.Z:F3}]",
                    bbMin = bb != null ? $"[{bb.Min.X * 304.8:F1}, {bb.Min.Y * 304.8:F1}, {bb.Min.Z * 304.8:F1}]" : "null",
                    bbMax = bb != null ? $"[{bb.Max.X * 304.8:F1}, {bb.Max.Y * 304.8:F1}, {bb.Max.Z * 304.8:F1}]" : "null"
                });
            }

            // 2. Check Project Base Point and Survey Point
            var basePoints = new List<object>();
            foreach (var bp in new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ProjectBasePoint).Cast<BasePoint>())
            {
                basePoints.Add(new
                {
                    type = "ProjectBasePoint",
                    ew = bp.get_Parameter(BuiltInParameter.BASEPOINT_EASTWEST_PARAM)?.AsDouble() * 304.8,
                    ns = bp.get_Parameter(BuiltInParameter.BASEPOINT_NORTHSOUTH_PARAM)?.AsDouble() * 304.8,
                    elev = bp.get_Parameter(BuiltInParameter.BASEPOINT_ELEVATION_PARAM)?.AsDouble() * 304.8,
                    angle = bp.get_Parameter(BuiltInParameter.BASEPOINT_ANGLETON_PARAM)?.AsDouble() * 180.0 / Math.PI
                });
            }
            foreach (var sp in new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_SharedBasePoint).Cast<BasePoint>())
            {
                basePoints.Add(new
                {
                    type = "SurveyPoint",
                    ew = sp.get_Parameter(BuiltInParameter.BASEPOINT_EASTWEST_PARAM)?.AsDouble() * 304.8,
                    ns = sp.get_Parameter(BuiltInParameter.BASEPOINT_NORTHSOUTH_PARAM)?.AsDouble() * 304.8,
                    elev = sp.get_Parameter(BuiltInParameter.BASEPOINT_ELEVATION_PARAM)?.AsDouble() * 304.8
                });
            }

            // 3. Check Grids in Revit to see the project coordinate system
            var grids = new List<object>();
            foreach (var g in new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>())
            {
                var curve = g.Curve;
                grids.Add(new
                {
                    name = g.Name,
                    p0 = $"[{curve.GetEndPoint(0).X * 304.8:F1}, {curve.GetEndPoint(0).Y * 304.8:F1}]",
                    p1 = $"[{curve.GetEndPoint(1).X * 304.8:F1}, {curve.GetEndPoint(1).Y * 304.8:F1}]"
                });
            }

            // 4. Check Level 1 (Tầng 1) ID
            var level1 = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("1"));

            return new
            {
                level1 = level1 != null ? new { id = level1.Id.Value, name = level1.Name, elev = level1.Elevation * 304.8 } : null,
                cadLinks,
                basePoints,
                grids
            };
        }
    }
}
