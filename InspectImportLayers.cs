using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectImportLayers
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var importCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_ImportObjectStyles);
            if (importCat == null) return new { error = "OST_ImportObjectStyles not found" };

            var rootSubs = new List<object>();
            foreach (Category sub in importCat.SubCategories)
            {
                var children = new List<object>();
                foreach (Category child in sub.SubCategories)
                {
                    children.Add(new
                    {
                        name = child.Name,
                        id = child.Id.Value,
                        lineColor = child.LineColor != null ? $"RGB({child.LineColor.Red},{child.LineColor.Green},{child.LineColor.Blue})" : null,
                        materialId = child.Material?.Id.Value,
                        materialName = child.Material?.Name,
                        materialColor = child.Material?.Color != null ? $"RGB({child.Material.Color.Red},{child.Material.Color.Green},{child.Material.Color.Blue})" : null
                    });
                }

                rootSubs.Add(new
                {
                    name = sub.Name,
                    id = sub.Id.Value,
                    lineColor = sub.LineColor != null ? $"RGB({sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue})" : null,
                    materialName = sub.Material?.Name,
                    childCount = children.Count,
                    children = children
                });
            }

            return new
            {
                doc = doc.Title,
                importCategory = importCat.Name,
                rootSubCount = rootSubs.Count,
                rootSubs = rootSubs
            };
        }
    }
}
