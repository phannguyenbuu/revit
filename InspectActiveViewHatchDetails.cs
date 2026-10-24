using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveViewHatchDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView;
                if (doc == null) return new { error = "No doc" };
                if (view == null) return new { error = "No view" };

                var wt100 = new FilteredElementCollector(doc)
                    .OfClass(typeof(WallType))
                    .Cast<WallType>()
                    .FirstOrDefault(w => w.Name == "gach100_xay moi");

                var cs = wt100?.GetCompoundStructure();
                var layers = cs?.GetLayers().Select(l =>
                {
                    var mat = doc.GetElement(l.MaterialId) as Material;
                    var fgPat = mat != null && mat.CutForegroundPatternId != ElementId.InvalidElementId ? doc.GetElement(mat.CutForegroundPatternId) as FillPatternElement : null;
                    var bgPat = mat != null && mat.CutBackgroundPatternId != ElementId.InvalidElementId ? doc.GetElement(mat.CutBackgroundPatternId) as FillPatternElement : null;
                    return new
                    {
                        widthMm = l.Width * 304.8,
                        matName = mat?.Name,
                        fgPat = fgPat?.Name,
                        fgColor = mat != null ? $"{mat.CutForegroundPatternColor.Red},{mat.CutForegroundPatternColor.Green},{mat.CutForegroundPatternColor.Blue}" : null,
                        bgPat = bgPat?.Name
                    };
                }).ToList();

                var coarseParam = wt100?.LookupParameter("Coarse Scale Fill Pattern");
                var coarsePat = coarseParam != null && coarseParam.AsElementId() != ElementId.InvalidElementId
                    ? doc.GetElement(coarseParam.AsElementId()) as FillPatternElement : null;

                return new
                {
                    viewName = view.Name,
                    viewType = view.ViewType.ToString(),
                    scale = view.Scale,
                    detailLevel = view.DetailLevel.ToString(),
                    displayStyle = view.DisplayStyle.ToString(),
                    coarsePatternOnWallType = coarsePat?.Name,
                    layers = layers
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
