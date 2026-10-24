using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSymbolicAndVisibility
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                // Check extrusions visibility
                var extVis = new List<object>();
                foreach (var ext in new FilteredElementCollector(famDoc).OfClass(typeof(Extrusion)).Cast<Extrusion>())
                {
                    var vis = ext.GetVisibility();
                    extVis.Add(new
                    {
                        id = ext.Id.Value,
                        isPlanVisible = vis.IsShownInPlanRCPCut,
                        isFine = vis.IsShownInFine,
                        isMedium = vis.IsShownInMedium,
                        isCoarse = vis.IsShownInCoarse
                    });
                }

                // Check Symbolic Lines
                var symLines = new List<object>();
                foreach (var sc in new FilteredElementCollector(famDoc).OfClass(typeof(CurveElement)).Cast<CurveElement>())
                {
                    var c = sc.GeometryCurve;
                    symLines.Add(new
                    {
                        id = sc.Id.Value,
                        type = sc.GetType().Name,
                        subCat = (sc as SymbolicCurve)?.Subcategory?.Name ?? sc.LineStyle?.Name ?? "none",
                        p0 = $"[{c.GetEndPoint(0).X * 304.8:F1}, {c.GetEndPoint(0).Y * 304.8:F1}, {c.GetEndPoint(0).Z * 304.8:F1}]",
                        p1 = $"[{c.GetEndPoint(1).X * 304.8:F1}, {c.GetEndPoint(1).Y * 304.8:F1}, {c.GetEndPoint(1).Z * 304.8:F1}]"
                    });
                }

                famDoc.Close(false);

                return new
                {
                    extVis = extVis,
                    symLineCount = symLines.Count,
                    symLines = symLines
                };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
