using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestSortedRefChain
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

            // Function to evaluate the actual projected coordinate along dimension line direction (Y)
            Func<Reference, double?> getProjY = (r) => {
                var el = doc.GetElement(r.ElementId);
                if (el is Grid g)
                {
                    return g.Curve.GetEndPoint(0).Y * FT_TO_MM;
                }
                var geoObj = el?.GetGeometryObjectFromReference(r);
                if (geoObj is PlanarFace pf)
                {
                    // If it's from a family instance, pf.Origin is already transformed to document coordinates
                    return pf.Origin.Y * FT_TO_MM;
                }
                return null;
            };

            // Test building West Wall Detail (Dim 2 at X = -1200 mm)
            // Specific elements:
            // Grid A (0)
            // Wall 2378815 at 350
            // Wall 2378819 at 1250
            // Wall 2378819 at 1550
            // Wall 2378823 at 2450
            // Wall 2362083 at 2900 (or S1)
            // Wall 2362083 at 4400 (or S1)
            // Grid B at 5400
            // Wall 2362083 at 5650 (Door D1)
            // Wall 2362083 at 7550 (Door D1)
            // Grid C at 7800
            // Wall 2362083 at 8800 (or S1)
            // Wall 2361560 at 10300
            // Wall 2361558 at 10750
            // Wall 2361554 at 11650
            // Wall 2361554 at 11950
            // Wall 2361549 at 12850
            // Grid D at 13200
            // Grid E at 14900

            var westRefList = new List<Tuple<double, Reference, string>>();
            westRefList.Add(Tuple.Create(0.0, new Reference(hGrids.First(g => g.Name == "A")), "Grid A"));

            var westWallIds = new long[] {
                2378815, 2378819, 2378823, 2362083, 2361560, 2361558, 2361554, 2361549
            };
            foreach (var wId in westWallIds)
            {
                var el = doc.GetElement(new ElementId(wId));
                var geom = el?.get_Geometry(opt);
                if (geom == null) continue;
                foreach (var gObj in geom)
                {
                    if (gObj is Solid s && s.Faces != null)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                            {
                                double y = Math.Round(pf.Origin.Y * FT_TO_MM, 1);
                                if (y >= 300 && y <= 13000)
                                {
                                    westRefList.Add(Tuple.Create(y, pf.Reference, $"{el.Name} id={wId}"));
                                }
                            }
                        }
                    }
                }
            }
            westRefList.Add(Tuple.Create(5400.0, new Reference(hGrids.First(g => g.Name == "B")), "Grid B"));
            westRefList.Add(Tuple.Create(7800.0, new Reference(hGrids.First(g => g.Name == "C")), "Grid C"));
            westRefList.Add(Tuple.Create(13200.0, new Reference(hGrids.First(g => g.Name == "D")), "Grid D"));
            westRefList.Add(Tuple.Create(14900.0, new Reference(hGrids.First(g => g.Name == "E")), "Grid E"));

            // Filter targets for West Wall:
            double[] westTargets = new double[] {
                0, 350, 1250, 1550, 2450, 2900, 4400, 5400, 5650, 7550, 7800, 8800, 10300, 10750, 11650, 11950, 12850, 13200, 14900
            };

            var westFinalList = new List<Tuple<double, Reference>>();
            foreach (var t in westTargets)
            {
                var match = westRefList.Where(p => Math.Abs(p.Item1 - t) <= 30.0).OrderBy(p => Math.Abs(p.Item1 - t)).FirstOrDefault();
                if (match != null && !westFinalList.Any(x => Math.Abs(x.Item1 - match.Item1) < 20.0))
                {
                    westFinalList.Add(Tuple.Create(match.Item1, match.Item2));
                }
            }
            westFinalList = westFinalList.OrderBy(x => x.Item1).ToList();

            // Test East Wall Detail (Dim 3 at X = 40500 mm)
            var eastRefList = new List<Tuple<double, Reference, string>>();
            eastRefList.Add(Tuple.Create(0.0, new Reference(hGrids.First(g => g.Name == "A")), "Grid A"));

            var eastWallIds = new long[] {
                2379821, 2379825, 2361336, 2361333, 2408364, 2361271, 2361258, 2361274, 2379798, 2361533
            };
            foreach (var wId in eastWallIds)
            {
                var el = doc.GetElement(new ElementId(wId));
                var geom = el?.get_Geometry(opt);
                if (geom == null) continue;
                foreach (var gObj in geom)
                {
                    if (gObj is Solid s && s.Faces != null)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                            {
                                double y = Math.Round(pf.Origin.Y * FT_TO_MM, 1);
                                if (y >= 300 && y <= 13000)
                                {
                                    eastRefList.Add(Tuple.Create(y, pf.Reference, $"{el.Name} id={wId}"));
                                }
                            }
                        }
                    }
                }
            }
            eastRefList.Add(Tuple.Create(5400.0, new Reference(hGrids.First(g => g.Name == "B")), "Grid B"));
            eastRefList.Add(Tuple.Create(7800.0, new Reference(hGrids.First(g => g.Name == "C")), "Grid C"));
            eastRefList.Add(Tuple.Create(13200.0, new Reference(hGrids.First(g => g.Name == "D")), "Grid D"));
            eastRefList.Add(Tuple.Create(14900.0, new Reference(hGrids.First(g => g.Name == "E")), "Grid E"));

            double[] eastTargets = new double[] {
                0, 350, 1250, 1550, 2450, 5400, 5500, 5900, 7300, 7700, 7800, 9400, 9500, 10750, 11650, 11950, 12850, 13200, 14900
            };

            var eastFinalList = new List<Tuple<double, Reference>>();
            foreach (var t in eastTargets)
            {
                var match = eastRefList.Where(p => Math.Abs(p.Item1 - t) <= 30.0).OrderBy(p => Math.Abs(p.Item1 - t)).FirstOrDefault();
                if (match != null && !eastFinalList.Any(x => Math.Abs(x.Item1 - match.Item1) < 20.0))
                {
                    eastFinalList.Add(Tuple.Create(match.Item1, match.Item2));
                }
            }
            eastFinalList = eastFinalList.OrderBy(x => x.Item1).ToList();

            // Test West Sảnh Chính & Facade (Dim 1 at X = -7200 mm)
            // Major features along West facade:
            // Grid A (0)
            // Window K2 stack 1 edge (350)
            // Window S1 edge (2900)
            // Portico south pier (4768)
            // Grid B (5400)
            // Door D1 opening (5650, 7550)
            // Grid C (7800)
            // Portico north pier (8432)
            // Window S1 edge (10300)
            // Window K2 stack 4 edge (12850)
            // Grid D (13200)
            // Grid E (14900)
            var westFacadeTargets = new double[] {
                0, 350, 2900, 4400, 5400, 5650, 7550, 7800, 8800, 10300, 12850, 13200, 14900
            };
            var westFacadeFinalList = new List<Tuple<double, Reference>>();
            foreach (var t in westFacadeTargets)
            {
                var match = westRefList.Where(p => Math.Abs(p.Item1 - t) <= 30.0).OrderBy(p => Math.Abs(p.Item1 - t)).FirstOrDefault();
                if (match != null && !westFacadeFinalList.Any(x => Math.Abs(x.Item1 - match.Item1) < 20.0))
                {
                    westFacadeFinalList.Add(Tuple.Create(match.Item1, match.Item2));
                }
            }
            westFacadeFinalList = westFacadeFinalList.OrderBy(x => x.Item1).ToList();

            // Try creating dimensions
            using (var tx = new Transaction(doc, "Test Dimension Chains"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);
                tx.Start();

                // West Wall
                var refArrW = new ReferenceArray();
                foreach (var w in westFinalList) refArrW.Append(w.Item2);
                var lineW = Line.CreateBound(new XYZ(-1200.0 * MM_TO_FT, 0, 0), new XYZ(-1200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var dimW = doc.Create.NewDimension(view, lineW, refArrW, dimType);
                var segsW = new List<double>();
                foreach (DimensionSegment s in dimW.Segments) segsW.Add(Math.Round(s.Value.Value * FT_TO_MM, 1));

                // East Wall
                var refArrE = new ReferenceArray();
                foreach (var e in eastFinalList) refArrE.Append(e.Item2);
                var lineE = Line.CreateBound(new XYZ(40500.0 * MM_TO_FT, 0, 0), new XYZ(40500.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var dimE = doc.Create.NewDimension(view, lineE, refArrE, dimType);
                var segsE = new List<double>();
                foreach (DimensionSegment s in dimE.Segments) segsE.Add(Math.Round(s.Value.Value * FT_TO_MM, 1));

                // West Facade
                var refArrF = new ReferenceArray();
                foreach (var f in westFacadeFinalList) refArrF.Append(f.Item2);
                var lineF = Line.CreateBound(new XYZ(-7200.0 * MM_TO_FT, 0, 0), new XYZ(-7200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var dimF = doc.Create.NewDimension(view, lineF, refArrF, dimType);
                var segsF = new List<double>();
                foreach (DimensionSegment s in dimF.Segments) segsF.Add(Math.Round(s.Value.Value * FT_TO_MM, 1));

                tx.RollBack();

                return new {
                    westWall = new { count = segsW.Count, segs = segsW },
                    eastWall = new { count = segsE.Count, segs = segsE },
                    westFacade = new { count = segsF.Count, segs = segsF }
                };
            }
        }
    }
}
