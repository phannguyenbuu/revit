import urllib.request, json

code = """
using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBeamParams
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var b = doc.GetElement(new ElementId(2382666L)) as FamilyInstance;
            if (b == null) return new { error = "Beam not found" };

            var paramsList = new List<object>();
            foreach (Parameter p in b.Parameters)
            {
                if (p.Definition.Name.Contains("Offset") || p.Definition.Name.Contains("Elevation") || p.Definition.Name.Contains("Level") || p.Definition.Name.Contains("z ") || p.Definition.Name.Contains("Z "))
                {
                    paramsList.Add(new {
                        name = p.Definition.Name,
                        bip = (p.Definition as InternalDefinition)?.BuiltInParameter.ToString(),
                        storageType = p.StorageType.ToString(),
                        isReadOnly = p.IsReadOnly,
                        val = p.AsValueString() ?? p.AsDouble().ToString()
                    });
                }
            }

            return new { beamId = b.Id.Value, paramsList };
        }
    }
}
"""
print("InspectBeamParams ready")
