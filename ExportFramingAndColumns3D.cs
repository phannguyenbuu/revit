using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportFramingAndColumns3D
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            View3D targetView = null;

            using (var tx = new Transaction(doc, "Create Structure 3D View"))
            {
                tx.Start();

                var viewFamilyTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewFamilyType))
                    .Cast<ViewFamilyType>()
                    .Where(x => x.ViewFamily == ViewFamily.ThreeDimensional)
                    .FirstOrDefault();

                // Find existing or create new
                targetView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name == "3D_Option1_Structure");

                if (targetView == null && viewFamilyTypes != null)
                {
                    targetView = View3D.CreateIsometric(doc, viewFamilyTypes.Id);
                    targetView.Name = "3D_Option1_Structure";
                }

                if (targetView != null)
                {
                    // Hide walls, floors, roofs, windows, doors, stairs to isolate columns and beams
                    var catsToHide = new BuiltInCategory[]
                    {
                        BuiltInCategory.OST_Walls,
                        BuiltInCategory.OST_Floors,
                        BuiltInCategory.OST_Roofs,
                        BuiltInCategory.OST_Windows,
                        BuiltInCategory.OST_Doors,
                        BuiltInCategory.OST_Stairs
                    };

                    foreach (var cat in catsToHide)
                    {
                        var catObj = Category.GetCategory(doc, cat);
                        if (catObj != null && targetView.CanCategoryBeHidden(catObj.Id))
                        {
                            targetView.SetCategoryHidden(catObj.Id, true);
                        }
                    }

                    // Ensure Structural Columns and Framing are visible
                    var catCols = Category.GetCategory(doc, BuiltInCategory.OST_StructuralColumns);
                    if (catCols != null && targetView.CanCategoryBeHidden(catCols.Id))
                    {
                        targetView.SetCategoryHidden(catCols.Id, false);
                    }

                    var catFraming = Category.GetCategory(doc, BuiltInCategory.OST_StructuralFraming);
                    if (catFraming != null && targetView.CanCategoryBeHidden(catFraming.Id))
                    {
                        targetView.SetCategoryHidden(catFraming.Id, false);
                    }
                }

                tx.Commit();
            }

            if (targetView == null) return new { error = "Could not create target view" };

            uidoc.ActiveView = targetView;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == targetView.Id);
            uiview?.ZoomToFit();

            string outStructure = Path.Combine(folder, "revit_columns_option1_structure_isolated_3d.png");
            if (File.Exists(outStructure)) File.Delete(outStructure);

            var opts = new ImageExportOptions
            {
                FilePath = outStructure,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 3000
            };
            doc.ExportImage(opts);

            return new
            {
                success = true,
                image = outStructure
            };
        }
    }
}
