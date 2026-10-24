using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExteriorElements
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. Dimension Types
            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                .Select(dt => new { id = dt.Id.Value, name = dt.Name })
                .ToList();

            // 2. Grids
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g => {
                    var c = g.Curve;
                    var p1 = c.GetEndPoint(0) * FT_TO_MM;
                    var p2 = c.GetEndPoint(1) * FT_TO_MM;
                    return new {
                        id = g.Id.Value,
                        name = g.Name,
                        isVertical = Math.Abs(p1.X - p2.X) < 1.0,
                        coord = Math.Abs(p1.X - p2.X) < 1.0 ? Math.Round((p1.X + p2.X) / 2.0, 1) : Math.Round((p1.Y + p2.Y) / 2.0, 1),
                        p1 = new { x = p1.X, y = p1.Y },
                        p2 = new { x = p2.X, y = p2.Y }
                    };
                })
                .OrderBy(g => g.name)
                .ToList();

            // 3. Exterior Walls (BoundingBox or LocationCurve)
            var walls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w => {
                    var bb = w.get_BoundingBox(view);
                    var locCurve = w.Location as LocationCurve;
                    var p1 = locCurve?.Curve.GetEndPoint(0) * FT_TO_MM;
                    var p2 = locCurve?.Curve.GetEndPoint(1) * FT_TO_MM;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        wallType = w.WallType.Name,
                        minX = bb != null ? bb.Min.X * FT_TO_MM : 0,
                        maxX = bb != null ? bb.Max.X * FT_TO_MM : 0,
                        minY = bb != null ? bb.Min.Y * FT_TO_MM : 0,
                        maxY = bb != null ? bb.Max.Y * FT_TO_MM : 0,
                        p1 = p1 != null ? new { x = p1.X, y = p1.Y } : null,
                        p2 = p2 != null ? new { x = p2.X, y = p2.Y } : null
                    };
                })
                .ToList();

            // 4. Doors & Windows on view
            var doors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Select(fi => {
                    var pt = (fi.Location as LocationPoint)?.Point * FT_TO_MM;
                    var bb = fi.get_BoundingBox(view);
                    return new {
                        id = fi.Id.Value,
                        name = fi.Name,
                        symbol = fi.Symbol.Name,
                        pt = pt != null ? new { x = pt.X, y = pt.Y } : null,
                        minX = bb != null ? bb.Min.X * FT_TO_MM : 0,
                        maxX = bb != null ? bb.Max.X * FT_TO_MM : 0,
                        minY = bb != null ? bb.Min.Y * FT_TO_MM : 0,
                        maxY = bb != null ? bb.Max.Y * FT_TO_MM : 0
                    };
                })
                .ToList();

            var windows = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Select(fi => {
                    var pt = (fi.Location as LocationPoint)?.Point * FT_TO_MM;
                    var bb = fi.get_BoundingBox(view);
                    return new {
                        id = fi.Id.Value,
                        name = fi.Name,
                        symbol = fi.Symbol.Name,
                        pt = pt != null ? new { x = pt.X, y = pt.Y } : null,
                        minX = bb != null ? bb.Min.X * FT_TO_MM : 0,
                        maxX = bb != null ? bb.Max.X * FT_TO_MM : 0,
                        minY = bb != null ? bb.Min.Y * FT_TO_MM : 0,
                        maxY = bb != null ? bb.Max.Y * FT_TO_MM : 0
                    };
                })
                .ToList();

            // 5. Entrance / Facade elements (Generic Models, Columns, etc.)
            var facade = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_GenericModel,
                    BuiltInCategory.OST_Columns,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Stairs,
                    BuiltInCategory.OST_Ramps
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    return new {
                        id = e.Id.Value,
                        cat = e.Category?.Name,
                        name = e.Name,
                        minX = bb != null ? bb.Min.X * FT_TO_MM : 0,
                        maxX = bb != null ? bb.Max.X * FT_TO_MM : 0,
                        minY = bb != null ? bb.Min.Y * FT_TO_MM : 0,
                        maxY = bb != null ? bb.Max.Y * FT_TO_MM : 0
                    };
                })
                .ToList();

            return new {
                viewScale = view.Scale,
                dimTypes,
                grids,
                totalWalls = walls.Count,
                doors,
                windows,
                facade
            };
        }
    }
}
