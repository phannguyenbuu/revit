import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Let's write an InspectAllColumns script to run dynamically in Revit
code = '''
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCurrentColumns
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var structCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(c => new
                {
                    id = c.Id.Value,
                    name = c.Name,
                    symName = c.Symbol.Name,
                    familyName = c.Symbol.FamilyName,
                    loc = c.Location is LocationPoint lp ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null
                })
                .ToList();

            var archCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Columns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(c => new
                {
                    id = c.Id.Value,
                    name = c.Name,
                    symName = c.Symbol.Name,
                    familyName = c.Symbol.FamilyName,
                    loc = c.Location is LocationPoint lp ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null
                })
                .ToList();

            return new
            {
                structColumnsCount = structCols.Count,
                structColumns = structCols,
                archColumnsCount = archCols.Count,
                archColumns = archCols
            };
        }
    }
}
'''
with open("InspectCurrentColumns.cs", "w", encoding="utf-8") as f:
    f.write(code)

print("Wrote InspectCurrentColumns.cs")
