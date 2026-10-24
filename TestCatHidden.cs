using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCatHidden
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc?.ActiveView;
            if (view == null) return new { error = "no view" };

            var doorCatId = new ElementId(BuiltInCategory.OST_DoorTags);
            var winCatId = new ElementId(BuiltInCategory.OST_WindowTags);

            var doorCat = Category.GetCategory(doc, BuiltInCategory.OST_DoorTags);
            var winCat = Category.GetCategory(doc, BuiltInCategory.OST_WindowTags);

            bool canHideDoor = view.CanCategoryBeHidden(doorCatId);
            bool canHideWin = view.CanCategoryBeHidden(winCatId);
            bool isDoorHidden = view.GetCategoryHidden(doorCatId);
            bool isWinHidden = view.GetCategoryHidden(winCatId);

            string setDoorResult = "not tried";
            using (Transaction tx = new Transaction(doc, "Test Hide Door Tags"))
            {
                tx.Start();
                try
                {
                    view.SetCategoryHidden(doorCatId, true);
                    setDoorResult = "Success: SetCategoryHidden(doorCatId, true)";
                }
                catch (Exception ex)
                {
                    setDoorResult = "Exception: " + ex.Message;
                }
                tx.RollBack();
            }

            return new
            {
                viewId = view.Id.Value,
                viewName = view.Name,
                hasTemplate = view.ViewTemplateId != ElementId.InvalidElementId,
                doorCatFound = doorCat != null,
                canHideDoor,
                canHideWin,
                isDoorHidden,
                isWinHidden,
                setDoorResult
            };
        }
    }
}
