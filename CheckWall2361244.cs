using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckWall2361244
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var opt = new Options { ComputeReferences = true, View = view };
            var wall = doc.GetElement(new ElementId(2361244)) as Wall;
            if (wall == null) return new { error = "Wall not found" };

            var geom = wall.get_Geometry(opt);
            var xFaces = new List<double>();
            if (geom != null)
            {
                foreach (var g in geom)
                {
                    if (g is Solid s && s.Faces != null)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                            {
                                xFaces.Add(Math.Round(pf.Origin.X * FT_TO_MM, 0));
                            }
                        }
                    }
                }
            }

            return new { wallId = wall.Id.Value, wallName = wall.Name, xFaces = xFaces.Distinct().OrderBy(x => x) };
        }
    }
}
