using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckColumnVisibility
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (view == null) return new { error = "No view" };

            var cat = Category.GetCategory(doc, BuiltInCategory.OST_StructuralColumns);
            bool catHidden = cat != null && view.CanCategoryBeHidden(cat.Id) && view.GetCategoryHidden(cat.Id);

            var template = view.ViewTemplateId != ElementId.InvalidElementId ? doc.GetElement(view.ViewTemplateId) as View : null;
            bool templateCatHidden = template != null && cat != null && template.CanCategoryBeHidden(cat.Id) && template.GetCategoryHidden(cat.Id);

            var colsInView = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .ToElementIds();

            var allCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .ToElementIds();

            return new
            {
                viewName = view.Name,
                templateName = template?.Name,
                categoryHiddenInView = catHidden,
                categoryHiddenInTemplate = templateCatHidden,
                columnsVisibleInView = colsInView.Count,
                totalColumnsInProject = allCols.Count
            };
        }
    }
}
