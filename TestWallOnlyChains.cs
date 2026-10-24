using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestWallOnlyChains
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

        public class DimPt
        {
            public double X { get; set; }
            public Reference Ref { get; set; }
            public string Source { get; set; }
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

            Func<Wall, List<DimPt>> getWallXPoints = (w) => {
                var list = new List<DimPt>();
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
                                list.Add(new DimPt { X = x, Ref = pf.Reference, Source = $"{w.Name} ({w.Id.Value})" });
                            }
                        }
                    }
                }
                return list;
            };

            // Test collecting for Band AB
            var allWalls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .ToList();

            Func<double, double, List<DimPt>> collectBand = (minY, maxY) => {
                var pts = new List<DimPt>();
                foreach (var g in vGrids) pts.Add(new DimPt { X = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1), Ref = new Reference(g), Source = $"Grid {g.Name}" });

                var bandWalls = allWalls.Where(w => {
                    var bb = w.get_BoundingBox(view);
                    if (bb == null) return false;
                    return bb.Max.Y * FT_TO_MM >= minY && bb.Min.Y * FT_TO_MM <= maxY;
                }).ToList();

                foreach (var w in bandWalls) pts.AddRange(getWallXPoints(w));
                return pts;
            };

            var abRaw = collectBand(50, 5350);
            var cdRaw = collectBand(7850, 13150);
            var southRaw = collectBand(-1000, 1500);
            var northRaw = collectBand(13500, 15500);

            // Group by ~40mm
            Func<List<DimPt>, List<double>> getDistinctCoords = (raw) => {
                return raw.GroupBy(p => Math.Round(p.X / 50.0) * 50.0)
                          .Select(g => g.Key)
                          .OrderBy(x => x)
                          .ToList();
            };

            return new {
                southCoords = getDistinctCoords(southRaw),
                northCoords = getDistinctCoords(northRaw),
                abCoords = getDistinctCoords(abRaw),
                cdCoords = getDistinctCoords(cdRaw)
            };
        }
    }
}
