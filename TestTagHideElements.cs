using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestTagHideElements
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc?.ActiveView;
            if (view == null) return new { error = "no view" };

            var doorCatId = new ElementId(BuiltInCategory.OST_DoorTags);
            var winCatId = new ElementId(BuiltInCategory.OST_WindowTags);

            // Collect all tags belonging to this view (regardless of hidden or not)
            var allTagsInDoc = new FilteredElementCollector(doc)
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .Where(t => t.OwnerViewId.Value == view.Id.Value)
                .ToList();

            var doorTags = allTagsInDoc.Where(t => t.Category != null && t.Category.Id.Value == doorCatId.Value).ToList();
            var winTags = allTagsInDoc.Where(t => t.Category != null && t.Category.Id.Value == winCatId.Value).ToList();

            int doorHidden = doorTags.Count(t => t.IsHidden(view));
            int winHidden = winTags.Count(t => t.IsHidden(view));

            // Test unhiding all winTags
            string unhideResult = "none";
            using (Transaction tx = new Transaction(doc, "Unhide All Window Tags"))
            {
                tx.Start();
                var hiddenWins = winTags.Where(t => t.IsHidden(view)).Select(t => t.Id).ToList();
                if (hiddenWins.Count > 0)
                {
                    view.UnhideElements(hiddenWins);
                    unhideResult = $"Unhid {hiddenWins.Count} window tags successfully!";
                }
                else
                {
                    unhideResult = "No hidden window tags to unhide.";
                }
                tx.Commit();
            }

            int winHiddenAfter = winTags.Count(t => t.IsHidden(view));

            return new
            {
                viewId = view.Id.Value,
                viewName = view.Name,
                totalDoorTags = doorTags.Count,
                doorHiddenBefore = doorHidden,
                totalWinTags = winTags.Count,
                winHiddenBefore = winHidden,
                unhideResult,
                winHiddenAfter
            };
        }
    }
}
