using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTestBeamParams
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var sampleBeams = beams
                .GroupBy(b => {
                    var bb = b.get_BoundingBox(null);
                    double topZ = Math.Round((bb?.Max.Z ?? 0) * FT2M, 1);
                    return topZ;
                })
                .OrderBy(g => g.Key)
                .Select(g => {
                    var b = g.First();
                    var bb = b.get_BoundingBox(null);
                    var lvl = doc.GetElement(b.LevelId) as Level;
                    return new {
                        groupTopZM = g.Key,
                        count = g.Count(),
                        sampleId = b.Id.Value,
                        name = b.Name,
                        levelName = lvl?.Name,
                        zMinM = Math.Round((bb?.Min.Z ?? 0) * FT2M, 3),
                        zMaxM = Math.Round((bb?.Max.Z ?? 0) * FT2M, 3),
                        topOffsetMm = Math.Round((b.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE)?.AsDouble() ?? 0) * FT2M * 1000, 1),
                        elevationAtTopM = Math.Round((b.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP)?.AsDouble() ?? 0) * FT2M, 3),
                        elevationAtBottomM = Math.Round((b.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM)?.AsDouble() ?? 0) * FT2M, 3)
                    };
                })
                .ToList();

            return new { totalBeams = beams.Count, sampleBeams };
        }
    }
}
