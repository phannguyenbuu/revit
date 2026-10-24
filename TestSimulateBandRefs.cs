using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestSimulateBandRefs
    {
        private const double FT_TO_MM = 304.8;
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc.GetElement(new ElementId(312L)) as View;
            var opt = new Options { ComputeReferences = true, View = view };

            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            Func<Wall, List<double>> getWallXFaces = (w) =>
            {
                var list = new List<double>();
                if (w == null) return list;
                var geom = w.get_Geometry(opt);
                if (geom == null) return list;
                foreach (var gObj in geom)
                {
                    if (gObj is Solid s && s.Faces != null)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                            {
                                list.Add(Math.Round(pf.Origin.X * FT_TO_MM, 1));
                            }
                        }
                    }
                }
                return list;
            };

            // Band AB expanded to include Grid B wall: [50, 5600]
            var abWalls = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                return bb.Max.Y * FT_TO_MM >= 50 && bb.Min.Y * FT_TO_MM <= 5600;
            }).ToList();

            var abCoords = new HashSet<double>();
            foreach (var w in abWalls)
            {
                foreach (var x in getWallXFaces(w)) abCoords.Add(x);
            }

            // Band CD expanded to include Grid C wall: [7600, 13150]
            var cdWalls = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                return bb.Max.Y * FT_TO_MM >= 7600 && bb.Min.Y * FT_TO_MM <= 13150;
            }).ToList();

            var cdCoords = new HashSet<double>();
            foreach (var w in cdWalls)
            {
                foreach (var x in getWallXFaces(w)) cdCoords.Add(x);
            }

            return new {
                abCount = abCoords.Count,
                abSorted = abCoords.OrderBy(x => x).ToList(),
                cdCount = cdCoords.Count,
                cdSorted = cdCoords.OrderBy(x => x).ToList()
            };
        }
    }
}
