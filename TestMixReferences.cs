using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestMixReferences
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var dimType = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .FirstOrDefault(dt => dt.Name == "Linear Dimension Style")
                ?? new FilteredElementCollector(doc).OfClass(typeof(DimensionType)).Cast<DimensionType>().First();

            var g1 = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().First(g => g.Name == "1");
            var g2 = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().First(g => g.Name == "2");

            try
            {
                long dimId = 0;
                using (var tx = new Transaction(doc, "Test Mix Ref"))
                {
                    tx.Start();

                    // ReferencePlane in between at X = 2000
                    XYZ p1 = new XYZ(2000.0 * MM_TO_FT, 2000.0 * MM_TO_FT, 0);
                    XYZ p2 = new XYZ(2000.0 * MM_TO_FT, 4000.0 * MM_TO_FT, 0);
                    var rp = doc.Create.NewReferencePlane(p1, p2, XYZ.BasisZ, view);

                    var refArr = new ReferenceArray();
                    refArr.Append(new Reference(g1));
                    refArr.Append(rp.GetReference());
                    refArr.Append(new Reference(g2));

                    var dimLine = Line.CreateBound(
                        new XYZ(0, 3000.0 * MM_TO_FT, 0),
                        new XYZ(5000.0 * MM_TO_FT, 3000.0 * MM_TO_FT, 0)
                    );

                    var dim = doc.Create.NewDimension(view, dimLine, refArr, dimType);
                    if (dim != null) dimId = dim.Id.Value;

                    tx.RollBack();
                }

                return new { success = dimId != 0, dimId };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
