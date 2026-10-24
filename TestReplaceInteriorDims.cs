using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestReplaceInteriorDims
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var options = args.TryGetProperty("args", out var n) && n.ValueKind == System.Text.Json.JsonValueKind.Object ? n : args;

            ViewPlan? view = null;
            if (options.TryGetProperty("viewId", out var pViewId) || args.TryGetProperty("viewId", out pViewId))
            {
                view = doc?.GetElement(new ElementId(pViewId.GetInt64())) as ViewPlan;
            }
            if (view == null) view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No doc or view" };

            // Find transparent dim style
            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .ToList();

            DimensionType? targetDimType = null;
            foreach (var dt in dimTypes)
            {
                var pBg = dt.get_Parameter(BuiltInParameter.TEXT_BACKGROUND);
                if (pBg != null && pBg.AsInteger() == 1)
                {
                    targetDimType = dt;
                    break;
                }
            }
            if (targetDimType == null) targetDimType = dimTypes.FirstOrDefault();

            var opt = new Options { ComputeReferences = true, View = view };

            // Vertical grids
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

            var hGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => {
                    var p1 = g.Curve.GetEndPoint(0);
                    var p2 = g.Curve.GetEndPoint(1);
                    return Math.Abs(p1.Y - p2.Y) < 0.01;
                })
                .OrderBy(g => g.Curve.GetEndPoint(0).Y)
                .ToList();

            var gridB = hGrids.FirstOrDefault(g => g.Name == "B");
            var gridC = hGrids.FirstOrDefault(g => g.Name == "C");

            double yB = gridB != null ? gridB.Curve.GetEndPoint(0).Y * FT_TO_MM : 5400.0;
            double yC = gridC != null ? gridC.Curve.GetEndPoint(0).Y * FT_TO_MM : 7800.0;

            double offsetB = 1500.0;
            double offsetC = 1500.0;

            double yMm_AB = yB - offsetB; // 3900 mm
            double yMm_CD = yC + offsetC; // 9300 mm

            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            Func<Wall, List<Tuple<double, Reference, string>>> getWallXPlanarFaces = (w) =>
            {
                var list = new List<Tuple<double, Reference, string>>();
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
                                list.Add(Tuple.Create(x, pf.Reference, $"Wall_{w.Id.Value}"));
                            }
                        }
                    }
                }
                return list;
            };

            // Band AB points
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

            var abRawPoints = new List<Tuple<double, Reference, string>>();
            foreach (var w in bWalls) abRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var w in abPartitions) abRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var g in vGrids)
            {
                double x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1);
                abRawPoints.Add(Tuple.Create(x, new Reference(g), $"Grid_{g.Name}"));
            }

            var abClean = new List<Tuple<double, Reference, string>>();
            foreach (var p in abRawPoints.OrderBy(p => p.Item1))
            {
                if (abClean.Count == 0 || Math.Abs(abClean.Last().Item1 - p.Item1) > 20.0)
                    abClean.Add(p);
            }

            // Band CD points
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

            var cdRawPoints = new List<Tuple<double, Reference, string>>();
            foreach (var w in cWalls) cdRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var w in cdPartitions) cdRawPoints.AddRange(getWallXPlanarFaces(w));
            foreach (var g in vGrids)
            {
                double x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1);
                cdRawPoints.Add(Tuple.Create(x, new Reference(g), $"Grid_{g.Name}"));
            }

            var cdClean = new List<Tuple<double, Reference, string>>();
            foreach (var p in cdRawPoints.OrderBy(p => p.Item1))
            {
                if (cdClean.Count == 0 || Math.Abs(cdClean.Last().Item1 - p.Item1) > 20.0)
                    cdClean.Add(p);
            }

            // Execute in Transaction
            var createdDims = new List<Dimension>();
            int shiftedCount = 0;

            using (var tx = new Transaction(doc, "Replace Interior Dims with Dynamic Doors"))
            {
                tx.Start();

                // Delete the old interior dimensions if they exist near Y = yMm_AB and yMm_CD
                var existingDims = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                foreach (var d in existingDims)
                {
                    if (d.Curve is Line l)
                    {
                        var dir = l.Direction;
                        if (Math.Abs(Math.Abs(dir.X) - 1.0) < 0.1)
                        {
                            double yMm = l.Origin.Y * FT_TO_MM;
                            if (Math.Abs(yMm - yMm_AB) < 500 || Math.Abs(yMm - yMm_CD) < 500)
                            {
                                try { doc.Delete(d.Id); } catch {}
                            }
                        }
                    }
                }

                // Helper to create and stagger chain
                Action<List<Tuple<double, Reference, string>>, double> buildChain = (pts, yMm) =>
                {
                    if (pts.Count < 2) return;
                    var refArr = new ReferenceArray();
                    foreach (var p in pts) refArr.Append(p.Item2);

                    double yFt = yMm * MM_TO_FT;
                    double x1Ft = (pts.First().Item1 - 800.0) * MM_TO_FT;
                    double x2Ft = (pts.Last().Item1 + 800.0) * MM_TO_FT;
                    var line = Line.CreateBound(new XYZ(x1Ft, yFt, 0), new XYZ(x2Ft, yFt, 0));

                    try
                    {
                        var dim = doc.Create.NewDimension(view, line, refArr, targetDimType);
                        if (dim != null)
                        {
                            createdDims.Add(dim);

                            // Stagger segments <= 200 mm
                            if (dim.Segments != null && dim.Segments.Size > 1)
                            {
                                var movedHistory = new List<Tuple<double, double>>(); // X, offset
                                foreach (DimensionSegment seg in dim.Segments)
                                {
                                    double valMm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 0) : 0;
                                    if (valMm > 200) continue;
                                    if (!seg.IsTextPositionAdjustable()) continue;

                                    var origPos = seg.TextPosition;
                                    if (origPos == null) continue;

                                    double alongX = origPos.X * FT_TO_MM;
                                    var nearby = movedHistory.Where(m => Math.Abs(m.Item1 - alongX) < 800.0).ToList();

                                    bool goPositive = true;
                                    int level = 1;
                                    if (nearby.Count > 0)
                                    {
                                        var last = nearby.Last();
                                        goPositive = last.Item2 < 0; // alternate
                                        level = (nearby.Count % 3) + 1;
                                    }

                                    double offsetVal = level switch
                                    {
                                        1 => 500.0,
                                        2 => 800.0,
                                        _ => 1100.0
                                    };
                                    double shiftMm = goPositive ? offsetVal : -offsetVal;

                                    XYZ newPos = new XYZ(origPos.X, origPos.Y + (shiftMm * MM_TO_FT), origPos.Z);
                                    seg.TextPosition = newPos;
                                    movedHistory.Add(Tuple.Create(alongX, shiftMm));
                                    shiftedCount++;
                                }
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        // Catch error
                    }
                };

                buildChain(abClean, yMm_AB);
                buildChain(cdClean, yMm_CD);

                tx.Commit();
            }

            var resDims = createdDims.Select(d => new {
                id = d.Id.Value,
                segmentCount = d.Segments?.Size ?? 0,
                segments = d.Segments != null ? d.Segments.Cast<DimensionSegment>().Select(s => s.ValueString).ToList() : null
            }).ToList();

            return new {
                success = true,
                viewName = view.Name,
                createdCount = createdDims.Count,
                shiftedCount,
                dimensions = resDims
            };
        }
    }
}
