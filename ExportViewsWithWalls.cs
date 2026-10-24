using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportViewsWithWalls
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Tầng 1 View
            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            // Ensure categories visible
            using (var tx = new Transaction(doc, "Ensure Categories Visible"))
            {
                tx.Start();
                var cats = new[]
                {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Grids
                };
                foreach (var catId in cats)
                {
                    var cat = doc.Settings.Categories.get_Item(catId);
                    if (cat != null)
                    {
                        if (viewTang1 != null && viewTang1.GetCategoryHidden(cat.Id))
                            viewTang1.SetCategoryHidden(cat.Id, false);
                    }
                }
                tx.Commit();
            }

            string outPlan = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_screen.png";
            if (File.Exists(outPlan)) { try { File.Delete(outPlan); } catch { } }

            if (viewTang1 != null)
            {
                uidoc.ActiveView = viewTang1;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);
                uiview?.ZoomToFit();

                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = outPlan,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1920,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { viewTang1.Id });
                doc.ExportImage(opt);
            }

            // 2. 3D View
            var view3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

            string out3d = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_3d_new_building.jpg";
            if (File.Exists(out3d)) { try { File.Delete(out3d); } catch { } }

            if (view3d != null)
            {
                uidoc.ActiveView = view3d;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                uiview?.ZoomToFit();

                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = out3d,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1920,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { view3d.Id });
                doc.ExportImage(opt);
            }

            return new
            {
                success = true,
                exportedPlan = outPlan,
                exported3d = out3d
            };
        }
    }
}
