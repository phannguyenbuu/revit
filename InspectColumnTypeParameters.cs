
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectColumnTypeParameters
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var syms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Where(s => s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase))
                .ToList();

            var result = syms.Select(s => new
            {
                id = s.Id.Value,
                name = s.Name,
                family = s.FamilyName,
                parameters = s.Parameters.Cast<Parameter>().Select(p => new
                {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? (p.StorageType == StorageType.Double ? p.AsDouble().ToString() : p.AsString()),
                    isReadOnly = p.IsReadOnly
                }).Where(p => p.val != null).ToList()
            }).ToList();

            return result;
        }
    }
}
