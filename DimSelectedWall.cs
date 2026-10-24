using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DimSelectedWall
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "Please open a plan view." };

            var options = args.TryGetProperty("args", out var n) && n.ValueKind == System.Text.Json.JsonValueKind.Object ? n : args;

            // 1. Get transparent dim style
            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .ToList();

            DimensionType? dimType = null;
            foreach (var dt in dimTypes)
            {
                var pBg = dt.get_Parameter(BuiltInParameter.TEXT_BACKGROUND);
                if (pBg != null && pBg.AsInteger() == 1)
                {
                    dimType = dt;
                    break;
                }
            }
            if (dimType == null) dimType = dimTypes.FirstOrDefault();

            // 2. Identify target walls
            var selIds = uidoc.Selection.GetElementIds();
            var targetWalls = new List<Wall>();

            if (options.TryGetProperty("wallIds", out var pWallIds) && pWallIds.ValueKind == System.Text.Json.JsonValueKind.Array)
            {
                foreach (var idElem in pWallIds.EnumerateArray())
                {
                    if (idElem.TryGetInt64(out var wid))
                    {
                        var w = doc.GetElement(new ElementId(wid)) as Wall;
                        if (w != null) targetWalls.Add(w);
                    }
                }
            }
            else
            {
                foreach (var id in selIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem is Wall w) targetWalls.Add(w);
                }
            }

            if (targetWalls.Count == 0)
            {
                return new {
                    success = false,
                    message = "No walls selected. Please select one or more walls in Revit before running."
                };
            }

            double userOffsetMm = 1200.0;
            if (options.TryGetProperty("offsetMm", out var pOff))
                userOffsetMm = pOff.GetDouble();

            var opt = new Options { ComputeReferences = true, View = view };

            // All grids
            var allGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            // All walls in view for intersections
            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            var createdDims = new List<Dimension>();
            int shiftedCount = 0;

            using (var tx = new Transaction(doc, "Dim Selected Walls with All Openings"))
            {
                tx.Start();

                foreach (var wall in targetWalls)
                {
                    var locCurve = wall.Location as LocationCurve;
                    if (locCurve == null || locCurve.Curve == null) continue;

                    var curve = locCurve.Curve;
                    var pt0 = curve.GetEndPoint(0);
                    var pt1 = curve.GetEndPoint(1);
                    var dir = (pt1 - pt0).Normalize();

                    bool isHorizontal = Math.Abs(dir.Y) < 0.1;
                    bool isVertical = Math.Abs(dir.X) < 0.1;

                    if (!isHorizontal && !isVertical) continue; // Currently support orthogonal walls

                    var wallPoints = new List<Tuple<double, Reference>>();

                    // 1. Get cut faces of the wall itself (openings, doors, windows, ends)
                    var geom = wall.get_Geometry(opt);
                    if (geom != null)
                    {
                        foreach (var gObj in geom)
                        {
                            if (gObj is Solid s && s.Faces != null)
                            {
                                foreach (Face f in s.Faces)
                                {
                                    if (f is PlanarFace pf && pf.Reference != null)
                                    {
                                        if (isHorizontal && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                        {
                                            wallPoints.Add(Tuple.Create(Math.Round(pf.Origin.X * FT_TO_MM, 1), pf.Reference));
                                        }
                                        else if (isVertical && Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01)
                                        {
                                            wallPoints.Add(Tuple.Create(Math.Round(pf.Origin.Y * FT_TO_MM, 1), pf.Reference));
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // 2. Intersecting perpendicular walls
                    var bb = wall.get_BoundingBox(view);
                    if (bb != null)
                    {
                        var perpWalls = allWalls.Where(pw => {
                            if (pw.Id.Value == wall.Id.Value) return false;
                            var pbb = pw.get_BoundingBox(view);
                            if (pbb == null) return false;

                            if (isHorizontal)
                            {
                                // Overlaps in Y and within X bounds
                                return pbb.Max.Y >= bb.Min.Y && pbb.Min.Y <= bb.Max.Y &&
                                       pbb.Max.X >= bb.Min.X && pbb.Min.X <= bb.Max.X;
                            }
                            else
                            {
                                return pbb.Max.X >= bb.Min.X && pbb.Min.X <= bb.Max.X &&
                                       pbb.Max.Y >= bb.Min.Y && pbb.Min.Y <= bb.Max.Y;
                            }
                        }).ToList();

                        foreach (var pw in perpWalls)
                        {
                            var pgeom = pw.get_Geometry(opt);
                            if (pgeom == null) continue;
                            foreach (var pgObj in pgeom)
                            {
                                if (pgObj is Solid ps && ps.Faces != null)
                                {
                                    foreach (Face pf in ps.Faces)
                                    {
                                        if (pf is PlanarFace ppf && ppf.Reference != null)
                                        {
                                            if (isHorizontal && Math.Abs(Math.Abs(ppf.FaceNormal.X) - 1.0) < 0.01)
                                            {
                                                wallPoints.Add(Tuple.Create(Math.Round(ppf.Origin.X * FT_TO_MM, 1), ppf.Reference));
                                            }
                                            else if (isVertical && Math.Abs(Math.Abs(ppf.FaceNormal.Y) - 1.0) < 0.01)
                                            {
                                                wallPoints.Add(Tuple.Create(Math.Round(ppf.Origin.Y * FT_TO_MM, 1), ppf.Reference));
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // 3. Intersecting grids
                    foreach (var g in allGrids)
                    {
                        var gp0 = g.Curve.GetEndPoint(0);
                        var gp1 = g.Curve.GetEndPoint(1);
                        bool gridIsVert = Math.Abs(gp0.X - gp1.X) < 0.01;
                        bool gridIsHoriz = Math.Abs(gp0.Y - gp1.Y) < 0.01;

                        if (isHorizontal && gridIsVert)
                        {
                            double gx = gp0.X * FT_TO_MM;
                            if (bb != null && gx >= (bb.Min.X * FT_TO_MM - 100) && gx <= (bb.Max.X * FT_TO_MM + 100))
                            {
                                wallPoints.Add(Tuple.Create(Math.Round(gx, 1), new Reference(g)));
                            }
                        }
                        else if (isVertical && gridIsHoriz)
                        {
                            double gy = gp0.Y * FT_TO_MM;
                            if (bb != null && gy >= (bb.Min.Y * FT_TO_MM - 100) && gy <= (bb.Max.Y * FT_TO_MM + 100))
                            {
                                wallPoints.Add(Tuple.Create(Math.Round(gy, 1), new Reference(g)));
                            }
                        }
                    }

                    // 4. Clean & deduplicate (< 20mm)
                    var sorted = wallPoints.OrderBy(p => p.Item1).ToList();
                    var clean = new List<Tuple<double, Reference>>();
                    foreach (var p in sorted)
                    {
                        if (clean.Count == 0 || Math.Abs(clean.Last().Item1 - p.Item1) > 20.0)
                        {
                            clean.Add(p);
                        }
                    }

                    if (clean.Count < 2) continue;

                    var refArr = new ReferenceArray();
                    foreach (var p in clean) refArr.Append(p.Item2);

                    Line dimLine;
                    if (isHorizontal)
                    {
                        double wallYMm = (pt0.Y + pt1.Y) * 0.5 * FT_TO_MM;
                        double dimYMm = wallYMm - userOffsetMm;
                        double xMinFt = (clean.First().Item1 - 800.0) * MM_TO_FT;
                        double xMaxFt = (clean.Last().Item1 + 800.0) * MM_TO_FT;
                        double yFt = dimYMm * MM_TO_FT;
                        dimLine = Line.CreateBound(new XYZ(xMinFt, yFt, 0), new XYZ(xMaxFt, yFt, 0));
                    }
                    else
                    {
                        double wallXMm = (pt0.X + pt1.X) * 0.5 * FT_TO_MM;
                        double dimXMm = wallXMm - userOffsetMm;
                        double yMinFt = (clean.First().Item1 - 800.0) * MM_TO_FT;
                        double yMaxFt = (clean.Last().Item1 + 800.0) * MM_TO_FT;
                        double xFt = dimXMm * MM_TO_FT;
                        dimLine = Line.CreateBound(new XYZ(xFt, yMinFt, 0), new XYZ(xFt, yMaxFt, 0));
                    }

                    try
                    {
                        var dim = doc.Create.NewDimension(view, dimLine, refArr, dimType);
                        if (dim != null)
                        {
                            createdDims.Add(dim);

                            // Stagger <= 200mm
                            if (dim.Segments != null && dim.Segments.Size > 1)
                            {
                                var movedHistory = new List<Tuple<double, double>>();
                                foreach (DimensionSegment seg in dim.Segments)
                                {
                                    double valMm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 0) : 0;
                                    if (valMm > 200 || !seg.IsTextPositionAdjustable()) continue;

                                    var origPos = seg.TextPosition;
                                    if (origPos == null) continue;

                                    double alongCoord = isHorizontal ? (origPos.X * FT_TO_MM) : (origPos.Y * FT_TO_MM);
                                    var nearby = movedHistory.Where(m => Math.Abs(m.Item1 - alongCoord) < 800.0).ToList();

                                    bool goPos = true;
                                    int level = 1;
                                    if (nearby.Count > 0)
                                    {
                                        goPos = nearby.Last().Item2 < 0;
                                        level = (nearby.Count % 3) + 1;
                                    }

                                    double offVal = level switch { 1 => 500.0, 2 => 800.0, _ => 1100.0 };
                                    double shiftMm = goPos ? offVal : -offVal;

                                    XYZ newPos = isHorizontal
                                        ? new XYZ(origPos.X, origPos.Y + shiftMm * MM_TO_FT, origPos.Z)
                                        : new XYZ(origPos.X + shiftMm * MM_TO_FT, origPos.Y, origPos.Z);

                                    seg.TextPosition = newPos;
                                    movedHistory.Add(Tuple.Create(alongCoord, shiftMm));
                                    shiftedCount++;
                                }
                            }
                        }
                    }
                    catch {}
                }

                tx.Commit();
            }

            return new {
                success = true,
                wallsProcessed = targetWalls.Count,
                dimensionsCreated = createdDims.Count,
                shiftedCount,
                dimensions = createdDims.Select(d => new {
                    id = d.Id.Value,
                    numSegments = d.Segments?.Size ?? 0
                }).ToList()
            };
        }
    }
}
