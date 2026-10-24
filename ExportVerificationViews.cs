using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportVerificationViews
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

                var view3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d == null) return new { error = "No 3D view found" };

                uidoc.ActiveView = view3d;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);

                // 1. Full 3D View
                string full3dPath = Path.Combine(folder, "revit_3d_windows_clean_final.jpg");
                uiview3d?.ZoomToFit();
                if (File.Exists(full3dPath)) File.Delete(full3dPath);

                var expOptFull = new ImageExportOptions
                {
                    FilePath = full3dPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOptFull);

                // 2. Front Window S1 Closeup (e.g. S1 on Axis A)
                string closeupS1Path = Path.Combine(folder, "revit_closeup_s1_window.png");
                var s1Win = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .FirstOrDefault(w => w.Symbol.Name.Equals("S1_1500x1800", StringComparison.OrdinalIgnoreCase));

                if (s1Win != null && uiview3d != null)
                {
                    var bb = s1Win.get_BoundingBox(view3d);
                    if (bb != null)
                    {
                        XYZ center = (bb.Min + bb.Max) * 0.5;
                        double margin = 3.2; // ~1m around window
                        uiview3d.ZoomAndCenterRectangle(
                            new XYZ(center.X - margin, center.Y - margin, center.Z - margin),
                            new XYZ(center.X + margin, center.Y + margin, center.Z + margin)
                        );

                        if (File.Exists(closeupS1Path)) File.Delete(closeupS1Path);
                        var expOptClose = new ImageExportOptions
                        {
                            FilePath = closeupS1Path,
                            FitDirection = FitDirectionType.Horizontal,
                            HLRandWFViewsFileType = ImageFileType.PNG,
                            ImageResolution = ImageResolution.DPI_300,
                            ExportRange = ExportRange.CurrentView,
                            ZoomType = ZoomFitType.FitToPage,
                            PixelSize = 2500
                        };
                        doc.ExportImage(expOptClose);
                    }
                }

                // 3. Side Window 900x1900 Closeup (in CUA SO2 CANH NHOM KINH CO O THOANG)
                string closeup900Path = Path.Combine(folder, "revit_closeup_900x1900_window.png");
                var win900 = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .FirstOrDefault(w => w.Symbol.FamilyName.Equals("CUA SO2 CANH NHOM KINH CO O THOANG", StringComparison.OrdinalIgnoreCase));

                if (win900 != null && uiview3d != null)
                {
                    var bb = win900.get_BoundingBox(view3d);
                    if (bb != null)
                    {
                        XYZ center = (bb.Min + bb.Max) * 0.5;
                        double margin = 3.5;
                        uiview3d.ZoomAndCenterRectangle(
                            new XYZ(center.X - margin, center.Y - margin, center.Z - margin),
                            new XYZ(center.X + margin, center.Y + margin, center.Z + margin)
                        );

                        if (File.Exists(closeup900Path)) File.Delete(closeup900Path);
                        var expOptClose900 = new ImageExportOptions
                        {
                            FilePath = closeup900Path,
                            FitDirection = FitDirectionType.Horizontal,
                            HLRandWFViewsFileType = ImageFileType.PNG,
                            ImageResolution = ImageResolution.DPI_300,
                            ExportRange = ExportRange.CurrentView,
                            ZoomType = ZoomFitType.FitToPage,
                            PixelSize = 2500
                        };
                        doc.ExportImage(expOptClose900);
                    }
                }

                // Zoom back to fit
                uiview3d?.ZoomToFit();

                return new
                {
                    success = true,
                    full3dPath,
                    closeupS1Path,
                    closeup900Path
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
