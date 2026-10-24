using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSanhColors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Inspect Wall Category and Wall Materials
            var wallCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls);
            var wallMat = wallCat?.Material;
            var wallLineColor = wallCat?.LineColor;

            // Sample a wall in the project
            var sampleWall = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .FirstOrDefault();
            
            string wallTypeName = sampleWall?.WallType?.Name;
            var wallMatIds = sampleWall?.GetMaterialIds(false);
            List<string> wallMatNames = new List<string>();
            List<object> wallMatColors = new List<object>();
            if (wallMatIds != null)
            {
                foreach (var mid in wallMatIds)
                {
                    var m = doc.GetElement(mid) as Material;
                    if (m != null)
                    {
                        wallMatNames.Add(m.Name);
                        wallMatColors.Add(new { name = m.Name, color = $"{m.Color.Red},{m.Color.Green},{m.Color.Blue}", transparency = m.Transparency });
                    }
                }
            }

            // 2. Inspect Sanh Instance
            var inst = doc.GetElement(new ElementId(2385103)) as FamilyInstance;
            var fam = inst?.Symbol?.Family;

            // Inspect Imported Objects categories in project doc
            var importCat = doc.Settings.Categories.Cast<Category>()
                .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase) 
                                  || c.Name.Equals("Imported Objects", StringComparison.OrdinalIgnoreCase));
            
            List<object> subCatList = new List<object>();
            if (importCat != null)
            {
                foreach (Category sub in importCat.SubCategories)
                {
                    subCatList.Add(new {
                        name = sub.Name,
                        lineColor = sub.LineColor != null ? $"{sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue}" : "null",
                        material = sub.Material?.Name,
                        materialColor = sub.Material != null ? $"{sub.Material.Color.Red},{sub.Material.Color.Green},{sub.Material.Color.Blue}" : "null"
                    });
                }
            }

            // Also check Generic Models subcategories
            var genCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
            List<object> genSubCats = new List<object>();
            if (genCat != null)
            {
                foreach (Category sub in genCat.SubCategories)
                {
                    genSubCats.Add(new {
                        name = sub.Name,
                        material = sub.Material?.Name,
                        lineColor = sub.LineColor != null ? $"{sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue}" : "null"
                    });
                }
            }

            // 3. Inspect materials inside Sanh_Chinh_3dsMax.rfa
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa";
            List<object> famSubCats = new List<object>();
            List<object> famMats = new List<object>();
            if (File.Exists(famPath))
            {
                var famDoc = uiapp.Application.OpenDocumentFile(famPath);
                if (famDoc != null)
                {
                    foreach (var m in new FilteredElementCollector(famDoc).OfClass(typeof(Material)).Cast<Material>())
                    {
                        famMats.Add(new { name = m.Name, color = $"{m.Color.Red},{m.Color.Green},{m.Color.Blue}" });
                    }
                    var fImportCat = famDoc.Settings.Categories.Cast<Category>()
                        .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));
                    if (fImportCat != null)
                    {
                        foreach (Category sub in fImportCat.SubCategories)
                        {
                            famSubCats.Add(new {
                                name = sub.Name,
                                lineCol = $"{sub.LineColor?.Red},{sub.LineColor?.Green},{sub.LineColor?.Blue}",
                                mat = sub.Material?.Name
                            });
                        }
                    }
                    famDoc.Close(false);
                }
            }

            return new {
                wallTypeName,
                wallMatColors,
                projectImportSubCats = subCatList,
                projectGenSubCats = genSubCats,
                famMats,
                famSubCats
            };
        }
    }
}
