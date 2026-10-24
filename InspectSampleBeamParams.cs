using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSampleBeamParams
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beam = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            if (beam == null) return new { error = "No beam" };

            var pars = new List<object>();
            foreach (Parameter p in beam.Parameters)
            {
                if (p.Definition == null) continue;
                string name = p.Definition.Name;
                if (name.Contains("Offset") || name.Contains("Elevation") || name.Contains("Level") || name.Contains("Justification") || name.Contains("Z"))
                {
                    string valStr = p.AsValueString();
                    string rawVal = "";
                    if (p.StorageType == StorageType.Double) rawVal = (p.AsDouble() * FT2MM).ToString("F1") + " mm";
                    else if (p.StorageType == StorageType.Integer) rawVal = p.AsInteger().ToString();
                    else if (p.StorageType == StorageType.String) rawVal = p.AsString();
                    else if (p.StorageType == StorageType.ElementId) rawVal = p.AsElementId().Value.ToString();

                    pars.Add(new {
                        name,
                        readOnly = p.IsReadOnly,
                        valStr,
                        rawVal
                    });
                }
            }

            return new {
                id = beam.Id.Value,
                name = beam.Name,
                sym = beam.Symbol.Name,
                pars
            };
        }
    }
}
