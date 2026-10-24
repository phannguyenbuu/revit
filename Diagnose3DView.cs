using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Diagnose3DView
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var activeView = uidoc.ActiveView;
                var view3D = activeView as View3D;

                bool isSectionBoxActive = false;
                object sectionBox = null;
                if (view3D != null)
                {
                    isSectionBoxActive = view3D.IsSectionBoxActive;
                    if (isSectionBoxActive)
                    {
                        var sb = view3D.GetSectionBox();
                        sectionBox = new
                        {
                            min = new { x = sb.Min.X * FT2M, y = sb.Min.Y * FT2M, z = sb.Min.Z * FT2M },
                            max = new { x = sb.Max.X * FT2M, y = sb.Max.Y * FT2M, z = sb.Max.Z * FT2M }
                        };
                    }
                }

                // Check all open UI Views
                var openUIViews = uidoc.GetOpenUIViews().Select(uv =>
                {
                    var v = doc.GetElement(uv.ViewId) as View;
                    return new
                    {
                        viewId = uv.ViewId.Value,
                        viewName = v?.Name,
                        viewType = v?.ViewType.ToString()
                    };
                }).ToList();

                // Select the 3 windows and 4 walls and isolate them temporarily or refresh
                var k2Windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(w => w.Symbol.FamilyName == "Window_K2")
                    .Select(w => w.Id)
                    .ToList();

                var stackWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var lc = (w.Location as LocationCurve)?.Curve;
                        if (lc == null) return false;
                        double x = lc.GetEndPoint(0).X * FT2M;
                        double y0 = lc.GetEndPoint(0).Y * FT2M;
                        return Math.Abs(x - 0.55) < 0.05 && Math.Abs(y0 - 12.09375) < 0.05;
                    })
                    .Select(w => w.Id)
                    .ToList();

                var allTargetIds = k2Windows.Concat(stackWalls).ToList();

                // If section box is active, make sure it encompasses the elements
                if (view3D != null && isSectionBoxActive)
                {
                    using (Transaction tx = new Transaction(doc, "Expand Section Box for K2"))
                    {
                        tx.Start();
                        view3D.IsSectionBoxActive = false; // Turn off section box so nothing is clipped
                        tx.Commit();
                    }
                }

                // Select in UI
                uidoc.Selection.SetElementIds(allTargetIds);

                // Zoom to elements in open UI views
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == activeView.Id);
                if (uiview != null)
                {
                    // Zoom directly to fit selected elements
                    uiview.ZoomToFit();
                }

                // Force refresh
                uidoc.RefreshActiveView();

                return new
                {
                    success = true,
                    activeViewName = activeView.Name,
                    activeViewType = activeView.ViewType.ToString(),
                    is3D = view3D != null,
                    isSectionBoxActive,
                    sectionBox,
                    openUIViews,
                    selectedElementCount = allTargetIds.Count,
                    selectedIds = allTargetIds.Select(id => id.Value).ToList()
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
