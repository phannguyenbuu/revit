using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyFormulas
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2361246L)) as FamilyInstance;
            if (win == null) return new { error = "Window 2361246 not found" };

            var fam = win.Symbol.Family;
            var famDoc = doc.EditFamily(fam);

            var mgr = famDoc.FamilyManager;
            var famParams = new List<object>();

            foreach (FamilyParameter fp in mgr.Parameters)
            {
                famParams.Add(new
                {
                    name = fp.Definition.Name,
                    formula = fp.Formula,
                    isInstance = fp.IsInstance,
                    isReadOnly = fp.IsReadOnly,
                    storage = fp.StorageType.ToString()
                });
            }

            var types = new List<object>();
            foreach (FamilyType ft in mgr.Types)
            {
                var dict = new Dictionary<string, string>();
                foreach (FamilyParameter fp in mgr.Parameters)
                {
                    if (fp.StorageType == StorageType.Double)
                    {
                        var val = ft.AsDouble(fp);
                        if (val.HasValue) dict[fp.Definition.Name] = ToMm(val.Value).ToString("F1");
                    }
                    else if (fp.StorageType == StorageType.String)
                    {
                        dict[fp.Definition.Name] = ft.AsString(fp) ?? "";
                    }
                }
                types.Add(new { typeName = ft.Name, values = dict });
            }

            famDoc.Close(false);

            return new
            {
                familyName = fam.Name,
                parameters = famParams,
                types
            };
        }
    }
}
