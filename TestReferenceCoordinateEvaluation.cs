using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestReferenceCoordinateEvaluation
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. Check a window
            var win = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            var winRefs = new List<object>();
            if (win != null)
            {
                var left = win.GetReferences(FamilyInstanceReferenceType.Left);
                var right = win.GetReferences(FamilyInstanceReferenceType.Right);
                var center = win.GetReferences(FamilyInstanceReferenceType.CenterLeftRight);
                winRefs.Add(new {
                    name = win.Name,
                    leftCount = left.Count,
                    rightCount = right.Count,
                    centerCount = center.Count
                });
            }

            // 2. Check a door
            var door = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            var doorRefs = new List<object>();
            if (door != null)
            {
                var left = door.GetReferences(FamilyInstanceReferenceType.Left);
                var right = door.GetReferences(FamilyInstanceReferenceType.Right);
                var center = door.GetReferences(FamilyInstanceReferenceType.CenterLeftRight);
                doorRefs.Add(new {
                    name = door.Name,
                    leftCount = left.Count,
                    rightCount = right.Count,
                    centerCount = center.Count
                });
            }

            // 3. Check stair runs
            var stairs = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_StairsRuns)
                .Cast<Element>()
                .ToList();

            var stairList = new List<object>();
            var opt = new Options { ComputeReferences = true, View = view };
            foreach (var s in stairs)
            {
                var geom = s.get_Geometry(opt);
                var xFaces = new List<double>();
                if (geom != null)
                {
                    foreach (var g in geom)
                    {
                        if (g is Solid sol && sol.Faces != null)
                        {
                            foreach (Face f in sol.Faces)
                            {
                                if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                {
                                    xFaces.Add(Math.Round(pf.Origin.X * FT_TO_MM, 1));
                                }
                            }
                        }
                    }
                }
                stairList.Add(new { name = s.Name, id = s.Id.Value, xFaces });
            }

            return new { winRefs, doorRefs, stairList };
        }
    }
}
