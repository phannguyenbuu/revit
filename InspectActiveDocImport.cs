using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveDocImport
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var importList = new List<object>();
            var imports = new FilteredElementCollector(doc).OfClass(typeof(ImportInstance)).Cast<ImportInstance>().ToList();
            foreach (var imp in imports)
            {
                var type = doc.GetElement(imp.GetTypeId()) as ElementType;
                importList.Add(new
                {
                    id = imp.Id.Value,
                    name = imp.Name,
                    typeName = type?.Name,
                    category = imp.Category?.Name,
                    isLinked = imp.IsLinked
                });
            }

            var subCatList = new List<object>();
            // Search all categories for imported layers
            foreach (Category cat in doc.Settings.Categories)
            {
                if (cat.Name.IndexOf("import", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    cat.Name.IndexOf("dxf", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    cat.Name.IndexOf("dwg", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    cat.SubCategories.Size > 0)
                {
                    var subs = new List<object>();
                    foreach (Category sub in cat.SubCategories)
                    {
                        var mat = sub.Material;
                        subs.Add(new
                        {
                            name = sub.Name,
                            lineColor = sub.LineColor != null ? $"RGB({sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue})" : null,
                            materialId = sub.Material?.Id.Value,
                            materialName = sub.Material?.Name,
                            materialColor = sub.Material?.Color != null ? $"RGB({sub.Material.Color.Red},{sub.Material.Color.Green},{sub.Material.Color.Blue})" : null
                        });
                    }
                    if (subs.Count > 0)
                    {
                        subCatList.Add(new
                        {
                            categoryName = cat.Name,
                            subCategories = subs
                        });
                    }
                }
            }

            return new
            {
                doc = doc.Title,
                isFamily = doc.IsFamilyDocument,
                imports = importList,
                categoriesWithSubs = subCatList
            };
        }
    }
}
