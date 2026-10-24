using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpRevitColumnCoords
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var list = new List<object>();
            foreach (var c in cols)
            {
                var pt = (c.Location as LocationPoint)?.Point;
                if (pt != null)
                {
                    list.Add(new
                    {
                        id = c.Id.Value,
                        x = Math.Round(pt.X * 304.8, 1),
                        y = Math.Round(pt.Y * 304.8, 1),
                        baseLevel = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsValueString()
                    });
                }
            }

            var xs = list.Select(o => ((dynamic)o).x).Distinct().OrderBy(x => x).ToList();
            var ys = list.Select(o => ((dynamic)o).y).Distinct().OrderBy(y => y).ToList();

            return new { count = list.Count, xs, ys, list };
        }
    }
}
