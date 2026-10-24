using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class StairFailurePreprocessor : IFailuresPreprocessor
    {
        public List<string> Warnings = new List<string>();
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failList = failuresAccessor.GetFailureMessages();
            foreach (var fail in failList)
            {
                Warnings.Add(fail.GetDescriptionText());
                if (fail.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(fail);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class TestCreateStair
    {
        private static double M(double meters) => meters / 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var prep = new StairFailurePreprocessor();

            try
            {
                // Find levels
                Level baseLevel = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name.Contains("TẦNG 1") || l.Name.Contains("TANG 1"));

                Level topLevel = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name.Contains("TẦNG 2") || l.Name.Contains("TANG 2"));

                if (baseLevel == null || topLevel == null)
                    return new { error = "Levels not found" };

                // Find or duplicate stair type
                StairsType stairType = null;
                using (Transaction t = new Transaction(doc, "Prepare Stair Type"))
                {
                    t.Start();
                    var existingCustom = new FilteredElementCollector(doc)
                        .WhereElementIsElementType()
                        .OfType<StairsType>()
                        .FirstOrDefault(st => st.Name == "BẬC THANG LÁT ĐÁ GRANIT - 21 BẬC");

                    if (existingCustom != null)
                    {
                        stairType = existingCustom;
                    }
                    else
                    {
                        var baseGranit = new FilteredElementCollector(doc)
                            .WhereElementIsElementType()
                            .OfType<StairsType>()
                            .FirstOrDefault(st => st.Id.Value == 702992 || st.Name.Contains("GRANIT"));

                        if (baseGranit == null)
                            baseGranit = new FilteredElementCollector(doc).WhereElementIsElementType().OfType<StairsType>().First();

                        stairType = baseGranit.Duplicate("BẬC THANG LÁT ĐÁ GRANIT - 21 BẬC") as StairsType;
                        stairType.MaxRiserHeight = M(0.180); // 180mm
                        stairType.MinRunWidth = M(1.000);   // 1000mm
                        stairType.MinTreadDepth = M(0.280); // 280mm
                    }
                    t.Commit();
                }

                // Check existing test stairs and delete them if any
                var oldStairs = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Stairs)
                    .WhereElementIsNotElementType()
                    .Cast<Stairs>()
                    .Where(s => s.Name.Contains("BẬC THANG LÁT ĐÁ GRANIT - 21 BẬC") || s.LookupParameter("Comments")?.AsString() == "CAD_CONVERTED")
                    .Select(s => s.Id)
                    .ToList();

                if (oldStairs.Count > 0)
                {
                    using (Transaction t = new Transaction(doc, "Delete Old Stairs"))
                    {
                        t.Start();
                        doc.Delete(oldStairs);
                        t.Commit();
                    }
                }

                ElementId stairsId = ElementId.InvalidElementId;
                ElementId run1Id = ElementId.InvalidElementId;
                ElementId run2Id = ElementId.InvalidElementId;
                ElementId landingId = ElementId.InvalidElementId;

                StairsEditScope scope = new StairsEditScope(doc, "Create Stair From CAD");
                stairsId = scope.Start(baseLevel.Id, topLevel.Id);

                using (Transaction t = new Transaction(doc, "Add Runs and Landing"))
                {
                    t.Start();

                    Stairs stairs = doc.GetElement(stairsId) as Stairs;
                    stairs.ChangeTypeId(stairType.Id);
                    stairs.DesiredRisersNumber = 21;
                    stairs.ActualTreadDepth = M(0.300);
                    stairs.LookupParameter("Comments")?.Set("CAD_CONVERTED");

                    // Run 1: Center X = 5.1125, Y from 10.100 to 13.100 (10 treads * 300mm = 3000mm)
                    XYZ pt1Start = new XYZ(M(5.1125), M(10.100), 0);
                    XYZ pt1End = new XYZ(M(5.1125), M(13.100), 0);
                    Line line1 = Line.CreateBound(pt1Start, pt1End);
                    StairsRun run1 = StairsRun.CreateStraightRun(doc, stairsId, line1, StairsRunJustification.Center);
                    run1.ActualRunWidth = M(1.325);
                    run1Id = run1.Id;

                    // Landing elevation is at top of run1
                    double landingElev = run1.TopElevation;

                    // Run 2: Center X = 7.2875, Y from 13.100 down to 10.100
                    XYZ pt2Start = new XYZ(M(7.2875), M(13.100), landingElev);
                    XYZ pt2End = new XYZ(M(7.2875), M(10.100), landingElev);
                    Line line2 = Line.CreateBound(pt2Start, pt2End);
                    StairsRun run2 = StairsRun.CreateStraightRun(doc, stairsId, line2, StairsRunJustification.Center);
                    run2.ActualRunWidth = M(1.325);
                    // To have 21 total risers (11 in run1 + 10 in run2):
                    run2.EndsWithRiser = false;
                    run2Id = run2.Id;

                    // Sketched Landing matching CAD boundary (Y = 13.100 to 14.800, X = 4.450 to 7.950)
                    CurveLoop landingLoop = new CurveLoop();
                    XYZ p1 = new XYZ(M(4.450), M(13.100), landingElev);
                    XYZ p2 = new XYZ(M(4.450), M(14.800), landingElev);
                    XYZ p3 = new XYZ(M(7.950), M(14.800), landingElev);
                    XYZ p4 = new XYZ(M(7.950), M(13.100), landingElev);
                    landingLoop.Append(Line.CreateBound(p1, p2));
                    landingLoop.Append(Line.CreateBound(p2, p3));
                    landingLoop.Append(Line.CreateBound(p3, p4));
                    landingLoop.Append(Line.CreateBound(p4, p1));

                    StairsLanding landing = StairsLanding.CreateSketchedLanding(doc, stairsId, landingLoop, landingElev);
                    landingId = landing.Id;

                    t.Commit();
                }

                scope.Commit(prep);

                // Fetch final stair details
                var createdStairs = doc.GetElement(stairsId) as Stairs;
                return new {
                    success = true,
                    stairsId = stairsId.Value,
                    actualRisers = createdStairs?.ActualRisersNumber,
                    desiredRisers = createdStairs?.DesiredRisersNumber,
                    actualTreadDepthMm = (createdStairs?.ActualTreadDepth ?? 0) * 304.8,
                    actualRiserHeightMm = (createdStairs?.ActualRiserHeight ?? 0) * 304.8,
                    landingCreated = landingId != ElementId.InvalidElementId,
                    warnings = prep.Warnings
                };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.ToString(), warnings = prep.Warnings };
            }
        }
    }
}
