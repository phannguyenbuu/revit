using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBandFeatures
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. Elements between A and B (Y in 0..5400)
            var abElements = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Stairs
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return null;
                    double minY = bb.Min.Y * FT_TO_MM;
                    double maxY = bb.Max.Y * FT_TO_MM;
                    // Intersect with band Y in [0, 5400]
                    if (maxY < 50 || minY > 5350) return null;

                    return new {
                        id = e.Id.Value,
                        cat = e.Category.Name,
                        name = e.Name,
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        minY = Math.Round(minY, 1),
                        maxY = Math.Round(maxY, 1)
                    };
                })
                .Where(x => x != null)
                .OrderBy(x => x.minX)
                .ToList();

            // 2. Elements between C and D (Y in 7800..13200)
            var cdElements = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Stairs,
                    BuiltInCategory.OST_StairsRuns,
                    BuiltInCategory.OST_StairsLandings
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return null;
                    double minY = bb.Min.Y * FT_TO_MM;
                    double maxY = bb.Max.Y * FT_TO_MM;
                    // Intersect with band Y in [7800, 13200]
                    if (maxY < 7850 || minY > 13150) return null;

                    return new {
                        id = e.Id.Value,
                        cat = e.Category.Name,
                        name = e.Name,
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        minY = Math.Round(minY, 1),
                        maxY = Math.Round(maxY, 1)
                    };
                })
                .Where(x => x != null)
                .OrderBy(x => x.minX)
                .ToList();

            return new {
                abCount = abElements.Count,
                abDoorsWindows = abElements.Where(x => x.cat == "Doors" || x.cat == "Windows").ToList(),
                abWalls = abElements.Where(x => x.cat == "Walls" && (x.maxX - x.minX) <= 600).ToList(),
                cdCount = cdElements.Count,
                cdDoorsWindows = cdElements.Where(x => x.cat == "Doors" || x.cat == "Windows").ToList(),
                cdStairs = cdElements.Where(x => x.cat.Contains("Stair")).ToList(),
                cdWalls = cdElements.Where(x => x.cat == "Walls" && (x.maxX - x.minX) <= 600).ToList()
            };
        }
    }
}
