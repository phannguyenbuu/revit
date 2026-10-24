using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestDimCopyIndividual
    {
        public class CopyWarningSwallower : IFailuresPreprocessor
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
            if (doc == null) return new { error = "No doc" };

            var v1 = doc.GetElement(new ElementId(312)) as ViewPlan;
            var v2 = doc.GetElement(new ElementId(695)) as ViewPlan;

            var v1Dims = new FilteredElementCollector(doc, v1.Id)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .ToList();

            var results = new List<object>();

            using (var tx = new Transaction(doc, "Test Copy Each Dim"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new CopyWarningSwallower());
                tx.SetFailureHandlingOptions(opts);
                tx.Start();

                foreach (var d in v1Dims)
                {
                    try
                    {
                        var cpOpts = new CopyPasteOptions();
                        var copied = ElementTransformUtils.CopyElements(v1, new List<ElementId> { d.Id }, v2, null, cpOpts);
                        results.Add(new {
                            id = d.Id.Value,
                            segs = d.NumberOfSegments,
                            success = true,
                            copiedCount = copied.Count
                        });
                    }
                    catch (Exception ex)
                    {
                        results.Add(new {
                            id = d.Id.Value,
                            segs = d.NumberOfSegments,
                            success = false,
                            error = ex.Message
                        });
                    }
                }

                tx.RollBack();
            }

            return results;
        }
    }
}
