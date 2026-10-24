using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDimensionRefs
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                var targetIds = new long[] { 2373764, 2373765, 2373805, 2373806, 2373713, 2373714, 2373744 };
                var dims = new List<object>();
                foreach (var id in targetIds)
                {
                    var d = famDoc.GetElement(new ElementId(id)) as Dimension;
                    if (d == null) continue;

                    var refElements = new List<object>();
                    foreach (Reference r in d.References)
                    {
                        var elem = famDoc.GetElement(r.ElementId);
                        refElements.Add(new
                        {
                            elemId = r.ElementId.Value,
                            elemType = elem?.GetType().Name,
                            name = elem?.Name
                        });
                    }

                    dims.Add(new
                    {
                        id = id,
                        valMm = (d.Value ?? 0) * 304.8,
                        isLocked = d.IsLocked,
                        refs = refElements
                    });
                }

                famDoc.Close(false);

                return new { dims };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
