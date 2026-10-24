using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Visual;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateLidlRfa
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string dxfPath = args.GetProperty("dxfPath").GetString()!;
            string rfaPath = args.GetProperty("rfaPath").GetString()!;
            string templatePath = args.TryGetProperty("templatePath", out var tp) 
                ? tp.GetString()! 
                : @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";

            if (!File.Exists(templatePath))
            {
                templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            }

            var app = uiapp.Application;
            var famDoc = app.NewFamilyDocument(templatePath);

            View3D? view3D = new FilteredElementCollector(famDoc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            View targetView = (View?)view3D ?? famDoc.ActiveView ?? new FilteredElementCollector(famDoc)
                .OfClass(typeof(View))
                .Cast<View>()
                .FirstOrDefault(v => !v.IsTemplate);

            if (targetView == null)
            {
                famDoc.Close(false);
                return new { error = "No view found in family document" };
            }

            // Transaction 1: Set category and import DXF into 3D View
            ElementId importedId = ElementId.InvalidElementId;
            using (var tx = new Transaction(famDoc, "Import DXF Mesh"))
            {
                var failOpts = tx.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new WarningSwallower());
                failOpts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(failOpts);

                tx.Start();
                var cat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_SpecialityEquipment) 
                          ?? famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                if (cat != null) famDoc.OwnerFamily.FamilyCategory = cat;

                var opt = new DWGImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Millimeter,
                    ColorMode = ImportColorMode.Preserved,
                    AutoCorrectAlmostVHLines = false,
                    ThisViewOnly = false
                };

                famDoc.Import(dxfPath, opt, targetView, out importedId);
                tx.Commit();
            }

            // Transaction 2: Create materials, assign to subcategories, optimize view
            int assignedCount = 0;
            var assignedDetails = new List<string>();

            using (var tx = new Transaction(famDoc, "Assign Materials to SubCategories"))
            {
                var failOpts = tx.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(failOpts);

                tx.Start();

                var materialCache = new Dictionary<string, Material>(StringComparer.OrdinalIgnoreCase);
                var allMaterials = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .ToList();

                foreach (var m in allMaterials)
                {
                    materialCache[m.Name] = m;
                }

                var baseAssetElem = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(AppearanceAssetElement))
                    .Cast<AppearanceAssetElement>()
                    .FirstOrDefault(a => a.Name.Equals("Default", StringComparison.OrdinalIgnoreCase) ||
                                         a.Name.Equals("Default Wall", StringComparison.OrdinalIgnoreCase));

                Material GetOrCreateMaterial(string matName, byte r, byte g, byte b)
                {
                    if (materialCache.TryGetValue(matName, out var m)) return m;

                    var id = Material.Create(famDoc, matName);
                    var mat = (Material)famDoc.GetElement(id);
                    mat.Color = new Color(r, g, b);

                    try
                    {
                        if (baseAssetElem != null)
                        {
                            string newAssetName = "Asset_" + matName;
                            var assetElem = new FilteredElementCollector(famDoc)
                                .OfClass(typeof(AppearanceAssetElement))
                                .Cast<AppearanceAssetElement>()
                                .FirstOrDefault(a => a.Name.Equals(newAssetName, StringComparison.OrdinalIgnoreCase))
                                ?? baseAssetElem.Duplicate(newAssetName);

                            using (var editScope = new AppearanceAssetEditScope(famDoc))
                            {
                                Asset asset = editScope.Start(assetElem.Id);
                                var c = new Color(r, g, b);
                                var prop = asset.FindByName("generic_diffuse") as AssetPropertyDoubleArray4d;
                                if (prop != null) prop.SetValueAsColor(c);
                                else
                                {
                                    for (int i = 0; i < asset.Size; i++)
                                    {
                                        if (asset[i] is AssetPropertyDoubleArray4d colP &&
                                            (asset[i].Name.ToLower().Contains("color") || asset[i].Name.ToLower().Contains("diffuse")))
                                        {
                                            try { colP.SetValueAsColor(c); } catch { }
                                        }
                                    }
                                }
                                editScope.Commit(true);
                            }
                            mat.AppearanceAssetId = assetElem.Id;
                        }
                    }
                    catch { }

                    materialCache[matName] = mat;
                    return mat;
                }

                // Pre-create the 7 standard Lidl materials
                var matLidlBlue = GetOrCreateMaterial("Lidl Blue", 0, 91, 162);
                var matLidlDarkBlue = GetOrCreateMaterial("Lidl Dark Blue", 0, 47, 103);
                var matLidlRed = GetOrCreateMaterial("Lidl Red", 237, 28, 36);
                var matLidlYellow = GetOrCreateMaterial("Lidl Yellow", 255, 242, 0);
                var matLidlWhite = GetOrCreateMaterial("Lidl White", 255, 255, 255);
                var matLidlPole = GetOrCreateMaterial("Lidl Pole Grey", 128, 128, 128);
                var matLidlFrame = GetOrCreateMaterial("Lidl Frame Dark Grey", 86, 86, 86);

                Category? importCat = famDoc.Settings.Categories
                    .Cast<Category>()
                    .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                if (importCat != null)
                {
                    foreach (Category sub in importCat.SubCategories)
                    {
                        string sn = sub.Name.ToUpperInvariant();
                        Material targetMat;
                        Color lineColor;

                        if (sn.Contains("DARKBLUE") || sn.Contains("DARK_BLUE"))
                        {
                            targetMat = matLidlDarkBlue;
                            lineColor = new Color(0, 47, 103);
                        }
                        else if (sn.Contains("BLUE"))
                        {
                            targetMat = matLidlBlue;
                            lineColor = new Color(0, 91, 162);
                        }
                        else if (sn.Contains("RED"))
                        {
                            targetMat = matLidlRed;
                            lineColor = new Color(237, 28, 36);
                        }
                        else if (sn.Contains("YELLOW"))
                        {
                            targetMat = matLidlYellow;
                            lineColor = new Color(255, 242, 0);
                        }
                        else if (sn.Contains("POLE") || sn.Contains("CYLINDER"))
                        {
                            targetMat = matLidlPole;
                            lineColor = new Color(128, 128, 128);
                        }
                        else if (sn.Contains("FRAME") || sn.Contains("BOX"))
                        {
                            targetMat = matLidlFrame;
                            lineColor = new Color(86, 86, 86);
                        }
                        else
                        {
                            targetMat = matLidlWhite;
                            lineColor = new Color(255, 255, 255);
                        }

                        sub.Material = targetMat;
                        sub.LineColor = lineColor;
                        assignedCount++;
                        assignedDetails.Add($"{sub.Name} -> {targetMat.Name}");
                    }
                }

                // Configure 3D view display style and smooth edges
                if (view3D != null)
                {
                    try
                    {
                        view3D.DisplayStyle = DisplayStyle.FlatColors; // Consistent Colors
                        var vdm = view3D.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        view3D.SetViewDisplayModel(vdm);
                    }
                    catch { }
                }

                tx.Commit();
            }

            // Save family document with view3D active
            famDoc.SaveAs(rfaPath, new SaveAsOptions { OverwriteExistingFile = true });
            famDoc.Close(false);

            // Open and activate document in Revit UI
            try
            {
                var uidoc = uiapp.OpenAndActivateDocument(rfaPath);
                if (uidoc != null)
                {
                    var v3d = new FilteredElementCollector(uidoc.Document)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate);
                    if (v3d != null)
                    {
                        uidoc.ActiveView = v3d;
                        var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == v3d.Id);
                        uiview?.ZoomToFit();
                    }
                }
            }
            catch { }

            return new
            {
                success = true,
                rfa = rfaPath,
                assignedSubcategories = assignedCount,
                sample = assignedDetails.Take(10).ToList()
            };
        }
    }
}
