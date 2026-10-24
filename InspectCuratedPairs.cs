using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCuratedPairs
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

            var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().ToList();
            var hGrids = grids.Where(g => {
                var p1 = g.Curve.GetEndPoint(0);
                var p2 = g.Curve.GetEndPoint(1);
                return Math.Abs(p1.Y - p2.Y) < 0.01;
            }).OrderBy(g => g.Curve.GetEndPoint(0).Y).ToList();

            Func<Element, List<Tuple<double, Reference, string>>> getYFaces = (el) => {
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
                                    if (Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                                    {
                                        double y = Math.Round(pf.Origin.Y * FT_TO_MM, 1);
                                        list.Add(Tuple.Create(y, pf.Reference, $"{el.Name} ({el.Category?.Name}, id={el.Id.Value})"));
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

            var westPool = new List<Tuple<double, Reference, string>>();
            foreach (var g in hGrids) westPool.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
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
                    return bb != null && bb.Min.X * FT_TO_MM <= 1500 && bb.Max.X * FT_TO_MM >= -500;
                })
                .ToList();
            foreach (var e in westEls) westPool.AddRange(getYFaces(e));

            // Look at pool entries between -100 and 500
            var nearZero = westPool.Where(p => p.Item1 >= -100 && p.Item1 <= 500).Select(p => new { y = p.Item1, src = p.Item3 }).Distinct().ToList();

            return new { nearZero };
        }
    }
}
