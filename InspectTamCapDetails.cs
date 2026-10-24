using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTamCapDetails
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var doc = uiapp.ActiveUIDocument?.Document;
                var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No view" };

                var ftBac = doc.GetElement(new ElementId(1196262L)) as FloorType;
                double thick = 0;
                var cs = ftBac?.GetCompoundStructure();
                if (cs != null)
                {
                    thick = cs.GetWidth() * 304.8;
                }

                // Check materials of ftBac
                var matNames = cs?.GetLayers().Select(l => {
                    var m = doc.GetElement(l.MaterialId) as Material;
                    return new { name = m?.Name, width = l.Width * 304.8 };
                }).ToList();

                // Check wall near X=37250, Y in [5000, 8000]
                var walls = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w => {
                        var lc = w.Location as LocationCurve;
                        if (lc == null) return false;
                        var p1 = lc.Curve.GetEndPoint(0) * 304.8;
                        var p2 = lc.Curve.GetEndPoint(1) * 304.8;
                        return (Math.Abs(p1.X - 37150) < 500 || Math.Abs(p2.X - 37150) < 500)
                            && (p1.Y >= 4000 && p1.Y <= 9000 || p2.Y >= 4000 && p2.Y <= 9000);
                    })
                    .Select(w => new {
                        id = w.Id.Value,
                        name = w.Name,
                        type = w.WallType.Name
                    })
                    .ToList();

                return new
                {
                    ftBacName = ftBac?.Name,
                    thickness = thick,
                    layers = matNames,
                    walls = walls
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
