using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestBuildInteriorChainsWithDoors
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc.GetElement(new ElementId(312L)) as ViewPlan;
            var opt = new Options { ComputeReferences = true, View = view };

            var dimType = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .FirstOrDefault(dt => dt.Name == "Linear Dimension Style - Transparent" || dt.Name.Contains("SecretInternal"));

            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            var vGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => Math.Abs(g.Curve.GetEndPoint(0).X - g.Curve.GetEndPoint(1).X) < 0.01)
                .OrderBy(g => g.Curve.GetEndPoint(0).X)
                .ToList();

            Func<Wall, List<Tuple<double, Reference>>> getWallXFaces = (w) =>
            {
                var list = new List<Tuple<double, Reference>>();
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
                                double x = Math.Round(pf.Origin.X * FT_TO_MM, 1);
                                list.Add(Tuple.Create(x, pf.Reference));
                            }
                        }
                    }
                }
                return list;
            };

            Func<double, double, List<Tuple<double, Reference>>> collectBandRefs = (minY, maxY) =>
            {
                var list = new List<Tuple<double, Reference>>();
                foreach (var g in vGrids)
                {
                    list.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), new Reference(g)));
                }
                var bandWalls = allWalls.Where(w => {
                    var bb = w.get_BoundingBox(view);
                    if (bb == null) return false;
                    return bb.Max.Y * FT_TO_MM >= minY && bb.Min.Y * FT_TO_MM <= maxY;
                }).ToList();
                foreach (var w in bandWalls) list.AddRange(getWallXFaces(w));
                return list;
            };

            // Test collection with expanded ranges
            var abAvailable = collectBandRefs(50, 5600);
            var cdAvailable = collectBandRefs(7600, 13150);

            // Door targets
            var abDoorTargets = new List<double> { 1750, 3150, 5950, 7350, 8750, 10150, 13150, 14550, 15550, 16550, 22650, 23650, 30050, 31050, 34750, 35550 };
            var cdDoorTargets = new List<double> { 4450, 5750, 8387, 9387, 15487, 16487, 20250, 21250, 22862, 23862, 24337, 25337, 28412, 29412, 31950, 33150, 33550, 34350 };

            var abMatchedDoors = new List<object>();
            foreach (var dt in abDoorTargets)
            {
                var match = abAvailable.Where(r => Math.Abs(r.Item1 - dt) <= 20.0).FirstOrDefault();
                abMatchedDoors.Add(new { target = dt, matched = match != null ? match.Item1 : -1 });
            }

            var cdMatchedDoors = new List<object>();
            foreach (var dt in cdDoorTargets)
            {
                var match = cdAvailable.Where(r => Math.Abs(r.Item1 - dt) <= 20.0).FirstOrDefault();
                cdMatchedDoors.Add(new { target = dt, matched = match != null ? match.Item1 : -1 });
            }

            return new {
                abAvailableCount = abAvailable.Count,
                abDoorMatches = abMatchedDoors,
                cdAvailableCount = cdAvailable.Count,
                cdDoorMatches = cdMatchedDoors
            };
        }
    }
}
