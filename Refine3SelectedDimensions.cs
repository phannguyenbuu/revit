using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Refine3SelectedDimensions
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

            // Helper to get PlanarFaces with normal parallel to Y
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

            // Targets for West Wall (Dim 2 at X = -1200 mm):
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

            // Targets for East Wall & Tam Cap & WC (Dim 3 at X = 40500 mm):
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

            // Targets for West Mat Tien & Sanh Chinh (Dim 1 at X = -7200 mm):
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

            Func<Line, double[], List<Tuple<double, Reference, string>>, double, Tuple<Dimension, List<double>>> createDim = (line, targets, pool, maxDist) => {
                var found = new List<Tuple<double, Reference>>();
                foreach (var t in targets)
                {
                    var r = findNearestRef(pool, t, maxDist);
                    if (r != null) found.Add(Tuple.Create(t, r));
                }

                var refArr = new ReferenceArray();
                foreach (var f in found) refArr.Append(f.Item2);

                try
                {
                    var dim = doc.Create.NewDimension(view, line, refArr, dimType);
                    var segs = new List<double>();
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
                    }
                    return Tuple.Create(dim, segs);
                }
                catch
                {
                    return Tuple.Create((Dimension)null, new List<double>());
                }
            };

            var newDimIds = new List<ElementId>();
            var results = new List<object>();

            using (var tx = new Transaction(doc, "Refine 3 Selected Dimensions to Full Detail"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);

                tx.Start();

                // 1. Delete old 3 coarse dimensions
                var oldDimIds = new List<long> { 2408826, 2408827, 2408830 };
                foreach (var id in oldDimIds)
                {
                    try
                    {
                        var el = doc.GetElement(new ElementId(id));
                        if (el != null) doc.Delete(el.Id);
                    }
                    catch { }
                }

                // 2. Recreate Dim 2: West Wall Detail along Grid 1 at X = -1200 mm
                var lineWestWall = Line.CreateBound(new XYZ(-1200.0 * MM_TO_FT, 0, 0), new XYZ(-1200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resWestWall = createDim(lineWestWall, westWallTargets, westPool, 25.0);
                if (resWestWall.Item1 != null)
                {
                    newDimIds.Add(resWestWall.Item1.Id);
                    results.Add(new {
                        name = "Dim 2 (West Wall Detail at X = -1200 mm)",
                        id = resWestWall.Item1.Id.Value,
                        segments = resWestWall.Item2
                    });
                }

                // 3. Recreate Dim 3: East Wall Detail & Tam Cap & WC at X = 40500 mm
                var lineEastWall = Line.CreateBound(new XYZ(40500.0 * MM_TO_FT, 0, 0), new XYZ(40500.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resEastWall = createDim(lineEastWall, eastWallTargets, eastPool, 25.0);
                if (resEastWall.Item1 != null)
                {
                    newDimIds.Add(resEastWall.Item1.Id);
                    results.Add(new {
                        name = "Dim 3 (East Wall Detail at X = 40500 mm)",
                        id = resEastWall.Item1.Id.Value,
                        segments = resEastWall.Item2
                    });
                }

                // 4. Recreate Dim 1: West Mat Tien & Sanh Chinh at X = -7200 mm
                var lineMatTien = Line.CreateBound(new XYZ(-7200.0 * MM_TO_FT, 0, 0), new XYZ(-7200.0 * MM_TO_FT, 14900.0 * MM_TO_FT, 0));
                var resMatTien = createDim(lineMatTien, matTienTargets, matTienPool, 25.0);
                if (resMatTien.Item1 != null)
                {
                    newDimIds.Add(resMatTien.Item1.Id);
                    results.Add(new {
                        name = "Dim 1 (West Mat Tien / Sanh Chinh at X = -7200 mm)",
                        id = resMatTien.Item1.Id.Value,
                        segments = resMatTien.Item2
                    });
                }

                tx.Commit();
            }

            // Set user selection to the 3 newly created detailed dimensions!
            if (newDimIds.Count > 0)
            {
                uidoc.Selection.SetElementIds(newDimIds);
            }

            // -----------------------------------------------------------------
            // EXPORT CLEAN VERIFICATION IMAGES
            // -----------------------------------------------------------------
            string artifactDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            Directory.CreateDirectory(artifactDir);

            Action<string, XYZ, XYZ, int> exportZoom = (fileName, minPt, maxPt, pixelSize) => {
                using (var tCrop = new Transaction(doc, "Export Zoom View"))
                {
                    var optCrop = tCrop.GetFailureHandlingOptions();
                    optCrop.SetFailuresPreprocessor(new WarningSwallower());
                    tCrop.SetFailureHandlingOptions(optCrop);
                    tCrop.Start();

                    bool origCropActive = view.CropBoxActive;
                    bool origCropVisible = view.CropBoxVisible;
                    var origCropBox = view.CropBox;

                    try
                    {
                        view.CropBoxActive = true;
                        view.CropBoxVisible = false;

                        var newBox = new BoundingBoxXYZ();
                        newBox.Min = minPt;
                        newBox.Max = maxPt;
                        view.CropBox = newBox;
                        doc.Regenerate();

                        string outPath = Path.Combine(artifactDir, fileName);
                        if (File.Exists(outPath)) { try { File.Delete(outPath); } catch { } }

                        var imgOpts = new ImageExportOptions {
                            ZoomType = ZoomFitType.FitToPage,
                            PixelSize = pixelSize,
                            FilePath = outPath,
                            FitDirection = FitDirectionType.Horizontal,
                            HLRandWFViewsFileType = ImageFileType.PNG,
                            ImageResolution = ImageResolution.DPI_300,
                            ExportRange = ExportRange.CurrentView,
                            ShadowViewsFileType = ImageFileType.PNG
                        };

                        doc.ExportImage(imgOpts);
                    }
                    finally
                    {
                        view.CropBox = origCropBox;
                        view.CropBoxActive = origCropActive;
                        view.CropBoxVisible = origCropVisible;
                        tCrop.RollBack();
                    }
                }
            };

            // 1. Zoom West facade and sảnh chính: X in [-11000, 3000], Y in [-1000, 16000]
            exportZoom("revit_zoom_west_sanh_chinh_dims.png",
                new XYZ(-11500.0 * MM_TO_FT, -1200.0 * MM_TO_FT, -50.0),
                new XYZ(3500.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 50.0),
                2600);

            // 2. Zoom East WC and tam cap: X in [33000, 46000], Y in [-1000, 16000]
            exportZoom("revit_zoom_tam_cap_with_dims_and_arrow.png",
                new XYZ(33000.0 * MM_TO_FT, -1200.0 * MM_TO_FT, -50.0),
                new XYZ(46000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 50.0),
                2600);

            // 3. Full overview: X in [-12000, 47000], Y in [-3000, 23000]
            exportZoom("revit_full_tang1_3layer_dimensions.png",
                new XYZ(-12500.0 * MM_TO_FT, -2500.0 * MM_TO_FT, -50.0),
                new XYZ(47000.0 * MM_TO_FT, 22000.0 * MM_TO_FT, 50.0),
                3200);

            return new {
                success = true,
                createdDims = results,
                selectedIds = newDimIds.Select(id => id.Value).ToList()
            };
        }
    }
}
