import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect column family parameters
query_code = """
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectColFamilyParams
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var colSyms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => {
                    var pars = new Dictionary<string, string>();
                    foreach (Parameter p in s.Parameters)
                    {
                        if (p.HasValue && !string.IsNullOrEmpty(p.Definition.Name))
                        {
                            pars[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString();
                        }
                    }
                    return new {
                        id = s.Id.Value,
                        name = s.Name,
                        family = s.FamilyName,
                        pars
                    };
                })
                .ToList();

            return new { colSyms };
        }
    }
}
"""

with open(r'D:\Dropbox\_Documents\RevitAI\InspectColFamilyParams.cs', 'w', encoding='utf-8') as f:
    f.write(query_code)
print("Wrote InspectColFamilyParams.cs")
