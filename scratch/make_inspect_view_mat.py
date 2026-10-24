import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

code = '''
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveViewAndWall100Mat
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No doc or view" };

            // Check view detail level and discipline
            var detailLevel = view.DetailLevel.ToString();
            var displayModel = view.DisplayStyle.ToString();

            // Check wall category override in this view
            var wallCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls);
            var overrides = view.GetCategoryOverrides(wallCat.Id);
            var cutFgPat = doc.GetElement(overrides.CutForegroundPatternId) as FillPatternElement;

            // Check gach100_xay moi material
            var wt100 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach100_xay moi");

            var cs = wt100?.GetCompoundStructure();
            var layer0 = cs?.GetLayers().FirstOrDefault();
            var mat = layer0 != null ? doc.GetElement(layer0.MaterialId) as Material : null;

            var matCutFg = mat != null && mat.CutForegroundPatternId != ElementId.InvalidElementId
                ? doc.GetElement(mat.CutForegroundPatternId) as FillPatternElement : null;

            var wtCoarsePat = wt100 != null
                ? doc.GetElement(wt100.get_Parameter(BuiltInParameter.COARSE_SCALE_FILL_PATTERN_ID)?.AsElementId() ?? ElementId.InvalidElementId) as FillPatternElement : null;

            return new
            {
                viewName = view.Name,
                detailLevel = detailLevel,
                displayStyle = displayModel,
                wallCategoryOverrideCutPattern = cutFgPat?.Name,
                wallType100 = new
                {
                    name = wt100?.Name,
                    materialName = mat?.Name,
                    materialCutFgPattern = matCutFg?.Name,
                    materialCutFgPatternId = matCutFg?.Id.Value,
                    coarseScalePattern = wtCoarsePat?.Name,
                    coarseScalePatternId = wtCoarsePat?.Id.Value
                }
            };
        }
    }
}
'''

with open("InspectActiveViewAndWall100Mat.cs", "w", encoding="utf-8") as f:
    f.write(code)
print("Wrote InspectActiveViewAndWall100Mat.cs")
