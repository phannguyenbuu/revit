
using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckViewTemplate
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc?.ActiveView;
            if (view == null) return new { error = "No view" };

            var vtId = view.ViewTemplateId;
            var vt = vtId != ElementId.InvalidElementId ? doc.GetElement(vtId) as View : null;

            var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            bool isOverridable = view.IsCategoryOverridable(floorCat.Id);

            return new {
                viewName = view.Name,
                hasTemplate = vtId != ElementId.InvalidElementId,
                templateName = vt?.Name,
                isFloorOverridable = isOverridable
            };
        }
    }
}
