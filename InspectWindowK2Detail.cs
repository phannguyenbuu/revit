using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowK2Detail
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            long instId = args.TryGetProperty("id", out var idProp) ? idProp.GetInt64() : 2377860L;
            var elem = doc.GetElement(new ElementId(instId)) as FamilyInstance;
            if (elem == null) return new { error = $"Element {instId} not found or not FamilyInstance" };

            var view = doc.ActiveView;
            var vr = view as ViewPlan;
            object viewRangeInfo = null;

            if (vr != null)
            {
                var pvr = vr.GetViewRange();
                var topLvl = doc.GetElement(pvr.GetLevelId(PlanViewPlane.TopClipPlane))?.Name;
                var cutLvl = doc.GetElement(pvr.GetLevelId(PlanViewPlane.CutPlane))?.Name;
                var botLvl = doc.GetElement(pvr.GetLevelId(PlanViewPlane.BottomClipPlane))?.Name;
                var depLvl = doc.GetElement(pvr.GetLevelId(PlanViewPlane.ViewDepthPlane))?.Name;

                viewRangeInfo = new
                {
                    top = $"{topLvl} + {pvr.GetOffset(PlanViewPlane.TopClipPlane) * FT2MM:F1} mm",
                    cut = $"{cutLvl} + {pvr.GetOffset(PlanViewPlane.CutPlane) * FT2MM:F1} mm",
                    bottom = $"{botLvl} + {pvr.GetOffset(PlanViewPlane.BottomClipPlane) * FT2MM:F1} mm",
                    depth = $"{depLvl} + {pvr.GetOffset(PlanViewPlane.ViewDepthPlane) * FT2MM:F1} mm"
                };
            }

            var bbWorld = elem.get_BoundingBox(null);
            var host = elem.Host;
            var symbol = elem.Symbol;
            var family = symbol?.Family;

            var instParams = new Dictionary<string, string>();
            foreach (Parameter p in elem.Parameters)
            {
                if (p.HasValue && !string.IsNullOrEmpty(p.Definition.Name))
                {
                    instParams[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString();
                }
            }

            // Inspect Family Document
            object familyDocInfo = null;
            if (family != null && family.IsEditable)
            {
                var famDoc = doc.EditFamily(family);
                if (famDoc != null)
                {
                    try
                    {
                        var solids = new List<object>();
                        var forms = new FilteredElementCollector(famDoc)
                            .WherePasses(new ElementMulticlassFilter(new List<Type> {
                                typeof(GenericForm),
                                typeof(FreeFormElement),
                                typeof(ImportInstance)
                            })).ToList();

                        foreach (var f in forms)
                        {
                            var fev = (f as GenericForm)?.GetVisibility() ?? (f as FreeFormElement)?.GetVisibility();
                            solids.Add(new
                            {
                                id = f.Id.Value,
                                type = f.GetType().Name,
                                category = f.Category?.Name,
                                isSolid = (f as GenericForm)?.IsSolid ?? true,
                                planCut = fev?.IsShownInPlanRCPCut ?? false,
                                frontBack = fev?.IsShownInFrontBack ?? false,
                                leftRight = fev?.IsShownInLeftRight ?? false,
                                coarse = fev?.IsShownInCoarse ?? false,
                                medium = fev?.IsShownInMedium ?? false,
                                fine = fev?.IsShownInFine ?? false
                            });
                        }

                        var curves2d = new FilteredElementCollector(famDoc)
                            .OfClass(typeof(CurveElement))
                            .Cast<CurveElement>()
                            .Select(c => new {
                                id = c.Id.Value,
                                type = c.GetType().Name,
                                style = c.LineStyle?.Name,
                                isSymbolic = c is SymbolicCurve
                            })
                            .ToList();

                        var openings = new FilteredElementCollector(famDoc)
                            .OfClass(typeof(Opening))
                            .Select(o => new { id = o.Id.Value, name = o.Name })
                            .ToList();

                        var famCat = famDoc.OwnerFamily.FamilyCategory;

                        familyDocInfo = new
                        {
                            familyName = family.Name,
                            category = famCat?.Name,
                            numForms = forms.Count,
                            forms = solids,
                            numCurves = curves2d.Count,
                            curves = curves2d,
                            numOpenings = openings.Count,
                            openings = openings
                        };
                    }
                    finally
                    {
                        famDoc.Close(false);
                    }
                }
            }

            return new
            {
                success = true,
                instanceId = instId,
                familyName = family?.Name,
                symbolName = symbol?.Name,
                host = host != null ? $"{host.Name} (ID: {host.Id.Value})" : "None (Un-hosted)",
                location = elem.Location is LocationPoint lp ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1}) mm" : "Curve",
                bboxWorld = bbWorld != null ? new {
                    min = $"({bbWorld.Min.X * FT2MM:F1}, {bbWorld.Min.Y * FT2MM:F1}, {bbWorld.Min.Z * FT2MM:F1}) mm",
                    max = $"({bbWorld.Max.X * FT2MM:F1}, {bbWorld.Max.Y * FT2MM:F1}, {bbWorld.Max.Z * FT2MM:F1}) mm",
                    height = $"{(bbWorld.Max.Z - bbWorld.Min.Z) * FT2MM:F1} mm"
                } : null,
                viewRange = viewRangeInfo,
                activeView = $"{view.Name} (ID: {view.Id.Value})",
                familyDetails = familyDocInfo,
                parameters = instParams
            };
        }
    }
}
