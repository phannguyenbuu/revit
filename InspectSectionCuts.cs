using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSectionCuts
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            var floorCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Floors);
            var beamCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralFraming);

            // Object styles
            var floorStyle = new {
                projLineWeight = floorCat?.GetLineWeight(GraphicsStyleType.Projection),
                cutLineWeight = floorCat?.GetLineWeight(GraphicsStyleType.Cut),
                lineColor = floorCat?.LineColor != null ? $"{floorCat.LineColor.Red},{floorCat.LineColor.Green},{floorCat.LineColor.Blue}" : "null",
                material = floorCat?.Material?.Name
            };

            var beamStyle = new {
                projLineWeight = beamCat?.GetLineWeight(GraphicsStyleType.Projection),
                cutLineWeight = beamCat?.GetLineWeight(GraphicsStyleType.Cut),
                lineColor = beamCat?.LineColor != null ? $"{beamCat.LineColor.Red},{beamCat.LineColor.Green},{beamCat.LineColor.Blue}" : "null",
                material = beamCat?.Material?.Name
            };

            // Sample elements
            var sampleBeam = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            var sampleFloor = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .FirstOrDefault();

            List<object> beamMaterials = new List<object>();
            if (sampleBeam != null)
            {
                foreach (var mid in sampleBeam.GetMaterialIds(false))
                {
                    var m = doc.GetElement(mid) as Material;
                    if (m != null)
                    {
                        var cutPat = doc.GetElement(m.CutForegroundPatternId) as FillPatternElement;
                        beamMaterials.Add(new {
                            name = m.Name,
                            color = $"{m.Color.Red},{m.Color.Green},{m.Color.Blue}",
                            cutPatternName = cutPat?.Name,
                            cutPatternColor = $"{m.CutForegroundPatternColor.Red},{m.CutForegroundPatternColor.Green},{m.CutForegroundPatternColor.Blue}"
                        });
                    }
                }
            }

            List<object> floorMaterials = new List<object>();
            if (sampleFloor != null)
            {
                foreach (var mid in sampleFloor.GetMaterialIds(false))
                {
                    var m = doc.GetElement(mid) as Material;
                    if (m != null)
                    {
                        var cutPat = doc.GetElement(m.CutForegroundPatternId) as FillPatternElement;
                        floorMaterials.Add(new {
                            name = m.Name,
                            color = $"{m.Color.Red},{m.Color.Green},{m.Color.Blue}",
                            cutPatternName = cutPat?.Name,
                            cutPatternColor = $"{m.CutForegroundPatternColor.Red},{m.CutForegroundPatternColor.Green},{m.CutForegroundPatternColor.Blue}"
                        });
                    }
                }
            }

            // List all Section views
            var sectionViews = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSection))
                .Cast<ViewSection>()
                .Where(v => !v.IsTemplate)
                .Select(v => {
                    var floorOvr = v.GetCategoryOverrides(floorCat.Id);
                    var beamOvr = v.GetCategoryOverrides(beamCat.Id);
                    return new {
                        id = v.Id.Value,
                        name = v.Name,
                        viewType = v.ViewType.ToString(),
                        scale = v.Scale,
                        detailLevel = v.DetailLevel.ToString(),
                        displayStyle = v.DisplayStyle.ToString(),
                        floorCutLineWeight = floorOvr?.CutLineWeight,
                        floorCutLineColor = floorOvr?.CutLineColor?.IsValid == true ? $"{floorOvr.CutLineColor.Red},{floorOvr.CutLineColor.Green},{floorOvr.CutLineColor.Blue}" : "none",
                        floorCutPatId = floorOvr?.CutForegroundPatternId?.Value,
                        beamCutLineWeight = beamOvr?.CutLineWeight,
                        beamCutLineColor = beamOvr?.CutLineColor?.IsValid == true ? $"{beamOvr.CutLineColor.Red},{beamOvr.CutLineColor.Green},{beamOvr.CutLineColor.Blue}" : "none",
                        beamCutPatId = beamOvr?.CutForegroundPatternId?.Value
                    };
                })
                .ToList();

            var activeView = uidoc.ActiveView;

            return new {
                activeView = new { id = activeView?.Id.Value, name = activeView?.Name, viewType = activeView?.ViewType.ToString() },
                floorStyle,
                beamStyle,
                sampleBeam = sampleBeam != null ? new { id = sampleBeam.Id.Value, type = sampleBeam.Name, materials = beamMaterials } : null,
                sampleFloor = sampleFloor != null ? new { id = sampleFloor.Id.Value, type = sampleFloor.Name, materials = floorMaterials } : null,
                sectionViews
            };
        }
    }
}
