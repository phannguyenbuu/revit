using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectHorizontalBands
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Vertical Grids (1 to 11)
            var vGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => {
                    var p1 = g.Curve.GetEndPoint(0);
                    var p2 = g.Curve.GetEndPoint(1);
                    return Math.Abs(p1.X - p2.X) < 0.01;
                })
                .OrderBy(g => g.Curve.GetEndPoint(0).X)
                .Select(g => new {
                    name = g.Name,
                    x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1)
                })
                .ToList();

            // Horizontal Grids (A to E)
            var hGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => {
                    var p1 = g.Curve.GetEndPoint(0);
                    var p2 = g.Curve.GetEndPoint(1);
                    return Math.Abs(p1.Y - p2.Y) < 0.01;
                })
                .OrderBy(g => g.Curve.GetEndPoint(0).Y)
                .Select(g => new {
                    name = g.Name,
                    y = Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1)
                })
                .ToList();

            // Stairs
            var stairs = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Stairs,
                    BuiltInCategory.OST_StairsRuns,
                    BuiltInCategory.OST_StairsLandings
                }))
                .WhereElementIsNotElementType()
                .Select(s => {
                    var bb = s.get_BoundingBox(view);
                    return new {
                        id = s.Id.Value,
                        cat = s.Category?.Name,
                        name = s.Name,
                        minX = bb != null ? Math.Round(bb.Min.X * FT_TO_MM, 1) : 0,
                        maxX = bb != null ? Math.Round(bb.Max.X * FT_TO_MM, 1) : 0,
                        minY = bb != null ? Math.Round(bb.Min.Y * FT_TO_MM, 1) : 0,
                        maxY = bb != null ? Math.Round(bb.Max.Y * FT_TO_MM, 1) : 0
                    };
                })
                .ToList();

            // Band 1: A to B (Y in [0, 5400])
            var bandAB_doors_windows = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Walls
                }))
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    double midY = (bb.Min.Y + bb.Max.Y) * 0.5 * FT_TO_MM;
                    return midY > 0 && midY < 5400;
                })
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    return new {
                        id = e.Id.Value,
                        cat = e.Category?.Name,
                        name = e.Name,
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        minY = Math.Round(bb.Min.Y * FT_TO_MM, 1),
                        maxY = Math.Round(bb.Max.Y * FT_TO_MM, 1)
                    };
                })
                .OrderBy(x => x.minX)
                .ToList();

            // Band 2: C to D (Y in [7800, 13200])
            var bandCD_doors_windows = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Walls
                }))
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    double midY = (bb.Min.Y + bb.Max.Y) * 0.5 * FT_TO_MM;
                    return midY > 7800 && midY < 13200;
                })
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    return new {
                        id = e.Id.Value,
                        cat = e.Category?.Name,
                        name = e.Name,
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        minY = Math.Round(bb.Min.Y * FT_TO_MM, 1),
                        maxY = Math.Round(bb.Max.Y * FT_TO_MM, 1)
                    };
                })
                .OrderBy(x => x.minX)
                .ToList();

            return new {
                vGrids,
                hGrids,
                stairs,
                bandAB_count = bandAB_doors_windows.Count,
                bandAB = bandAB_doors_windows.Where(x => x.cat != "Walls" || (x.maxX - x.minX) < 1000).ToList(),
                bandCD_count = bandCD_doors_windows.Count,
                bandCD = bandCD_doors_windows.Where(x => x.cat != "Walls" || (x.maxX - x.minX) < 1000).ToList()
            };
        }
    }
}
