using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetupTang1View
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find Floor Plan view for Tầng 1
            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (viewTang1 == null) return new { error = "View Tầng 1 not found" };

            // Switch active view
            uidoc.ActiveView = viewTang1;

            // Link PLAN_TANG_1.dwg if not already linked
            string dwgPath = @"D:\Dropbox\_Documents\RevitAI\PLAN_TANG_1.dwg";
            ElementId? linkId = null;

            var existingCadLinks = new FilteredElementCollector(doc, viewTang1.Id)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .ToList();

            if (existingCadLinks.Count == 0 && File.Exists(dwgPath))
            {
                using (var tx = new Transaction(doc, "Link Plan Tầng 1"))
                {
                    tx.Start();
                    var opt = new DWGImportOptions
                    {
                        Placement = ImportPlacement.Origin,
                        Unit = ImportUnit.Millimeter,
                        ThisViewOnly = true
                    };
                    doc.Link(dwgPath, opt, viewTang1, out ElementId newLinkId);
                    linkId = newLinkId;
                    tx.Commit();
                }
            }
            else if (existingCadLinks.Count > 0)
            {
                linkId = existingCadLinks[0].Id;
            }

            // Ensure structural columns category is visible
            using (var tx = new Transaction(doc, "Ensure Visibility"))
            {
                tx.Start();
                var catCols = doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralColumns);
                if (catCols != null && viewTang1.GetCategoryHidden(catCols.Id))
                {
                    viewTang1.SetCategoryHidden(catCols.Id, false);
                }
                var catGrids = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Grids);
                if (catGrids != null && viewTang1.GetCategoryHidden(catGrids.Id))
                {
                    viewTang1.SetCategoryHidden(catGrids.Id, false);
                }
                tx.Commit();
            }

            // Zoom to fit
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);
            uiview?.ZoomToFit();

            return new
            {
                success = true,
                viewName = viewTang1.Name,
                linkId = linkId?.Value
            };
        }
    }
}
