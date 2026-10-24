using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDetailedPerimeter
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. South Face (Y <= 1500)
            var southDoors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .Cast<FamilyInstance>()
                .Where(f => (f.Location as LocationPoint)?.Point.Y * FT_TO_MM < 2000)
                .Select(f => {
                    var pt = (f.Location as LocationPoint).Point * FT_TO_MM;
                    var bb = f.get_BoundingBox(view);
                    return new {
                        id = f.Id.Value,
                        name = f.Symbol.FamilyName + " : " + f.Symbol.Name,
                        x = Math.Round(pt.X, 1),
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        y = Math.Round(pt.Y, 1)
                    };
                })
                .OrderBy(f => f.x)
                .ToList();

            var southWindows = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .Where(f => (f.Location as LocationPoint)?.Point.Y * FT_TO_MM < 2000)
                .Select(f => {
                    var pt = (f.Location as LocationPoint).Point * FT_TO_MM;
                    var bb = f.get_BoundingBox(view);
                    return new {
                        id = f.Id.Value,
                        name = f.Symbol.FamilyName + " : " + f.Symbol.Name,
                        x = Math.Round(pt.X, 1),
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        y = Math.Round(pt.Y, 1)
                    };
                })
                .OrderBy(f => f.x)
                .ToList();

            // 2. North Face (Y >= 12000)
            var northWindows = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .Where(f => (f.Location as LocationPoint)?.Point.Y * FT_TO_MM > 12000)
                .Select(f => {
                    var pt = (f.Location as LocationPoint).Point * FT_TO_MM;
                    var bb = f.get_BoundingBox(view);
                    return new {
                        id = f.Id.Value,
                        name = f.Symbol.FamilyName + " : " + f.Symbol.Name,
                        x = Math.Round(pt.X, 1),
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        y = Math.Round(pt.Y, 1)
                    };
                })
                .OrderBy(f => f.x)
                .ToList();

            var northDoors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .Cast<FamilyInstance>()
                .Where(f => (f.Location as LocationPoint)?.Point.Y * FT_TO_MM > 12000)
                .Select(f => {
                    var pt = (f.Location as LocationPoint).Point * FT_TO_MM;
                    var bb = f.get_BoundingBox(view);
                    return new {
                        id = f.Id.Value,
                        name = f.Symbol.FamilyName + " : " + f.Symbol.Name,
                        x = Math.Round(pt.X, 1),
                        minX = Math.Round(bb.Min.X * FT_TO_MM, 1),
                        maxX = Math.Round(bb.Max.X * FT_TO_MM, 1),
                        y = Math.Round(pt.Y, 1)
                    };
                })
                .OrderBy(f => f.x)
                .ToList();

            // 3. West Face (X <= 1500)
            var westElements = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_GenericModel
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    return new {
                        id = e.Id.Value,
                        cat = e.Category.Name,
                        name = e.Name,
                        minX = bb != null ? Math.Round(bb.Min.X * FT_TO_MM, 1) : 0,
                        maxX = bb != null ? Math.Round(bb.Max.X * FT_TO_MM, 1) : 0,
                        minY = bb != null ? Math.Round(bb.Min.Y * FT_TO_MM, 1) : 0,
                        maxY = bb != null ? Math.Round(bb.Max.Y * FT_TO_MM, 1) : 0
                    };
                })
                .Where(x => x.minX < 2000)
                .OrderBy(x => x.minY)
                .ToList();

            // 4. East Face (X >= 36000)
            var eastElements = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Floors,
                    BuiltInCategory.OST_Walls
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    return new {
                        id = e.Id.Value,
                        cat = e.Category.Name,
                        name = e.Name,
                        minX = bb != null ? Math.Round(bb.Min.X * FT_TO_MM, 1) : 0,
                        maxX = bb != null ? Math.Round(bb.Max.X * FT_TO_MM, 1) : 0,
                        minY = bb != null ? Math.Round(bb.Min.Y * FT_TO_MM, 1) : 0,
                        maxY = bb != null ? Math.Round(bb.Max.Y * FT_TO_MM, 1) : 0
                    };
                })
                .Where(x => x.maxX > 36500)
                .OrderBy(x => x.minY)
                .ToList();

            return new {
                southDoors,
                southWindows,
                northDoors,
                northWindows,
                westElements,
                eastElements
            };
        }
    }
}
