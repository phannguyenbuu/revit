using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestDetailDims
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

            var results = new List<string>();

            // Test A: Can we dim between door Left and Right references?
            var southWindow = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .FirstOrDefault(w => (w.Location as LocationPoint)?.Point.Y * 304.8 < 2000 && w.Symbol.FamilyName.Contains("CUA SO"));

            if (southWindow != null)
            {
                var leftRefs = southWindow.GetReferences(FamilyInstanceReferenceType.Left);
                var rightRefs = southWindow.GetReferences(FamilyInstanceReferenceType.Right);
                var centerRefs = southWindow.GetReferences(FamilyInstanceReferenceType.CenterLeftRight);

                results.Add($"Window {southWindow.Id}: Left={leftRefs.Count}, Right={rightRefs.Count}, Center={centerRefs.Count}");

                if (leftRefs.Count > 0 && rightRefs.Count > 0)
                {
                    using (var tx = new Transaction(doc, "Test Window Dim"))
                    {
                        tx.Start();
                        var refArr = new ReferenceArray();
                        refArr.Append(leftRefs[0]);
                        refArr.Append(rightRefs[0]);

                        var pt = (southWindow.Location as LocationPoint).Point;
                        var line = Line.CreateBound(
                            new XYZ(pt.X - 3.0, -1200.0 * MM_TO_FT, 0),
                            new XYZ(pt.X + 3.0, -1200.0 * MM_TO_FT, 0)
                        );
                        try
                        {
                            var d = doc.Create.NewDimension(view, line, refArr, dimType);
                            results.Add($"Window width dim success: ID = {d.Id.Value}, val = {d.Value * 304.8}");
                        }
                        catch (Exception ex)
                        {
                            results.Add($"Window width dim failed: {ex.Message}");
                        }
                        tx.RollBack();
                    }
                }
            }

            // Test B: Floor side faces (Tam Cap steps)
            var floor = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .FirstOrDefault(f => f.Name == "BAC");

            if (floor != null)
            {
                var opt = new Options { ComputeReferences = true, View = view };
                var geom = floor.get_Geometry(opt);
                var xFaces = new List<PlanarFace>();
                if (geom != null)
                {
                    foreach (var obj in geom)
                    {
                        if (obj is Solid s && s.Faces != null)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                {
                                    xFaces.Add(pf);
                                }
                            }
                        }
                    }
                }
                results.Add($"Floor {floor.Id} vertical X faces: {xFaces.Count}");

                if (xFaces.Count >= 2)
                {
                    using (var tx = new Transaction(doc, "Test Floor Dim"))
                    {
                        tx.Start();
                        var refArr = new ReferenceArray();
                        refArr.Append(xFaces[0].Reference);
                        refArr.Append(xFaces[1].Reference);

                        var line = Line.CreateBound(
                            new XYZ(37000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0),
                            new XYZ(40000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0)
                        );
                        try
                        {
                            var d = doc.Create.NewDimension(view, line, refArr, dimType);
                            results.Add($"Floor step dim success: ID = {d.Id.Value}, val = {d.Value * 304.8}");
                        }
                        catch (Exception ex)
                        {
                            results.Add($"Floor step dim failed: {ex.Message}");
                        }
                        tx.RollBack();
                    }
                }
            }

            return new { results };
        }
    }
}
