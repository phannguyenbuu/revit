using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectNorthSouthDetails
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };

            Func<Element, List<Tuple<double, string, ElementId>>> getXFaces = (el) => {
                var list = new List<Tuple<double, string, ElementId>>();
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
                                        list.Add(Tuple.Create(x, $"{el.Name} ({el.Category?.Name})", el.Id));
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

            // South elements: Y in [-1000, 1500]
            var southEls = new FilteredElementCollector(doc, view.Id)
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
                    return bb.Max.Y * FT_TO_MM > -1000 && bb.Min.Y * FT_TO_MM < 1500;
                })
                .ToList();

            var southFaces = new List<Tuple<double, string, ElementId>>();
            foreach (var e in southEls) southFaces.AddRange(getXFaces(e));

            // North elements: Y in [13500, 15500]
            var northEls = new FilteredElementCollector(doc, view.Id)
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
                    return bb.Max.Y * FT_TO_MM > 13500 && bb.Min.Y * FT_TO_MM < 15500;
                })
                .ToList();

            var northFaces = new List<Tuple<double, string, ElementId>>();
            foreach (var e in northEls) northFaces.AddRange(getXFaces(e));

            return new {
                south = southFaces.GroupBy(f => Math.Round(f.Item1 / 10.0) * 10.0).Select(g => new { x = g.Key, items = g.Select(x => x.Item2).Distinct().Take(3) }).OrderBy(x => x.x),
                north = northFaces.GroupBy(f => Math.Round(f.Item1 / 10.0) * 10.0).Select(g => new { x = g.Key, items = g.Select(x => x.Item2).Distinct().Take(3) }).OrderBy(x => x.x)
            };
        }
    }
}
