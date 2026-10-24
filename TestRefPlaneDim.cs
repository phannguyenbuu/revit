using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestRefPlaneDim
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

            try
            {
                long dimId = 0;
                using (var tx = new Transaction(doc, "Test RefPlane Dim"))
                {
                    tx.Start();

                    // Create 2 vertical reference planes at X = 37250 and X = 39550
                    XYZ p1_start = new XYZ(37250.0 * MM_TO_FT, 4000.0 * MM_TO_FT, 0);
                    XYZ p1_end = new XYZ(37250.0 * MM_TO_FT, 9000.0 * MM_TO_FT, 0);
                    XYZ p2_start = new XYZ(39550.0 * MM_TO_FT, 4000.0 * MM_TO_FT, 0);
                    XYZ p2_end = new XYZ(39550.0 * MM_TO_FT, 9000.0 * MM_TO_FT, 0);

                    var rp1 = doc.Create.NewReferencePlane(p1_start, p1_end, XYZ.BasisZ, view);
                    var rp2 = doc.Create.NewReferencePlane(p2_start, p2_end, XYZ.BasisZ, view);

                    var refArr = new ReferenceArray();
                    refArr.Append(rp1.GetReference());
                    refArr.Append(rp2.GetReference());

                    var dimLine = Line.CreateBound(
                        new XYZ(37000.0 * MM_TO_FT, 4500.0 * MM_TO_FT, 0),
                        new XYZ(40000.0 * MM_TO_FT, 4500.0 * MM_TO_FT, 0)
                    );

                    var dim = doc.Create.NewDimension(view, dimLine, refArr, dimType);
                    if (dim != null) dimId = dim.Id.Value;

                    tx.RollBack(); // just testing
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
