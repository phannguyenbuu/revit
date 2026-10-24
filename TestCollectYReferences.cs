using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCollectYReferences
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };

            // Helper to get Y faces from element
            Func<Element, List<Tuple<Reference, double, string>>> getYFaces = (el) => {
                var list = new List<Tuple<Reference, double, string>>();
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
                                    if (Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                                    {
                                        double yMm = Math.Round(pf.Origin.Y * FT_TO_MM, 1);
                                        list.Add(Tuple.Create(pf.Reference, yMm, $"{el.Name} ({el.Category?.Name})"));
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

            // 1. Collect on West (X <= 1500)
            var westEls = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows
                }))
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    return bb != null && bb.Min.X * FT_TO_MM <= 1500;
                })
                .ToList();

            var westRefList = new List<Tuple<Reference, double, string>>();
            foreach (var e in westEls)
            {
                westRefList.AddRange(getYFaces(e));
            }

            // Also add Grids A, B, C, D, E
            var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().ToList();
            foreach (var g in grids)
            {
                var p1 = g.Curve.GetEndPoint(0);
                var p2 = g.Curve.GetEndPoint(1);
                if (Math.Abs(p1.Y - p2.Y) < 0.01)
                {
                    westRefList.Add(Tuple.Create(new Reference(g), Math.Round(p1.Y * FT_TO_MM, 1), $"Grid {g.Name}"));
                }
            }

            var westSorted = westRefList
                .GroupBy(t => Math.Round(t.Item2 / 20.0) * 20.0) // group within 20mm
                .Select(grp => new {
                    coordY = grp.Key,
                    sources = grp.Select(x => x.Item3).Distinct().ToList()
                })
                .OrderBy(x => x.coordY)
                .ToList();

            // 2. Collect on East (X >= 36500)
            var eastEls = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Floors
                }))
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    return bb != null && bb.Max.X * FT_TO_MM >= 36500;
                })
                .ToList();

            var eastRefList = new List<Tuple<Reference, double, string>>();
            foreach (var e in eastEls)
            {
                eastRefList.AddRange(getYFaces(e));
            }
            foreach (var g in grids)
            {
                var p1 = g.Curve.GetEndPoint(0);
                var p2 = g.Curve.GetEndPoint(1);
                if (Math.Abs(p1.Y - p2.Y) < 0.01)
                {
                    eastRefList.Add(Tuple.Create(new Reference(g), Math.Round(p1.Y * FT_TO_MM, 1), $"Grid {g.Name}"));
                }
            }

            var eastSorted = eastRefList
                .GroupBy(t => Math.Round(t.Item2 / 20.0) * 20.0)
                .Select(grp => new {
                    coordY = grp.Key,
                    sources = grp.Select(x => x.Item3).Distinct().ToList()
                })
                .OrderBy(x => x.coordY)
                .ToList();

            return new {
                westCount = westSorted.Count,
                westSorted,
                eastCount = eastSorted.Count,
                eastSorted
            };
        }
    }
}
