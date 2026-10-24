using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairVisibility
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var view = uiapp.ActiveUIDocument.ActiveView;

            var stairCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Stairs);
            var subCats = new List<object>();

            foreach (Category sub in stairCat.SubCategories)
            {
                bool isHidden = false;
                try
                {
                    isHidden = view.GetCategoryHidden(sub.Id);
                }
                catch { }

                subCats.Add(new {
                    name = sub.Name,
                    id = sub.Id.Value,
                    isHiddenInView = isHidden
                });
            }

            return new {
                viewName = view.Name,
                stairCatHidden = view.GetCategoryHidden(stairCat.Id),
                subCategories = subCats
            };
        }
    }
}
