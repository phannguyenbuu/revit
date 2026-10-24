using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairReferences
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var stairs = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Stairs))
                .Cast<Stairs>()
                .ToList();

            var list = new List<object>();
            var opt = new Options { ComputeReferences = true, View = view };

            foreach (var st in stairs)
            {
                var runs = st.GetStairsRuns().Select(id => doc.GetElement(id) as StairsRun).ToList();
                var landings = st.GetStairsLandings().Select(id => doc.GetElement(id) as StairsLanding).ToList();
                var runInfo = runs.Select(r => {
                    var bb = r?.get_BoundingBox(view);
                    return new {
                        id = r?.Id.Value,
                        minX = bb != null ? Math.Round(bb.Min.X * FT_TO_MM, 0) : 0,
                        maxX = bb != null ? Math.Round(bb.Max.X * FT_TO_MM, 0) : 0,
                        minY = bb != null ? Math.Round(bb.Min.Y * FT_TO_MM, 0) : 0,
                        maxY = bb != null ? Math.Round(bb.Max.Y * FT_TO_MM, 0) : 0
                    };
                }).ToList();

                list.Add(new {
                    stairId = st.Id.Value,
                    name = st.Name,
                    runs = runInfo
                });
            }

            return list;
        }
    }
}
