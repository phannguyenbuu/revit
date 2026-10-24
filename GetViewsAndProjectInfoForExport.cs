using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class GetViewsAndProjectInfoForExport
    {
        public class TreeGroupItem
        {
            public string GroupKey { get; set; } = "";
            public string GroupTitle { get; set; } = "";
            public string Icon { get; set; } = "folder";
            public List<TreeChildItem> Children { get; set; } = new List<TreeChildItem>();
        }

        public class TreeChildItem
        {
            public long Id { get; set; }
            public string Name { get; set; } = "";
            public string? SheetNumber { get; set; }
            public string ViewType { get; set; } = "";
            public string Scale { get; set; } = "";
            public bool IsSheet { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            // 1. Lấy thông tin Project Information
            var pi = doc.ProjectInformation;
            var projectInfo = new
            {
                projectName = pi?.Name ?? "DỰ ÁN XÂY DỰNG",
                projectNumber = pi?.Number ?? "DA-01",
                projectAddress = pi?.Address ?? "Hà Nội, Việt Nam",
                clientName = pi?.ClientName ?? "CHỦ ĐẦU TƯ",
                buildingName = pi?.BuildingName ?? "TRỤ SỞ LÀM VIỆC",
                issueDate = pi?.IssueDate ?? DateTime.Now.ToString("dd/MM/yyyy"),
                author = pi?.Author ?? "CÔNG TY THIẾT KẾ",
                status = pi?.Status ?? "Thiết kế thi công",
                organizationName = pi?.OrganizationName ?? "PHÒNG THIẾT KẾ KIẾN TRÚC"
            };

            // 2. Lấy danh sách khung tên (Titleblock Family Symbols) trong dự án
            var titleblockSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_TitleBlocks)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(tb => new
                {
                    id = tb.Id.Value,
                    name = tb.Name,
                    familyName = tb.FamilyName
                })
                .ToList();

            // 3. Lấy tất cả các View xuất được (Views + Sheets)
            var allViews = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(v => !v.IsTemplate &&
                            v.ViewType != ViewType.Internal &&
                            v.ViewType != ViewType.ProjectBrowser &&
                            v.ViewType != ViewType.SystemBrowser)
                .ToList();

            var groupsDict = new Dictionary<string, TreeGroupItem>(StringComparer.OrdinalIgnoreCase);

            void AddChild(string groupKey, string groupTitle, string icon, TreeChildItem child)
            {
                if (!groupsDict.TryGetValue(groupKey, out var grp))
                {
                    grp = new TreeGroupItem
                    {
                        GroupKey = groupKey,
                        GroupTitle = groupTitle,
                        Icon = icon
                    };
                    groupsDict[groupKey] = grp;
                }
                grp.Children.Add(child);
            }

            foreach (var v in allViews)
            {
                string scaleStr = (v.Scale > 0) ? $"1:{v.Scale}" : "--";

                if (v is ViewSheet vs)
                {
                    AddChild("sheets", "Bản vẽ phát hành (Sheets)", "layout", new TreeChildItem
                    {
                        Id = vs.Id.Value,
                        Name = vs.Name,
                        SheetNumber = vs.SheetNumber,
                        ViewType = "Sheet",
                        Scale = scaleStr,
                        IsSheet = true
                    });
                }
                else if (v is ViewPlan vp)
                {
                    if (vp.ViewType == ViewType.CeilingPlan)
                    {
                        AddChild("ceiling_plans", "Mặt bằng trần (Ceiling Plans)", "box", new TreeChildItem
                        {
                            Id = vp.Id.Value,
                            Name = vp.Name,
                            ViewType = "CeilingPlan",
                            Scale = scaleStr,
                            IsSheet = false
                        });
                    }
                    else if (vp.ViewType == ViewType.AreaPlan)
                    {
                        AddChild("area_plans", "Mặt bằng diện tích (Area Plans)", "square", new TreeChildItem
                        {
                            Id = vp.Id.Value,
                            Name = vp.Name,
                            ViewType = "AreaPlan",
                            Scale = scaleStr,
                            IsSheet = false
                        });
                    }
                    else
                    {
                        AddChild("floor_plans", "Mặt bằng kiến trúc (Floor Plans)", "grid", new TreeChildItem
                        {
                            Id = vp.Id.Value,
                            Name = vp.Name,
                            ViewType = "FloorPlan",
                            Scale = scaleStr,
                            IsSheet = false
                        });
                    }
                }
                else if (v is ViewSection vsct)
                {
                    var vft = doc.GetElement(vsct.GetTypeId()) as ViewFamilyType;
                    string typeName = vft?.Name ?? "";
                    if (typeName.Contains("Detail", StringComparison.OrdinalIgnoreCase) || vsct.ViewType == ViewType.Detail)
                    {
                        AddChild("detail_views", "Chi tiết trích đoạn (Detail Views)", "zoom-in", new TreeChildItem
                        {
                            Id = vsct.Id.Value,
                            Name = vsct.Name,
                            ViewType = "Detail",
                            Scale = scaleStr,
                            IsSheet = false
                        });
                    }
                    else
                    {
                        AddChild("sections", "Mặt cắt công trình (Sections)", "scissors", new TreeChildItem
                        {
                            Id = vsct.Id.Value,
                            Name = vsct.Name,
                            ViewType = "Section",
                            Scale = scaleStr,
                            IsSheet = false
                        });
                    }
                }
                else if (v.ViewType == ViewType.Elevation)
                {
                    AddChild("elevations", "Mặt đứng công trình (Elevations)", "building", new TreeChildItem
                    {
                        Id = v.Id.Value,
                        Name = v.Name,
                        ViewType = "Elevation",
                        Scale = scaleStr,
                        IsSheet = false
                    });
                }
                else if (v.ViewType == ViewType.DraftingView)
                {
                    AddChild("drafting_views", "Hình vẽ soạn thảo (Drafting Views)", "file-text", new TreeChildItem
                    {
                        Id = v.Id.Value,
                        Name = v.Name,
                        ViewType = "DraftingView",
                        Scale = scaleStr,
                        IsSheet = false
                    });
                }
                else if (v.ViewType == ViewType.ThreeD && !v.IsTemplate)
                {
                    AddChild("3d_views", "Hình chiếu 3D (3D Views)", "cuboid", new TreeChildItem
                    {
                        Id = v.Id.Value,
                        Name = v.Name,
                        ViewType = "ThreeD",
                        Scale = scaleStr,
                        IsSheet = false
                    });
                }
            }

            // Sắp xếp các view con trong từng group
            foreach (var g in groupsDict.Values)
            {
                if (g.GroupKey == "sheets")
                {
                    g.Children = g.Children.OrderBy(c => c.SheetNumber).ThenBy(c => c.Name).ToList();
                }
                else
                {
                    g.Children = g.Children.OrderBy(c => c.Name).ToList();
                }
            }

            // Danh sách thứ tự ưu tiên của các group
            var groupOrder = new List<string>
            {
                "floor_plans",
                "sections",
                "elevations",
                "sheets",
                "detail_views",
                "ceiling_plans",
                "drafting_views",
                "3d_views",
                "area_plans"
            };

            var orderedGroups = groupsDict.Values
                .OrderBy(g =>
                {
                    int idx = groupOrder.IndexOf(g.GroupKey);
                    return idx >= 0 ? idx : 99;
                })
                .ToList();

            int totalViews = orderedGroups.Sum(g => g.Children.Count);

            return new
            {
                success = true,
                totalViews,
                projectInfo,
                titleblocks = titleblockSymbols,
                groups = orderedGroups
            };
        }
    }
}
