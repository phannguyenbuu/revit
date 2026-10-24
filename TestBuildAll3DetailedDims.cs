using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestBuildAll3DetailedDims
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

            // Function to safely build a dimension line from candidate references
            Func<Line, List<Tuple<double, Reference, string>>, Tuple<Dimension, List<double>, List<string>>> tryBuildDim = (line, candidates) => {
                // Deduplicate within 20mm
                var sorted = candidates
                    .OrderBy(c => c.Item1)
                    .GroupBy(c => Math.Round(c.Item1 / 25.0) * 25.0)
                    .Select(g => g.First())
                    .OrderBy(c => c.Item1)
                    .ToList();

                var validRefs = new List<Tuple<double, Reference, string>>();
                foreach (var item in sorted)
                {
                    var testArr = new ReferenceArray();
                    foreach (var v in validRefs) testArr.Append(v.Item2);
                    testArr.Append(item.Item2);

                    if (testArr.Size >= 2)
                    {
                        try
                        {
                            var d = doc.Create.NewDimension(view, line, testArr, dimType);
                            if (d != null)
                            {
                                doc.Delete(d.Id);
                                validRefs.Add(item);
                            }
                        }
                        catch { }
                    }
                    else
                    {
                        validRefs.Add(item);
                    }
                }

                if (validRefs.Count < 2) return Tuple.Create((Dimension)null, new List<double>(), new List<string>());

                var finalArr = new ReferenceArray();
                foreach (var v in validRefs) finalArr.Append(v.Item2);

                try
                {
                    var finalDim = doc.Create.NewDimension(view, line, finalArr, dimType);
                    var segs = new List<double>();
                    if (finalDim.Segments != null && finalDim.Segments.Size > 0)
                    {
                        foreach (DimensionSegment seg in finalDim.Segments)
                        {
                            if (seg.Value.HasValue) segs.Add(Math.Round(seg.Value.Value * FT_TO_MM, 1));
                        }
                    }
                    else if (finalDim.Value.HasValue)
                    {
                        segs.Add(Math.Round(finalDim.Value.Value * FT_TO_MM, 1));
                    }
                    var names = validRefs.Select(v => $"{v.Item1:F0}mm: {v.Item3}").ToList();
                    return Tuple.Create(finalDim, segs, names);
                }
                catch
                {
                    return Tuple.Create((Dimension)null, new List<double>(), new List<string>());
                }
            };

            // Helper to get Y faces from element
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
                                        list.Add(Tuple.Create(y, pf.Reference, $"{el.Name} ({el.Category?.Name})"));
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

            using (var tx = new Transaction(doc, "Test Build 3 Detailed Dims"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);

                tx.Start();

                // -------------------------------------------------------------
                // 1. DIM 2: West Wall Detail along Grid 1 at X = -1200 mm
                // -------------------------------------------------------------
                var westWallCandidates = new List<Tuple<double, Reference, string>>();
                foreach (var g in hGrids)
                {
                    westWallCandidates.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
                }
                var westWallEls = new FilteredElementCollector(doc, view.Id)
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
                foreach (var e in westWallEls)
                {
                    // Filter out interior window mullion faces that clutter
                    if (e is FamilyInstance fi && fi.Symbol.FamilyName.Contains("S1"))
                    {
                        var leftRefs = fi.GetReferences(FamilyInstanceReferenceType.Left);
                        var rightRefs = fi.GetReferences(FamilyInstanceReferenceType.Right);
                        var bb = fi.get_BoundingBox(view);
                        if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                        {
                            westWallCandidates.Add(Tuple.Create(Math.Round(bb.Min.Y * FT_TO_MM, 1), leftRefs[0], $"{fi.Name} Left"));
                            westWallCandidates.Add(Tuple.Create(Math.Round(bb.Max.Y * FT_TO_MM, 1), rightRefs[0], $"{fi.Name} Right"));
                        }
                    }
                    else
                    {
                        westWallCandidates.AddRange(getYFaces(e));
                    }
                }
                var lineWestWall = Line.CreateBound(new XYZ(-1200.0 * MM_TO_FT, 0, 0), new XYZ(-1200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resWestWall = tryBuildDim(lineWestWall, westWallCandidates);

                // -------------------------------------------------------------
                // 2. DIM 3: East Wall & Tam Cấp & WC at X = 40500 mm
                // -------------------------------------------------------------
                var eastWallCandidates = new List<Tuple<double, Reference, string>>();
                foreach (var g in hGrids)
                {
                    eastWallCandidates.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
                }
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
                foreach (var e in eastEls)
                {
                    // Door D2
                    if (e.Id.Value == 2408526 && e is FamilyInstance fi)
                    {
                        var leftRefs = fi.GetReferences(FamilyInstanceReferenceType.Left);
                        var rightRefs = fi.GetReferences(FamilyInstanceReferenceType.Right);
                        var bb = fi.get_BoundingBox(view);
                        if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                        {
                            eastWallCandidates.Add(Tuple.Create(Math.Round(bb.Min.Y * FT_TO_MM, 1), leftRefs[0], "Door D2 Left"));
                            eastWallCandidates.Add(Tuple.Create(Math.Round(bb.Max.Y * FT_TO_MM, 1), rightRefs[0], "Door D2 Right"));
                        }
                    }
                    else
                    {
                        eastWallCandidates.AddRange(getYFaces(e));
                    }
                }
                var lineEastWall = Line.CreateBound(new XYZ(40500.0 * MM_TO_FT, 0, 0), new XYZ(40500.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resEastWall = tryBuildDim(lineEastWall, eastWallCandidates);

                // -------------------------------------------------------------
                // 3. DIM 1: West Mặt Tiền / Sảnh Chính at X = -7200 mm
                // -------------------------------------------------------------
                var westFacadeCandidates = new List<Tuple<double, Reference, string>>();
                foreach (var g in hGrids)
                {
                    westFacadeCandidates.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1), new Reference(g), $"Grid {g.Name}"));
                }
                // Mat_Tien_3dsMax (2391783)
                var matTien = doc.GetElement(new ElementId(2391783));
                if (matTien != null)
                {
                    westFacadeCandidates.AddRange(getYFaces(matTien));
                }
                // Floor NỀN COS 0.00 2
                var floor2 = doc.GetElement(new ElementId(2407783));
                if (floor2 != null)
                {
                    westFacadeCandidates.AddRange(getYFaces(floor2));
                }
                // Door D1
                var doorD1 = doc.GetElement(new ElementId(2364731)) as FamilyInstance;
                if (doorD1 != null)
                {
                    var leftRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Left);
                    var rightRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Right);
                    var bb = doorD1.get_BoundingBox(view);
                    if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                    {
                        westFacadeCandidates.Add(Tuple.Create(Math.Round(bb.Min.Y * FT_TO_MM, 1), leftRefs[0], "Door D1 Left"));
                        westFacadeCandidates.Add(Tuple.Create(Math.Round(bb.Max.Y * FT_TO_MM, 1), rightRefs[0], "Door D1 Right"));
                    }
                }
                var lineWestFacade = Line.CreateBound(new XYZ(-7200.0 * MM_TO_FT, 0, 0), new XYZ(-7200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resWestFacade = tryBuildDim(lineWestFacade, westFacadeCandidates);

                tx.RollBack();

                return new {
                    westWall = new {
                        count = resWestWall.Item2.Count,
                        segments = resWestWall.Item2,
                        names = resWestWall.Item3
                    },
                    eastWall = new {
                        count = resEastWall.Item2.Count,
                        segments = resEastWall.Item2,
                        names = resEastWall.Item3
                    },
                    westFacade = new {
                        count = resWestFacade.Item2.Count,
                        segments = resWestFacade.Item2,
                        names = resWestFacade.Item3
                    }
                };
            }
        }
    }
}
