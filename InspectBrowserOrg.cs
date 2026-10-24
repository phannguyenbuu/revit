using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBrowserOrg
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Check BrowserOrganization for Views
            var orgs = new FilteredElementCollector(doc)
                .OfClass(typeof(BrowserOrganization))
                .Cast<BrowserOrganization>()
                .ToList();

            var orgList = new List<object>();
            foreach (var bo in orgs)
            {
                orgList.Add(new {
                    id = bo.Id.Value,
                    name = bo.Name,
                    type = bo.Type.ToString(),
                    areFiltersSatisfied = bo.AreFiltersSatisfied(doc.ActiveView?.Id ?? ElementId.InvalidElementId)
                });
            }

            var currentViewOrg = BrowserOrganization.GetCurrentBrowserOrganizationForViews(doc);

            // 2. Collect all non-template views and see their grouping parameters & types
            var allViews = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(v => !v.IsTemplate && (v is ViewPlan || v is ViewSection || v is ViewDrafting || v.ViewType == ViewType.Elevation))
                .ToList();

            var groups = new Dictionary<string, List<object>>();

            foreach (var v in allViews)
            {
                // Common parameters used for grouping
                string groupKey = v.ViewType.ToString();
                
                // Check Discipline or Sub-Discipline or custom parameter
                var pSub = v.LookupParameter("Sub-Discipline") ?? v.LookupParameter("Phân loại") ?? v.LookupParameter("Views (all)");
                string subVal = pSub?.AsString() ?? "";

                string fullGroup = $"{v.ViewType}" + (!string.IsNullOrEmpty(subVal) ? $" ({subVal})" : "");
                
                // Detail view check
                if (v is ViewSection vs && vs.IsCallout)
                {
                    fullGroup = $"Detail Views ({v.get_Parameter(BuiltInParameter.VIEW_TYPE_SCHEDULES)?.AsString() ?? ""})";
                }

                if (!groups.ContainsKey(fullGroup)) groups[fullGroup] = new List<object>();
                groups[fullGroup].Add(new {
                    id = v.Id.Value,
                    name = v.Name,
                    viewType = v.ViewType.ToString()
                });
            }

            return new {
                currentOrg = currentViewOrg != null ? new { id = currentViewOrg.Id.Value, name = currentViewOrg.Name } : null,
                allOrgs = orgList,
                totalViews = allViews.Count,
                groupsSummary = groups.Select(kv => new {
                    group = kv.Key,
                    count = kv.Value.Count,
                    views = kv.Value
                }).ToList()
            };
        }
    }
}
