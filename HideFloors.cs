using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FloorHider
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string mode = "hide";
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("mode", out var m))
            {
                mode = m.GetString()?.ToLowerInvariant() ?? "hide";
            }

            if (mode == "unhide" || mode == "show")
            {
                return UnhideFloors(uiapp, args);
            }

            return HideFloors(uiapp, args);
        }

        public static object HideFloors(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            var activeView = uidoc.ActiveView;
            if (activeView == null) return new { error = "No active view" };

            var floorElements = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .ToList();

            var floorCategory = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            var categoryId = floorCategory?.Id;

            int hiddenElementCount = 0;
            bool categoryHiddenInActiveView = false;
            var affectedViews = new List<string>();

            using (var tx = new Transaction(doc, "Hide All Floors"))
            {
                tx.Start();

                if (categoryId != null && activeView.CanCategoryBeHidden(categoryId))
                {
                    activeView.SetCategoryHidden(categoryId, true);
                    categoryHiddenInActiveView = true;
                    affectedViews.Add(activeView.Name);
                }

                var hideableIds = floorElements
                    .Where(e => e.CanBeHidden(activeView) && !e.IsHidden(activeView))
                    .Select(e => e.Id)
                    .ToList();

                if (hideableIds.Count > 0)
                {
                    activeView.HideElements(hideableIds);
                    hiddenElementCount = hideableIds.Count;
                }

                try
                {
                    var openViews = uidoc.GetOpenUIViews();
                    foreach (var uiview in openViews)
                    {
                        var view = doc.GetElement(uiview.ViewId) as View;
                        if (view != null && view.Id != activeView.Id && !view.IsTemplate)
                        {
                            if (categoryId != null && view.CanCategoryBeHidden(categoryId))
                            {
                                view.SetCategoryHidden(categoryId, true);
                                affectedViews.Add(view.Name);
                            }
                        }
                    }
                }
                catch { }

                tx.Commit();
            }

            try
            {
                uidoc.RefreshActiveView();
            }
            catch { }

            return new
            {
                success = true,
                action = "hidden",
                totalFloorsFound = floorElements.Count,
                hiddenElementCount,
                categoryHiddenInActiveView,
                activeView = activeView.Name,
                affectedViews = affectedViews.Distinct().ToList(),
                floorIds = floorElements.Select(e => e.Id.Value).ToList()
            };
        }

        public static object UnhideFloors(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            var activeView = uidoc.ActiveView;
            if (activeView == null) return new { error = "No active view" };

            var floorElements = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .ToList();

            var floorCategory = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            var categoryId = floorCategory?.Id;

            int unhiddenCount = 0;

            using (var tx = new Transaction(doc, "Unhide All Floors"))
            {
                tx.Start();

                if (categoryId != null && activeView.CanCategoryBeHidden(categoryId))
                {
                    activeView.SetCategoryHidden(categoryId, false);
                }

                var hiddenIds = floorElements
                    .Where(e => e.IsHidden(activeView))
                    .Select(e => e.Id)
                    .ToList();

                if (hiddenIds.Count > 0)
                {
                    activeView.UnhideElements(hiddenIds);
                    unhiddenCount = hiddenIds.Count;
                }

                tx.Commit();
            }

            try
            {
                uidoc.RefreshActiveView();
            }
            catch { }

            return new
            {
                success = true,
                action = "unhidden",
                totalFloorsFound = floorElements.Count,
                unhiddenCount,
                activeView = activeView.Name
            };
        }
    }
}
