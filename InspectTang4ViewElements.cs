using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTang4ViewElements
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var v4 = doc.GetElement(new ElementId(931687L)) as ViewPlan;
            if (v4 == null) return new { error = "View 931687 not found" };

            var els = new FilteredElementCollector(doc, v4.Id)
                .WhereElementIsNotElementType()
                .Select(e => new {
                    id = e.Id.Value,
                    cat = e.Category?.Name,
                    name = e.Name
                })
                .ToList();

            var catCounts = els.GroupBy(e => e.cat ?? "None").ToDictionary(g => g.Key, g => g.Count());

            // Check walls in whole doc on Level 4
            var l4_1 = doc.GetElement(new ElementId(2360634L)) as Level;
            var l4_2 = doc.GetElement(new ElementId(931615L)) as Level;

            var walls1 = l4_1 != null ? new FilteredElementCollector(doc).OfClass(typeof(Wall)).Cast<Wall>().Where(w => w.LevelId == l4_1.Id).Count() : 0;
            var walls2 = l4_2 != null ? new FilteredElementCollector(doc).OfClass(typeof(Wall)).Cast<Wall>().Where(w => w.LevelId == l4_2.Id).Count() : 0;

            // Check if any view has GenLevel == l4_1
            var v_l4_1 = l4_1 != null ? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().Where(v => v.GenLevel?.Id == l4_1.Id).Select(v => new { id = v.Id.Value, name = v.Name }).ToList() : null;
            var v_l4_2 = l4_2 != null ? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().Where(v => v.GenLevel?.Id == l4_2.Id).Select(v => new { id = v.Id.Value, name = v.Name }).ToList() : null;

            return new {
                catCountsInView931687 = catCounts,
                wallsOnLevel2360634 = walls1,
                wallsOnLevel931615 = walls2,
                viewsForLevel2360634 = v_l4_1,
                viewsForLevel931615 = v_l4_2
            };
        }
    }
}
