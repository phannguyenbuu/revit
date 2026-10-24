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
                    var cutPat = mat != null ? doc.GetElement(mat.CutPatternId) as FillPatternElement : null;
                    var surfPat = mat != null ? doc.GetElement(mat.SurfacePatternId) as FillPatternElement : null;
                    return new
                    {
                        function = l.Function.ToString(),
                        widthMm = l.Width * 304.8,
                        materialName = mat?.Name,
                        materialId = l.MaterialId.Value,
                        cutPatternName = cutPat?.Name,
                        surfacePatternName = surfPat?.Name
                    };
                }).ToList();

                var coarsePat = doc.GetElement(wt.get_Parameter(BuiltInParameter.COARSE_SCALE_FILL_PATTERN)?.AsElementId() ?? ElementId.InvalidElementId) as FillPatternElement;

                return new
                {
                    id = wt.Id.Value,
                    name = wt.Name,
                    coarsePattern = coarsePat?.Name,
                    layers = layers
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

            return new
            {
                wall100Types = wallInfo,
                matchedFillPatterns = fillPatterns
            };
        }
    }
}
'''

with open("InspectHatchAndWall100.cs", "w", encoding="utf-8") as f:
    f.write(code)
print("Wrote InspectHatchAndWall100.cs")
