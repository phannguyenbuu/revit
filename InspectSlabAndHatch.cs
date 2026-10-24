using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSlabAndHatch
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var v1 = doc.GetElement(new ElementId(312)) as ViewPlan;
                var v2 = doc.GetElement(new ElementId(695)) as ViewPlan;
                var v3 = doc.GetElement(new ElementId(1727632)) as ViewPlan;

                // View floor category visibility & overrides
                var viewSettings = new List<object>();
                foreach (var v in new[] { v1, v2, v3 })
                {
                    if (v == null) continue;
                    var catId = new ElementId(BuiltInCategory.OST_Floors);
                    bool isHidden = v.GetCategoryHidden(catId);
                    var og = v.GetCategoryOverrides(catId);
                    viewSettings.Add(new {
                        viewId = v.Id.Value,
                        viewName = v.Name,
                        floorsCatHidden = isHidden,
                        surfacePatternVisible = og.IsSurfaceForegroundPatternVisible,
                        surfacePatternId = og.SurfaceForegroundPatternId.Value
                    });
                }

                // Slabs on Level 1
                var floors1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .Where(f => f.LevelId.Value == 311)
                    .Select(f => {
                        var ft = f.FloorType;
                        var matId = ft.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)?.AsElementId();
                        Material mat = null;
                        if (matId != null && matId != ElementId.InvalidElementId)
                        {
                            mat = doc.GetElement(matId) as Material;
                        }
                        // Also check compound structure layers
                        var cs = ft.GetCompoundStructure();
                        var layerMats = new List<string>();
                        if (cs != null)
                        {
                            foreach (var layer in cs.GetLayers())
                            {
                                var lm = doc.GetElement(layer.MaterialId) as Material;
                                if (lm != null)
                                {
                                    var pat = doc.GetElement(lm.SurfaceForegroundPatternId) as FillPatternElement;
                                    layerMats.Add($"{lm.Name} (Pattern:{pat?.Name ?? "None"})");
                                }
                            }
                        }

                        // Check element override in v1
                        var elemOg = v1?.GetElementOverrides(f.Id);

                        return new {
                            id = f.Id.Value,
                            name = f.Name,
                            floorType = ft.Name,
                            layerMats,
                            v1ElemOgPattern = elemOg?.SurfaceForegroundPatternId.Value ?? -1,
                            v1ElemPatternVis = elemOg?.IsSurfaceForegroundPatternVisible ?? false
                        };
                    }).ToList();

                return new {
                    viewSettings,
                    floors1
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
