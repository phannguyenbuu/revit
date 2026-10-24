using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateFull3LayerDimensions
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

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No active ViewPlan" };

            // 1. Pick DimensionType
            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                .ToList();

            var dimType = dimTypes.FirstOrDefault(dt => dt.Name == "Linear Dimension Style")
                       ?? dimTypes.FirstOrDefault(dt => dt.Name == "kt nam")
                       ?? dimTypes.First();

            var textType = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .FirstOrDefault(t => t.Name == "2.5mm Arial")
                ?? new FilteredElementCollector(doc).OfClass(typeof(TextNoteType)).Cast<TextNoteType>().First();

            var createdDimIds = new List<long>();
            var createdCurveIds = new List<long>();
            var log = new List<string>();

            using (var tx = new Transaction(doc, "Create Tam Cap Arrow and 3-Layer Dimensions"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);

                tx.Start();

                // -------------------------------------------------------------
                // PART 0: Clean up any old dimensions/curves created in testing
                // -------------------------------------------------------------
                var existingDims = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Dimension))
                    .ToElementIds();
                foreach (var id in existingDims)
                {
                    try { doc.Delete(id); } catch { }
                }

                var oldCurveIds = new List<long> {
                    2408696, 2408697, 2408698, 2408699, 2408700, 2408701,
                    2408714, 2408715, 2408716, 2408717, 2408718, 2408719
                };
                foreach (var id in oldCurveIds)
                {
                    try
                    {
                        var el = doc.GetElement(new ElementId(id));
                        if (el != null) doc.Delete(el.Id);
                    }
                    catch { }
                }

                // -------------------------------------------------------------
                // PART 1: STAIR PATH ARROW (Tam Cap 5 bac)
                // -------------------------------------------------------------
                // Tim: Y = 6600 mm. From X = 39400 mm (right, low step) to X = 37800 mm (left, high landing)
                double yTim = 6600.0 * MM_TO_FT;
                double xStart = 39400.0 * MM_TO_FT; // Low step on right
                double xEnd = 37800.0 * MM_TO_FT;   // High step on left (landing before door D2)

                // Shaft line
                var shaft = Line.CreateBound(new XYZ(xStart, yTim, 0), new XYZ(xEnd, yTim, 0));
                var cShaft = doc.Create.NewDetailCurve(view, shaft);
                createdCurveIds.Add(cShaft.Id.Value);

                // Start circle (R = 70 mm)
                double rCircle = 70.0 * MM_TO_FT;
                var arc1 = Arc.Create(new XYZ(xStart - rCircle, yTim, 0), new XYZ(xStart + rCircle, yTim, 0), new XYZ(xStart, yTim + rCircle, 0));
                var arc2 = Arc.Create(new XYZ(xStart + rCircle, yTim, 0), new XYZ(xStart - rCircle, yTim, 0), new XYZ(xStart, yTim - rCircle, 0));
                var cArc1 = doc.Create.NewDetailCurve(view, arc1);
                var cArc2 = doc.Create.NewDetailCurve(view, arc2);
                createdCurveIds.Add(cArc1.Id.Value);
                createdCurveIds.Add(cArc2.Id.Value);

                // Arrowhead pointing LEFT at xEnd
                double barbX = 220.0 * MM_TO_FT;
                double barbY = 85.0 * MM_TO_FT;
                var barbTop = Line.CreateBound(new XYZ(xEnd, yTim, 0), new XYZ(xEnd + barbX, yTim + barbY, 0));
                var barbBottom = Line.CreateBound(new XYZ(xEnd, yTim, 0), new XYZ(xEnd + barbX, yTim - barbY, 0));
                var cBarb1 = doc.Create.NewDetailCurve(view, barbTop);
                var cBarb2 = doc.Create.NewDetailCurve(view, barbBottom);
                createdCurveIds.Add(cBarb1.Id.Value);
                createdCurveIds.Add(cBarb2.Id.Value);

                // TextNote "LÊN" cleanly above arrow shaft (Y = 6600 + 300 = 6900 mm)
                var textPt = new XYZ(38550.0 * MM_TO_FT, 6900.0 * MM_TO_FT, 0);
                var note = TextNote.Create(doc, view.Id, textPt, "LÊN", new TextNoteOptions {
                    TypeId = textType.Id,
                    HorizontalAlignment = HorizontalTextAlignment.Center
                });
                if (note != null) createdCurveIds.Add(note.Id.Value);

                log.Add("Tam Cap Stair Path Arrow created successfully.");

                // -------------------------------------------------------------
                // Collect Grids
                // -------------------------------------------------------------
                var allGrids = new FilteredElementCollector(doc)
                    .OfClass(typeof(Grid))
                    .Cast<Grid>()
                    .ToList();

                var vGrids = new List<Grid>(); // 1 to 11
                var hGrids = new List<Grid>(); // A to E

                foreach (var g in allGrids)
                {
                    var p1 = g.Curve.GetEndPoint(0);
                    var p2 = g.Curve.GetEndPoint(1);
                    if (Math.Abs(p1.X - p2.X) < 0.01) vGrids.Add(g);
                    else if (Math.Abs(p1.Y - p2.Y) < 0.01) hGrids.Add(g);
                }
                vGrids = vGrids.OrderBy(g => g.Curve.GetEndPoint(0).X).ToList();
                hGrids = hGrids.OrderBy(g => g.Curve.GetEndPoint(0).Y).ToList();

                // Helper method to create a dimension from a list of RefPoints
                Func<List<RefPoint>, bool, double, Dimension> createDimChain = (pts, isHorizontal, fixedCoordMm) =>
                {
                    // Sort by coordinate
                    var sorted = pts.OrderBy(p => p.Coord).ToList();
                    // Deduplicate within 10mm
                    var clean = new List<RefPoint>();
                    foreach (var p in sorted)
                    {
                        if (clean.Count == 0 || Math.Abs(clean.Last().Coord - p.Coord) > 10.0)
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
                        double xMin = (clean.First().Coord - 1000.0) * MM_TO_FT;
                        double xMax = (clean.Last().Coord + 1000.0) * MM_TO_FT;
                        dimLine = Line.CreateBound(new XYZ(xMin, yFt, 0), new XYZ(xMax, yFt, 0));
                    }
                    else
                    {
                        double xFt = fixedCoordMm * MM_TO_FT;
                        double yMin = (clean.First().Coord - 1000.0) * MM_TO_FT;
                        double yMax = (clean.Last().Coord + 1000.0) * MM_TO_FT;
                        dimLine = Line.CreateBound(new XYZ(xFt, yMin, 0), new XYZ(xFt, yMax, 0));
                    }

                    try
                    {
                        var d = doc.Create.NewDimension(view, dimLine, refArr, dimType);
                        if (d != null) createdDimIds.Add(d.Id.Value);
                        return d;
                    }
                    catch (Exception ex)
                    {
                        log.Add($"Error creating chain ({clean.Count} refs): {ex.Message}");
                        return null;
                    }
                };

                // -------------------------------------------------------------
                // PART 2: DIM 3 LỚP PHÍA NAM (SOUTH - X Axis, below Grid A)
                // -------------------------------------------------------------
                // Lớp 1 (ngoài cùng): Dim tổng Trục 1 - Trục 11 at Y = -4600 mm (below section callout)
                var southL1 = new List<RefPoint> {
                    new RefPoint { Ref = new Reference(vGrids.First()), Coord = vGrids.First().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 1" },
                    new RefPoint { Ref = new Reference(vGrids.Last()), Coord = vGrids.Last().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 11" }
                };
                createDimChain(southL1, true, -4600.0);

                // Lớp 2 (ở giữa): Dim tim trục 1 -> 11 at Y = -2200 mm (between wall and grid bubbles)
                var southL2 = vGrids.Select(g => new RefPoint {
                    Ref = new Reference(g),
                    Coord = g.Curve.GetEndPoint(0).X * FT_TO_MM,
                    Name = g.Name
                }).ToList();
                createDimChain(southL2, true, -2200.0);

                // Lớp 3 (trong cùng): Dim chi tiết tường, cửa sổ S1, vách kính K2 at Y = -1200 mm
                var southL3 = new List<RefPoint>();
                // Add Grid 1 & 11 as boundary anchors
                southL3.Add(new RefPoint { Ref = new Reference(vGrids.First()), Coord = vGrids.First().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 1" });
                southL3.Add(new RefPoint { Ref = new Reference(vGrids.Last()), Coord = vGrids.Last().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 11" });

                // South windows S1 (IDs 2361245..2361252)
                var southS1Windows = new FilteredElementCollector(doc, view.Id)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .Cast<FamilyInstance>()
                    .Where(w => (w.Location as LocationPoint)?.Point.Y * FT_TO_MM < 2000 && w.Symbol.FamilyName.Contains("CUA SO"))
                    .ToList();

                foreach (var w in southS1Windows)
                {
                    var leftRefs = w.GetReferences(FamilyInstanceReferenceType.Left);
                    var rightRefs = w.GetReferences(FamilyInstanceReferenceType.Right);
                    var pt = (w.Location as LocationPoint).Point * FT_TO_MM;
                    if (leftRefs.Count > 0 && rightRefs.Count > 0)
                    {
                        southL3.Add(new RefPoint { Ref = leftRefs[0], Coord = pt.X - 750.0, Name = $"Window {w.Id} Left" });
                        southL3.Add(new RefPoint { Ref = rightRefs[0], Coord = pt.X + 750.0, Name = $"Window {w.Id} Right" });
                    }
                }
                var dSouthL3 = createDimChain(southL3, true, -1200.0);
                log.Add($"South Dims created (L1, L2, L3 result: {dSouthL3 != null})");

                // -------------------------------------------------------------
                // PART 3: DIM 3 LỚP PHÍA BẮC (NORTH - X Axis, above Grid E)
                // -------------------------------------------------------------
                // Lớp 1 (ngoài cùng): Dim tổng Trục 1 - Trục 11 at Y = 19600 mm (above grid bubbles)
                var northL1 = new List<RefPoint> {
                    new RefPoint { Ref = new Reference(vGrids.First()), Coord = vGrids.First().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 1" },
                    new RefPoint { Ref = new Reference(vGrids.Last()), Coord = vGrids.Last().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 11" }
                };
                createDimChain(northL1, true, 19600.0);

                // Lớp 2 (ở giữa): Dim tim trục 1 -> 11 at Y = 17200 mm
                var northL2 = vGrids.Select(g => new RefPoint {
                    Ref = new Reference(g),
                    Coord = g.Curve.GetEndPoint(0).X * FT_TO_MM,
                    Name = g.Name
                }).ToList();
                createDimChain(northL2, true, 17200.0);

                // Lớp 3 (trong cùng): Dim chi tiết cửa sổ K3, S1, S5, S4 buồng thang at Y = 16000 mm
                var northL3 = new List<RefPoint>();
                northL3.Add(new RefPoint { Ref = new Reference(vGrids.First()), Coord = vGrids.First().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 1" });
                northL3.Add(new RefPoint { Ref = new Reference(vGrids.Last()), Coord = vGrids.Last().Curve.GetEndPoint(0).X * FT_TO_MM, Name = "Grid 11" });

                var northWindows = new FilteredElementCollector(doc, view.Id)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .Cast<FamilyInstance>()
                    .Where(w => (w.Location as LocationPoint)?.Point.Y * FT_TO_MM > 12000 && !w.Symbol.Name.Contains("K2"))
                    .ToList();

                foreach (var w in northWindows)
                {
                    var leftRefs = w.GetReferences(FamilyInstanceReferenceType.Left);
                    var rightRefs = w.GetReferences(FamilyInstanceReferenceType.Right);
                    var bb = w.get_BoundingBox(view);
                    if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                    {
                        northL3.Add(new RefPoint { Ref = leftRefs[0], Coord = bb.Min.X * FT_TO_MM, Name = $"Window {w.Id} Left" });
                        northL3.Add(new RefPoint { Ref = rightRefs[0], Coord = bb.Max.X * FT_TO_MM, Name = $"Window {w.Id} Right" });
                    }
                }
                var dNorthL3 = createDimChain(northL3, true, 16000.0);
                log.Add($"North Dims created (L1, L2, L3 result: {dNorthL3 != null})");

                // -------------------------------------------------------------
                // PART 4: DIM 3 LỚP PHÍA TÂY (WEST - Y Axis, left of Grid 1 & Facade)
                // -------------------------------------------------------------
                // Facade extends to X = -6274 mm. Section head is around X = -8300 mm.
                // Lớp 1 (ngoài cùng): Dim tổng Trục A - Trục E at X = -10400 mm
                var westL1 = new List<RefPoint> {
                    new RefPoint { Ref = new Reference(hGrids.First()), Coord = hGrids.First().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid A" },
                    new RefPoint { Ref = new Reference(hGrids.Last()), Coord = hGrids.Last().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid E" }
                };
                createDimChain(westL1, false, -10400.0);

                // Lớp 2 (ở giữa): Dim tim trục A -> E at X = -9200 mm
                var westL2 = hGrids.Select(g => new RefPoint {
                    Ref = new Reference(g),
                    Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM,
                    Name = g.Name
                }).ToList();
                createDimChain(westL2, false, -9200.0);

                // Lớp 3 (trong cùng ngoài sảnh): Dim chi tiết bao sảnh chính, cửa D1, trục A, D, E at X = -7200 mm
                var westL3 = new List<RefPoint>();
                foreach (var g in hGrids)
                {
                    westL3.Add(new RefPoint { Ref = new Reference(g), Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM, Name = g.Name });
                }

                // Cửa đi D1 (2364731) sảnh chính
                var doorD1 = doc.GetElement(new ElementId(2364731)) as FamilyInstance;
                if (doorD1 != null)
                {
                    var leftRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Left);
                    var rightRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Right);
                    var bb = doorD1.get_BoundingBox(view);
                    if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                    {
                        westL3.Add(new RefPoint { Ref = leftRefs[0], Coord = bb.Min.Y * FT_TO_MM, Name = "Door D1 Bottom" });
                        westL3.Add(new RefPoint { Ref = rightRefs[0], Coord = bb.Max.Y * FT_TO_MM, Name = "Door D1 Top" });
                    }
                }
                var dWestL3 = createDimChain(westL3, false, -7200.0);

                // Dim chi tiết diện tường sảnh chính dọc Trục 1 (X = -1200 mm)
                var westWallDetail = new List<RefPoint>();
                westWallDetail.Add(new RefPoint { Ref = new Reference(hGrids.First()), Coord = 0, Name = "Grid A" });
                if (doorD1 != null)
                {
                    var leftRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Left);
                    var rightRefs = doorD1.GetReferences(FamilyInstanceReferenceType.Right);
                    var bb = doorD1.get_BoundingBox(view);
                    if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                    {
                        westWallDetail.Add(new RefPoint { Ref = leftRefs[0], Coord = bb.Min.Y * FT_TO_MM, Name = "Door D1 Bottom" });
                        westWallDetail.Add(new RefPoint { Ref = rightRefs[0], Coord = bb.Max.Y * FT_TO_MM, Name = "Door D1 Top" });
                    }
                }
                westWallDetail.Add(new RefPoint { Ref = new Reference(hGrids.Last()), Coord = 14900, Name = "Grid E" });
                createDimChain(westWallDetail, false, -1200.0);
                log.Add($"West Dims created (L1, L2, L3 result: {dWestL3 != null})");

                // -------------------------------------------------------------
                // PART 5: DIM 3 LỚP PHÍA ĐÔNG (EAST - Y Axis, right of Tam Cap & Grid 11)
                // -------------------------------------------------------------
                // Tam cap extends to X = 39550 mm. Section head extends to X = 42500 mm.
                // Lớp 1 (ngoài cùng): Dim tổng Trục A - Trục E at X = 44400 mm
                var eastL1 = new List<RefPoint> {
                    new RefPoint { Ref = new Reference(hGrids.First()), Coord = hGrids.First().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid A" },
                    new RefPoint { Ref = new Reference(hGrids.Last()), Coord = hGrids.Last().Curve.GetEndPoint(0).Y * FT_TO_MM, Name = "Grid E" }
                };
                createDimChain(eastL1, false, 44400.0);

                // Lớp 2 (ở giữa): Dim tim trục A -> E at X = 43200 mm (cleanly clear of section callout)
                var eastL2 = hGrids.Select(g => new RefPoint {
                    Ref = new Reference(g),
                    Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM,
                    Name = g.Name
                }).ToList();
                createDimChain(eastL2, false, 43200.0);

                // Lớp 3 (trong cùng): Dim chi tiết mép tam cấp, cửa D2, WC at X = 40500 mm
                var eastL3 = new List<RefPoint>();
                foreach (var g in hGrids)
                {
                    eastL3.Add(new RefPoint { Ref = new Reference(g), Coord = g.Curve.GetEndPoint(0).Y * FT_TO_MM, Name = g.Name });
                }

                // Cửa đi D2 ra tam cấp (2408526)
                var doorD2 = doc.GetElement(new ElementId(2408526)) as FamilyInstance;
                if (doorD2 != null)
                {
                    var leftRefs = doorD2.GetReferences(FamilyInstanceReferenceType.Left);
                    var rightRefs = doorD2.GetReferences(FamilyInstanceReferenceType.Right);
                    var bb = doorD2.get_BoundingBox(view);
                    if (leftRefs.Count > 0 && rightRefs.Count > 0 && bb != null)
                    {
                        eastL3.Add(new RefPoint { Ref = leftRefs[0], Coord = bb.Min.Y * FT_TO_MM, Name = "Door D2 Bottom" });
                        eastL3.Add(new RefPoint { Ref = rightRefs[0], Coord = bb.Max.Y * FT_TO_MM, Name = "Door D2 Top" });
                    }
                }
                var dEastL3 = createDimChain(eastL3, false, 40500.0);
                log.Add($"East Dims created (L1, L2, L3 result: {dEastL3 != null})");

                // -------------------------------------------------------------
                // PART 6: DIM CHI TIẾT 5 BẬC TAM CẤP (X & Y Axis at Tam Cap)
                // -------------------------------------------------------------
                // Tam cap step floors: 2408631, 2408638, 2408645, 2408652, 2408659
                var tamCapStepFloorIds = new List<long> { 2408631, 2408638, 2408645, 2408652, 2408659 };
                var stepRefPoints = new List<RefPoint>();
                var optGeom = new Options { ComputeReferences = true, View = view };

                foreach (var sId in tamCapStepFloorIds)
                {
                    var fl = doc.GetElement(new ElementId(sId)) as Floor;
                    if (fl == null) continue;
                    var geom = fl.get_Geometry(optGeom);
                    if (geom == null) continue;

                    foreach (var obj in geom)
                    {
                        if (obj is Solid s && s.Faces != null)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01 && pf.Reference != null)
                                {
                                    double coordX = pf.Origin.X * FT_TO_MM;
                                    stepRefPoints.Add(new RefPoint { Ref = pf.Reference, Coord = coordX, Name = $"Step {sId} X={coordX}" });
                                }
                            }
                        }
                    }
                }

                // Create horizontal dimension across 5 steps at Y = 4600 mm (below tam cap)
                var dStepsX = createDimChain(stepRefPoints, true, 4600.0);
                log.Add($"Tam Cap Step Dims (X axis) created: {dStepsX != null} ({stepRefPoints.Count} face refs)");

                // Create overall tam cap length dimension at Y = 4000 mm
                var overallStepPoints = new List<RefPoint>();
                var sortedSteps = stepRefPoints.OrderBy(p => p.Coord).ToList();
                if (sortedSteps.Count >= 2)
                {
                    overallStepPoints.Add(sortedSteps.First());
                    overallStepPoints.Add(sortedSteps.Last());
                    createDimChain(overallStepPoints, true, 4000.0);
                }

                // Create width dimension of tam cap (Y = 5500 to 7700) at X = 39800 mm
                var tamCapYRefs = new List<RefPoint>();
                var fl1 = doc.GetElement(new ElementId(2408631)) as Floor;
                if (fl1 != null)
                {
                    var geom = fl1.get_Geometry(optGeom);
                    if (geom != null)
                    {
                        foreach (var obj in geom)
                        {
                            if (obj is Solid s && s.Faces != null)
                            {
                                foreach (Face f in s.Faces)
                                {
                                    if (f is PlanarFace pf && Math.Abs(Math.Abs(pf.FaceNormal.Y) - 1.0) < 0.01 && pf.Reference != null)
                                    {
                                        double coordY = pf.Origin.Y * FT_TO_MM;
                                        tamCapYRefs.Add(new RefPoint { Ref = pf.Reference, Coord = coordY, Name = $"TamCap Y={coordY}" });
                                    }
                                }
                            }
                        }
                    }
                }
                var dStepsY = createDimChain(tamCapYRefs, false, 39800.0);
                log.Add($"Tam Cap Step Dims (Y axis) created: {dStepsY != null}");

                tx.Commit();
            }

            return new {
                status = "Success",
                createdDimCount = createdDimIds.Count,
                createdDimIds,
                createdCurveCount = createdCurveIds.Count,
                createdCurveIds,
                log
            };
        }
    }
}
