using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpColumnParameters
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var col = doc?.GetElement(new ElementId(2363711L)) as FamilyInstance;
            if (col == null) return new { error = "Not found" };

            var pars = col.Parameters.Cast<Parameter>().Select(p => new
            {
                name = p.Definition.Name,
                storageType = p.StorageType.ToString(),
                val = p.AsValueString() ?? (p.StorageType == StorageType.Double ? p.AsDouble().ToString() : (p.StorageType == StorageType.ElementId ? p.AsElementId().Value.ToString() : (p.StorageType == StorageType.String ? p.AsString() : p.AsInteger().ToString()))),
                isReadOnly = p.IsReadOnly
            }).ToList();

            return new
            {
                id = col.Id.Value,
                name = col.Name,
                parameters = pars
            };
        }
    }
}
