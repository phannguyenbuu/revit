using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetBottomGridOnly
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var view = uidoc.ActiveView as View3D;
            if (view == null) return new { error = "Active view is not 3D" };

            // Find all levels, ordered by elevation
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            // The user requested: "giữ cái dưới cùng thôi nha" (keep the bottom-most one only)
            // Let's find the bottom-most level (lowest elevation)
            // In the building: HẦM 3 is the lowest level (lowest elevation), OR HẦM 1, OR TẦNG TRỆT.
            // Let's inspect the lowest level and levels around ground
            var lowestLevel = levels.FirstOrDefault(); // Lowest elevation level (HẦM 3 or similar)
            
            // Check view template
            var templateId = view.ViewTemplateId;
            View3D? template = null;
            if (templateId != ElementId.InvalidElementId)
            {
                template = doc.GetElement(templateId) as View3D;
            }

            var logs = new List<string>();

            using (var tx = new Transaction(doc, "Keep Bottom Grid Only in 3D"))
            {
                tx.Start();

                var singleLevelSet = new HashSet<ElementId>();
                if (lowestLevel != null)
                {
                    singleLevelSet.Add(lowestLevel.Id);
                }

                // Try setting on view directly
                try
                {
                    view.ShowGridsOnLevels(singleLevelSet);
                    logs.Add($"Direct view.ShowGridsOnLevels({lowestLevel?.Name}) succeeded");
                }
                catch (Exception ex)
                {
                    logs.Add($"Direct view error: {ex.Message}");
                }

                // If view has template, check if template controls ShowGrids or if we can set it on template or remove parameter control
                if (template != null)
                {
                    try
                    {
                        template.ShowGridsOnLevels(singleLevelSet);
                        logs.Add($"Template {template.Name}.ShowGridsOnLevels succeeded");
                    }
                    catch (Exception ex)
                    {
                        logs.Add($"Template error: {ex.Message}");
                    }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                viewName = view.Name,
                viewTemplate = template?.Name ?? "None",
                lowestLevelName = lowestLevel?.Name,
                lowestLevelElevationMeters = (lowestLevel?.Elevation ?? 0) * 0.3048,
                levelsShowingGrids = view.GetLevelsThatShowGrids().Select(id => id.Value).ToList(),
                logs = logs
            };
        }
    }
}
