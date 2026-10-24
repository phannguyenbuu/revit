using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestDynamicWallDimension
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var options = args.TryGetProperty("args", out var n) && n.ValueKind == System.Text.Json.JsonValueKind.Object ? n : args;
            ViewPlan? view = null;
            if (options.TryGetProperty("viewId", out var pViewId) || args.TryGetProperty("viewId", out pViewId))
            {
                view = doc.GetElement(new ElementId(pViewId.GetInt64())) as ViewPlan;
            }
            if (view == null)
            {
                view = uidoc?.ActiveView as ViewPlan;
            }
            if (view == null) return new { error = "No viewplan found" };

            var opt = new Options { ComputeReferences = true, View = view };

            // 1. Get grids
            var vGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => {
                    var p1 = g.Curve.GetEndPoint(0);
                    var p2 = g.Curve.GetEndPoint(1);
                    return Math.Abs(p1.X - p2.X) < 0.01;
                })
                .OrderBy(g => g.Curve.GetEndPoint(0).X)
                .ToList();

            var hGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => {
                    var p1 = g.Curve.GetEndPoint(0);
                    var p2 = g.Curve.GetEndPoint(1);
                    return Math.Abs(p1.Y - p2.Y) < 0.01;
                })
                .OrderBy(g => g.Curve.GetEndPoint(0).Y)
                .ToList();

            var gridB = hGrids.FirstOrDefault(g => g.Name == "B");
            var gridC = hGrids.FirstOrDefault(g => g.Name == "C");

            double yB = gridB != null ? gridB.Curve.GetEndPoint(0).Y * FT_TO_MM : 5400.0;
            double yC = gridC != null ? gridC.Curve.GetEndPoint(0).Y * FT_TO_MM : 7800.0;

            // 2. Collect all walls in view
            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            // Helper to get all X-perpendicular planar faces with references from a wall
            Func<Wall, List<Tuple<double, Reference, string>>> getWallXPlanarFaces = (w) =>
            {
                var list = new List<Tuple<double, Reference, string>>();
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
                                list.Add(Tuple.Create(x, pf.Reference, $"Wall_{w.Id.Value}"));
                            }
                        }
                    }
                }
                return list;
            };

            // Test building Band AB:
            // Walls along Grid B (Y in [5200, 5600])
            var bWalls = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                double minY = bb.Min.Y * FT_TO_MM;
                double maxY = bb.Max.Y * FT_TO_MM;
                return maxY >= (yB - 300) && minY <= (yB + 300);
            }).ToList();

            // Also partition walls between A and B (Y in [1000, 5300]) that are vertical (oriented along Y)
            var abPartitions = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                double minY = bb.Min.Y * FT_TO_MM;
                double maxY = bb.Max.Y * FT_TO_MM;
                // Vertical wall spanning into the band
                return maxY >= (yB - 1000) && minY <= (yB - 200);
            }).ToList();

            var abRawPoints = new List<Tuple<double, Reference, string>>();
            foreach (var w in bWalls) abRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var w in abPartitions) abRawPoints.AddRange(getWallXPlanarFaces(w));

            // Also add vertical grids
            foreach (var g in vGrids)
            {
                double x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1);
                abRawPoints.Add(Tuple.Create(x, new Reference(g), $"Grid_{g.Name}"));
            }

            // Clean & sort: deduplicate points within 15mm
            var abSorted = abRawPoints.OrderBy(p => p.Item1).ToList();
            var abClean = new List<Tuple<double, Reference, string>>();
            foreach (var p in abSorted)
            {
                if (abClean.Count == 0 || Math.Abs(abClean.Last().Item1 - p.Item1) > 20.0)
                {
                    abClean.Add(p);
                }
            }

            // Same for Band CD:
            var cWalls = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                double minY = bb.Min.Y * FT_TO_MM;
                double maxY = bb.Max.Y * FT_TO_MM;
                return maxY >= (yC - 300) && minY <= (yC + 300);
            }).ToList();

            var cdPartitions = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                double minY = bb.Min.Y * FT_TO_MM;
                double maxY = bb.Max.Y * FT_TO_MM;
                return maxY >= (yC + 200) && minY <= (yC + 1500);
            }).ToList();

            var cdRawPoints = new List<Tuple<double, Reference, string>>();
            foreach (var w in cWalls) cdRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var w in cdPartitions) cdRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var g in vGrids)
            {
                double x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1);
                cdRawPoints.Add(Tuple.Create(x, new Reference(g), $"Grid_{g.Name}"));
            }

            var cdSorted = cdRawPoints.OrderBy(p => p.Item1).ToList();
            var cdClean = new List<Tuple<double, Reference, string>>();
            foreach (var p in cdSorted)
            {
                if (cdClean.Count == 0 || Math.Abs(cdClean.Last().Item1 - p.Item1) > 20.0)
                {
                    cdClean.Add(p);
                }
            }

            return new {
                viewName = view.Name,
                bWallsCount = bWalls.Count,
                abPartitionsCount = abPartitions.Count,
                abPointsCount = abClean.Count,
                abPoints = abClean.Select(p => new { x = p.Item1, src = p.Item3 }).ToList(),
                cWallsCount = cWalls.Count,
                cdPartitionsCount = cdPartitions.Count,
                cdPointsCount = cdClean.Count,
                cdPoints = cdClean.Select(p => new { x = p.Item1, src = p.Item3 }).ToList()
            };
        }
    }
}
