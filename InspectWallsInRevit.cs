using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWallsInRevit
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w =>
                {
                    var loc = w.Location as LocationCurve;
                    var c = loc?.Curve;
                    return new
                    {
                        id = w.Id.Value,
                        wallType = w.WallType.Name,
                        widthMm = w.WallType.Width * 304.8,
                        level = doc.GetElement(w.LevelId)?.Name,
                        start = c != null ? new { x = c.GetEndPoint(0).X * 0.3048, y = c.GetEndPoint(0).Y * 0.3048, z = c.GetEndPoint(0).Z * 0.3048 } : null,
                        end = c != null ? new { x = c.GetEndPoint(1).X * 0.3048, y = c.GetEndPoint(1).Y * 0.3048, z = c.GetEndPoint(1).Z * 0.3048 } : null,
                        lengthM = c?.Length * 0.3048
                    };
                })
                .ToList();

            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            object? vrInfo = null;
            if (viewTang1 != null)
            {
                var vr = viewTang1.GetViewRange();
                vrInfo = new
                {
                    cutPlaneOffsetM = vr.GetOffset(PlanViewPlane.CutPlane) * 0.3048,
                    topOffsetM = vr.GetOffset(PlanViewPlane.TopClipPlane) * 0.3048,
                    bottomOffsetM = vr.GetOffset(PlanViewPlane.BottomClipPlane) * 0.3048,
                    viewDepthOffsetM = vr.GetOffset(PlanViewPlane.ViewDepthPlane) * 0.3048,
                    isWallsCatHidden = viewTang1.GetCategoryHidden(new ElementId(BuiltInCategory.OST_Walls))
                };
            }

            return new
            {
                totalWalls = walls.Count,
                walls = walls,
                viewRange = vrInfo
            };
        }
    }
}
