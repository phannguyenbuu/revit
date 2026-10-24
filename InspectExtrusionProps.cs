using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExtrusionProps
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                var targetIds = new long[] { 2373653, 2373672, 2373697, 2373857 };
                var list = new List<object>();

                foreach (var id in targetIds)
                {
                    var ext = famDoc.GetElement(new ElementId(id)) as Extrusion;
                    if (ext == null) continue;

                    var paramMap = new Dictionary<string, string>();
                    foreach (Parameter p in ext.Parameters)
                    {
                        if (p.HasValue)
                        {
                            paramMap[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString();
                        }
                    }

                    // Check family parameter associations
                    var associations = new Dictionary<string, string>();
                    foreach (Parameter p in ext.Parameters)
                    {
                        var fp = famDoc.FamilyManager.GetAssociatedFamilyParameter(p);
                        if (fp != null)
                        {
                            associations[p.Definition.Name] = fp.Definition.Name;
                        }
                    }

                    list.Add(new
                    {
                        id = id,
                        subCategory = ext.Subcategory?.Name ?? "none",
                        paramMap = paramMap,
                        associations = associations
                    });
                }

                famDoc.Close(false);

                return new { extrusions = list };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
