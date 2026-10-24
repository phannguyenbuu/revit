using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectOpeningElement
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                var openings = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Opening))
                    .Cast<Opening>()
                    .ToList();

                var opList = new List<object>();
                foreach (var op in openings)
                {
                    var curves = new List<string>();
                    try
                    {
                        foreach (Curve c in op.BoundaryCurves)
                        {
                            curves.Add($"{c.GetType().Name}: [{c.GetEndPoint(0).X * 304.8:F1}, {c.GetEndPoint(0).Y * 304.8:F1}, {c.GetEndPoint(0).Z * 304.8:F1}] -> [{c.GetEndPoint(1).X * 304.8:F1}, {c.GetEndPoint(1).Y * 304.8:F1}, {c.GetEndPoint(1).Z * 304.8:F1}]");
                        }
                    }
                    catch (Exception ex)
                    {
                        curves.Add("Err: " + ex.Message);
                    }

                    opList.Add(new
                    {
                        id = op.Id.Value,
                        isTransparentIn3D = op.IsTransparentIn3D,
                        isTransparentInElevation = op.IsTransparentInElevation,
                        curves = curves
                    });
                }

                famDoc.Close(false);

                return new { openings = opList };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
