using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectNenWc
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var ft = doc.GetElement(new ElementId(107061)) as FloorType;
            if (ft == null) return new { error = "ft null" };

            var cs = ft.GetCompoundStructure();
            var layers = cs.GetLayers().Select(l => {
                var mat = doc.GetElement(l.MaterialId) as Material;
                return new {
                    func = l.Function.ToString(),
                    width = l.Width * 304.8,
                    matId = l.MaterialId.Value,
                    matName = mat?.Name,
                    surfPatternId = mat?.SurfaceForegroundPatternId.Value,
                    surfPatternName = (doc.GetElement(mat?.SurfaceForegroundPatternId ?? ElementId.InvalidElementId) as FillPatternElement)?.Name
                };
            }).ToList();

            return new {
                name = ft.Name,
                id = ft.Id.Value,
                layers = layers
            };
        }
    }
}
