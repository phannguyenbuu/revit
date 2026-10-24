using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowTransform
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            if (win == null) return new { error = "No win" };

            var hostWall = win.Host as Wall;
            var wallLoc = (hostWall.Location as LocationCurve)?.Curve;
            var winLoc = (win.Location as LocationPoint)?.Point;

            var tr = win.GetTransform();

            var opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
            var geom = win.get_Geometry(opt);
            var solids = new List<object>();

            foreach (var obj in geom)
            {
                if (obj is GeometryInstance gi)
                {
                    var symbolGeom = gi.GetSymbolGeometry();
                    foreach (var so in symbolGeom)
                    {
                        if (so is Solid s && s.Volume > 0.00001)
                        {
                            var bb = s.GetBoundingBox();
                            solids.Add(new
                            {
                                type = "SymbolSolid",
                                min = $"[{bb.Min.X*304.8:F1}, {bb.Min.Y*304.8:F1}, {bb.Min.Z*304.8:F1}]",
                                max = $"[{bb.Max.X*304.8:F1}, {bb.Max.Y*304.8:F1}, {bb.Max.Z*304.8:F1}]"
                            });
                        }
                    }

                    var instGeom = gi.GetInstanceGeometry();
                    foreach (var so in instGeom)
                    {
                        if (so is Solid s && s.Volume > 0.00001)
                        {
                            var bb = s.GetBoundingBox();
                            solids.Add(new
                            {
                                type = "InstanceSolid",
                                min = $"[{bb.Min.X*304.8:F1}, {bb.Min.Y*304.8:F1}, {bb.Min.Z*304.8:F1}]",
                                max = $"[{bb.Max.X*304.8:F1}, {bb.Max.Y*304.8:F1}, {bb.Max.Z*304.8:F1}]"
                            });
                        }
                    }
                }
            }

            return new
            {
                winLoc = winLoc != null ? $"[{winLoc.X*304.8:F1}, {winLoc.Y*304.8:F1}, {winLoc.Z*304.8:F1}]" : "null",
                basisX = $"[{tr.BasisX.X:F3}, {tr.BasisX.Y:F3}, {tr.BasisX.Z:F3}]",
                basisY = $"[{tr.BasisY.X:F3}, {tr.BasisY.Y:F3}, {tr.BasisY.Z:F3}]",
                basisZ = $"[{tr.BasisZ.X:F3}, {tr.BasisZ.Y:F3}, {tr.BasisZ.Z:F3}]",
                origin = $"[{tr.Origin.X*304.8:F1}, {tr.Origin.Y*304.8:F1}, {tr.Origin.Z*304.8:F1}]",
                facing = $"[{win.FacingOrientation.X:F3}, {win.FacingOrientation.Y:F3}, {win.FacingOrientation.Z:F3}]",
                hand = $"[{win.HandOrientation.X:F3}, {win.HandOrientation.Y:F3}, {win.HandOrientation.Z:F3}]",
                solids
            };
        }
    }
}
