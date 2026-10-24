using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindDimTypeBuiltInParams
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var dt = doc.GetElement(new ElementId(277L)) as DimensionType;
            if (dt == null) return new { error = "No dt" };

            var found = new List<object>();
            foreach (BuiltInParameter bip in Enum.GetValues(typeof(BuiltInParameter)))
            {
                try
                {
                    var p = dt.get_Parameter(bip);
                    if (p != null)
                    {
                        found.Add(new {
                            bip = bip.ToString(),
                            name = p.Definition?.Name,
                            val = p.AsValueString() ?? (p.StorageType == StorageType.Integer ? p.AsInteger().ToString() : p.AsString())
                        });
                    }
                }
                catch { }
            }

            return new { count = found.Count, found };
        }
    }
}
