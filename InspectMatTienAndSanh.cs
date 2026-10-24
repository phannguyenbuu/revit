using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectMatTienAndSanh
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };

            // Inspect Mat_Tien_3dsMax (2391783)
            var matTien = doc.GetElement(new ElementId(2391783));
            var yFaces = new List<object>();
            if (matTien != null)
            {
                var geom = matTien.get_Geometry(opt);
                if (geom != null)
                {
                    Action<GeometryElement> scan = null;
                    scan = (gElem) => {
                        foreach (var gObj in gElem)
                        {
                            if (gObj is Solid s && s.Faces != null)
                            {
                                foreach (Face f in s.Faces)
                                {
                                    if (f is PlanarFace pf)
                                    {
                                        if (Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                                        {
                                            yFaces.Add(new {
                                                y = Math.Round(pf.Origin.Y * FT_TO_MM, 1),
                                                normalY = Math.Round(pf.FaceNormal.Y, 2),
                                                area = Math.Round(pf.Area * FT_TO_MM * FT_TO_MM, 1),
                                                hasRef = pf.Reference != null
                                            });
                                        }
                                    }
                                }
                            }
                            else if (gObj is GeometryInstance gi)
                            {
                                var instG = gi.GetInstanceGeometry();
                                if (instG != null) scan(instG);
                            }
                        }
                    };
                    scan(geom);
                }
            }

            // Also inspect Floor NỀN COS 0.00 2 (2407783) boundary/faces
            var floor2 = doc.GetElement(new ElementId(2407783)) as Floor;
            var floorYFaces = new List<object>();
            if (floor2 != null)
            {
                var geom = floor2.get_Geometry(opt);
                if (geom != null)
                {
                    foreach (var gObj in geom)
                    {
                        if (gObj is Solid s && s.Faces != null)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                                {
                                    floorYFaces.Add(new {
                                        y = Math.Round(pf.Origin.Y * FT_TO_MM, 1),
                                        normalY = Math.Round(pf.FaceNormal.Y, 2),
                                        area = Math.Round(pf.Area * FT_TO_MM * FT_TO_MM, 1),
                                        hasRef = pf.Reference != null
                                    });
                                }
                            }
                        }
                    }
                }
            }

            return new {
                matTienYFaces = yFaces.GroupBy(x => ((dynamic)x).y).Select(g => g.First()).OrderBy(x => ((dynamic)x).y).ToList(),
                floorYFaces = floorYFaces.GroupBy(x => ((dynamic)x).y).Select(g => g.First()).OrderBy(x => ((dynamic)x).y).ToList()
            };
        }
    }
}
