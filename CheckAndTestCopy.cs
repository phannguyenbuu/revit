using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckAndTestCopy
    {
        public class CopyWarningSwallower : IFailuresPreprocessor
        {
            public List<string> Warnings { get; } = new List<string>();
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                var messages = failuresAccessor.GetFailureMessages();
                foreach (var msg in messages)
                {
                    Warnings.Add($"{msg.GetSeverity()}: {msg.GetDescriptionText()}");
                }
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
                if (doc == null) return new { error = "No doc" };

                // 1. Check Floor Plans
                var floorPlanVft = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewFamilyType))
                    .Cast<ViewFamilyType>()
                    .FirstOrDefault(vft => vft.ViewFamily == ViewFamily.FloorPlan);

                var lvl1 = doc.GetElement(new ElementId(311)) as Level;
                var lvl2 = doc.GetElement(new ElementId(694)) as Level;
                var lvl3 = doc.GetElement(new ElementId(1727584)) as Level;
                var lvl4 = doc.GetElement(new ElementId(2360634)) as Level;

                var v1 = doc.GetElement(new ElementId(312)) as ViewPlan;
                var v2 = doc.GetElement(new ElementId(695)) as ViewPlan;
                var v3 = doc.GetElement(new ElementId(1727632)) as ViewPlan;
                
                // Check if Level 4 has a ViewPlan
                var v4 = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(vp => !vp.IsTemplate && !vp.IsCallout && vp.GenLevel?.Id.Value == 2360634);

                string v4Info = v4 != null ? $"{v4.Name} (Id:{v4.Id.Value})" : "None";

                // 2. Sections check
                var sections = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .Where(s => !s.IsCallout && s.ViewType == ViewType.Section)
                    .Select(s => new {
                        id = s.Id.Value,
                        name = s.Name
                    }).ToList();

                // Check sections visibility on v1, v2, v3
                var secStatus = new Dictionary<string, object>();
                foreach (var (v, label) in new[] { (v1, "Tang1"), (v2, "Tang2"), (v3, "Tang3") })
                {
                    if (v == null) continue;
                    bool catHidden = v.GetCategoryHidden(new ElementId(BuiltInCategory.OST_Sections));
                    secStatus[label] = new {
                        viewName = v.Name,
                        catHidden,
                        scale = v.Scale
                    };
                }

                // 3. Test copying 1 dimension to v2 in a rolled-back sub-transaction or transaction
                var v1Dims = new FilteredElementCollector(doc, v1.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .Select(d => d.Id)
                    .ToList();

                string testDimCopyResult = "";
                var swallower = new CopyWarningSwallower();

                using (var tx = new Transaction(doc, "Test Copy Dim"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    try
                    {
                        var cpOpts = new CopyPasteOptions();
                        var copiedIds = ElementTransformUtils.CopyElements(v1, v1Dims, v2, null, cpOpts);
                        testDimCopyResult = $"SUCCESS: Copied {copiedIds.Count} of {v1Dims.Count} dims to Tang 2";
                    }
                    catch (Exception ex)
                    {
                        testDimCopyResult = $"EXCEPTION: {ex.Message}";
                    }

                    // Roll back test
                    tx.RollBack();
                }

                // 4. Test copying 3D elements (Slabs and Plumbing) to Level 2
                var floorsTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .Where(f => f.LevelId.Value == 311)
                    .Select(f => f.Id)
                    .ToList();

                var plumbingTang1 = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_PlumbingFixtures)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(fi => fi.LevelId.Value == 311)
                    .Select(fi => fi.Id)
                    .ToList();

                string testModelCopyResult = "";
                using (var tx = new Transaction(doc, "Test Copy Model"))
                {
                    var opts = tx.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(swallower);
                    tx.SetFailureHandlingOptions(opts);
                    tx.Start();

                    try
                    {
                        double dz = (3.9 - 0.0) / 0.3048; // Level 2 is +3.9m
                        XYZ translation = new XYZ(0, 0, dz);
                        var toCopy = new List<ElementId>();
                        toCopy.AddRange(floorsTang1);
                        toCopy.AddRange(plumbingTang1);

                        var cpOpts = new CopyPasteOptions();
                        var copied = ElementTransformUtils.CopyElements(doc, toCopy, doc, Transform.CreateTranslation(translation), cpOpts);
                        testModelCopyResult = $"SUCCESS: Copied {copied.Count} model elements ({floorsTang1.Count} floors, {plumbingTang1.Count} plumbing)";
                    }
                    catch (Exception ex)
                    {
                        testModelCopyResult = $"EXCEPTION: {ex.Message}";
                    }

                    tx.RollBack();
                }

                return new {
                    v4Info,
                    sections,
                    secStatus,
                    testDimCopyResult,
                    warningsDimCopy = swallower.Warnings,
                    testModelCopyResult,
                    floorsTang1Count = floorsTang1.Count,
                    plumbingTang1Count = plumbingTang1.Count
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
