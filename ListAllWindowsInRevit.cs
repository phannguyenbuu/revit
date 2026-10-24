using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListAllWindowsInRevit
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var doc = uiapp.ActiveUIDocument?.Document;
                if (doc == null) return new { error = "No doc" };

                var windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Select(w =>
                    {
                        var loc = (w.Location as LocationPoint)?.Point;
                        var bb = w.get_BoundingBox(null);
                        return new
                        {
                            id = w.Id.Value,
                            fam = w.Symbol.FamilyName,
                            sym = w.Symbol.Name,
                            level = doc.GetElement(w.LevelId)?.Name,
                            loc = loc != null ? new { x = Math.Round(loc.X * FT2M, 3), y = Math.Round(loc.Y * FT2M, 3), z = Math.Round(loc.Z * FT2M, 3) } : null,
                            bbZ = bb != null ? new { minZ = Math.Round(bb.Min.Z * FT2M, 3), maxZ = Math.Round(bb.Max.Z * FT2M, 3) } : null
                        };
                    })
                    .OrderBy(w => w.loc?.z ?? 0)
                    .ThenBy(w => w.loc?.x ?? 0)
                    .ToList();

                return new { totalWindows = windows.Count, windows };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
