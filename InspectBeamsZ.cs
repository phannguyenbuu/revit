using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBeamsZ
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
                .Select(b => {
                    var pRef = b.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM);
                    var lvl = pRef != null && pRef.AsElementId() != ElementId.InvalidElementId
                        ? doc.GetElement(pRef.AsElementId()) as Level : null;

                    var lc = b.Location as LocationCurve;
                    var c = lc?.Curve;
                    var z0 = c != null ? c.GetEndPoint(0).Z * FT2M : 0;
                    var z1 = c != null ? c.GetEndPoint(1).Z * FT2M : 0;

                    var pZOff = b.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE)?.AsDouble() * FT2M * 1000 ?? 0;
                    var p0Off = b.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION)?.AsDouble() * FT2M * 1000 ?? 0;
                    var p1Off = b.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION)?.AsDouble() * FT2M * 1000 ?? 0;

                    return new {
                        id = b.Id.Value,
                        level = lvl?.Name ?? "Unknown",
                        levelElevM = lvl != null ? Math.Round(lvl.Elevation * FT2M, 3) : 0,
                        z0M = Math.Round(z0, 3),
                        z1M = Math.Round(z1, 3),
                        zOffMm = Math.Round(pZOff, 1),
                        p0OffMm = Math.Round(p0Off, 1),
                        p1OffMm = Math.Round(p1Off, 1)
                    };
                })
                .ToList();

            var grouped = beams
                .GroupBy(b => b.level)
                .Select(g => new {
                    level = g.Key,
                    count = g.Count(),
                    levelElevM = g.First().levelElevM,
                    z0M = g.Select(b => b.z0M).Distinct().ToList(),
                    p0OffMm = g.Select(b => b.p0OffMm).Distinct().ToList()
                })
                .ToList();

            return new { totalBeams = beams.Count, grouped };
        }
    }
}
