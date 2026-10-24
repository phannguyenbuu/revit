using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowSolids
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            if (win == null) return new { error = "No win" };

            var opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
            var geom = win.get_Geometry(opt);

            var solids = new List<object>();
            if (geom != null)
            {
                foreach (var obj in geom)
                {
                    if (obj is GeometryInstance gi)
                    {
                        var instGeom = gi.GetInstanceGeometry();
                        foreach (var so in instGeom)
                        {
                            if (so is Solid s && s.Volume > 0.00001)
                            {
                                var bb = s.GetBoundingBox();
                                solids.Add(new
                                {
                                    vol = s.Volume * Math.Pow(304.8, 3) / 1e6,
                                    min = $"[{bb.Min.X * 304.8:F1}, {bb.Min.Y * 304.8:F1}, {bb.Min.Z * 304.8:F1}]",
                                    max = $"[{bb.Max.X * 304.8:F1}, {bb.Max.Y * 304.8:F1}, {bb.Max.Z * 304.8:F1}]",
                                    widthX = (bb.Max.X - bb.Min.X) * 304.8,
                                    thickY = (bb.Max.Y - bb.Min.Y) * 304.8,
                                    heightZ = (bb.Max.Z - bb.Min.Z) * 304.8
                                });
                            }
                        }
                    }
                }
            }

            var bbWin = win.get_BoundingBox(null);
            string bbWinStr = bbWin != null ? $"Min: [{bbWin.Min.X * 304.8:F1}, {bbWin.Min.Y * 304.8:F1}, {bbWin.Min.Z * 304.8:F1}], Max: [{bbWin.Max.X * 304.8:F1}, {bbWin.Max.Y * 304.8:F1}, {bbWin.Max.Z * 304.8:F1}], Width: {(bbWin.Max.X - bbWin.Min.X) * 304.8:F1}, DepthY: {(bbWin.Max.Y - bbWin.Min.Y) * 304.8:F1}" : "none";

            var hostWall = win.Host as Wall;
            var bbWall = hostWall?.get_BoundingBox(null);
            string bbWallStr = bbWall != null ? $"Min: [{bbWall.Min.X * 304.8:F1}, {bbWall.Min.Y * 304.8:F1}, {bbWall.Min.Z * 304.8:F1}], Max: [{bbWall.Max.X * 304.8:F1}, {bbWall.Max.Y * 304.8:F1}, {bbWall.Max.Z * 304.8:F1}], ThickY: {(bbWall.Max.Y - bbWall.Min.Y) * 304.8:F1}" : "none";

            return new { bbWin = bbWinStr, bbWall = bbWallStr, count = solids.Count, solids };
        }
    }
}
