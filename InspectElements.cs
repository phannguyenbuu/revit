using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectElements
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // Check current selection first
            var selIds = uidoc.Selection.GetElementIds();
            var selList = new List<object>();
            foreach (var id in selIds)
            {
                var el = doc.GetElement(id);
                if (el != null)
                {
                    selList.Add(DescribeElement(el));
                }
            }

            // Also inspect candidate IDs from recent user clicks
            long[] candidateIds = new long[] { 2369925, 2369927, 2369930, 2395602, 2378823, 2369688, 2369740 };
            var candList = new List<object>();
            foreach (var cid in candidateIds)
            {
                var el = doc.GetElement(new ElementId(cid));
                if (el != null)
                {
                    candList.Add(DescribeElement(el));
                }
            }

            // Also get all levels in project
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = l.Id.Value, name = l.Name, elevation = l.Elevation * 304.8 })
                .ToList();

            return new
            {
                selection = selList,
                candidates = candList,
                levels = levels,
                activeView = uidoc.ActiveView?.Name
            };
        }

        private static object DescribeElement(Element el)
        {
            string baseLvl = el.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsValueString() ?? "None";
            string topLvl = el.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsValueString() ?? "Unconnected";
            double height = (el.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() ?? 0) * 304.8;
            double baseOffset = (el.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() ?? 0) * 304.8;
            double topOffset = (el.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() ?? 0) * 304.8;

            string curveStr = "";
            if (el.Location is LocationCurve lc)
            {
                var c = lc.Curve;
                var p0 = c.GetEndPoint(0) * 304.8;
                var p1 = c.GetEndPoint(1) * 304.8;
                curveStr = $"[{p0.X:F0}, {p0.Y:F0}, {p0.Z:F0}] -> [{p1.X:F0}, {p1.Y:F0}, {p1.Z:F0}]";
            }

            return new
            {
                id = el.Id.Value,
                name = el.Name,
                category = el.Category?.Name ?? "NoCat",
                className = el.GetType().Name,
                baseLevel = baseLvl,
                topLevel = topLvl,
                height = height,
                baseOffset = baseOffset,
                topOffset = topOffset,
                curve = curveStr
            };
        }
    }
}
