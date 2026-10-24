using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class GetProjectBrowserGroups
    {
        public class ViewGroupInfo
        {
            public string GroupName { get; set; }
            public string ViewTypeName { get; set; }
            public string FamilyTypeName { get; set; }
            public List<ViewItemInfo> Views { get; set; } = new List<ViewItemInfo>();
        }

        public class ViewItemInfo
        {
            public long Id { get; set; }
            public string Name { get; set; }
            public string ViewType { get; set; }
            public string FamilyTypeName { get; set; }
        }

        public static string GetExactBrowserGroupName(Document doc, View v)
        {
            if (v.IsTemplate) return null;

            var vft = doc.GetElement(v.GetTypeId()) as ViewFamilyType;
            string typeName = vft?.Name ?? "";

            switch (v.ViewType)
            {
                case ViewType.FloorPlan:
                    return !string.IsNullOrEmpty(typeName) && typeName != "Floor Plan" 
                        ? $"Floor Plans ({typeName})" 
                        : "Floor Plans";

                case ViewType.CeilingPlan:
                    return !string.IsNullOrEmpty(typeName) && typeName != "Ceiling Plan" 
                        ? $"Ceiling Plans ({typeName})" 
                        : "Ceiling Plans";

                case ViewType.Section:
                    return !string.IsNullOrEmpty(typeName) 
                        ? $"Sections ({typeName})" 
                        : "Sections";

                case ViewType.Elevation:
                    return !string.IsNullOrEmpty(typeName) 
                        ? $"Elevations ({typeName})" 
                        : "Elevations";

                case ViewType.Detail:
                    return !string.IsNullOrEmpty(typeName) 
                        ? $"Detail Views ({typeName})" 
                        : "Detail Views";

                case ViewType.DraftingView:
                    return !string.IsNullOrEmpty(typeName) && typeName != "Drafting View" 
                        ? $"Drafting Views ({typeName})" 
                        : "Drafting Views";

                case ViewType.ThreeD:
                    return "3D Views";

                case ViewType.AreaPlan:
                    return !string.IsNullOrEmpty(typeName) 
                        ? $"Area Plans ({typeName})" 
                        : "Area Plans";

                default:
                    return v.ViewType.ToString();
            }
        }

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, message = "No doc" };

            var allViews = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(v => !v.IsTemplate && v.ViewType != ViewType.Internal && v.ViewType != ViewType.ProjectBrowser && v.ViewType != ViewType.SystemBrowser && v.ViewType != ViewType.DrawingSheet)
                .ToList();

            var groupsDict = new Dictionary<string, ViewGroupInfo>(StringComparer.OrdinalIgnoreCase);

            foreach (var v in allViews)
            {
                string groupName = GetExactBrowserGroupName(doc, v);
                if (string.IsNullOrEmpty(groupName)) continue;

                if (!groupsDict.TryGetValue(groupName, out var groupInfo))
                {
                    var vft = doc.GetElement(v.GetTypeId()) as ViewFamilyType;
                    groupInfo = new ViewGroupInfo
                    {
                        GroupName = groupName,
                        ViewTypeName = v.ViewType.ToString(),
                        FamilyTypeName = vft?.Name ?? ""
                    };
                    groupsDict[groupName] = groupInfo;
                }

                groupInfo.Views.Add(new ViewItemInfo
                {
                    Id = v.Id.Value,
                    Name = v.Name,
                    ViewType = v.ViewType.ToString(),
                    FamilyTypeName = (doc.GetElement(v.GetTypeId()) as ViewFamilyType)?.Name ?? ""
                });
            }

            // Order views by name within each group
            foreach (var g in groupsDict.Values)
            {
                g.Views = g.Views.OrderBy(x => x.Name).ToList();
            }

            var sortedGroups = groupsDict.Values.OrderBy(g => g.GroupName).ToList();

            return new
            {
                success = true,
                groupCount = sortedGroups.Count,
                groups = sortedGroups
            };
        }
    }
}
