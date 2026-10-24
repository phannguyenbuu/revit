using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckCurrentSelection
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                var selIds = uidoc.Selection.GetElementIds();
                var items = selIds.Select(id =>
                {
                    var elem = doc.GetElement(id);
                    var bb = elem?.get_BoundingBox(null);
                    return new
                    {
                        id = id.Value,
                        category = elem?.Category?.Name,
                        builtInCat = elem?.Category != null ? ((BuiltInCategory)elem.Category.Id.Value).ToString() : null,
                        name = elem?.Name,
                        type = (elem as FamilyInstance)?.Symbol?.Name ?? (elem as Wall)?.WallType?.Name,
                        bbMin = bb != null ? new { x = Math.Round(bb.Min.X * FT2M, 3), y = Math.Round(bb.Min.Y * FT2M, 3), z = Math.Round(bb.Min.Z * FT2M, 3) } : null,
                        bbMax = bb != null ? new { x = Math.Round(bb.Max.X * FT2M, 3), y = Math.Round(bb.Max.Y * FT2M, 3), z = Math.Round(bb.Max.Z * FT2M, 3) } : null
                    };
                }).ToList();

                return new
                {
                    success = true,
                    count = selIds.Count,
                    elements = items
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
