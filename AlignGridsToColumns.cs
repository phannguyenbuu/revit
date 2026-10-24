using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class AlignGridsToColumns
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Target X coordinates for vertical grids 1 to 11 (in meters)
            var targetGrids = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase)
            {
                { "1",   0.55 },
                { "2",   4.35 },
                { "3",   8.05 },
                { "4",  11.65 },
                { "5",  15.25 },
                { "6",  18.85 },
                { "7",  22.45 },
                { "8",  26.05 },
                { "9",  29.65 },
                { "10", 33.35 },
                { "11", 37.15 }
            };

            var existingGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var adjustedGrids = new List<object>();

            using (var tx = new Transaction(doc, "Align Grids to Columns"))
            {
                tx.Start();

                foreach (var g in existingGrids)
                {
                    if (targetGrids.TryGetValue(g.Name, out double targetXm))
                    {
                        var c = g.Curve;
                        var p1 = c.GetEndPoint(0);
                        var p2 = c.GetEndPoint(1);

                        // Check if vertical (same X roughly)
                        if (Math.Abs(p1.X - p2.X) < 0.1)
                        {
                            double currentXm = p1.X * 0.3048;
                            double diffXm = targetXm - currentXm;

                            if (Math.Abs(diffXm) > 0.001) // if needs moving
                            {
                                var moveVec = new XYZ(diffXm * M2FT, 0, 0);
                                ElementTransformUtils.MoveElement(doc, g.Id, moveVec);

                                adjustedGrids.Add(new
                                {
                                    name = g.Name,
                                    id = g.Id.Value,
                                    oldX = Math.Round(currentXm, 4),
                                    newX = Math.Round(targetXm, 4),
                                    deltaX = Math.Round(diffXm, 4)
                                });
                            }
                            else
                            {
                                adjustedGrids.Add(new
                                {
                                    name = g.Name,
                                    id = g.Id.Value,
                                    currentX = Math.Round(currentXm, 4),
                                    status = "Already aligned"
                                });
                            }
                        }
                    }
                }

                tx.Commit();
            }

            // Ensure active view is updated and zoom to grids
            try
            {
                var viewTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

                if (viewTang1 != null)
                {
                    uidoc.ActiveView = viewTang1;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);
                    uiview?.ZoomToFit();
                }
            }
            catch { }

            return new
            {
                success = true,
                totalAdjusted = adjustedGrids.Count,
                grids = adjustedGrids
            };
        }
    }
}
