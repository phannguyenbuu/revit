import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

code = """
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSymbolParams
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var sym = doc?.GetElement(new ElementId(2361376L)) as FamilySymbol;
            if (sym == null) return new { error = "Not found" };

            var pars = sym.Parameters.Cast<Parameter>().Select(p => new
            {
                name = p.Definition.Name,
                storageType = p.StorageType.ToString(),
                val = p.AsValueString() ?? (p.StorageType == StorageType.Double ? p.AsDouble().ToString() : p.AsString()),
                isReadOnly = p.IsReadOnly
            }).ToList();

            return new { id = sym.Id.Value, name = sym.Name, parameters = pars };
        }
    }
}
"""
print("Code ready")
