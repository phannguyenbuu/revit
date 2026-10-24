using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCreatedStair
    {
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var stairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .FirstOrDefault();

            if (stairs == null)
                return new { error = "No stairs found" };

            var runs = stairs.GetStairsRuns()
                .Select(id => doc.GetElement(id) as StairsRun)
                .Where(r => r != null)
                .Select(r => new {
                    id = r.Id.Value,
                    actualRisers = r.ActualRisersNumber,
                    actualTreads = r.ActualTreadsNumber,
                    baseElevationM = ToM(r.BaseElevation),
                    topElevationM = ToM(r.TopElevation),
                    widthM = ToM(r.ActualRunWidth),
                    beginsWithRiser = r.BeginsWithRiser,
                    endsWithRiser = r.EndsWithRiser
                })
                .ToList();

            var landings = stairs.GetStairsLandings()
                .Select(id => doc.GetElement(id) as StairsLanding)
                .Where(l => l != null)
                .Select(l => {
                    var curves = l.GetFootprintBoundary();
                    var pts = new System.Collections.Generic.List<object>();
                    if (curves != null)
                    {
                        foreach (Curve c in curves)
                        {
                            pts.Add(new {
                                start = new { x = ToM(c.GetEndPoint(0).X), y = ToM(c.GetEndPoint(0).Y) },
                                end = new { x = ToM(c.GetEndPoint(1).X), y = ToM(c.GetEndPoint(1).Y) }
                            });
                        }
                    }
                    return new {
                        id = l.Id.Value,
                        baseElevationM = ToM(l.BaseElevation),
                        thicknessM = ToM(l.Thickness),
                        isAutomatic = l.IsAutomaticLanding,
                        boundaryCurves = pts
                    };
                })
                .ToList();

            return new {
                stairsId = stairs.Id.Value,
                actualRisers = stairs.ActualRisersNumber,
                desiredRisers = stairs.DesiredRisersNumber,
                runs,
                landings
            };
        }
    }
}
