using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCadLinkIn3D
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var importInst = doc.GetElement(new ElementId(2567055)) as ImportInstance;
            if (importInst == null)
            {
                // Find any import instance
                importInst = new FilteredElementCollector(doc)
                    .OfClass(typeof(ImportInstance))
                    .Cast<ImportInstance>()
                    .FirstOrDefault();
            }

            if (importInst == null) return new { error = "No ImportInstance found in project" };

            var view3D = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name == "3D Coordination");

            if (view3D == null) return new { error = "3D Coordination not found" };

            var cat = importInst.Category;
            bool catHiddenIn3D = cat != null && view3D.CanCategoryBeHidden(cat.Id) && view3D.GetCategoryHidden(cat.Id);

            var template = view3D.ViewTemplateId != ElementId.InvalidElementId 
                ? doc.GetElement(view3D.ViewTemplateId) as View 
                : null;

            bool catHiddenInTemplate = template != null && cat != null && template.CanCategoryBeHidden(cat.Id) && template.GetCategoryHidden(cat.Id);

            return new
            {
                importId = importInst.Id.Value,
                isViewSpecific = importInst.ViewSpecific,
                ownerViewId = importInst.OwnerViewId.Value,
                ownerViewName = importInst.OwnerViewId != ElementId.InvalidElementId ? doc.GetElement(importInst.OwnerViewId)?.Name : "None",
                categoryName = cat?.Name,
                categoryId = cat?.Id.Value,
                view3DName = view3D.Name,
                templateName = template?.Name ?? "None",
                catHiddenIn3D = catHiddenIn3D,
                catHiddenInTemplate = catHiddenInTemplate,
                sectionBoxActive = view3D.IsSectionBoxActive,
                discipline = view3D.Discipline.ToString()
            };
        }
    }
}
