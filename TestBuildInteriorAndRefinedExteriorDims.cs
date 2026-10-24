using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestBuildInteriorAndRefinedExteriorDims
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

            // Helper to build a clean sorted chain
            Func<List<DimPoint>, double, double, Dimension> buildChain = (candidates, yMm, minGapMm) => {
                var sorted = candidates.OrderBy(p => p.X).ToList();
                var filtered = new List<DimPoint>();
                foreach (var p in sorted)
                {
                    if (p.Ref == null) continue;
                    if (filtered.Count == 0 || (p.X - filtered.Last().X) >= minGapMm)
                    {
                        filtered.Add(p);
                    }
                }

                if (filtered.Count < 2) return null;

                var refArray = new ReferenceArray();
                foreach (var p in filtered) refArray.Append(p.Ref);

                double yFt = yMm * MM_TO_FT;
                double x1Ft = (filtered.First().X - 1000.0) * MM_TO_FT;
                double x2Ft = (filtered.Last().X + 1000.0) * MM_TO_FT;
                var line = Line.CreateBound(new XYZ(x1Ft, yFt, 0), new XYZ(x2Ft, yFt, 0));

                return doc.Create.NewDimension(view, line, refArray, dimType);
            };

            var results = new List<object>();
            var newDimIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Build Horizontal Interior & Refined Exterior Dimensions"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);
                tx.Start();

                // 1. Delete old 2408820 (South L3) and 2408823 (North L3)
                foreach (var oldId in new long[] { 2408820, 2408823 })
                {
                    try { doc.Delete(new ElementId(oldId)); } catch { }
                }

                // 2. CHAIN 1: South Exterior Refined Detail at Y = -1200 mm
                var southPoints = new List<DimPoint>();
                foreach (var g in vGrids) southPoints.Add(new DimPoint { Ref = new Reference(g), X = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), Name = $"Grid {g.Name}" });
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
                foreach (var e in southEls) southPoints.AddRange(getXPoints(e));
                var dSouth = buildChain(southPoints, -1200.0, 150.0);
                if (dSouth != null) newDimIds.Add(dSouth.Id);

                // 3. CHAIN 2: North Exterior Refined Detail at Y = 16000 mm
                var northPoints = new List<DimPoint>();
                foreach (var g in vGrids) northPoints.Add(new DimPoint { Ref = new Reference(g), X = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), Name = $"Grid {g.Name}" });
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
                        return bb.Max.Y * FT_TO_MM > 13500 && bb.Min.Y * FT_TO_MM < 16500;
                    })
                    .ToList();
                foreach (var e in northEls) northPoints.AddRange(getXPoints(e));
                var dNorth = buildChain(northPoints, 16000.0, 150.0);
                if (dNorth != null) newDimIds.Add(dNorth.Id);

                // 4. CHAIN 3: Interior Band AB at Y = 3000 mm
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
                var dAB = buildChain(abPoints, 3000.0, 150.0);
                if (dAB != null) newDimIds.Add(dAB.Id);

                // 5. CHAIN 4: Interior Band CD at Y = 10800 mm
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
                var dCD = buildChain(cdPoints, 10800.0, 150.0);
                if (dCD != null) newDimIds.Add(dCD.Id);

                tx.Commit();
            }

            // Set selection to new dimensions
            if (newDimIds.Count > 0)
            {
                uidoc.Selection.SetElementIds(newDimIds);
            }

            Func<Dimension, List<double>> getSegs = (d) => {
                var sList = new List<double>();
                if (d == null) return sList;
                if (d.Segments != null && d.Segments.Size > 0)
                {
                    foreach (DimensionSegment s in d.Segments)
                    {
                        if (s.Value.HasValue) sList.Add(Math.Round(s.Value.Value * FT_TO_MM, 0));
                    }
                }
                else if (d.Value.HasValue)
                {
                    sList.Add(Math.Round(d.Value.Value * FT_TO_MM, 0));
                }
                return sList;
            };

            var finalDims = newDimIds.Select(id => {
                var d = doc.GetElement(id) as Dimension;
                var segs = getSegs(d);
                return new {
                    id = id.Value,
                    y = d?.Curve is Line l ? Math.Round(l.Origin.Y * FT_TO_MM, 0) : 0,
                    segCount = segs.Count,
                    segs = string.Join(", ", segs)
                };
            }).ToList();

            return new {
                success = true,
                count = finalDims.Count,
                dims = finalDims
            };
        }
    }
}
