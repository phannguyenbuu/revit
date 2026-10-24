using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestRebuildZeroDim
    {
        private const double FT_TO_MM = 304.8;

        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Dim 2409100 on View 312
            var d = doc.GetElement(new ElementId(2409100L)) as Dimension;
            if (d == null) return new { error = "Dim not found" };

            var view = doc.GetElement(d.OwnerViewId) as View;
            var line = d.Curve as Line;
            var dt = d.DimensionType;
            var refs = d.References;

            // Find which segments have value 0
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
                }
            }

            // Filter references: if segment i is 0, omit reference i+1 (duplicate)
            var newRefArray = new ReferenceArray();
            int refIdx = 0;
            for (int i = 0; i < refs.Size; i++)
            {
                var r = refs.get_Item(i);
                // If this reference is the end of a 0-segment, skip it
                if (i > 0 && zeroIndices.Contains(i - 1))
                {
                    // Skip duplicate reference
                    continue;
                }
                newRefArray.Append(r);
                refIdx++;
            }

            Dimension newDim = null;
            using (var tx = new Transaction(doc, "Test Rebuild Dim Without Zero"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(opts);
                tx.Start();

                try
                {
                    newDim = doc.Create.NewDimension(view, line, newRefArray, dt);
                    // if successful, delete old dim
                    doc.Delete(d.Id);
                    tx.Commit();
                }
                catch (Exception ex)
                {
                    tx.RollBack();
                    return new { error = ex.Message };
                }
            }

            var segs = new List<double>();
            if (newDim != null)
            {
                if (newDim.Segments != null && newDim.Segments.Size > 0)
                {
                    foreach (DimensionSegment s in newDim.Segments)
                    {
                        if (s.Value.HasValue) segs.Add(Math.Round(s.Value.Value * FT_TO_MM, 1));
                    }
                }
                else if (newDim.Value.HasValue)
                {
                    segs.Add(Math.Round(newDim.Value.Value * FT_TO_MM, 1));
                }
            }

            return new
            {
                success = true,
                newDimId = newDim?.Id.Value,
                newSegCount = newDim?.NumberOfSegments,
                hasZero = segs.Any(x => x == 0.0),
                segs
            };
        }
    }
}
