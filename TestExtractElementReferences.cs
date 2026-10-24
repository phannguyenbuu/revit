using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestExtractElementReferences
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var testIds = new List<long> {
                2378828, // Window_K2_Stack West
                2378831, // S1 West
                2378830, // Column A-1
                2361391, // Column B-1
                2364731, // Door D1
                2379833, // Window_K2_Stack East
                2361258, // WC dividing wall
                2379807  // Window_K2_Stack East WC
            };

            var opt = new Options { ComputeReferences = true, View = view };
            var results = new List<object>();

            foreach (var id in testIds)
            {
                var el = doc.GetElement(new ElementId(id));
                if (el == null) continue;

                var yPlanarFaces = new List<object>();
                var geom = el.get_Geometry(opt);
                if (geom != null)
                {
                    Action<GeometryElement> scanGeom = null;
                    scanGeom = (gElem) => {
                        foreach (var gObj in gElem)
                        {
                            if (gObj is Solid s && s.Faces != null)
                            {
                                foreach (Face f in s.Faces)
                                {
                                    if (f is PlanarFace pf && f.Reference != null)
                                    {
                                        // Check if normal is along Y
                                        if (Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                                        {
                                            yPlanarFaces.Add(new {
                                                coordY = Math.Round(pf.Origin.Y * FT_TO_MM, 1),
                                                normalY = Math.Round(pf.FaceNormal.Y, 1)
                                            });
                                        }
                                    }
                                }
                            }
                            else if (gObj is GeometryInstance gi)
                            {
                                var instG = gi.GetInstanceGeometry();
                                if (instG != null) scanGeom(instG);
                            }
                        }
                    };
                    scanGeom(geom);
                }

                results.Add(new {
                    id = el.Id.Value,
                    name = el.Name,
                    cat = el.Category?.Name,
                    yFacesCount = yPlanarFaces.Count,
                    yFaces = yPlanarFaces.Take(6)
                });
            }

            return new { results };
        }
    }
}
