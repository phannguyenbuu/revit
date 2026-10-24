using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateCompleteFloorDimensions
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

        private class RefPoint
        {
            public Reference Ref { get; set; }
            public double Coord { get; set; } // in mm
            public string Name { get; set; }
        }

        private class MovedText
        {
            public double X { get; set; }
            public double Y { get; set; }
            public bool IsUpOrRight { get; set; }
            public int Level { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var options = args;
            if (args.TryGetProperty("args", out var nestedArgs) && nestedArgs.ValueKind == JsonValueKind.Object)
            {
                options = nestedArgs;
            }

            // 1. Determine target view(s)
            var targetViews = new List<ViewPlan>();
            if ((options.TryGetProperty("viewId", out var vProp) || args.TryGetProperty("viewId", out vProp)) && vProp.GetInt64() > 0)
            {
                var v = doc.GetElement(new ElementId(vProp.GetInt64())) as ViewPlan;
                if (v != null && !v.IsTemplate) targetViews.Add(v);
            }
            else if ((options.TryGetProperty("viewIds", out var arrProp) || args.TryGetProperty("viewIds", out arrProp)) && arrProp.ValueKind == JsonValueKind.Array)
            {
                foreach (var el in arrProp.EnumerateArray())
                {
                    var v = doc.GetElement(new ElementId(el.GetInt64())) as ViewPlan;
                    if (v != null && !v.IsTemplate) targetViews.Add(v);
                }
            }

            // Check selected elements in UIDocument (e.g. selected in Project Browser)
            if (targetViews.Count == 0)
            {
                var selIds = uidoc.Selection.GetElementIds();
                foreach (var id in selIds)
                {
                    var v = doc.GetElement(id) as ViewPlan;
                    if (v != null && !v.IsTemplate) targetViews.Add(v);
                }
            }

            // Fallback to active view if it's a ViewPlan
            if (targetViews.Count == 0 && uidoc.ActiveView is ViewPlan activeVp && !activeVp.IsTemplate)
            {
                targetViews.Add(activeVp);
            }

            // Default fallback: Floor 1 (ID 312)
            if (targetViews.Count == 0)
            {
                var f1 = doc.GetElement(new ElementId(312L)) as ViewPlan;
                if (f1 != null) targetViews.Add(f1);
            }

            if (targetViews.Count == 0)
            {
                return new { error = "Không tìm thấy ViewPlan nào phù hợp để tạo dim!" };
            }

            var allResults = new List<object>();

            using (var tx = new Transaction(doc, "Create 3-Layer and Interior Dimensions with Transparent Text"))
            {
                var fOpts = tx.GetFailureHandlingOptions();
                fOpts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(fOpts);
                tx.Start();

                // 2. Setup Transparent DimensionType ("Linear Dimension Style - Transparent")
                var dimTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(DimensionType))
                    .Cast<DimensionType>()
                    .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                    .ToList();

                var baseDimType = dimTypes.FirstOrDefault(dt => dt.Name == "Linear Dimension Style")
                               ?? dimTypes.FirstOrDefault(dt => dt.Name == "kt nam")
                               ?? dimTypes.First();

                string transparentTypeName = "Linear Dimension Style - Transparent";
                var transDimType = dimTypes.FirstOrDefault(dt => dt.Name == transparentTypeName);
                if (transDimType == null)
                {
                    transDimType = baseDimType.Duplicate(transparentTypeName) as DimensionType;
                }

                // Ensure DIM_TEXT_BACKGROUND = 1 (Transparent) & Witness Line Fixed Length 800mm (8.0mm paper)
                if (transDimType != null)
                {
                    var pBg = transDimType.get_Parameter(BuiltInParameter.DIM_TEXT_BACKGROUND);
                    if (pBg != null && !pBg.IsReadOnly) pBg.Set(1); // 1 = Transparent

                    var pCntrl = transDimType.get_Parameter(BuiltInParameter.DIM_WITNS_LINE_CNTRL);
                    if (pCntrl != null && !pCntrl.IsReadOnly) pCntrl.Set(1); // 1 = Fixed to Dimension Line

                    var pLen = transDimType.get_Parameter(BuiltInParameter.DIM_WITNS_LINE_EXTENSION_BELOW);
                    if (pLen != null && !pLen.IsReadOnly) pLen.Set(8.0 * MM_TO_FT); // 8mm paper = 800mm at 1:100

                    var pExt = transDimType.get_Parameter(BuiltInParameter.WITNS_LINE_EXTENSION);
                    if (pExt != null && !pExt.IsReadOnly) pExt.Set(2.0 * MM_TO_FT);

                    var pLineExt = transDimType.get_Parameter(BuiltInParameter.DIM_LINE_EXTENSION);
                    if (pLineExt != null && !pLineExt.IsReadOnly) pLineExt.Set(1.5 * MM_TO_FT);
                }

                var activeDimType = transDimType ?? baseDimType;

                bool cleanExisting = true;
                if (options.TryGetProperty("cleanExisting", out var pClean) || args.TryGetProperty("cleanExisting", out pClean))
                    cleanExisting = pClean.GetBoolean();

                double offsetB = 1500.0;
                if (options.TryGetProperty("offsetB", out var pOffB) || args.TryGetProperty("offsetB", out pOffB))
                    offsetB = pOffB.GetDouble();

                double offsetC = 1500.0;
                if (options.TryGetProperty("offsetC", out var pOffC) || args.TryGetProperty("offsetC", out pOffC))
                    offsetC = pOffC.GetDouble();

                // 3. Process each target view
                foreach (var view in targetViews)
                {
                    var viewResult = ProcessViewDimensions(doc, view, activeDimType, cleanExisting, offsetB, offsetC);
                    allResults.Add(viewResult);
                }

                tx.Commit();
            }

            return new
            {
                success = true,
                dimensionTypeName = "Linear Dimension Style - Transparent",
                textBackground = "Transparent (No Fill)",
                viewCount = targetViews.Count,
                results = allResults
            };
        }

        private static object ProcessViewDimensions(Document doc, ViewPlan view, DimensionType dimType, bool cleanExisting, double offsetB, double offsetC)
        {
            if (cleanExisting)
            {
                var existingDims = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();
                foreach (var ed in existingDims)
                {
                    try { doc.Delete(ed.Id); } catch {}
                }
            }

            var opt = new Options { ComputeReferences = true, View = view };

            // Collect vertical grids (1 to 11) and horizontal grids (A to E)
            var allGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var vGrids = new List<Grid>();
            var hGrids = new List<Grid>();

            foreach (var g in allGrids)
            {
                var p1 = g.Curve.GetEndPoint(0);
                var p2 = g.Curve.GetEndPoint(1);
                if (Math.Abs(p1.X - p2.X) < 0.01) vGrids.Add(g);
                else if (Math.Abs(p1.Y - p2.Y) < 0.01) hGrids.Add(g);
            }
            vGrids = vGrids.OrderBy(g => g.Curve.GetEndPoint(0).X).ToList();
            hGrids = hGrids.OrderBy(g => g.Curve.GetEndPoint(0).Y).ToList();

            var createdDims = new List<Dimension>();

            // Helper to create a single dimension chain from RefPoints
            Func<List<RefPoint>, bool, double, Dimension> createDimChain = (pts, isHorizontal, fixedCoordMm) =>
            {
                var sorted = pts.OrderBy(p => p.Coord).ToList();
                var clean = new List<RefPoint>();
                foreach (var p in sorted)
                {
                    if (clean.Count == 0 || Math.Abs(clean.Last().Coord - p.Coord) > 20.0)
                    {
                        clean.Add(p);
                    }
                }

                if (clean.Count < 2) return null;

                var refArr = new ReferenceArray();
                foreach (var p in clean) refArr.Append(p.Ref);

                Line dimLine;
                if (isHorizontal)
                {
                    double yFt = fixedCoordMm * MM_TO_FT;
                    double xMin = (clean.First().Coord - 800.0) * MM_TO_FT;
                    double xMax = (clean.Last().Coord + 800.0) * MM_TO_FT;
                    dimLine = Line.CreateBound(new XYZ(xMin, yFt, 0), new XYZ(xMax, yFt, 0));
                }
                else
                {
                    double xFt = fixedCoordMm * MM_TO_FT;
                    double yMin = (clean.First().Coord - 800.0) * MM_TO_FT;
                    double yMax = (clean.Last().Coord + 800.0) * MM_TO_FT;
                    dimLine = Line.CreateBound(new XYZ(xFt, yMin, 0), new XYZ(xFt, yMax, 0));
                }

                try
                {
                    var d = doc.Create.NewDimension(view, dimLine, refArr, dimType);
                    if (d != null) createdDims.Add(d);
                    return d;
                }
                catch { return null; }
            };

            // Walls and wall faces helpers
            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            Func<Wall, List<Tuple<double, Reference>>> getWallXFaces = (w) =>
            {
                var list = new List<Tuple<double, Reference>>();
                if (w == null) return list;
                var geom = w.get_Geometry(opt);
                if (geom == null) return list;
                foreach (var gObj in geom)
                {
                    if (gObj is Solid s && s.Faces != null)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                            {
                                double x = Math.Round(pf.Origin.X * FT_TO_MM, 1);
                                list.Add(Tuple.Create(x, pf.Reference));
                            }
                        }
                    }
                }
                return list;
            };

            Func<double, double, List<Tuple<double, Reference>>> collectBandRefs = (minY, maxY) =>
            {
                var list = new List<Tuple<double, Reference>>();
                foreach (var g in vGrids)
                {
                    list.Add(Tuple.Create(Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), new Reference(g)));
                }
                var bandWalls = allWalls.Where(w => {
                    var bb = w.get_BoundingBox(view);
                    if (bb == null) return false;
                    return bb.Max.Y * FT_TO_MM >= minY && bb.Min.Y * FT_TO_MM <= maxY;
                }).ToList();
                foreach (var w in bandWalls) list.AddRange(getWallXFaces(w));
                return list;
            };

            Func<double, List<double>, List<Tuple<double, Reference>>, Dimension> buildCuratedChain = (yMm, targets, available) =>
            {
                var chosen = new List<Tuple<double, Reference>>();
                foreach (var t in targets)
                {
                    var match = available
                        .Where(r => Math.Abs(r.Item1 - t) <= 45.0)
                        .OrderBy(r => Math.Abs(r.Item1 - t))
                        .FirstOrDefault();
                    if (match != null && !chosen.Any(c => Math.Abs(c.Item1 - match.Item1) < 45.0))
                    {
                        chosen.Add(match);
                    }
                }
                chosen = chosen.OrderBy(c => c.Item1).ToList();
                if (chosen.Count < 2) return null;

                var refArr = new ReferenceArray();
                foreach (var c in chosen) refArr.Append(c.Item2);

                double yFt = yMm * MM_TO_FT;
                double x1Ft = (chosen.First().Item1 - 800.0) * MM_TO_FT;
                double x2Ft = (chosen.Last().Item1 + 800.0) * MM_TO_FT;
                var line = Line.CreateBound(new XYZ(x1Ft, yFt, 0), new XYZ(x2Ft, yFt, 0));

                try
                {
                    var d = doc.Create.NewDimension(view, line, refArr, dimType);
                    if (d != null) createdDims.Add(d);
                    return d;
                }
                catch { return null; }
            };

            // -----------------------------------------------------------------
            // 1. SOUTH (Phía Nam - below Grid A)
            // -----------------------------------------------------------------
            // L1: Dim tổng Trục 1 - 11 at Y = -4600 mm
            var southL1 = new List<RefPoint> {
                new RefPoint { Ref = new Reference(vGrids.First()), Coord = vGrids.First().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 1" },
                new RefPoint { Ref = new Reference(vGrids.Last()), Coord = vGrids.Last().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 11" }
            };
            createDimChain(southL1, true, -4600.0);

            // L2: Dim tim trục 1 -> 11 at Y = -2200 mm
            var southL2 = vGrids.Select(g => new RefPoint {
                Ref = new Reference(g),
                Coord = g.Curve.GetEndPoint(0).X * FT_TO_MM,
                Name = g.Name
            }).ToList();
            createDimChain(southL2, true, -2200.0);

            // L3: Dim chi tiết tường, cửa sổ S1 at Y = -1200 mm
            var southAvailable = collectBandRefs(-1000, 1500);
            var southTargets = new List<double> {
                550, 700, 800, 900, 1800, 2100, 3000, 3150, 3300, 4150, 4250, 4350,
                5558, 7058, 7950, 8050, 8150, 9108, 10608, 11650, 12708, 14208,
                15150, 15250, 15350, 16308, 17808, 18850, 19908, 21408, 22350, 22450,
                22550, 23508, 25008, 26050, 27108, 28608, 29550, 29650, 29750, 30658,
                32150, 33350, 34450, 34650, 35650, 35950, 37050, 37150, 37550
            };
            buildCuratedChain(-1200.0, southTargets, southAvailable);

            // -----------------------------------------------------------------
            // 2. NORTH (Phía Bắc - above Grid E)
            // -----------------------------------------------------------------
            // L1: Dim tổng Trục 1 - 11 at Y = 19600 mm
            var northL1 = new List<RefPoint> {
                new RefPoint { Ref = new Reference(vGrids.First()), Coord = vGrids.First().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 1" },
                new RefPoint { Ref = new Reference(vGrids.Last()), Coord = vGrids.Last().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 11" }
            };
            createDimChain(northL1, true, 19600.0);

            // L2: Dim tim trục 1 -> 11 at Y = 17200 mm
            var northL2 = vGrids.Select(g => new RefPoint {
                Ref = new Reference(g),
                Coord = g.Curve.GetEndPoint(0).X * FT_TO_MM,
                Name = g.Name
            }).ToList();
            createDimChain(northL2, true, 17200.0);

            // L3: Dim chi tiết tường, cửa sổ mặt Bắc at Y = 16000 mm
            var northAvailable = collectBandRefs(13100, 15500);
            var northTargets = new List<double> {
                550, 4350, 4450, 4658, 7758, 7950, 8050, 8150, 9058, 10558,
                11650, 12658, 14158, 15250, 16308, 17808, 18850, 22450, 24296,
                25796, 26050, 27446, 28946, 29550, 29650, 29750, 29958, 33058,
                33250, 33350, 33450, 33758, 35258, 37150, 37550
            };
            buildCuratedChain(16000.0, northTargets, northAvailable);

            // -----------------------------------------------------------------
            // 3. WEST (Phía Tây - left of Grid 1)
            // -----------------------------------------------------------------
            // L1: Dim tổng Trục A - E at X = -10400 mm
            var westL1 = new List<RefPoint> {
                new RefPoint { Ref = new Reference(hGrids.First()), Coord = hGrids.First().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid A" },
                new RefPoint { Ref = new Reference(hGrids.Last()), Coord = hGrids.Last().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid E" }
            };
            createDimChain(westL1, false, -10400.0);

            // L2: Dim tim trục A -> E at X = -9200 mm
            var westL2 = hGrids.Select(g => new RefPoint {
                Ref = new Reference(g),
                Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM,
                Name = g.Name
            }).ToList();
            createDimChain(westL2, false, -9200.0);

            // L3: Dim chi tiết trục A, D, E và cửa sảnh chính at X = -7200 mm
            var westL3 = new List<RefPoint>();
            foreach (var g in hGrids)
            {
                westL3.Add(new RefPoint { Ref = new Reference(g), Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM, Name = g.Name });
            }
            createDimChain(westL3, false, -7200.0);

            // -----------------------------------------------------------------
            // 4. EAST (Phía Đông - right of Grid 11)
            // -----------------------------------------------------------------
            // L1: Dim tổng Trục A - E at X = 44400 mm
            var eastL1 = new List<RefPoint> {
                new RefPoint { Ref = new Reference(hGrids.First()), Coord = hGrids.First().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid A" },
                new RefPoint { Ref = new Reference(hGrids.Last()), Coord = hGrids.Last().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid E" }
            };
            createDimChain(eastL1, false, 44400.0);

            // L2: Dim tim trục A -> E at X = 43200 mm
            var eastL2 = hGrids.Select(g => new RefPoint {
                Ref = new Reference(g),
                Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM,
                Name = g.Name
            }).ToList();
            createDimChain(eastL2, false, 43200.0);

            // L3: Dim chi tiết các trục A -> E at X = 40500 mm
            var eastL3 = hGrids.Select(g => new RefPoint {
                Ref = new Reference(g),
                Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM,
                Name = g.Name
            }).ToList();
            createDimChain(eastL3, false, 40500.0);

            // -----------------------------------------------------------------
            // 5. TWO HORIZONTAL INTERIOR CHAINS: Band AB & Band CD
            // -----------------------------------------------------------------
            var gridB = hGrids.FirstOrDefault(g => g.Name == "B");
            var gridC = hGrids.FirstOrDefault(g => g.Name == "C");

            double yB = gridB != null ? (gridB.Curve.GetEndPoint(0).Y * FT_TO_MM) : 5400.0;
            double yC = gridC != null ? (gridC.Curve.GetEndPoint(0).Y * FT_TO_MM) : 7800.0;

            double yMm_AB = yB - offsetB;
            double yMm_CD = yC + offsetC;

            // Band AB: Dynamic Wall B and partition wall extraction (captures 100% doors)
            var bWalls = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                return bb.Max.Y * FT_TO_MM >= (yB - 300) && bb.Min.Y * FT_TO_MM <= (yB + 300);
            }).ToList();

            var abPartitions = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                return bb.Max.Y * FT_TO_MM >= (yB - 1000) && bb.Min.Y * FT_TO_MM <= (yB - 200);
            }).ToList();

            var abRawPoints = new List<Tuple<double, Reference>>();
            foreach (var w in bWalls) abRawPoints.AddRange(getWallXFaces(w));
            foreach (var w in abPartitions) abRawPoints.AddRange(getWallXFaces(w));
            foreach (var g in vGrids)
            {
                double x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1);
                abRawPoints.Add(Tuple.Create(x, new Reference(g)));
            }

            var abClean = new List<RefPoint>();
            foreach (var p in abRawPoints.OrderBy(p => p.Item1))
            {
                if (abClean.Count == 0 || Math.Abs(abClean.Last().Coord - p.Item1) > 20.0)
                    abClean.Add(new RefPoint { Ref = p.Item2, Coord = p.Item1, Name = "AB_Ref" });
            }
            createDimChain(abClean, true, yMm_AB);

            // Band CD: Dynamic Wall C and partition wall extraction (captures 100% doors)
            var cWalls = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                return bb.Max.Y * FT_TO_MM >= (yC - 300) && bb.Min.Y * FT_TO_MM <= (yC + 300);
            }).ToList();

            var cdPartitions = allWalls.Where(w => {
                var bb = w.get_BoundingBox(view);
                if (bb == null) return false;
                return bb.Max.Y * FT_TO_MM >= (yC + 200) && bb.Min.Y * FT_TO_MM <= (yC + 1500);
            }).ToList();

            var cdRawPoints = new List<Tuple<double, Reference>>();
            foreach (var w in cWalls) cdRawPoints.AddRange(getWallXFaces(w));
            foreach (var w in cdPartitions) cdRawPoints.AddRange(getWallXFaces(w));
            foreach (var g in vGrids)
            {
                double x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1);
                cdRawPoints.Add(Tuple.Create(x, new Reference(g)));
            }

            var cdClean = new List<RefPoint>();
            foreach (var p in cdRawPoints.OrderBy(p => p.Item1))
            {
                if (cdClean.Count == 0 || Math.Abs(cdClean.Last().Coord - p.Item1) > 20.0)
                    cdClean.Add(new RefPoint { Ref = p.Item2, Coord = p.Item1, Name = "CD_Ref" });
            }
            createDimChain(cdClean, true, yMm_CD);

            // -----------------------------------------------------------------
            // 6. OFFSET SMALL TEXTS (<= 200 mm) UP/DOWN / LEFT/RIGHT
            // -----------------------------------------------------------------
            int totalShifted = 0;
            foreach (var dim in createdDims)
            {
                if (dim.Segments == null || dim.Segments.Size <= 1) continue;

                var c = dim.Curve;
                if (c == null) continue;

                XYZ dir = XYZ.BasisX;
                if (c.IsBound) dir = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize();
                else if (c is Line l) dir = l.Direction;

                bool isHoriz = Math.Abs(Math.Abs(dir.X) - 1.0) < 0.1;
                double fixedCoordMm = 0;
                if (c is Line lineObj) fixedCoordMm = (isHoriz ? lineObj.Origin.Y : lineObj.Origin.X) * FT_TO_MM;
                else if (c.IsBound) fixedCoordMm = (isHoriz ? c.GetEndPoint(0).Y : c.GetEndPoint(0).X) * FT_TO_MM;

                var movedHistory = new List<MovedText>();

                foreach (DimensionSegment seg in dim.Segments)
                {
                    double valMm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 0) : 0;
                    if (valMm > 200) continue; // Condition: dim <= 200 mm

                    if (!seg.IsTextPositionAdjustable()) continue;

                    var origPos = seg.TextPosition;
                    if (origPos == null) continue;

                    double alongCoord = isHoriz ? (origPos.X * FT_TO_MM) : (origPos.Y * FT_TO_MM);

                    // Check nearby moved texts within 800mm
                    var nearby = movedHistory
                        .Where(m => Math.Abs((isHoriz ? m.X : m.Y) - alongCoord) < 800.0)
                        .OrderByDescending(m => isHoriz ? m.X : m.Y)
                        .ToList();

                    bool goPositive = true;
                    int level = 1;

                    if (nearby.Count > 0)
                    {
                        var last = nearby.First();
                        goPositive = !last.IsUpOrRight;

                        var sameSideNearby = nearby.Where(m => m.IsUpOrRight == goPositive && Math.Abs((isHoriz ? m.X : m.Y) - alongCoord) < 450.0).ToList();
                        if (sameSideNearby.Count > 0)
                        {
                            level = sameSideNearby.Max(m => m.Level) + 1;
                        }
                    }

                    double baseOffset = (level == 1) ? 500.0 : (level == 2 ? 800.0 : 1100.0);
                    double offsetMm = goPositive ? baseOffset : -baseOffset;

                    XYZ newPos = isHoriz
                        ? new XYZ(origPos.X, (fixedCoordMm + offsetMm) * MM_TO_FT, origPos.Z)
                        : new XYZ((fixedCoordMm + offsetMm) * MM_TO_FT, origPos.Y, origPos.Z);

                    try
                    {
                        seg.TextPosition = newPos;
                        movedHistory.Add(new MovedText {
                            X = origPos.X * FT_TO_MM,
                            Y = origPos.Y * FT_TO_MM,
                            IsUpOrRight = goPositive,
                            Level = level
                        });
                        totalShifted++;
                    }
                    catch { }
                }
            }

            return new
            {
                viewId = view.Id.Value,
                viewName = view.Name,
                createdDimCount = createdDims.Count,
                dimIds = createdDims.Select(d => d.Id.Value).ToList(),
                shiftedSmallTextsCount = totalShifted
            };
        }
    }
}
