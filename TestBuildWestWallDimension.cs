using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestBuildWestWallDimension
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

        private class CandidateRef
        {
            public Reference Ref { get; set; }
            public double Y { get; set; }
            public string Source { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };

            var candidates = new List<CandidateRef>();

            // 1. Grids
            var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().ToList();
            foreach (var g in grids)
            {
                var c = g.Curve;
                var p1 = c.GetEndPoint(0);
                var p2 = c.GetEndPoint(1);
                if (Math.Abs(p1.Y - p2.Y) < 0.001)
                {
                    candidates.Add(new CandidateRef {
                        Ref = new Reference(g),
                        Y = Math.Round(p1.Y * FT_TO_MM, 1),
                        Source = $"Grid {g.Name}"
                    });
                }
            }

            // 2. West elements (X <= 1500)
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

            foreach (var el in westEls)
            {
                var geom = el.get_Geometry(opt);
                if (geom == null) continue;

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
                                        // only include if Y is within 0 to 14900
                                        if (y >= -50 && y <= 15000)
                                        {
                                            candidates.Add(new CandidateRef {
                                                Ref = pf.Reference,
                                                Y = y,
                                                Source = $"{el.Name} ({el.Category?.Name}, id={el.Id.Value})"
                                            });
                                        }
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
            }

            // Group candidates by Y within 25mm to avoid duplicates / near-duplicates
            var grouped = candidates
                .GroupBy(c => Math.Round(c.Y / 30.0) * 30.0)
                .Select(grp => {
                    // prefer Grid if present, then Door/Window, then Wall/Column
                    var best = grp.OrderBy(x => {
                        if (x.Source.StartsWith("Grid")) return 0;
                        if (x.Source.Contains("Doors")) return 1;
                        if (x.Source.Contains("Windows")) return 2;
                        if (x.Source.Contains("Structural Columns")) return 3;
                        return 4;
                    }).First();
                    return new {
                        targetY = grp.Key,
                        actualY = best.Y,
                        best.Source,
                        best.Ref,
                        count = grp.Count()
                    };
                })
                .OrderBy(x => x.actualY)
                .ToList();

            // Try creating dimension with these references
            var dimType = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .FirstOrDefault(dt => dt.StyleType == DimensionStyleType.Linear && dt.Name == "Linear Dimension Style")
                ?? new FilteredElementCollector(doc).OfClass(typeof(DimensionType)).Cast<DimensionType>().First();

            var line = Line.CreateBound(new XYZ(-1200.0 * MM_TO_FT, 0, 0), new XYZ(-1200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));

            // Test batch adding
            var refArray = new ReferenceArray();
            var addedList = new List<object>();

            using (var tx = new Transaction(doc, "Test Dim West"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);

                tx.Start();

                foreach (var item in grouped)
                {
                    // test if adding this reference works
                    var testArr = new ReferenceArray();
                    foreach (var prev in addedList)
                    {
                        testArr.Append((Reference)((dynamic)prev).Ref);
                    }
                    testArr.Append(item.Ref);

                    if (testArr.Size >= 2)
                    {
                        try
                        {
                            var testDim = doc.Create.NewDimension(view, line, testArr, dimType);
                            if (testDim != null)
                            {
                                doc.Delete(testDim.Id);
                                addedList.Add(item);
                            }
                        }
                        catch (Exception ex)
                        {
                            // Skip incompatible reference
                        }
                    }
                    else
                    {
                        addedList.Add(item);
                    }
                }

                // Now create the final combined dimension
                var finalArr = new ReferenceArray();
                foreach (var item in addedList)
                {
                    finalArr.Append((Reference)((dynamic)item).Ref);
                }

                Dimension createdDim = null;
                string error = null;
                try
                {
                    createdDim = doc.Create.NewDimension(view, line, finalArr, dimType);
                }
                catch (Exception ex)
                {
                    error = ex.Message;
                }

                var segs = new List<double>();
                if (createdDim != null)
                {
                    if (createdDim.Segments != null && createdDim.Segments.Size > 0)
                    {
                        foreach (DimensionSegment seg in createdDim.Segments)
                        {
                            if (seg.Value.HasValue) segs.Add(Math.Round(seg.Value.Value * FT_TO_MM, 1));
                        }
                    }
                    else if (createdDim.Value.HasValue)
                    {
                        segs.Add(Math.Round(createdDim.Value.Value * FT_TO_MM, 1));
                    }
                }

                tx.RollBack(); // just testing

                return new {
                    totalGrouped = grouped.Count,
                    addedCount = addedList.Count,
                    error,
                    segments = segs,
                    items = addedList.Select(x => new {
                        y = ((dynamic)x).actualY,
                        source = ((dynamic)x).Source
                    }).ToList()
                };
            }
        }
    }
}
