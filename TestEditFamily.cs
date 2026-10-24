using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestEditFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("Mat_Tien_3dsMax", StringComparison.OrdinalIgnoreCase));

            if (fam == null) return new { error = "Family Mat_Tien_3dsMax not found" };

            string dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Sync_3dsMax_To_Revit.dwg";
            if (!File.Exists(dwgPath)) return new { error = "DWG file not found: " + dwgPath };

            bool loadResult = false;
            string log = "";

            Document famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Could not edit family" };

            try
            {
                using (var tx = new Transaction(famDoc, "Update Imported DWG"))
                {
                    tx.Start();

                    // Delete existing ImportInstances in family
                    var existingImports = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(ImportInstance))
                        .Cast<ImportInstance>()
                        .ToList();

                    foreach (var imp in existingImports)
                    {
                        famDoc.Delete(imp.Id);
                    }
                    log += $"Deleted {existingImports.Count} old imports. ";

                    // Import new DWG
                    var view = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate);

                    var dwgOpt = new DWGImportOptions
                    {
                        Placement = ImportPlacement.Origin,
                        Unit = ImportUnit.Millimeter,
                        ColorMode = ImportColorMode.BlackAndWhite,
                        AutoCorrectAlmostVHLines = false,
                        ThisViewOnly = false
                    };

                    ElementId importedId;
                    famDoc.Import(dwgPath, dwgOpt, view, out importedId);
                    log += $"Imported new DWG id: {importedId.Value}. ";

                    // Material setup
                    var mat = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Material))
                        .Cast<Material>()
                        .FirstOrDefault(m => m.Name.Contains("Đồng Bộ") || m.Name.Contains("Trắng"));

                    if (mat == null)
                    {
                        var matId = Material.Create(famDoc, "Vật liệu Đồng Bộ (Trắng)");
                        mat = (Material)famDoc.GetElement(matId);
                        mat.Color = new Color(255, 255, 255);
                    }

                    var importCat = famDoc.Settings.Categories.Cast<Category>()
                        .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                    if (importCat != null)
                    {
                        foreach (Category sub in importCat.SubCategories)
                        {
                            sub.Material = mat;
                            sub.LineColor = new Color(0, 0, 0);
                        }
                    }

                    tx.Commit();
                }

                // Load family back into document
                Family loadedFam = famDoc.LoadFamily(doc, new SyncFamilyLoadOptions());
                loadResult = loadedFam != null;
                log += $"LoadFamily into doc result: {loadResult}, loadedFam: {loadedFam?.Name}. ";
            }
            catch (Exception ex)
            {
                log += $"Exception: {ex.Message} ";
            }
            finally
            {
                famDoc.Close(false);
            }

            return new
            {
                success = loadResult,
                log
            };
        }
    }
}
