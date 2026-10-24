using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTang3ViewDetails
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

            ViewPlan planTang3 = doc.GetElement(new ElementId(1727632L)) as ViewPlan;
            if (planTang3 == null) return new { error = "View 1727632 not found" };

            // 1. Check categories hidden in View 1727632
            var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
            bool gridsHidden = gridCat != null && planTang3.GetCategoryHidden(gridCat.Id);

            var stairCat = Category.GetCategory(doc, BuiltInCategory.OST_Stairs);
            bool stairsHidden = stairCat != null && planTang3.GetCategoryHidden(stairCat.Id);

            // 2. Check all Grids in document and their 3D extents
            var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().ToList();
            var gridInfo = grids.Select(g => new
            {
                id = g.Id.Value,
                name = g.Name,
                canBeHidden = g.CanBeHidden(planTang3)
            }).Take(5).ToList();

            // 3. Check all Stairs in doc
            var stairs = new FilteredElementCollector(doc).OfClass(typeof(Stairs)).Cast<Stairs>().ToList();
            var stairInfo = stairs.Select(s => new
            {
                id = s.Id.Value,
                baseLevel = s.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL)?.AsValueString(),
                topLevel = s.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL)?.AsValueString()
            }).ToList();

            // 4. Find elements near 3/12 marker (X ~ 1m, Y < 0m or Y in [0, 2])
            var elementsNearMarker = new FilteredElementCollector(doc, planTang3.Id)
                .WhereElementIsNotElementType()
                .Where(e =>
                {
                    var bb = e.get_BoundingBox(planTang3);
                    if (bb == null) return false;
                    return bb.Min.Y < 0.0 || (bb.Min.X < 5 * M2FT && bb.Min.Y < 5 * M2FT && e.Category?.BuiltInCategory == BuiltInCategory.OST_Elev);
                })
                .Select(e => new
                {
                    id = e.Id.Value,
                    name = e.Name,
                    cat = e.Category?.Name,
                    catId = e.Category?.BuiltInCategory.ToString(),
                    canBeHidden = e.CanBeHidden(planTang3),
                    isAlreadyHidden = e.IsHidden(planTang3)
                }).ToList();

            // Also check all Elevation markers or Section markers in doc
            var elevMarkers = new FilteredElementCollector(doc).OfClass(typeof(ElevationMarker)).Cast<ElevationMarker>().Select(em => new
            {
                id = em.Id.Value,
                isMarkerHidden = em.IsHidden(planTang3)
            }).ToList();

            return new
            {
                viewName = planTang3.Name,
                gridsHidden,
                stairsHidden,
                totalGrids = grids.Count,
                sampleGrids = gridInfo,
                stairInfo,
                elevMarkers,
                elementsNearMarker
            };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
