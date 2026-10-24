using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllBeams
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var list = new List<object>();
            var levelGroups = new Dictionary<string, int>();

            foreach (var b in beams)
            {
                var bb = b.get_BoundingBox(null);
                var lvlName = doc.GetElement(b.LevelId)?.Name ?? "No Level";
                if (!levelGroups.ContainsKey(lvlName)) levelGroups[lvlName] = 0;
                levelGroups[lvlName]++;

                var pStartOff = b.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION);
                var pEndOff = b.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION);
                var pZOff = b.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                var pZJust = b.get_Parameter(BuiltInParameter.Z_JUSTIFICATION);

                list.Add(new {
                    id = b.Id.Value,
                    name = b.Name,
                    sym = b.Symbol.Name,
                    level = lvlName,
                    zJust = pZJust?.AsValueString() ?? pZJust?.AsInteger().ToString(),
                    zOffsetMm = pZOff != null ? pZOff.AsDouble() * FT2MM : 0.0,
                    startElevMm = pStartOff != null ? pStartOff.AsDouble() * FT2MM : 0.0,
                    endElevMm = pEndOff != null ? pEndOff.AsDouble() * FT2MM : 0.0,
                    minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                    maxZ = bb != null ? bb.Max.Z * FT2MM : 0
                });
            }

            return new {
                totalBeams = beams.Count,
                levelGroups,
                sample = list.Take(10).ToList()
            };
        }
    }
}
