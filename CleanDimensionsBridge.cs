using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CleanDimensionsBridge
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active Revit document" };

                string targetViewArg = "all";
                bool removeZeros = true;
                bool removeBrokenChains = true;
                bool previewOnly = false;

                try
                {
                    if (args.ValueKind == JsonValueKind.Object)
                    {
                        if (args.TryGetProperty("targetView", out var tvProp)) targetViewArg = tvProp.GetString() ?? "all";
                        if (args.TryGetProperty("removeZeros", out var rzProp)) removeZeros = rzProp.GetBoolean();
                        if (args.TryGetProperty("removeBrokenChains", out var rbcProp)) removeBrokenChains = rbcProp.GetBoolean();
                        if (args.TryGetProperty("previewOnly", out var poProp)) previewOnly = poProp.GetBoolean();
                    }
                }
                catch { }

                var viewIds = new List<ElementId>();
                if (targetViewArg == "active")
                {
                    if (uidoc.ActiveView != null) viewIds.Add(uidoc.ActiveView.Id);
                }
                else if (long.TryParse(targetViewArg, out long parsedViewId))
                {
                    viewIds.Add(new ElementId(parsedViewId));
                }
                else
                {
                    var views = new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewPlan))
                        .Cast<ViewPlan>()
                        .Where(v => !v.IsTemplate && (v.ViewType == ViewType.FloorPlan || v.ViewType == ViewType.CeilingPlan))
                        .ToList();
                    foreach (var v in views) viewIds.Add(v.Id);
                }

                var cleanSummary = new List<object>();
                int totalZerosEliminated = 0;
                int totalBrokenChainsRemoved = 0;
                int totalDimsRebuilt = 0;

                using (var tx = new Transaction(doc, "Clean Zero Values and Broken Dimension Chains"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(new WarningSwallower());
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    foreach (var vId in viewIds)
                    {
                        var view = doc.GetElement(vId) as View;
                        if (view == null) continue;

                        var dimIds = new FilteredElementCollector(doc, view.Id)
                            .OfClass(typeof(Dimension))
                            .ToElementIds();

                        var viewReport = new List<object>();

                        foreach (var dId in dimIds)
                        {
                            var d = doc.GetElement(dId) as Dimension;
                            if (d == null || !d.IsValidObject) continue;

                            var segVals = new List<double>();
                            var zeroIndices = new HashSet<int>();

                            if (d.Segments != null && d.Segments.Size > 0)
                            {
                                for (int i = 0; i < d.Segments.Size; i++)
                                {
                                    var seg = d.Segments.get_Item(i);
                                    double mm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 1) : -1;
                                    if (mm == 0.0 || seg.ValueString == "0")
                                    {
                                        zeroIndices.Add(i);
                                    }
                                    segVals.Add(mm);
                                }
                            }
                            else if (d.Value.HasValue)
                            {
                                double mm = Math.Round(d.Value.Value * FT_TO_MM, 1);
                                if (mm == 0.0 || d.ValueString == "0")
                                {
                                    zeroIndices.Add(0);
                                }
                                segVals.Add(mm);
                            }

                            bool hasZero = zeroIndices.Count > 0;

                            // Check if broken chain in middle
                            bool isBrokenInMiddle = false;
                            if (segVals.Count >= 4)
                            {
                                int middleZeros = 0;
                                for (int i = 1; i < segVals.Count - 1; i++)
                                {
                                    if (segVals[i] == 0.0) middleZeros++;
                                }
                                if (middleZeros >= 2) isBrokenInMiddle = true;
                            }

                            // Case 1: Entire dimension is 0 (or single segment 0)
                            if (hasZero && d.NumberOfSegments <= 1)
                            {
                                if (!previewOnly)
                                {
                                    doc.Delete(d.Id);
                                }
                                totalZerosEliminated++;
                                viewReport.Add(new
                                {
                                    action = "Deleted Zero Dimension",
                                    dimId = dId.Value,
                                    segVals
                                });
                                continue;
                            }

                            // Case 2: Chain is broken in middle and requested to remove
                            if (isBrokenInMiddle && removeBrokenChains)
                            {
                                if (!previewOnly)
                                {
                                    doc.Delete(d.Id);
                                }
                                totalBrokenChainsRemoved++;
                                viewReport.Add(new
                                {
                                    action = "Deleted Broken/Fragmented Chain",
                                    dimId = dId.Value,
                                    middleZeros = zeroIndices.Count,
                                    segVals
                                });
                                continue;
                            }

                            // Case 3: Dimension has zero segments, rebuild without duplicates
                            if (hasZero && removeZeros)
                            {
                                var refs = d.References;
                                var line = d.Curve as Line;
                                var dt = d.DimensionType;

                                if (refs != null && line != null && dt != null)
                                {
                                    var newRefArray = new ReferenceArray();
                                    for (int i = 0; i < refs.Size; i++)
                                    {
                                        var r = refs.get_Item(i);
                                        if (i > 0 && zeroIndices.Contains(i - 1))
                                        {
                                            continue;
                                        }
                                        newRefArray.Append(r);
                                    }

                                    if (newRefArray.Size >= 2)
                                    {
                                        try
                                        {
                                            if (!previewOnly)
                                            {
                                                var newDim = doc.Create.NewDimension(view, line, newRefArray, dt);
                                                doc.Delete(d.Id);
                                                totalDimsRebuilt++;
                                                totalZerosEliminated += zeroIndices.Count;

                                                viewReport.Add(new
                                                {
                                                    action = "Rebuilt Dimension Without Zeros",
                                                    oldDimId = dId.Value,
                                                    newDimId = newDim.Id.Value,
                                                    zerosRemoved = zeroIndices.Count
                                                });
                                            }
                                            else
                                            {
                                                viewReport.Add(new
                                                {
                                                    action = "Preview Rebuild Without Zeros",
                                                    dimId = dId.Value,
                                                    zerosToRemove = zeroIndices.Count
                                                });
                                            }
                                        }
                                        catch (Exception ex)
                                        {
                                            viewReport.Add(new
                                            {
                                                action = "Failed Rebuild",
                                                dimId = dId.Value,
                                                error = ex.Message
                                            });
                                        }
                                    }
                                    else
                                    {
                                        if (!previewOnly) doc.Delete(d.Id);
                                        totalZerosEliminated++;
                                        viewReport.Add(new
                                        {
                                            action = "Deleted Redundant Dimension (Less than 2 valid refs)",
                                            dimId = dId.Value
                                        });
                                    }
                                }
                            }
                        }

                        if (viewReport.Count > 0)
                        {
                            cleanSummary.Add(new
                            {
                                viewId = view.Id.Value,
                                viewName = view.Name,
                                actions = viewReport
                            });
                        }
                    }

                    if (!previewOnly)
                    {
                        tx.Commit();
                    }
                    else
                    {
                        tx.RollBack();
                    }
                }

                return new
                {
                    success = true,
                    previewOnly,
                    totalZerosEliminated,
                    totalBrokenChainsRemoved,
                    totalDimsRebuilt,
                    viewsCleaned = cleanSummary.Count,
                    details = cleanSummary
                };
            }
            catch (Exception gex)
            {
                return new { success = false, error = gex.ToString() };
            }
        }
    }
}
