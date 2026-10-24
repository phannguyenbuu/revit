using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyFile
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string famPath = Path.Combine(@"D:\Dropbox\_Documents\RevitAI", "Mat_Tien_3dsMax.rfa");
            if (!File.Exists(famPath)) return new { error = "File not found" };

            Document famDoc = null;
            try
            {
                famDoc = app.OpenDocumentFile(famPath);
                var cat = famDoc.OwnerFamily?.FamilyCategory?.Name ?? "NoCat";
                var imports = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(ImportInstance))
                    .Cast<ImportInstance>()
                    .Select(i => new { id = i.Id.Value, pinned = i.Pinned, cat = i.Category?.Name })
                    .ToList();

                var symbols = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(FamilySymbol))
                    .Cast<FamilySymbol>()
                    .Select(s => s.Name)
                    .ToList();

                return new
                {
                    openSuccess = true,
                    title = famDoc.Title,
                    category = cat,
                    importCount = imports.Count,
                    imports,
                    symbols
                };
            }
            catch (Exception ex)
            {
                return new { openSuccess = false, error = ex.Message };
            }
            finally
            {
                famDoc?.Close(false);
            }
        }
    }
}
