using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairs
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var stairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .Select(s => {
                    var bLvlId = s.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)?.AsElementId();
                    var tLvlId = s.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)?.AsElementId();
                    var bLvl = bLvlId != null && bLvlId != ElementId.InvalidElementId ? doc.GetElement(bLvlId) as Level : null;
                    var tLvl = tLvlId != null && tLvlId != ElementId.InvalidElementId ? doc.GetElement(tLvlId) as Level : null;
                    var runs = s.GetStairsRuns().Select(rid => {
                        var r = doc.GetElement(rid) as StairsRun;
                        return new {
                            runId = rid.Value,
                            actualRisers = r?.ActualRisersNumber,
                            actualTreads = r?.ActualTreadsNumber,
                            topElevM = r != null ? Math.Round(r.TopElevation * FT2M, 3) : 0,
                            baseElevM = r != null ? Math.Round(r.BaseElevation * FT2M, 3) : 0
                        };
                    }).ToList();

                    return new {
                        id = s.Id.Value,
                        name = s.Name,
                        baseLevel = bLvl?.Name,
                        baseLevelId = bLvlId?.Value,
                        topLevel = tLvl?.Name,
                        topLevelId = tLvlId?.Value,
                        actualRisers = s.ActualRisersNumber,
                        desiredRisers = s.DesiredRisersNumber,
                        actualRiserHeightMm = Math.Round(s.ActualRiserHeight * FT2M * 1000.0, 1),
                        heightMm = Math.Round(s.Height * FT2M * 1000.0, 1),
                        runs
                    };
                })
                .ToList();

            return new { stairsCount = stairs.Count, stairs };
        }
    }
}
