using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTang2ViewSettings
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            long vIdVal = 931687L;
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("viewId", out var vProp))
                vIdVal = vProp.GetInt64();
            ViewPlan plan = doc.GetElement(new ElementId(vIdVal)) as ViewPlan;
            if (plan == null) return new { error = $"View {vIdVal} not found" };

            var vr = plan.GetViewRange();
            var cutLevel = vr.GetLevelId(PlanViewPlane.CutPlane);
            var cutOffset = vr.GetOffset(PlanViewPlane.CutPlane);
            var topLevel = vr.GetLevelId(PlanViewPlane.TopClipPlane);
            var topOffset = vr.GetOffset(PlanViewPlane.TopClipPlane);
            var botLevel = vr.GetLevelId(PlanViewPlane.BottomClipPlane);
            var botOffset = vr.GetOffset(PlanViewPlane.BottomClipPlane);

            var wallCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls);
            var doorCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Doors);
            var winCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows);
            var textCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_TextNotes);

            bool wallsHidden = plan.GetCategoryHidden(wallCat.Id);
            bool doorsHidden = plan.GetCategoryHidden(doorCat.Id);
            bool winsHidden = plan.GetCategoryHidden(winCat.Id);
            bool textsHidden = plan.GetCategoryHidden(textCat.Id);

            var collector = new FilteredElementCollector(doc, plan.Id)
                .WhereElementIsNotElementType()
                .ToElementIds();

            var cropBox = plan.CropBox;

            return new {
                viewName = plan.Name,
                isTemplate = plan.IsTemplate,
                cropActive = plan.CropBoxActive,
                cropVisible = plan.CropBoxVisible,
                cutLevel = cutLevel.Value,
                cutOffset = cutOffset * 304.8,
                topLevel = topLevel.Value,
                topOffset = topOffset * 304.8,
                botLevel = botLevel.Value,
                botOffset = botOffset * 304.8,
                wallsHidden,
                doorsHidden,
                winsHidden,
                textsHidden,
                cropMin = cropBox != null ? new { x = cropBox.Min.X * 0.3048, y = cropBox.Min.Y * 0.3048, z = cropBox.Min.Z * 0.3048 } : null,
                cropMax = cropBox != null ? new { x = cropBox.Max.X * 0.3048, y = cropBox.Max.Y * 0.3048, z = cropBox.Max.Z * 0.3048 } : null,
                elementsInViewCount = collector.Count
            };
        }
    }
}
