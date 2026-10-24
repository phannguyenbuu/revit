using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCreateOneCallout
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

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
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No active ViewPlan" };

            // Check existing callout 2127444
            var existingCallout = doc.GetElement(new ElementId(2127444L)) as View;
            object existingInfo = null;
            if (existingCallout != null)
            {
                existingInfo = new {
                    id = existingCallout.Id.Value,
                    name = existingCallout.Name,
                    viewType = existingCallout.ViewType.ToString(),
                    vftId = existingCallout.GetTypeId().Value,
                    vftName = doc.GetElement(existingCallout.GetTypeId())?.Name,
                    cropMinMm = new {
                        x = existingCallout.CropBox.Min.X * FT_TO_MM,
                        y = existingCallout.CropBox.Min.Y * FT_TO_MM,
                        z = existingCallout.CropBox.Min.Z * FT_TO_MM
                    },
                    cropMaxMm = new {
                        x = existingCallout.CropBox.Max.X * FT_TO_MM,
                        y = existingCallout.CropBox.Max.Y * FT_TO_MM,
                        z = existingCallout.CropBox.Max.Z * FT_TO_MM
                    }
                };
            }

            // Test creating a callout for Item 2 (Stair 1: X: 3504 to 8720, Y: 7131 to 15618)
            // with Floor Plan VFT (49552)
            var floorPlanVft = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .FirstOrDefault(vft => vft.ViewFamily == ViewFamily.FloorPlan);

            if (floorPlanVft == null) return new { error = "No FloorPlan VFT" };

            XYZ p1 = new XYZ(3504.21 * MM_TO_FT, 7131.31 * MM_TO_FT, 0);
            XYZ p2 = new XYZ(8719.96 * MM_TO_FT, 15617.66 * MM_TO_FT, 0);

            long createdId = -1;
            string createdName = "";
            string createdViewType = "";

            using (var tx = new Transaction(doc, "Test Create Callout"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(opts);
                tx.Start();

                try
                {
                    var calloutView = ViewSection.CreateCallout(doc, view.Id, floorPlanVft.Id, p1, p2);
                    if (calloutView != null)
                    {
                        createdId = calloutView.Id.Value;
                        createdName = calloutView.Name;
                        createdViewType = calloutView.ViewType.ToString();
                    }
                    tx.Commit();
                }
                catch (Exception ex)
                {
                    tx.RollBack();
                    return new { error = ex.ToString(), existingInfo };
                }
            }

            return new {
                success = true,
                createdId,
                createdName,
                createdViewType,
                existingInfo
            };
        }
    }
}
