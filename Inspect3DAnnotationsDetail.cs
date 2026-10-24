using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Inspect3DAnnotationsDetail
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Check ModelText
            var modelTexts = new FilteredElementCollector(doc)
                .OfClass(typeof(ModelText))
                .Cast<ModelText>()
                .Select(mt => new { id = mt.Id.Value, text = mt.Text })
                .ToList();

            // 2. Check 3D views and their annotation settings
            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .Where(v => !v.IsTemplate)
                .Select(v => {
                    bool annoHidden = false;
                    try { annoHidden = v.AreAnnotationCategoriesHidden; } catch {}

                    bool gridsHidden = false;
                    var gridCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Grids);
                    if (gridCat != null) try { gridsHidden = v.GetCategoryHidden(gridCat.Id); } catch {}

                    bool levelsHidden = false;
                    var lvlCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Levels);
                    if (lvlCat != null) try { levelsHidden = v.GetCategoryHidden(lvlCat.Id); } catch {}

                    bool basePtHidden = false;
                    var bpCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_ProjectBasePoint);
                    if (bpCat != null) try { basePtHidden = v.GetCategoryHidden(bpCat.Id); } catch {}

                    return new {
                        id = v.Id.Value,
                        name = v.Name,
                        annoHidden,
                        gridsHidden,
                        levelsHidden,
                        basePtHidden
                    };
                })
                .ToList();

            // 3. Check Viewports on Sheets
            var viewports = new FilteredElementCollector(doc)
                .OfClass(typeof(Viewport))
                .Cast<Viewport>()
                .Select(vp => {
                    var sheet = doc.GetElement(vp.SheetId) as ViewSheet;
                    var v = doc.GetElement(vp.ViewId);
                    return new {
                        vpId = vp.Id.Value,
                        sheetName = sheet?.Name,
                        sheetNumber = sheet?.SheetNumber,
                        viewName = v?.Name,
                        viewType = v?.GetType().Name
                    };
                })
                .ToList();

            // 4. Check if any Family has 3D Text or tag
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "Sanh_Chinh_3dsMax");

            return new {
                modelTexts,
                view3Ds = view3Ds.Take(10).ToList(),
                viewportCount = viewports.Count,
                viewportsSample = viewports.Take(5).ToList()
            };
        }
    }
}
