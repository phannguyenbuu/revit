using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Visual;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestApplyMaterial
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var log = new List<string>();

            Category? importCat = doc.Settings.Categories
                .Cast<Category>()
                .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

            if (importCat == null)
            {
                return new { error = "Imports in Families category not found" };
            }

            log.Add($"Found category: {importCat.Name} with {importCat.SubCategories.Size} subcategories");

            using (var tx = new Transaction(doc, "Test Material Assignment"))
            {
                tx.Start();

                // Find or create test material
                string testMatName = "Lidl Blue";
                Material? mat = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .FirstOrDefault(m => m.Name.Equals(testMatName, StringComparison.OrdinalIgnoreCase));

                if (mat == null)
                {
                    ElementId id = Material.Create(doc, testMatName);
                    mat = doc.GetElement(id) as Material;
                    log.Add($"Created material {testMatName}");
                }

                if (mat != null)
                {
                    mat.Color = new Color(0, 91, 162);
                }

                // Try setting on Layer_BLEED_1060x710_Trang00_11
                Category? subBleed = null;
                foreach (Category sub in importCat.SubCategories)
                {
                    if (sub.Name.Contains("BLEED", StringComparison.OrdinalIgnoreCase))
                    {
                        subBleed = sub;
                        break;
                    }
                }

                if (subBleed != null && mat != null)
                {
                    try
                    {
                        subBleed.Material = mat;
                        subBleed.LineColor = new Color(0, 91, 162);
                        log.Add($"Successfully set subBleed.Material = {mat.Name} and LineColor!");
                    }
                    catch (Exception ex)
                    {
                        log.Add($"Error setting subBleed.Material: {ex.Message}");
                    }
                }
                else
                {
                    log.Add("subBleed or mat is null!");
                }

                tx.Commit();
            }

            return new
            {
                success = true,
                log = log
            };
        }
    }
}
