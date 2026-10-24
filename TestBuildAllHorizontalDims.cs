using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestBuildAllHorizontalDims
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public class DimPoint
        {
            public Reference Ref { get; set; }
            public double X { get; set; }
            public string Name { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };

            var dimType = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .FirstOrDefault(dt => dt.StyleType == DimensionStyleType.Linear && dt.Name == "Linear Dimension Style")
                ?? new FilteredElementCollector(doc).OfClass(typeof(DimensionType)).Cast<DimensionType>().First();

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

            Func<Element, List<DimPoint>> getXPoints = (el) => {
                var list = new List<DimPoint>();
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
                                        list.Add(new DimPoint {
                                            Ref = pf.Reference,
                                            X = x,
                                            Name = $"{el.Name} ({el.Category?.Name})"
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
                return list;
            };

            // Test collecting for Band AB
            var abPoints = new List<DimPoint>();
            foreach (var g in vGrids) abPoints.Add(new DimPoint { Ref = new Reference(g), X = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), Name = $"Grid {g.Name}" });

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
                    return bb.Max.Y * FT_TO_MM > 100 && bb.Min.Y * FT_TO_MM < 5300;
                })
                .ToList();

            foreach (var e in abEls) abPoints.AddRange(getXPoints(e));

            // Test collecting for Band CD
            var cdPoints = new List<DimPoint>();
            foreach (var g in vGrids) cdPoints.Add(new DimPoint { Ref = new Reference(g), X = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), Name = $"Grid {g.Name}" });

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
                    return bb.Max.Y * FT_TO_MM > 7900 && bb.Min.Y * FT_TO_MM < 13100;
                })
                .ToList();

            foreach (var e in cdEls) cdPoints.AddRange(getXPoints(e));

            return new {
                abRawCount = abPoints.Count,
                cdRawCount = cdPoints.Count
            };
        }
    }
}
