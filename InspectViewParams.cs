using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectViewParams
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var currentOrg = BrowserOrganization.GetCurrentBrowserOrganizationForViews(doc);
            
            // Collect sample views: one floor plan, one section, one detail
            long[] sampleIds = new long[] { 312L, 749996L, 1286610L, 2304952L };
            var list = new List<object>();
            foreach (var id in sampleIds)
            {
                var v = doc.GetElement(new ElementId(id)) as View;
                if (v == null) continue;
                var pList = new List<object>();
                foreach (Parameter p in v.Parameters)
                {
                    if (p.HasValue)
                    {
                        string val = p.AsValueString() ?? p.AsString();
                        if (!string.IsNullOrEmpty(val))
                        {
                            pList.Add(new { name = p.Definition.Name, val = val });
                        }
                    }
                }
                list.Add(new {
                    id = id,
                    name = v.Name,
                    viewType = v.ViewType.ToString(),
                    familyAndType = doc.GetElement(v.GetTypeId())?.Name,
                    paramsList = pList
                });
            }
            return new { currentOrg = currentOrg?.Name, samples = list };
        }
    }
}
