using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckAndFocusK2InRevit
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                var activeView = uidoc.ActiveView;

                // Find the 3 K2 windows
                var k2Windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(w => w.Symbol.FamilyName == "Window_K2")
                    .ToList();

                // Find the stacked walls
                var stackWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var lc = (w.Location as LocationCurve)?.Curve;
                        if (lc == null) return false;
                        double x = lc.GetEndPoint(0).X * FT2M;
                        double y0 = lc.GetEndPoint(0).Y * FT2M;
                        double y1 = lc.GetEndPoint(1).Y * FT2M;
                        return Math.Abs(x - 0.55) < 0.05 && Math.Abs(Math.Min(y0, y1) - 12.09375) < 0.05;
                    })
                    .ToList();

                var allTargetIds = k2Windows.Select(w => w.Id).Concat(stackWalls.Select(w => w.Id)).ToList();

                // Check visibility in active view
                bool winCatHidden = activeView.GetCategoryHidden(new ElementId(BuiltInCategory.OST_Windows));
                bool wallCatHidden = activeView.GetCategoryHidden(new ElementId(BuiltInCategory.OST_Walls));

                var winDetails = k2Windows.Select(w =>
                {
                    var bb = w.get_BoundingBox(activeView);
                    var loc = (w.Location as LocationPoint)?.Point;
                    return new
                    {
                        id = w.Id.Value,
                        name = w.Name,
                        isHidden = w.IsHidden(activeView),
                        locM = loc != null ? new { x = loc.X * FT2M, y = loc.Y * FT2M, z = loc.Z * FT2M } : null,
                        hasBB = bb != null
                    };
                }).ToList();

                var wallDetails = stackWalls.Select(w =>
                {
                    var bb = w.get_BoundingBox(activeView);
                    return new
                    {
                        id = w.Id.Value,
                        name = w.Name,
                        isHidden = w.IsHidden(activeView),
                        hasBB = bb != null
                    };
                }).ToList();

                // Select them in Revit UI!
                if (allTargetIds.Count > 0)
                {
                    uidoc.Selection.SetElementIds(allTargetIds);

                    // Zoom UI view to these elements
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == activeView.Id);
                    if (uiview != null)
                    {
                        // Bounding box around the stack: X[0.0, 1.5], Y[11.5, 13.5], Z[0, 12]
                        XYZ pMin = new XYZ(-2.0 * M2FT, 10.0 * M2FT, -1.0 * M2FT);
                        XYZ pMax = new XYZ(3.0 * M2FT, 14.5 * M2FT, 13.0 * M2FT);
                        uiview.ZoomAndCenterRectangle(pMin, pMax);
                    }
                }

                return new
                {
                    success = true,
                    activeViewName = activeView.Name,
                    activeViewType = activeView.ViewType.ToString(),
                    winCatHidden,
                    wallCatHidden,
                    selectedCount = allTargetIds.Count,
                    windows = winDetails,
                    walls = wallDetails
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
