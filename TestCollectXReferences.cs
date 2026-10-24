using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCollectXReferences
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };

            // Helper to get X faces from element
            Func<Element, List<Tuple<double, Reference, string>>> getXFaces = (el) => {
                var list = new List<Tuple<double, Reference, string>>();
                if (el == null) return list;
                var geom = el.get_Geometry(opt);
                if (geom == null) return list;

                Action<GeometryElement> scan = null;
                scan = (gElem) => {
                    foreach (var gObj in gElem)
                    {
                        if (gObj is Solid s && s.Faces != null)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && pf.Reference != null)
                                {
                                    if (Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                    {
                                        double x = Math.Round(pf.Origin.X * FT_TO_MM, 1);
                                        list.Add(Tuple.Create(x, pf.Reference, $"{el.Name} ({el.Category?.Name}, id={el.Id.Value})"));
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
                return list;
            };

            // Grids 1 to 11
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

            // 1. Band AB: Y in [0, 5400]
            var abRefs = new List<Tuple<double, Reference, string>>();
            foreach (var g in vGrids)
            {
                abRefs.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
            }
            var abEls = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_StructuralColumns
                }))
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    return bb.Max.Y * FT_TO_MM > 50 && bb.Min.Y * FT_TO_MM < 5350;
                })
                .ToList();
            foreach (var e in abEls) abRefs.AddRange(getXFaces(e));

            // Group AB within 35mm
            var abGrouped = abRefs
                .GroupBy(r => Math.Round(r.Item1 / 50.0) * 50.0)
                .Select(grp => new {
                    coordX = grp.Key,
                    sources = grp.Select(x => x.Item3).Distinct().Take(3).ToList()
                })
                .OrderBy(x => x.coordX)
                .ToList();

            // 2. Band CD: Y in [7800, 13200]
            var cdRefs = new List<Tuple<double, Reference, string>>();
            foreach (var g in vGrids)
            {
                cdRefs.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
            }
            var cdEls = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Stairs,
                    BuiltInCategory.OST_StairsRuns,
                    BuiltInCategory.OST_StairsLandings
                }))
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    return bb.Max.Y * FT_TO_MM > 7850 && bb.Min.Y * FT_TO_MM < 13150;
                })
                .ToList();
            foreach (var e in cdEls) cdRefs.AddRange(getXFaces(e));

            // Group CD within 35mm
            var cdGrouped = cdRefs
                .GroupBy(r => Math.Round(r.Item1 / 50.0) * 50.0)
                .Select(grp => new {
                    coordX = grp.Key,
                    sources = grp.Select(x => x.Item3).Distinct().Take(3).ToList()
                })
                .OrderBy(x => x.coordX)
                .ToList();

            return new {
                abCount = abGrouped.Count,
                abGrouped,
                cdCount = cdGrouped.Count,
                cdGrouped
            };
        }
    }
}
