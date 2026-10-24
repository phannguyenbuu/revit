using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGach200Layers
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var wt200 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach200_xay moi");

            var cs = wt200?.GetCompoundStructure();
            var layers = cs?.GetLayers().Select(l =>
            {
                var mat = doc.GetElement(l.MaterialId) as Material;
                var fgPat = mat != null && mat.CutForegroundPatternId != ElementId.InvalidElementId ? doc.GetElement(mat.CutForegroundPatternId) as FillPatternElement : null;
                var bgPat = mat != null && mat.CutBackgroundPatternId != ElementId.InvalidElementId ? doc.GetElement(mat.CutBackgroundPatternId) as FillPatternElement : null;
                return new
                {
                    widthMm = l.Width * 304.8,
                    matName = mat?.Name,
                    matId = l.MaterialId.Value,
                    fgPat = fgPat?.Name,
                    fgPatId = mat?.CutForegroundPatternId.Value,
                    bgPat = bgPat?.Name
                };
            }).ToList();

            var coarseParam = wt200?.LookupParameter("Coarse Scale Fill Pattern");
            var coarsePat = coarseParam != null && coarseParam.AsElementId() != ElementId.InvalidElementId
                ? doc.GetElement(coarseParam.AsElementId()) as FillPatternElement : null;

            return new
            {
                wall = wt200?.Name,
                coarsePat = coarsePat?.Name,
                layers = layers
            };
        }
    }
}
