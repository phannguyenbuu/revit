using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ManageDoorWindowTags
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { success = false, error = "No active document" };

            JsonElement targetArgs = args.TryGetProperty("args", out var innerArgs) ? innerArgs : args;

            string action = targetArgs.TryGetProperty("subAction", out var saProp) ? saProp.GetString() ?? "get_status"
                          : targetArgs.TryGetProperty("action", out var aProp) && aProp.GetString() != "execute_dynamic" ? aProp.GetString() ?? "get_status"
                          : "get_status";
            string target = targetArgs.TryGetProperty("target", out var tProp) ? tProp.GetString()?.ToLower() ?? "all" : "all"; // "door", "window", "all"
            string viewTarget = targetArgs.TryGetProperty("viewTarget", out var vtProp) ? vtProp.GetString() ?? "all" : "all"; // "all" or viewId integer as string

            var doorCatId = new ElementId(BuiltInCategory.OST_DoorTags);
            var winCatId = new ElementId(BuiltInCategory.OST_WindowTags);

            // Collect all non-template Floor / Ceiling plans
            var allPlanViews = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && (v.ViewType == ViewType.FloorPlan || v.ViewType == ViewType.CeilingPlan))
                .OrderBy(v => v.Name)
                .ToList();

            // Collect all IndependentTags in document to associate with views
            var allTagsInDoc = new FilteredElementCollector(doc)
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .ToList();

            if (action == "get_status")
            {
                var viewStatuses = new List<object>();
                foreach (var v in allPlanViews)
                {
                    var viewTags = allTagsInDoc.Where(t => t.OwnerViewId.Value == v.Id.Value).ToList();

                    var doorTags = viewTags.Where(t => t.Category != null && t.Category.Id.Value == doorCatId.Value).ToList();
                    var winTags = viewTags.Where(t => t.Category != null && t.Category.Id.Value == winCatId.Value).ToList();

                    int doorCount = doorTags.Count;
                    int winCount = winTags.Count;
                    int doorHiddenCount = doorTags.Count(t => t.IsHidden(v));
                    int winHiddenCount = winTags.Count(t => t.IsHidden(v));

                    // Category level hidden check
                    bool doorCatHidden = false;
                    bool winCatHidden = false;
                    try { doorCatHidden = v.GetCategoryHidden(doorCatId); } catch { }
                    try { winCatHidden = v.GetCategoryHidden(winCatId); } catch { }

                    viewStatuses.Add(new
                    {
                        viewId = v.Id.Value,
                        viewName = v.Name,
                        levelName = v.GenLevel?.Name ?? "",
                        doorTagCount = doorCount,
                        doorHiddenCount = doorHiddenCount,
                        doorTagsHidden = doorCatHidden || (doorCount > 0 && doorHiddenCount == doorCount),
                        windowTagCount = winCount,
                        winHiddenCount = winHiddenCount,
                        windowTagsHidden = winCatHidden || (winCount > 0 && winHiddenCount == winCount),
                        hasTemplate = v.ViewTemplateId != ElementId.InvalidElementId
                    });
                }

                return new
                {
                    success = true,
                    totalViews = allPlanViews.Count,
                    views = viewStatuses
                };
            }
            else if (action == "set_visibility")
            {
                bool hide = targetArgs.TryGetProperty("hide", out var hProp) ? hProp.GetBoolean() : true;

                // Determine target views
                List<ViewPlan> targetViews = new List<ViewPlan>();
                if (viewTarget == "all")
                {
                    targetViews = allPlanViews;
                }
                else if (long.TryParse(viewTarget, out long vid))
                {
                    var specificView = allPlanViews.FirstOrDefault(v => v.Id.Value == vid);
                    if (specificView != null) targetViews.Add(specificView);
                }

                if (targetViews.Count == 0)
                {
                    return new { success = false, error = "Không tìm thấy View mục tiêu hợp lệ." };
                }

                int totalAffectedTags = 0;
                var updatedDetails = new List<object>();

                using (Transaction tx = new Transaction(doc, $"Set Tags Visibility {(hide ? "Hide" : "Show")}"))
                {
                    tx.Start();

                    foreach (var v in targetViews)
                    {
                        var viewTags = allTagsInDoc.Where(t => t.OwnerViewId.Value == v.Id.Value).ToList();
                        var tagsToProcess = new List<IndependentTag>();

                        if (target == "door" || target == "all")
                        {
                            tagsToProcess.AddRange(viewTags.Where(t => t.Category != null && t.Category.Id.Value == doorCatId.Value));
                        }
                        if (target == "window" || target == "all")
                        {
                            tagsToProcess.AddRange(viewTags.Where(t => t.Category != null && t.Category.Id.Value == winCatId.Value));
                        }

                        int viewAffected = 0;
                        if (hide)
                        {
                            var toHide = tagsToProcess
                                .Where(t => !t.IsHidden(v) && t.CanBeHidden(v))
                                .Select(t => t.Id)
                                .ToList();

                            if (toHide.Count > 0)
                            {
                                v.HideElements(toHide);
                                viewAffected = toHide.Count;
                                totalAffectedTags += viewAffected;
                            }
                        }
                        else
                        {
                            var toUnhide = tagsToProcess
                                .Where(t => t.IsHidden(v))
                                .Select(t => t.Id)
                                .ToList();

                            if (toUnhide.Count > 0)
                            {
                                v.UnhideElements(toUnhide);
                                viewAffected = toUnhide.Count;
                                totalAffectedTags += viewAffected;
                            }
                        }

                        // Try category-level as well if possible
                        if (target == "door" || target == "all")
                        {
                            try { if (v.CanCategoryBeHidden(doorCatId)) v.SetCategoryHidden(doorCatId, hide); } catch { }
                        }
                        if (target == "window" || target == "all")
                        {
                            try { if (v.CanCategoryBeHidden(winCatId)) v.SetCategoryHidden(winCatId, hide); } catch { }
                        }

                        updatedDetails.Add(new
                        {
                            viewId = v.Id.Value,
                            viewName = v.Name,
                            affectedCount = viewAffected,
                            targetHidden = hide
                        });
                    }

                    tx.Commit();
                }

                string targetText = (target == "door") ? "Tag Cửa đi (Door Tags)"
                                  : (target == "window") ? "Tag Cửa sổ (Window Tags)"
                                  : "Tag Cửa đi & Cửa sổ (All Opening Tags)";
                string stateText = hide ? "ẨN" : "HIỆN";
                string viewText = (viewTarget == "all") ? $"TẤT CẢ {targetViews.Count} TẦNG" : $"Tầng '{targetViews.FirstOrDefault()?.Name}'";

                return new
                {
                    success = true,
                    message = $"Đã {stateText} thành công {targetText} tại {viewText} (Tổng cộng {totalAffectedTags} tag)! ",
                    totalAffectedTags = totalAffectedTags,
                    viewsCount = targetViews.Count,
                    updatedViews = updatedDetails
                };
            }

            return new { success = false, error = $"Hành động không xác định: {action}" };
        }
    }
}
