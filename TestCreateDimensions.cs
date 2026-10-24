using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCreateDimensions
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
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Find DimensionType: prefer "Linear Dimension Style" or "kt nam"
            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                .ToList();

            var dimType = dimTypes.FirstOrDefault(dt => dt.Name == "Linear Dimension Style") 
                       ?? dimTypes.FirstOrDefault(dt => dt.Name == "kt nam")
                       ?? dimTypes.First();

            // Find Grids
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var vGrids = new List<Grid>(); // vertical grids: 1 to 11
            var hGrids = new List<Grid>(); // horizontal grids: A to E

            foreach (var g in grids)
            {
                var p1 = g.Curve.GetEndPoint(0);
                var p2 = g.Curve.GetEndPoint(1);
                if (Math.Abs(p1.X - p2.X) < 0.01)
                {
                    vGrids.Add(g);
                }
                else if (Math.Abs(p1.Y - p2.Y) < 0.01)
                {
                    hGrids.Add(g);
                }
            }

            // Sort vertical grids by X
            vGrids = vGrids.OrderBy(g => g.Curve.GetEndPoint(0).X).ToList();
            // Sort horizontal grids by Y
            hGrids = hGrids.OrderBy(g => g.Curve.GetEndPoint(0).Y).ToList();

            var createdIds = new List<long>();

            using (var tx = new Transaction(doc, "Test Create Dimensions"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);

                tx.Start();

                // 1. South side: below Grid A (Y = 0)
                // Layer 1 (Overall: Grid 1 to 11) at Y = -3500 mm
                double yL1_South = -3500.0 * MM_TO_FT;
                var refL1_S = new ReferenceArray();
                refL1_S.Append(new Reference(vGrids.First()));
                refL1_S.Append(new Reference(vGrids.Last()));
                var lineL1_S = Line.CreateBound(
                    new XYZ(vGrids.First().Curve.GetEndPoint(0).X - 2.0, yL1_South, 0),
                    new XYZ(vGrids.Last().Curve.GetEndPoint(0).X + 2.0, yL1_South, 0)
                );
                var dimL1_S = doc.Create.NewDimension(view, lineL1_S, refL1_S, dimType);
                if (dimL1_S != null) createdIds.Add(dimL1_S.Id.Value);

                // Layer 2 (Grid-to-Grid: 1 to 11) at Y = -2300 mm
                double yL2_South = -2300.0 * MM_TO_FT;
                var refL2_S = new ReferenceArray();
                foreach (var g in vGrids) refL2_S.Append(new Reference(g));
                var lineL2_S = Line.CreateBound(
                    new XYZ(vGrids.First().Curve.GetEndPoint(0).X - 2.0, yL2_South, 0),
                    new XYZ(vGrids.Last().Curve.GetEndPoint(0).X + 2.0, yL2_South, 0)
                );
                var dimL2_S = doc.Create.NewDimension(view, lineL2_S, refL2_S, dimType);
                if (dimL2_S != null) createdIds.Add(dimL2_S.Id.Value);

                // 2. West side: left of Grid 1 (X = 550)
                // Layer 1 (Overall: Grid A to E) at X = -3500 mm (or further left of facade)
                // Facade minX is around -6274 mm! So West dims need to be outside facade!
                // Facade extends to -6300 mm. So Layer 1 at X = -9500 mm, Layer 2 at X = -8300 mm, Layer 3 at X = -7100 mm!
                double xL1_West = -9500.0 * MM_TO_FT;
                var refL1_W = new ReferenceArray();
                refL1_W.Append(new Reference(hGrids.First()));
                refL1_W.Append(new Reference(hGrids.Last()));
                var lineL1_W = Line.CreateBound(
                    new XYZ(xL1_West, hGrids.First().Curve.GetEndPoint(0).Y - 2.0, 0),
                    new XYZ(xL1_West, hGrids.Last().Curve.GetEndPoint(0).Y + 2.0, 0)
                );
                var dimL1_W = doc.Create.NewDimension(view, lineL1_W, refL1_W, dimType);
                if (dimL1_W != null) createdIds.Add(dimL1_W.Id.Value);

                // Layer 2 (Grid-to-Grid: A to E) at X = -8300 mm
                double xL2_West = -8300.0 * MM_TO_FT;
                var refL2_W = new ReferenceArray();
                foreach (var g in hGrids) refL2_W.Append(new Reference(g));
                var lineL2_W = Line.CreateBound(
                    new XYZ(xL2_West, hGrids.First().Curve.GetEndPoint(0).Y - 2.0, 0),
                    new XYZ(xL2_West, hGrids.Last().Curve.GetEndPoint(0).Y + 2.0, 0)
                );
                var dimL2_W = doc.Create.NewDimension(view, lineL2_W, refL2_W, dimType);
                if (dimL2_W != null) createdIds.Add(dimL2_W.Id.Value);

                tx.Commit();
            }

            return new {
                status = "Success",
                createdCount = createdIds.Count,
                createdIds,
                dimTypeName = dimType.Name
            };
        }
    }
}
