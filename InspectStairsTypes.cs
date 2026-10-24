using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairsTypes
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var doc = uiapp.ActiveUIDocument.Document;
                var stairTypes = new FilteredElementCollector(doc)
                    .WhereElementIsElementType()
                    .OfType<StairsType>()
                    .Select(t => new {
                        id = t.Id.Value,
                        name = t.Name,
                        maxRiserHeightMm = t.MaxRiserHeight * 304.8,
                        minTreadDepthMm = t.MinTreadDepth * 304.8,
                        minRunWidthMm = t.MinRunWidth * 304.8,
                        runType = doc.GetElement(t.get_Parameter(BuiltInParameter.STAIRSTYPE_RUN_TYPE)?.AsElementId())?.Name,
                        landingType = doc.GetElement(t.get_Parameter(BuiltInParameter.STAIRSTYPE_LANDING_TYPE)?.AsElementId())?.Name
                    })
                    .ToList();

                var existingStairs = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Stairs)
                    .WhereElementIsNotElementType()
                    .Cast<Stairs>()
                    .Select(s => new {
                        id = s.Id.Value,
                        name = s.Name,
                        actualRisers = s.ActualRisersNumber,
                        desiredRisers = s.DesiredRisersNumber,
                        actualTreadDepthMm = s.ActualTreadDepth * 304.8,
                        actualRiserHeightMm = s.ActualRiserHeight * 304.8
                    })
                    .ToList();

                return new { stairTypes, existingStairs };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
