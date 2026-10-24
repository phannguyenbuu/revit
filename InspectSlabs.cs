using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSlabs
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var floors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .Cast<Floor>()
                .Select(f => {
                    var lvl = doc.GetElement(f.LevelId) as Level;
                    var pOff = f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;
                    var bb = f.get_BoundingBox(null);
                    double zMin = bb != null ? bb.Min.Z * FT2M : 0;
                    double zMax = bb != null ? bb.Max.Z * FT2M : 0;

                    return new {
                        id = f.Id.Value,
                        name = f.Name,
                        level = lvl?.Name ?? "Unknown",
                        levelElevM = lvl != null ? Math.Round(lvl.Elevation * FT2M, 3) : 0,
                        offsetMm = Math.Round(pOff, 1),
                        zMinM = Math.Round(zMin, 3),
                        zMaxM = Math.Round(zMax, 3)
                    };
                })
                .ToList();

            return new { count = floors.Count, floors };
        }
    }
}
