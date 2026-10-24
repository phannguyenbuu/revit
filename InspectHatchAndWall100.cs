using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectHatchAndWall100
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Inspect WallType gach100_xay moi
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .Where(w => w.Name.Contains("100"))
                .ToList();

            var wallInfo = wallTypes.Select(wt =>
            {
                var cs = wt.GetCompoundStructure();
                var layers = cs?.GetLayers().Select(l =>
                {
                    var mat = doc.GetElement(l.MaterialId) as Material;
                    var cutFg = mat != null && mat.CutForegroundPatternId != ElementId.InvalidElementId 
                        ? doc.GetElement(mat.CutForegroundPatternId) as FillPatternElement : null;
                    var cutBg = mat != null && mat.CutBackgroundPatternId != ElementId.InvalidElementId 
                        ? doc.GetElement(mat.CutBackgroundPatternId) as FillPatternElement : null;
                    return new
                    {
                        function = l.Function.ToString(),
                        widthMm = l.Width * 304.8,
                        materialName = mat?.Name,
                        materialId = l.MaterialId.Value,
                        cutFgPattern = cutFg?.Name,
                        cutBgPattern = cutBg?.Name
                    };
                }).ToList();

                var pars = wt.Parameters.Cast<Parameter>()
                    .Where(p => p.Definition.Name.Contains("Pattern", StringComparison.OrdinalIgnoreCase)
                             || p.Definition.Name.Contains("Hatch", StringComparison.OrdinalIgnoreCase)
                             || p.Definition.Name.Contains("Coarse", StringComparison.OrdinalIgnoreCase))
                    .Select(p => new { name = p.Definition.Name, val = p.AsValueString() ?? p.AsString() })
                    .ToList();

                return new
                {
                    id = wt.Id.Value,
                    name = wt.Name,
                    layers = layers,
                    patternParams = pars
                };
            }).ToList();

            // 2. Find all FillPatternElements with "ANSI" or "31" or "Diagonal"
            var fillPatterns = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .Select(fp => new
                {
                    id = fp.Id.Value,
                    name = fp.Name,
                    target = fp.GetFillPattern()?.Target.ToString()
                })
                .Where(fp => fp.name.Contains("ANSI", StringComparison.OrdinalIgnoreCase)
                          || fp.name.Contains("31", StringComparison.OrdinalIgnoreCase)
                          || fp.name.Contains("Diag", StringComparison.OrdinalIgnoreCase)
                          || fp.name.Contains("Gạch", StringComparison.OrdinalIgnoreCase))
                .ToList();

            // Also inspect gach200_xay moi to see what pattern it uses!
            var wt200 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach200_xay moi");

            var cs200 = wt200?.GetCompoundStructure();
            var l200 = cs200?.GetLayers().FirstOrDefault();
            var mat200 = l200 != null ? doc.GetElement(l200.MaterialId) as Material : null;
            var cutFg200 = mat200 != null && mat200.CutForegroundPatternId != ElementId.InvalidElementId 
                ? doc.GetElement(mat200.CutForegroundPatternId) as FillPatternElement : null;

            return new
            {
                wall100Types = wallInfo,
                gach200Info = new
                {
                    wallName = wt200?.Name,
                    materialName = mat200?.Name,
                    cutFgPattern = cutFg200?.Name,
                    cutFgPatternId = cutFg200?.Id.Value
                },
                matchedFillPatterns = fillPatterns
            };
        }
    }
}
