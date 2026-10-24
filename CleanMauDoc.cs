using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CleanMauDoc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var deleted = new List<string>();
            using (var tx = new Transaction(doc, "Remove Imported Sign"))
            {
                tx.Start();
                var imports = new FilteredElementCollector(doc)
                    .OfClass(typeof(ImportInstance))
                    .Cast<ImportInstance>()
                    .Where(i => i.Category?.Name == "Imports in Families" || i.Name.Contains("Lidl") || i.Category?.Name == "Imported Objects")
                    .ToList();

                foreach (var imp in imports)
                {
                    if (imp.Name.Contains("Lidl") || imp.GetTypeId().Value == 2375103 || imp.Id.Value == 2375103)
                    {
                        deleted.Add($"{imp.Id.Value} - {imp.Name}");
                        doc.Delete(imp.Id);
                    }
                }
                tx.Commit();
            }

            return new { success = true, deleted };
        }
    }
}
