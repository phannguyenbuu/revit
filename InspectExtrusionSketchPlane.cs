using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExtrusionSketchPlane
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                var targetIds = new long[] { 2373653, 2373672, 2373697, 2373857 };
                var res = new List<object>();

                foreach (var id in targetIds)
                {
                    var ext = famDoc.GetElement(new ElementId(id)) as Extrusion;
                    if (ext == null) continue;

                    var sp = ext.Sketch?.SketchPlane;
                    var plane = sp?.GetPlane();

                    res.Add(new
                    {
                        id = id,
                        spId = sp?.Id.Value,
                        spName = sp?.Name,
                        origin = plane != null ? $"[{plane.Origin.X*304.8:F1}, {plane.Origin.Y*304.8:F1}, {plane.Origin.Z*304.8:F1}]" : "null",
                        normal = plane != null ? $"[{plane.Normal.X:F3}, {plane.Normal.Y:F3}, {plane.Normal.Z:F3}]" : "null",
                        xVec = plane != null ? $"[{plane.XVec.X:F3}, {plane.XVec.Y:F3}, {plane.XVec.Z:F3}]" : "null",
                        yVec = plane != null ? $"[{plane.YVec.X:F3}, {plane.YVec.Y:F3}, {plane.YVec.Z:F3}]" : "null"
                    });
                }

                famDoc.Close(false);
                return new { extrusions = res };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
