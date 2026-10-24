using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorPlanVisibility
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var plans = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                .ToList();

            var colCat = Category.GetCategory(doc, BuiltInCategory.OST_StructuralColumns);
            var colCatId = colCat.Id;

            var results = new List<object>();

            foreach (var plan in plans)
            {
                var template = plan.ViewTemplateId != ElementId.InvalidElementId 
                    ? doc.GetElement(plan.ViewTemplateId) as View 
                    : null;

                bool isColHiddenInView = plan.CanCategoryBeHidden(colCatId) && plan.GetCategoryHidden(colCatId);
                bool isColHiddenInTemplate = template != null && template.CanCategoryBeHidden(colCatId) && template.GetCategoryHidden(colCatId);

                // Check view range
                string cutPlaneInfo = "N/A";
                try
                {
                    var vr = plan.GetViewRange();
                    var cutOffset = vr.GetOffset(PlanViewPlane.CutPlane);
                    var bottomOffset = vr.GetOffset(PlanViewPlane.BottomClipPlane);
                    var topOffset = vr.GetOffset(PlanViewPlane.TopClipPlane);
                    var depthOffset = vr.GetOffset(PlanViewPlane.ViewDepthPlane);
                    cutPlaneInfo = $"Top:{topOffset * 304.8:F0}mm, Cut:{cutOffset * 304.8:F0}mm, Bottom:{bottomOffset * 304.8:F0}mm, Depth:{depthOffset * 304.8:F0}mm";
                }
                catch (Exception ex)
                {
                    cutPlaneInfo = ex.Message;
                }

                // Check elements in view
                var colsInView = new FilteredElementCollector(doc, plan.Id)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    .GetElementCount();

                var cropActive = plan.CropBoxActive;
                var cropVisible = plan.CropBoxVisible;

                results.Add(new
                {
                    id = plan.Id.Value,
                    name = plan.Name,
                    discipline = plan.Discipline.ToString(),
                    templateName = template?.Name ?? "None",
                    categoryHiddenInView = isColHiddenInView,
                    categoryHiddenInTemplate = isColHiddenInTemplate,
                    cropActive = cropActive,
                    viewRange = cutPlaneInfo,
                    columnsCountInView = colsInView
                });
            }

            return new
            {
                totalFloorPlans = plans.Count,
                plans = results
            };
        }
    }
}
