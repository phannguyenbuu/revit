using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllExistingStairs
    {
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var stairsList = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .ToList();

            var result = new List<object>();

            foreach (var s in stairsList)
            {
                var bb = s.get_BoundingBox(null);
                var baseLevelId = s.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL)?.AsElementId();
                var topLevelId = s.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL)?.AsElementId();
                var baseOffset = s.get_Parameter(BuiltInParameter.STAIRS_BASE_OFFSET)?.AsDouble() ?? 0;
                var topOffset = s.get_Parameter(BuiltInParameter.STAIRS_TOP_OFFSET)?.AsDouble() ?? 0;

                string baseName = baseLevelId != null && baseLevelId != ElementId.InvalidElementId ? doc.GetElement(baseLevelId)?.Name : "None";
                string topName = topLevelId != null && topLevelId != ElementId.InvalidElementId ? doc.GetElement(topLevelId)?.Name : "None";

                var runs = s.GetStairsRuns()
                    .Select(id => doc.GetElement(id) as StairsRun)
                    .Where(r => r != null)
                    .Select(r => new {
                        id = r.Id.Value,
                        risers = r.ActualRisersNumber,
                        treads = r.ActualTreadsNumber,
                        baseElev = ToM(r.BaseElevation),
                        topElev = ToM(r.TopElevation)
                    }).ToList();

                var landings = s.GetStairsLandings()
                    .Select(id => doc.GetElement(id) as StairsLanding)
                    .Where(l => l != null)
                    .Select(l => new {
                        id = l.Id.Value,
                        baseElev = ToM(l.BaseElevation)
                    }).ToList();

                result.Add(new
                {
                    id = s.Id.Value,
                    name = s.Name,
                    typeName = doc.GetElement(s.GetTypeId())?.Name,
                    baseLevel = baseName,
                    baseLevelId = baseLevelId?.Value,
                    topLevel = topName,
                    topLevelId = topLevelId?.Value,
                    baseOffsetM = ToM(baseOffset),
                    topOffsetM = ToM(topOffset),
                    min = bb != null ? new { x = Math.Round(ToM(bb.Min.X), 2), y = Math.Round(ToM(bb.Min.Y), 2), z = Math.Round(ToM(bb.Min.Z), 2) } : null,
                    max = bb != null ? new { x = Math.Round(ToM(bb.Max.X), 2), y = Math.Round(ToM(bb.Max.Y), 2), z = Math.Round(ToM(bb.Max.Z), 2) } : null,
                    runsCount = runs.Count,
                    landingsCount = landings.Count,
                    runs,
                    landings
                });
            }

            return new { count = stairsList.Count, stairs = result };
        }
    }
}
