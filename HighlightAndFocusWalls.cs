using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class HighlightAndFocusWalls
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (viewTang1 != null)
            {
                uidoc.ActiveView = viewTang1;
            }

            var wallIds = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .ToElementIds()
                .ToList();

            if (wallIds.Count > 0)
            {
                uidoc.Selection.SetElementIds(wallIds);
                uidoc.ShowElements(wallIds);
            }

            return new
            {
                success = true,
                selectedWallsCount = wallIds.Count,
                wallIds = wallIds.Select(id => id.Value).ToList()
            };
        }
    }
}
