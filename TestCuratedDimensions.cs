using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCuratedDimensions
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

            Func<List<Tuple<double, Reference, string>>, double, double, Reference> findNearestRef = (pool, targetY, maxDist) => {
                var match = pool.Where(p => Math.Abs(p.Item1 - targetY) <= maxDist)
                                .OrderBy(p => Math.Abs(p.Item1 - targetY))
                                .FirstOrDefault();
                return match?.Item2;
            };

            // 1. POOLS
            // West Wall Pool
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

            // Clean, non-redundant West Wall Targets:
            double[] westWallTargets = new double[] {
                0,      // Grid A
                150,    // Col A-1 face
                350,    // K2 Stack 1 start
                1250,   // K2 Stack 1 end
                1550,   // K2 Stack 2 start
                2450,   // K2 Stack 2 end
                2900,   // S1 start
                4400,   // S1 end
                5100,   // Col B-1 face
                5400,   // Grid B
                5650,   // Door D1 start
                7550,   // Door D1 end
                7700,   // Col C-1 face
                7800,   // Grid C
                8100,   // Col C-1 top
                8800,   // S1 start
                10300,  // S1 end
                10750,  // K2 Stack 3 start
                11650,  // K2 Stack 3 end
                11950,  // K2 Stack 4 start
                12850,  // K2 Stack 4 end
                13050,  // Col D-1 face
                13200,  // Grid D
                14900   // Grid E
            };

            // East Wall Pool
            var eastPool = new List<Tuple<double, Reference, string>>();
            foreach (var g in hGrids) eastPool.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
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
            foreach (var e in eastEls) eastPool.AddRange(getYFaces(e));

            // Clean East Wall Targets:
            double[] eastWallTargets = new double[] {
                0,      // Grid A
                150,    // Col A-11 face
                350,    // K2 Stack 1 start
                1250,   // K2 Stack 1 end
                1550,   // K2 Stack 2 start
                2450,   // K2 Stack 2 end
                5100,   // Col B-11 face
                5400,   // Grid B
                5500,   // Tam Cap landing
                5900,   // Door D2 start
                7300,   // Door D2 end
                7700,   // Tam Cap landing / Col C-11 face
                7800,   // Grid C
                8100,   // Col C-11 top
                9400,   // WC divider wall
                9500,   // WC divider wall
                10750,  // K2 Stack 3 start
                11650,  // K2 Stack 3 end
                11950,  // K2 Stack 4 start
                12850,  // K2 Stack 4 end
                13050,  // Col D-11 face
                13200,  // Grid D
                14900   // Grid E
            };

            // Mat Tien / Sanh Chinh Pool
            var matTienPool = new List<Tuple<double, Reference, string>>();
            foreach (var g in hGrids) matTienPool.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
            var matTien = doc.GetElement(new ElementId(2391783));
            if (matTien != null) matTienPool.AddRange(getYFaces(matTien));
            var doorD1 = doc.GetElement(new ElementId(2364731)) as FamilyInstance;
            if (doorD1 != null)
            {
                var leftRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Left);
                var rightRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Right);
                var bb = doorD1.get_BoundingBox(view);
                if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                {
                    matTienPool.Add(Tuple.Create(Math.Round(bb.Min.Y * FT_TO_MM, 1), leftRefs[0], "Door D1 Left"));
                    matTienPool.Add(Tuple.Create(Math.Round(bb.Max.Y * FT_TO_MM, 1), rightRefs[0], "Door D1 Right"));
                }
            }

            // Clean Mat Tien Targets:
            double[] matTienTargets = new double[] {
                0,       // Grid A
                3568,    // Portico Col South outer
                4768,    // Portico Col South inner
                5400,    // Grid B
                5575,    // Door D1 start
                7625,    // Door D1 end
                7800,    // Grid C
                8432,    // Portico Col North inner
                9632,    // Portico Col North outer
                10443,   // North wing projection
                13200,   // Grid D
                13542,   // Mat Tien North edge
                14900    // Grid E
            };

            Func<Line, double[], List<Tuple<double, Reference, string>>, double, object> testBuild = (line, targets, pool, maxDist) => {
                var found = new List<Tuple<double, Reference>>();
                var missing = new List<double>();
                foreach (var t in targets)
                {
                    var r = findNearestRef(pool, t, maxDist);
                    if (r != null) found.Add(Tuple.Create(t, r));
                    else missing.Add(t);
                }

                var refArr = new ReferenceArray();
                foreach (var f in found) refArr.Append(f.Item2);

                Dimension dim = null;
                string err = null;
                var segs = new List<double>();

                try
                {
                    dim = doc.Create.NewDimension(view, line, refArr, dimType);
                    if (dim != null)
                    {
                        if (dim.Segments != null && dim.Segments.Size > 0)
                        {
                            foreach (DimensionSegment seg in dim.Segments)
                            {
                                if (seg.Value.HasValue) segs.Add(Math.Round(seg.Value.Value * FT_TO_MM, 1));
                            }
                        }
                        else if (dim.Value.HasValue)
                        {
                            segs.Add(Math.Round(dim.Value.Value * FT_TO_MM, 1));
                        }
                        doc.Delete(dim.Id);
                    }
                }
                catch (Exception ex)
                {
                    err = ex.Message;
                }

                return new {
                    targetCount = targets.Length,
                    foundCount = found.Count,
                    missing,
                    success = dim != null,
                    error = err,
                    segments = segs
                };
            };

            using (var tx = new Transaction(doc, "Test Curated Dims Refined"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);

                tx.Start();

                var lineWestWall = Line.CreateBound(new XYZ(-1200.0 * MM_TO_FT, 0, 0), new XYZ(-1200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resWestWall = testBuild(lineWestWall, westWallTargets, westPool, 25.0);

                var lineEastWall = Line.CreateBound(new XYZ(40500.0 * MM_TO_FT, 0, 0), new XYZ(40500.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resEastWall = testBuild(lineEastWall, eastWallTargets, eastPool, 25.0);

                var lineMatTien = Line.CreateBound(new XYZ(-7200.0 * MM_TO_FT, 0, 0), new XYZ(-7200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resMatTien = testBuild(lineMatTien, matTienTargets, matTienPool, 25.0);

                tx.RollBack();

                return new {
                    resWestWall,
                    resEastWall,
                    resMatTien
                };
            }
        }
    }
}
