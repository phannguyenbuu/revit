using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExecuteFloorReplication
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public class Swallower : IFailuresPreprocessor
        {
            public List<string> Messages { get; } = new List<string>();
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                foreach (var msg in failuresAccessor.GetFailureMessages())
                {
                    Messages.Add($"{msg.GetSeverity()}: {msg.GetDescriptionText()}");
                }
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var report = new Dictionary<string, object>();
            var swallower = new Swallower();

            var lvl1 = doc.GetElement(new ElementId(311)) as Level;
            var lvl2 = doc.GetElement(new ElementId(694)) as Level;
            var lvl3 = doc.GetElement(new ElementId(1727584)) as Level;
            var lvl4 = doc.GetElement(new ElementId(2360634)) as Level;

            var v1 = doc.GetElement(new ElementId(312)) as ViewPlan;
            var v2 = doc.GetElement(new ElementId(695)) as ViewPlan;
            var v3 = doc.GetElement(new ElementId(1727632)) as ViewPlan;

            var floorPlanVft = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .FirstOrDefault(vft => vft.ViewFamily == ViewFamily.FloorPlan);

            if (floorPlanVft == null) return new { error = "No FloorPlan VFT" };

            // =================================================================
            // STEP 1: CREATE OR GET TẦNG 4 VIEWPLAN
            // =================================================================
            ViewPlan? v4 = null;
            try
            {
                v4 = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(vp => !vp.IsTemplate && !vp.IsCallout && vp.GenLevel?.Id.Value == 2360634);

                if (v4 == null && lvl4 != null)
                {
                    using (var tx = new Transaction(doc, "Create View Tang 4"))
                    {
                        var opts = tx.GetFailureHandlingOptions();
                        opts.SetFailuresPreprocessor(swallower);
                        tx.SetFailureHandlingOptions(opts);
                        tx.Start();

                        v4 = ViewPlan.Create(doc, floorPlanVft.Id, lvl4.Id);
                        try { v4.Name = "MẶT BẰNG TẦNG 4"; } 
                        catch { v4.Name = $"MẶT BẰNG TẦNG 4 ({v4.Id.Value})"; }

                        v4.Scale = 100;
                        v4.DetailLevel = ViewDetailLevel.Fine;

                        tx.Commit();
                    }
                }
                report["step1_viewTang4"] = v4 != null ? $"{v4.Name} (Id:{v4.Id.Value})" : "null";
            }
            catch (Exception ex)
            {
                report["step1_error"] = ex.Message;
            }

            var targetFloors = new List<(ViewPlan? view, Level? level, double dz_mm, string label)>
            {
                (v2, lvl2, 3900.0, "TẦNG 2"),
                (v3, lvl3, 7500.0, "TẦNG 3"),
                (v4, lvl4, 11100.0, "TẦNG 4")
            };

            // =================================================================
            // STEP 2: COPY SLABS & PLUMBING FIXTURES
            // =================================================================
            try
            {
                var archFloorsTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .Where(f => f.LevelId.Value == 311 && (f.FloorType.Name.Contains("NỀN") || f.FloorType.Name.Contains("BAC")))
                    .Select(f => f.Id)
                    .ToList();

                var structFloorTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .FirstOrDefault(f => f.LevelId.Value == 311 && f.FloorType.Name.Contains("BTCT"));

                var plumbingTang1 = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_PlumbingFixtures)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(fi => fi.LevelId.Value == 311)
                    .Select(fi => fi.Id)
                    .ToList();

                var cpOpts = new CopyPasteOptions();
                var step2Report = new List<object>();

                using (var tx = new Transaction(doc, "Copy Slabs and Plumbing to Levels 2, 3, 4"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    foreach (var (targetView, targetLvl, dz_mm, label) in targetFloors)
                    {
                        if (targetLvl == null) continue;

                        var toCopy = new List<ElementId>();
                        toCopy.AddRange(archFloorsTang1);
                        toCopy.AddRange(plumbingTang1);

                        // If Level 4 doesn't have structural slab yet, add it
                        if (targetLvl.Id.Value == 2360634 && structFloorTang1 != null)
                        {
                            bool hasStructFloor = new FilteredElementCollector(doc)
                                .OfClass(typeof(Floor))
                                .Cast<Floor>()
                                .Any(f => f.LevelId == targetLvl.Id && f.FloorType.Name.Contains("BTCT"));
                            if (!hasStructFloor)
                            {
                                toCopy.Add(structFloorTang1.Id);
                            }
                        }

                        XYZ translation = new XYZ(0, 0, dz_mm * MM_TO_FT);
                        var copiedIds = ElementTransformUtils.CopyElements(doc, toCopy, doc, Transform.CreateTranslation(translation), cpOpts);

                        int updatedLevels = 0;
                        foreach (var id in copiedIds)
                        {
                            var elem = doc.GetElement(id);
                            if (elem == null) continue;

                            var pLvl = elem.get_Parameter(BuiltInParameter.LEVEL_PARAM) 
                                    ?? elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM);
                            if (pLvl != null && !pLvl.IsReadOnly)
                            {
                                pLvl.Set(targetLvl.Id);
                                updatedLevels++;
                            }
                        }

                        step2Report.Add(new {
                            floor = label,
                            copiedTotal = copiedIds.Count,
                            updatedLevels
                        });
                    }

                    tx.Commit();
                }
                report["step2_slabsAndPlumbing"] = step2Report;
            }
            catch (Exception ex)
            {
                report["step2_error"] = ex.Message;
            }

            // =================================================================
            // STEP 3: COPY DIMENSIONS
            // =================================================================
            try
            {
                var v1Dims = new FilteredElementCollector(doc, v1.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                var cpOpts = new CopyPasteOptions();
                var step3Report = new List<object>();

                using (var tx = new Transaction(doc, "Copy Dimensions to Floor Plans"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    foreach (var (targetView, targetLvl, dz_mm, label) in targetFloors)
                    {
                        if (targetView == null) continue;
                        int success = 0;
                        int failed = 0;

                        foreach (var d in v1Dims)
                        {
                            try
                            {
                                var copied = ElementTransformUtils.CopyElements(v1, new List<ElementId> { d.Id }, targetView, null, cpOpts);
                                if (copied != null && copied.Count > 0) success++;
                                else failed++;
                            }
                            catch
                            {
                                failed++;
                            }
                        }

                        step3Report.Add(new {
                            floor = label,
                            success,
                            failed,
                            total = v1Dims.Count
                        });
                    }

                    tx.Commit();
                }
                report["step3_dimensions"] = step3Report;
            }
            catch (Exception ex)
            {
                report["step3_error"] = ex.Message;
            }

            // =================================================================
            // STEP 4: CREATE CALLOUT VIEWS ON UPPER FLOORS
            // =================================================================
            try
            {
                var calloutDefs = new List<(string name, double x1, double y1, double x2, double y2)>
                {
                    ("MẶT BẰNG CHI TIẾT CẦU THANG 1", 3504.245, 7131.311, 8720.000, 15617.656),
                    ("MẶT BẰNG CHI TIẾT CẦU THANG 2", 28784.245, 7131.311, 33999.992, 15617.656),
                    ("MẶT BẰNG CHI TIẾT KHU VỆ SINH", 32824.245, 7131.311, 37821.464, 14244.521),
                    ("MẶT BẰNG CHI TIẾT SẢNH CHÍNH", -5998.058, 2928.324, 1073.003, 11256.324),
                    ("MẶT BẰNG CHI TIẾT SẢNH PHỤ", 34169.378, -821.054, 37873.714, 5724.316)
                };

                var step4Report = new List<object>();

                using (var tx = new Transaction(doc, "Create Callouts on Floor Plans"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    foreach (var (targetView, targetLvl, dz_mm, label) in targetFloors)
                    {
                        if (targetView == null) continue;
                        var createdList = new List<string>();

                        foreach (var cdef in calloutDefs)
                        {
                            try
                            {
                                XYZ p1 = new XYZ(cdef.x1 * MM_TO_FT, cdef.y1 * MM_TO_FT, 0);
                                XYZ p2 = new XYZ(cdef.x2 * MM_TO_FT, cdef.y2 * MM_TO_FT, 0);

                                var calloutView = ViewSection.CreateCallout(doc, targetView.Id, floorPlanVft.Id, p1, p2);
                                if (calloutView != null)
                                {
                                    string finalName = $"{cdef.name} - {label}";
                                    try { calloutView.Name = finalName; } 
                                    catch { calloutView.Name = $"{finalName} ({calloutView.Id.Value})"; }

                                    calloutView.Scale = 50;
                                    calloutView.CropBoxActive = true;
                                    calloutView.CropBoxVisible = false;

                                    var pAnno = calloutView.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE);
                                    if (pAnno != null && !pAnno.IsReadOnly) pAnno.Set(1);

                                    // Clean callouts
                                    try { calloutView.SetCategoryHidden(new ElementId(BuiltInCategory.OST_ElevationMarks), true); } catch { }
                                    try { calloutView.SetCategoryHidden(new ElementId(BuiltInCategory.OST_Sections), true); } catch { }
                                    try { calloutView.SetCategoryHidden(new ElementId(BuiltInCategory.OST_Callouts), true); } catch { }

                                    createdList.Add($"{calloutView.Name} (Id:{calloutView.Id.Value})");
                                }
                            }
                            catch (Exception cex)
                            {
                                createdList.Add($"Failed {cdef.name}: {cex.Message}");
                            }
                        }

                        step4Report.Add(new {
                            floor = label,
                            callouts = createdList
                        });
                    }

                    tx.Commit();
                }
                report["step4_callouts"] = step4Report;
            }
            catch (Exception ex)
            {
                report["step4_error"] = ex.Message;
            }

            // =================================================================
            // STEP 5: VISIBILITY OF FLOORS, SECTIONS, DIMS
            // =================================================================
            try
            {
                var allPlans = new List<ViewPlan?> { v1, v2, v3, v4 };
                var catFloorId = new ElementId(BuiltInCategory.OST_Floors);
                var catSectionId = new ElementId(BuiltInCategory.OST_Sections);
                var catDimId = new ElementId(BuiltInCategory.OST_Dimensions);
                var catDoorTagId = new ElementId(BuiltInCategory.OST_DoorTags);

                using (var tx = new Transaction(doc, "Ensure View Visibility"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    foreach (var vp in allPlans)
                    {
                        if (vp == null) continue;
                        try { if (vp.GetCategoryHidden(catFloorId)) vp.SetCategoryHidden(catFloorId, false); } catch { }
                        try { if (vp.GetCategoryHidden(catSectionId)) vp.SetCategoryHidden(catSectionId, false); } catch { }
                        try { if (vp.GetCategoryHidden(catDimId)) vp.SetCategoryHidden(catDimId, false); } catch { }
                        try { if (vp.GetCategoryHidden(catDoorTagId)) vp.SetCategoryHidden(catDoorTagId, false); } catch { }
                    }

                    tx.Commit();
                }
                report["step5_visibility"] = "Success";
            }
            catch (Exception ex)
            {
                report["step5_error"] = ex.Message;
            }

            // =================================================================
            // STEP 6: CREATE DOOR TAGS FOR ALL DOORS
            // =================================================================
            try
            {
                var doorTagSym = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_DoorTags)
                    .WhereElementIsElementType()
                    .Cast<FamilySymbol>()
                    .FirstOrDefault();

                var allPlans = new List<ViewPlan?> { v1, v2, v3, v4 };
                var step6Report = new List<object>();

                using (var tx = new Transaction(doc, "Tag All Untagged Doors"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    foreach (var vp in allPlans)
                    {
                        if (vp == null) continue;

                        var existingTags = new FilteredElementCollector(doc, vp.Id)
                            .OfCategory(BuiltInCategory.OST_DoorTags)
                            .WhereElementIsNotElementType()
                            .Cast<IndependentTag>()
                            .ToList();

                        var taggedDoorIds = new HashSet<long>();
                        foreach (var tag in existingTags)
                        {
                            foreach (var lId in tag.GetTaggedElementIds())
                            {
                                if (lId.HostElementId != null && lId.HostElementId != ElementId.InvalidElementId)
                                {
                                    taggedDoorIds.Add(lId.HostElementId.Value);
                                }
                            }
                        }

                        var viewDoors = new FilteredElementCollector(doc, vp.Id)
                            .OfCategory(BuiltInCategory.OST_Doors)
                            .WhereElementIsNotElementType()
                            .Cast<FamilyInstance>()
                            .ToList();

                        int tagsCreated = 0;
                        foreach (var d in viewDoors)
                        {
                            if (taggedDoorIds.Contains(d.Id.Value)) continue;

                            var loc = d.Location as LocationPoint;
                            if (loc == null) continue;

                            var pt = loc.Point;
                            var face = d.FacingOrientation;
                            var headPt = pt + face * (400.0 * MM_TO_FT);

                            try
                            {
                                var tag = IndependentTag.Create(doc, vp.Id, new Reference(d), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, headPt);
                                if (doorTagSym != null) tag.ChangeTypeId(doorTagSym.Id);
                                taggedDoorIds.Add(d.Id.Value);
                                tagsCreated++;
                            }
                            catch
                            {
                                try
                                {
                                    var tag = IndependentTag.Create(doc, vp.Id, new Reference(d), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, pt);
                                    if (doorTagSym != null) tag.ChangeTypeId(doorTagSym.Id);
                                    taggedDoorIds.Add(d.Id.Value);
                                    tagsCreated++;
                                }
                                catch { }
                            }
                        }

                        step6Report.Add(new {
                            view = vp.Name,
                            doorsInView = viewDoors.Count,
                            existingTags = existingTags.Count,
                            tagsCreated
                        });
                    }

                    tx.Commit();
                }
                report["step6_doorTags"] = step6Report;
            }
            catch (Exception ex)
            {
                report["step6_error"] = ex.Message;
            }

            return report;
        }
    }
}
