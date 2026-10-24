using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestWallC
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No doc" };

            var opt = new Options { ComputeReferences = true, View = view };

            var walls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var bb = w.get_BoundingBox(view);
                    if (bb == null) return false;
                    double yMin = bb.Min.Y * 304.8;
                    double yMax = bb.Max.Y * 304.8;
                    return yMax >= 7500 && yMin <= 8100;
                })
                .ToList();

            var results = new List<object>();
            foreach (var w in walls)
            {
                var xFaces = new List<double>();
                var geom = w.get_Geometry(opt);
                if (geom != null)
                {
                    foreach (var gObj in geom)
                    {
                        if (gObj is Solid s)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                {
                                    xFaces.Add(Math.Round(pf.Origin.X * 304.8, 1));
                                }
                            }
                        }
                    }
                }
                xFaces.Sort();
                results.Add(new {
                    id = w.Id.Value,
                    name = w.Name,
                    xFaces
                });
            }

            return new { wallCount = walls.Count, walls = results };
        }
    }
}
