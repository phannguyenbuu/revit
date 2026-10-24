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
    public static class LidlSignColorApplicator
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var colorMap = new Dictionary<string, (string matName, byte r, byte g, byte b)>(StringComparer.OrdinalIgnoreCase)
            {
                // Main Sign Panel Background: Lidl Blue
                { "Layer_BLEED_1060x710_Trang00_11", ("Lidl Blue", 0, 91, 162) },
                
                // Logo Letters L, D, L: Lidl Blue
                { "Layer_LOGO_DOT_RED_Trang1_7", ("Lidl Blue", 0, 91, 162) },
                { "Layer_LOGO_DOT_RED_Trang004_20", ("Lidl Blue", 0, 91, 162) },
                
                // Circle behind Arrow: Lidl Dark Blue (Navy)
                { "Layer_DIELINE_CUT_1050x700_T_9", ("Lidl Dark Blue", 0, 47, 103) },
                { "Layer_DIELINE_CUT_1050x700_T_12", ("Lidl Dark Blue", 0, 47, 103) },
                
                // Logo Circular Border Ring & Letter 'i' with Dot: Lidl Red
                { "Layer_LOGO_CIRCLE_RED_Trang1_5", ("Lidl Red", 237, 28, 36) },
                { "Layer_LOGO_CIRCLE_RED_Trang0_14", ("Lidl Red", 237, 28, 36) },
                { "Layer_LOGO_DOT_RED_Trang1_8", ("Lidl Red", 237, 28, 36) },
                { "Layer_LOGO_DOT_RED_Trang003_19", ("Lidl Red", 237, 28, 36) },
                
                // Logo Inner Disc: Lidl Yellow
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_6", ("Lidl Yellow", 255, 242, 0) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_16", ("Lidl Yellow", 255, 242, 0) },
                
                // White Elements (Square Logo Outline, Directional Arrow, Bottom Symbols): White
                { "Layer_LOGO_BOX_WHITE_Trang1_4", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_BOX_WHITE_Trang00_13", ("Lidl White", 255, 255, 255) },
                { "Layer_ARROW_Trang1_0", ("Lidl White", 255, 255, 255) },
                { "Layer_ARROW_Trang003_10", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_1", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_15", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_2", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_17", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_3", ("Lidl White", 255, 255, 255) },
                { "Layer_LOGO_CIRCLE_YELLOW_Tra_18", ("Lidl White", 255, 255, 255) },
                
                // Support Pole & Frame: Metallic Grey
                { "Cylinder001_21", ("Lidl Pole Grey", 128, 128, 128) },
                { "Box001_22", ("Lidl Frame Dark Grey", 86, 86, 86) },
                { "Box002_23", ("Lidl Frame Dark Grey", 86, 86, 86) }
            };

            var assignments = new List<object>();
            var errors = new List<string>();

            using (var tx = new Transaction(doc, "Apply Brand Colors to Lidl Sign Layers"))
            {
                tx.Start();

                // 1. Get or create materials
                var materialCache = new Dictionary<string, Material>(StringComparer.OrdinalIgnoreCase);
                var allMaterials = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .ToList();

                foreach (var m in allMaterials)
                {
                    materialCache[m.Name] = m;
                }

                // Get base appearance asset to duplicate if available
                var baseAssetElem = new FilteredElementCollector(doc)
                    .OfClass(typeof(AppearanceAssetElement))
                    .Cast<AppearanceAssetElement>()
                    .FirstOrDefault(a => a.Name.Equals("Default", StringComparison.OrdinalIgnoreCase) ||
                                         a.Name.Equals("Default Wall", StringComparison.OrdinalIgnoreCase));

                var uniqueMatSpecs = colorMap.Values.Distinct().ToList();
                foreach (var spec in uniqueMatSpecs)
                {
                    Material mat;
                    if (!materialCache.TryGetValue(spec.matName, out mat!))
                    {
                        var id = Material.Create(doc, spec.matName);
                        mat = (Material)doc.GetElement(id);
                        materialCache[spec.matName] = mat;
                    }

                    // Set Shading Color
                    mat.Color = new Color(spec.r, spec.g, spec.b);

                    // Set Appearance Asset for Realistic Rendering
                    try
                    {
                        AppearanceAssetElement? assetElem = null;
                        if (mat.AppearanceAssetId != ElementId.InvalidElementId)
                        {
                            assetElem = doc.GetElement(mat.AppearanceAssetId) as AppearanceAssetElement;
                        }

                        if (assetElem == null && baseAssetElem != null)
                        {
                            string newAssetName = "Asset_" + spec.matName;
                            assetElem = new FilteredElementCollector(doc)
                                .OfClass(typeof(AppearanceAssetElement))
                                .Cast<AppearanceAssetElement>()
                                .FirstOrDefault(a => a.Name.Equals(newAssetName, StringComparison.OrdinalIgnoreCase));

                            if (assetElem == null)
                            {
                                assetElem = baseAssetElem.Duplicate(newAssetName);
                            }
                            mat.AppearanceAssetId = assetElem.Id;
                        }

                        if (assetElem != null)
                        {
                            using (var editScope = new AppearanceAssetEditScope(doc))
                            {
                                Asset asset = editScope.Start(assetElem.Id);
                                var c = new Color(spec.r, spec.g, spec.b);
                                var prop = asset.FindByName("generic_diffuse") as AssetPropertyDoubleArray4d;
                                if (prop != null)
                                {
                                    prop.SetValueAsColor(c);
                                }
                                else
                                {
                                    for (int i = 0; i < asset.Size; i++)
                                    {
                                        var p = asset[i];
                                        if (p is AssetPropertyDoubleArray4d colP &&
                                            (p.Name.ToLower().Contains("color") || p.Name.ToLower().Contains("diffuse")))
                                        {
                                            try { colP.SetValueAsColor(c); } catch { }
                                        }
                                    }
                                }
                                editScope.Commit(true);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        errors.Add($"AppearanceAsset warning for {spec.matName}: {ex.Message}");
                    }
                }

                // 2. Find target category "Imports in Families"
                Category? importCat = doc.Settings.Categories
                    .Cast<Category>()
                    .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                if (importCat == null)
                {
                    tx.RollBack();
                    return new { error = "Imports in Families category not found in active document" };
                }

                // 3. Assign material and line color to each subcategory
                foreach (Category sub in importCat.SubCategories)
                {
                    string subName = sub.Name;
                    string matchedKey = null!;

                    if (colorMap.ContainsKey(subName))
                    {
                        matchedKey = subName;
                    }
                    else
                    {
                        foreach (var kvp in colorMap)
                        {
                            if (subName.IndexOf(kvp.Key, StringComparison.OrdinalIgnoreCase) >= 0 ||
                                kvp.Key.IndexOf(subName, StringComparison.OrdinalIgnoreCase) >= 0)
                            {
                                matchedKey = kvp.Key;
                                break;
                            }
                        }
                    }

                    if (matchedKey != null)
                    {
                        var spec = colorMap[matchedKey];
                        var targetMat = materialCache[spec.matName];
                        sub.Material = targetMat;
                        sub.LineColor = new Color(spec.r, spec.g, spec.b);

                        assignments.Add(new
                        {
                            subCategory = subName,
                            material = spec.matName,
                            color = $"RGB({spec.r}, {spec.g}, {spec.b})",
                            hex = $"#{spec.r:X2}{spec.g:X2}{spec.b:X2}"
                        });
                    }
                }

                // 4. Configure active 3D view display style to Shading with Edges if possible
                if (uiapp.ActiveUIDocument?.ActiveView is View3D view3D && !view3D.IsTemplate)
                {
                    try
                    {
                        view3D.DisplayStyle = DisplayStyle.ShadingWithEdges;
                    }
                    catch { }
                }

                tx.Commit();
            }

            // Refresh active view
            try
            {
                uiapp.ActiveUIDocument?.RefreshActiveView();
            }
            catch { }

            return new
            {
                success = true,
                assignedCount = assignments.Count,
                assignments,
                errors
            };
        }
    }
}
