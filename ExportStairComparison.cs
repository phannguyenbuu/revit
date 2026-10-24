using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportStairComparison
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"));

            if (plan == null) return new { error = "View MẶT BẰNG TẦNG 1 not found" };

            if (uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

            // Clear selection
            uidoc.Selection.SetElementIds(new List<ElementId>());

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == plan.Id);
            var minPt = new XYZ(3.8 * M2FT, 9.5 * M2FT, 0.0);
            var maxPt = new XYZ(8.8 * M2FT, 15.6 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPt, maxPt);

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string withCadPath = Path.Combine(folder, "stair_with_cad.png");
            string pureRevitPath = Path.Combine(folder, "stair_pure_revit.png");

            // 1. Export with CAD
            try
            {
                if (File.Exists(withCadPath)) File.Delete(withCadPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = withCadPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = "Failed exporting with cad: " + ex.Message };
            }

            // 2. Hide CAD links / import instances and export pure Revit
            var importCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_ImportObjectStyles);
            bool wasImportHidden = false;
            try { wasImportHidden = plan.GetCategoryHidden(importCat.Id); } catch { }

            var cadImports = new FilteredElementCollector(doc, plan.Id)
                .OfClass(typeof(ImportInstance))
                .Select(i => i.Id)
                .ToList();

            using (Transaction t = new Transaction(doc, "Temp Hide CAD for Export"))
            {
                t.Start();
                if (importCat != null)
                {
                    try { plan.SetCategoryHidden(importCat.Id, true); } catch { }
                }
                if (cadImports.Count > 0)
                {
                    try { plan.HideElements(cadImports); } catch { }
                }
                t.Commit();
            }

            try
            {
                if (File.Exists(pureRevitPath)) File.Delete(pureRevitPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = pureRevitPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = "Failed exporting pure: " + ex.Message };
            }
            finally
            {
                // Restore CAD visibility
                using (Transaction t = new Transaction(doc, "Restore CAD"))
                {
                    t.Start();
                    if (importCat != null)
                    {
                        try { plan.SetCategoryHidden(importCat.Id, wasImportHidden); } catch { }
                    }
                    if (cadImports.Count > 0)
                    {
                        try { plan.UnhideElements(cadImports); } catch { }
                    }
                    t.Commit();
                }
            }

            // 3. Export 3D View as well!
            string threeDPath = Path.Combine(folder, "stair_3d.png");
            var view3D = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name == "{3D}");

            if (view3D != null)
            {
                try
                {
                    uidoc.ActiveView = view3D;
                    var ui3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);
                    ui3d?.ZoomAndCenterRectangle(new XYZ(3.0 * M2FT, 8.5 * M2FT, -1.0 * M2FT), new XYZ(9.5 * M2FT, 16.5 * M2FT, 5.0 * M2FT));

                    if (File.Exists(threeDPath)) File.Delete(threeDPath);
                    var expOpt3D = new ImageExportOptions
                    {
                        FilePath = threeDPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt3D);

                    // Switch back to plan
                    uidoc.ActiveView = plan;
                }
                catch { }
            }

            return new {
                success = true,
                withCad = withCadPath,
                pureRevit = pureRevitPath,
                threeD = threeDPath
            };
        }
    }
}
