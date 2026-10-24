using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairRunGeometry
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var run = doc.GetElement(new ElementId(2368347));
            var opt = new Options { ComputeReferences = true, View = view };
            var geom = run?.get_Geometry(opt);

            var faceList = new List<object>();
            if (geom != null)
            {
                foreach (var g in geom)
                {
                    if (g is Solid s && s.Faces != null)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf)
                            {
                                faceList.Add(new {
                                    hasRef = pf.Reference != null,
                                    normal = new { x = Math.Round(pf.FaceNormal.X, 2), y = Math.Round(pf.FaceNormal.Y, 2), z = Math.Round(pf.FaceNormal.Z, 2) },
                                    origin = new { x = Math.Round(pf.Origin.X * FT_TO_MM, 1), y = Math.Round(pf.Origin.Y * FT_TO_MM, 1) }
                                });
                            }
                            else
                            {
                                faceList.Add(new { type = f.GetType().Name });
                            }
                        }
                    }
                    else
                    {
                        faceList.Add(new { type = g.GetType().Name });
                    }
                }
            }

            return new { geomCount = geom != null ? geom.Count() : 0, faceCount = faceList.Count, faces = faceList.Take(20) };
        }
    }
}
