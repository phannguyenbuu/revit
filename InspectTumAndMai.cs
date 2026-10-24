using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTumAndMai
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            long[] viewIds = new long[] { 931687L, 2370740L, 1234140L };
            var list = new List<object>();

            foreach (var vid in viewIds)
            {
                var v = doc.GetElement(new ElementId(vid)) as ViewPlan;
                if (v == null) continue;

                var walls = new FilteredElementCollector(doc, v.Id)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Count();

                var dims = new FilteredElementCollector(doc, v.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .Count();

                var doors = new FilteredElementCollector(doc, v.Id)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .Count();

                var floors = new FilteredElementCollector(doc, v.Id)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .Count();

                list.Add(new {
                    id = v.Id.Value,
                    name = v.Name,
                    levelName = v.GenLevel?.Name,
                    walls,
                    dims,
                    doors,
                    floors
                });
            }

            return new { views = list };
        }
    }
}
