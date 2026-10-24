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
    public static class RebuildLidlFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            string dxfPath = args.GetProperty("dxfPath").GetString()!;
            if (!File.Exists(dxfPath))
            {
                return new { error = $"DXF file not found: {dxfPath}" };
            }

            var report = new List<string>();

            // Parse color mapping from args
            var layerColorMap = new Dictionary<string, (string matName, byte r, byte g, byte b)>(StringComparer.OrdinalIgnoreCase);
            if (args.TryGetProperty("layerMap", out var mapElem))
            {
                foreach (var prop in mapElem.EnumerateObject())
                {
                    string lName = prop.Name;
                    var obj = prop.Value;
                    string mName = obj.GetProperty("mat").GetString()!;
                    byte r = (byte)obj.GetProperty("r").GetInt32();
                    byte g = (byte)obj.GetProperty("g").GetInt32();
                    byte b = (byte)obj.GetProperty("b").GetInt32();
                    layerColorMap[lName] = (mName, r, g, b);
                }
            }

            // 1. Transaction to delete old imports and import new DXF
            using (var tx = new Transaction(doc, "Import 46-Object DXF"))
            {
                var failOpts = tx.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new WarningSwallower());
                failOpts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(failOpts);

                tx.Start();

                // Delete old import instances
                var oldImports = new FilteredElementCollector(doc)
                    .OfClass(typeof(ImportInstance))
                    .Cast<ImportInstance>()
                    .ToList();

                foreach (var imp in oldImports)
                {
                    try { doc.Delete(imp.Id); } catch { }
                }
                report.Add($"Deleted {oldImports.Count} old import instances.");

                // Find 3D or FloorPlan view
                var targetView = uiapp.ActiveUIDocument?.ActiveView ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View))
                    .Cast<View>()
                    .FirstOrDefault(v => !v.IsTemplate && (v.ViewType == ViewType.ThreeD || v.ViewType == ViewType.FloorPlan));

                if (targetView == null)
                {
                    tx.RollBack();
                    return new { error = "No valid view for import" };
                }

                var opt = new DWGImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Default,
                    ColorMode = ImportColorMode.Preserved,
                    AutoCorrectAlmostVHLines = false
                };

                doc.Import(dxfPath, opt, targetView, out ElementId newImportId);
                report.Add($"Imported new DXF: {dxfPath} (Id: {newImportId.Value})");

                tx.Commit();
            }

            // 2. Transaction to assign materials and configure display style
            using (var tx = new Transaction(doc, "Assign Materials to 46 Layers"))
            {
                var failOpts = tx.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(failOpts);

                tx.Start();

                var materialCache = new Dictionary<string, Material>(StringComparer.OrdinalIgnoreCase);
                var allMaterials = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .ToList();

                foreach (var m in allMaterials)
                {
                    materialCache[m.Name] = m;
                }

                var baseAssetElem = new FilteredElementCollector(doc)
                    .OfClass(typeof(AppearanceAssetElement))
                    .Cast<AppearanceAssetElement>()
                    .FirstOrDefault(a => a.Name.Equals("Default", StringComparison.OrdinalIgnoreCase) ||
                                         a.Name.Equals("Default Wall", StringComparison.OrdinalIgnoreCase));

                // Helper to get or create material
                Material GetOrCreateMaterial(string matName, byte r, byte g, byte b)
                {
                    if (materialCache.TryGetValue(matName, out var m)) return m;

                    var id = Material.Create(doc, matName);
                    var mat = (Material)doc.GetElement(id);
                    mat.Color = new Color(r, g, b);

                    try
                    {
                        if (baseAssetElem != null)
                        {
                            string newAssetName = "Asset_" + matName;
                            var assetElem = new FilteredElementCollector(doc)
                                .OfClass(typeof(AppearanceAssetElement))
                                .Cast<AppearanceAssetElement>()
                                .FirstOrDefault(a => a.Name.Equals(newAssetName, StringComparison.OrdinalIgnoreCase))
                                ?? baseAssetElem.Duplicate(newAssetName);

                            using (var editScope = new AppearanceAssetEditScope(doc))
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

                // Find category "Imports in Families"
                Category? importCat = doc.Settings.Categories
                    .Cast<Category>()
                    .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                int assignedCount = 0;
                if (importCat != null)
                {
                    foreach (Category sub in importCat.SubCategories)
                    {
                        string subName = sub.Name;
                        if (layerColorMap.TryGetValue(subName, out var spec))
                        {
                            var targetMat = GetOrCreateMaterial(spec.matName, spec.r, spec.g, spec.b);
                            sub.Material = targetMat;
                            sub.LineColor = new Color(spec.r, spec.g, spec.b);
                            assignedCount++;
                        }
                        else
                        {
                            // Try partial match
                            foreach (var kvp in layerColorMap)
                            {
                                if (subName.IndexOf(kvp.Key, StringComparison.OrdinalIgnoreCase) >= 0 ||
                                    kvp.Key.IndexOf(subName, StringComparison.OrdinalIgnoreCase) >= 0)
                                {
                                    var targetMat = GetOrCreateMaterial(kvp.Value.matName, kvp.Value.r, kvp.Value.g, kvp.Value.b);
                                    sub.Material = targetMat;
                                    sub.LineColor = new Color(kvp.Value.r, kvp.Value.g, kvp.Value.b);
                                    assignedCount++;
                                    break;
                                }
                            }
                        }
                    }
                }
                report.Add($"Assigned brand materials to {assignedCount} subcategories in Imports in Families.");

                // Set 3D view to FlatColors (Consistent Colors without edges)
                if (uiapp.ActiveUIDocument?.ActiveView is View3D view3D && !view3D.IsTemplate)
                {
                    try
                    {
                        view3D.DisplayStyle = DisplayStyle.FlatColors;
                        var vdm = view3D.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        view3D.SetViewDisplayModel(vdm);
                    }
                    catch { }
                }

                tx.Commit();
            }

            try
            {
                uiapp.ActiveUIDocument?.RefreshActiveView();
            }
            catch { }

            return new
            {
                success = true,
                report
            };
        }
    }
}
