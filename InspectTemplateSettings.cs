
using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTemplateSettings
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc?.ActiveView;
            if (view == null) return new { error = "No view" };

            var vt = doc.GetElement(view.ViewTemplateId) as View;
            if (vt == null) return new { error = "No template" };

            var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            var ovFloor = vt.GetCategoryOverrides(floorCat.Id);

            return new {
                templateName = vt.Name,
                floorHidden = vt.GetCategoryHidden(floorCat.Id),
                floorHalftone = ovFloor.Halftone,
                floorTransparency = ovFloor.Transparency,
                surfacePatVisible = ovFloor.IsSurfaceForegroundPatternVisible,
                surfacePatId = ovFloor.SurfaceForegroundPatternId.Value
            };
        }
    }
}
