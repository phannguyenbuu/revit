using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Inspect3DView
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var view3D = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("Coordination") || v.ViewType == ViewType.ThreeD));

            if (view3D == null) return new { error = "No 3D view found" };

            var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
            bool catHidden = gridCat != null && view3D.CanCategoryBeHidden(gridCat.Id) && view3D.GetCategoryHidden(gridCat.Id);

            var levelsShowingGrids = view3D.GetLevelsThatShowGrids().Select(id => id.Value).ToList();

            bool sectionBoxActive = view3D.IsSectionBoxActive;
            var sb = sectionBoxActive ? view3D.GetSectionBox() : null;

            return new
            {
                viewId = view3D.Id.Value,
                viewName = view3D.Name,
                categoryHidden = catHidden,
                sectionBoxActive = sectionBoxActive,
                sectionBoxMin = sb != null ? new double[] { sb.Min.X * 0.3048, sb.Min.Y * 0.3048, sb.Min.Z * 0.3048 } : null,
                sectionBoxMax = sb != null ? new double[] { sb.Max.X * 0.3048, sb.Max.Y * 0.3048, sb.Max.Z * 0.3048 } : null,
                levelsShowingGridsCount = levelsShowingGrids.Count,
                levelsShowingGrids = levelsShowingGrids
            };
        }
    }
}
