using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveSectionDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            var view = uidoc.ActiveView as ViewSection;
            if (view == null) return new { error = "Active view is not a section view" };

            var beamCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralFraming);
            var colCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralColumns);
            var floorCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Floors);
            var wallCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls);

            object GetCatOvr(Category cat)
            {
                if (cat == null) return null;
                var ovr = view.GetCategoryOverrides(cat.Id);
                var cutPat = doc.GetElement(ovr.CutForegroundPatternId) as FillPatternElement;
                return new {
                    cutLineWeight = ovr.CutLineWeight,
                    cutLineColor = ovr.CutLineColor?.IsValid == true ? $"{ovr.CutLineColor.Red},{ovr.CutLineColor.Green},{ovr.CutLineColor.Blue}" : "default",
                    cutLinePattern = doc.GetElement(ovr.CutLinePatternId)?.Name,
                    cutForegroundPattern = cutPat?.Name,
                    cutForegroundPatternColor = ovr.CutForegroundPatternColor?.IsValid == true ? $"{ovr.CutForegroundPatternColor.Red},{ovr.CutForegroundPatternColor.Green},{ovr.CutForegroundPatternColor.Blue}" : "default",
                    cutForegroundPatternVisible = ovr.IsCutForegroundPatternVisible
                };
            }

            return new {
                viewName = view.Name,
                viewId = view.Id.Value,
                beamOvr = GetCatOvr(beamCat),
                colOvr = GetCatOvr(colCat),
                floorOvr = GetCatOvr(floorCat),
                wallOvr = GetCatOvr(wallCat),
                fillPatterns = new FilteredElementCollector(doc)
                    .OfClass(typeof(FillPatternElement))
                    .Cast<FillPatternElement>()
                    .Select(fp => new { id = fp.Id.Value, name = fp.Name, isSolid = fp.GetFillPattern().IsSolidFill })
                    .ToList()
            };
        }
    }
}
