using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpColAndWallParams
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var col = doc.GetElement(new ElementId(2378215));
            var wall = doc.GetElement(new ElementId(2361540));

            var colParams = col.Parameters.Cast<Parameter>()
                .Where(p => p.Definition.Name.Contains("Level") || p.Definition.Name.Contains("Offset") || p.Definition.Name.Contains("Height") || p.Definition.Name.Contains("Top") || p.Definition.Name.Contains("Base"))
                .Select(p => new
                {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString(),
                    elemId = p.StorageType == StorageType.ElementId ? p.AsElementId().Value.ToString() : null,
                    bip = p.Definition is InternalDefinition id ? id.BuiltInParameter.ToString() : ""
                })
                .ToList();

            var wallParams = wall.Parameters.Cast<Parameter>()
                .Where(p => p.Definition.Name.Contains("Level") || p.Definition.Name.Contains("Offset") || p.Definition.Name.Contains("Height") || p.Definition.Name.Contains("Top") || p.Definition.Name.Contains("Base") || p.Definition.Name.Contains("Constraint"))
                .Select(p => new
                {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString(),
                    elemId = p.StorageType == StorageType.ElementId ? p.AsElementId().Value.ToString() : null,
                    bip = p.Definition is InternalDefinition id ? id.BuiltInParameter.ToString() : ""
                })
                .ToList();

            return new { colParams, wallParams };
        }
    }
}
