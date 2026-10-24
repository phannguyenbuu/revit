using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class BuildCompleteHorizontalDimensions
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
            if (doc == null || view == null) return new { error = "No active ViewPlan" };

            var opt = new Options { ComputeReferences = true, View = view };

            // Pick DimensionType: Linear Dimension Style
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

            // Helper to collect X planar faces from walls
            Func<Wall, List<Tuple<double, Reference>>> getWallXFaces = (w) => {
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

            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            // Helper to collect available references in a Y band
            Func<double, double, List<Tuple<double, Reference>>> collectBandRefs = (minY, maxY) => {
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

            // Helper to build a curated dimension chain
            Func<double, List<double>, List<Tuple<double, Reference>>, Dimension> buildCuratedChain = (yMm, targets, available) => {
                var chosen = new List<Tuple<double, Reference>>();
                foreach (var t in targets)
                {
                    var match = available
                        .Where(r => Math.Abs(r.Item1 - t) <= 45.0)
                        .OrderBy(r => Math.Abs(r.Item1 - t))
                        .FirstOrDefault();

                    if (match != null)
                    {
                        if (!chosen.Any(c => Math.Abs(c.Item1 - match.Item1) < 45.0))
                        {
                            chosen.Add(match);
                        }
                    }
                }
                chosen = chosen.OrderBy(c => c.Item1).ToList();
                if (chosen.Count < 2) return null;

                var refArray = new ReferenceArray();
                foreach (var c in chosen) refArray.Append(c.Item2);

                double yFt = yMm * MM_TO_FT;
                double x1Ft = (chosen.First().Item1 - 1000.0) * MM_TO_FT;
                double x2Ft = (chosen.Last().Item1 + 1000.0) * MM_TO_FT;
                var line = Line.CreateBound(new XYZ(x1Ft, yFt, 0), new XYZ(x2Ft, yFt, 0));

                return doc.Create.NewDimension(view, line, refArray, dimType);
            };

            var createdDimIds = new List<ElementId>();
            var dimSummaries = new List<object>();

            using (var tx = new Transaction(doc, "Build All 4 Detailed Horizontal Dimensions"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);
                tx.Start();

                // Delete old dimensions: 2408820, 2408823, and test dims 2409277..2409280
                var oldIds = new long[] { 2408820, 2408823, 2409277, 2409278, 2409279, 2409280 };
                foreach (var oldId in oldIds)
                {
                    try { doc.Delete(new ElementId(oldId)); } catch { }
                }

                // -------------------------------------------------------------
                // 1. CHAIN 1: South Exterior Refined Detail at Y = -1200 mm
                // -------------------------------------------------------------
                var southAvailable = collectBandRefs(-1000, 1500);
                var southTargets = new List<double> {
                    550, 700, 800, 900, 1800, 2100, 3000, 3150, 3300, 4150, 4250, 4350,
                    5558, 7058, 7950, 8050, 8150, 9108, 10608, 11650, 12708, 14208,
                    15150, 15250, 15350, 16308, 17808, 18850, 19908, 21408, 22350, 22450,
                    22550, 23508, 25008, 26050, 27108, 28608, 29550, 29650, 29750, 30658,
                    32150, 33350, 34450, 34650, 35650, 35950, 37050, 37150, 37550
                };
                var dSouth = buildCuratedChain(-1200.0, southTargets, southAvailable);
                if (dSouth != null) createdDimIds.Add(dSouth.Id);

                // -------------------------------------------------------------
                // 2. CHAIN 2: North Exterior Refined Detail at Y = 16000 mm
                // -------------------------------------------------------------
                var northAvailable = collectBandRefs(13100, 15500);
                var northTargets = new List<double> {
                    550, 4350, 4450, 4658, 7758, 7950, 8050, 8150, 9058, 10558,
                    11650, 12658, 14158, 15250, 16308, 17808, 18850, 22450, 24296,
                    25796, 26050, 27446, 28946, 29550, 29650, 29750, 29958, 33058,
                    33250, 33350, 33450, 33758, 35258, 37150, 37550
                };
                var dNorth = buildCuratedChain(16000.0, northTargets, northAvailable);
                if (dNorth != null) createdDimIds.Add(dNorth.Id);

                // -------------------------------------------------------------
                // 3. CHAIN 3: Interior Band AB at Y = 3000 mm
                // -------------------------------------------------------------
                var abAvailable = collectBandRefs(50, 5350);
                var abTargets = new List<double> {
                    550, 700, 800, 900, 1750, 1800, 2100, 3000, 3150, 3300, 4350,
                    5550, 5950, 7050, 7350, 7950, 8050, 8150, 8750, 9100, 10150, 10600,
                    11650, 12700, 13150, 14200, 14550, 15150, 15250, 15350, 15550,
                    16300, 16550, 17800, 18850, 19900, 21400, 22350, 22450, 22550,
                    22650, 23500, 23650, 25000, 26050, 27100, 28600, 29550, 29650,
                    29750, 30050, 30650, 31050, 32150, 33350, 33550, 34450, 34650,
                    34750, 35550, 35650, 35950, 36150, 36850, 37050, 37150, 37550
                };
                var dAB = buildCuratedChain(3000.0, abTargets, abAvailable);
                if (dAB != null) createdDimIds.Add(dAB.Id);

                // -------------------------------------------------------------
                // 4. CHAIN 4: Interior Band CD at Y = 10800 mm
                // -------------------------------------------------------------
                var cdAvailable = collectBandRefs(7850, 13150);
                var cdTargets = new List<double> {
                    550, 700, 800, 900, 1800, 2100, 3000, 3300, 4250, 4350,
                    4450, 4550, 5750, 7950, 8050, 8150, 8400, 9050, 9400, 10550,
                    11650, 12650, 14150, 15150, 15250, 15350, 15500, 16300, 16500,
                    17800, 18750, 18850, 18950, 19900, 20250, 21250, 21400, 21500,
                    22450, 22850, 23000, 23850, 23950, 24150, 24300, 24350, 25350,
                    25800, 26050, 26650, 26850, 27450, 28400, 28950, 29400, 29550,
                    29650, 29750, 31950, 33150, 33250, 33350, 33450, 33550, 33750,
                    34350, 34550, 34650, 34900, 35000, 35250, 37000, 37050, 37150,
                    37350, 37450, 37550
                };
                var dCD = buildCuratedChain(10800.0, cdTargets, cdAvailable);
                if (dCD != null) createdDimIds.Add(dCD.Id);

                tx.Commit();
            }

            // Set Revit selection to the newly created dimensions
            if (createdDimIds.Count > 0)
            {
                uidoc.Selection.SetElementIds(createdDimIds);
            }

            // Inspect segments
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

            foreach (var id in createdDimIds)
            {
                var d = doc.GetElement(id) as Dimension;
                var segs = getSegs(d);
                dimSummaries.Add(new {
                    id = id.Value,
                    y = d?.Curve is Line l ? Math.Round(l.Origin.Y * FT_TO_MM, 0) : 0,
                    segCount = segs.Count,
                    segs = string.Join(", ", segs)
                });
            }

            // Export verification images
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

            // 1. Zoom Band AB
            if (uiview != null)
            {
                XYZ p1 = new XYZ(-1000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                XYZ p2 = new XYZ(39000.0 * MM_TO_FT, 6000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }
            string imgAB = Path.Combine(outDir, "revit_zoom_band_ab_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgAB,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 2. Zoom Band CD with Stairs
            if (uiview != null)
            {
                XYZ p3 = new XYZ(-1000.0 * MM_TO_FT, 7000.0 * MM_TO_FT, 0);
                XYZ p4 = new XYZ(39000.0 * MM_TO_FT, 15000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p3, p4);
            }
            string imgCD = Path.Combine(outDir, "revit_zoom_band_cd_stairs_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgCD,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 3. Full floor plan overview
            if (uiview != null)
            {
                XYZ p5 = new XYZ(-12000.0 * MM_TO_FT, -6000.0 * MM_TO_FT, 0);
                XYZ p6 = new XYZ(46000.0 * MM_TO_FT, 21000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p5, p6);
            }
            string imgFull = Path.Combine(outDir, "revit_full_tang1_all_horizontal_and_exterior_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgFull,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            });

            return new {
                success = true,
                dimCount = createdDimIds.Count,
                dims = dimSummaries,
                images = new { imgAB, imgCD, imgFull }
            };
        }
    }
}
