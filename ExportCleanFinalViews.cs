using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCleanFinalViews
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Clear selection
            uidoc.Selection.SetElementIds(new List<ElementId>());

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path3D = Path.Combine(outDir, "revit_facade_and_beams_clean_3d.png");
            string pathSection = Path.Combine(outDir, "revit_section_beams_and_walls.png");

            if (File.Exists(path3D)) try { File.Delete(path3D); } catch {}
            if (File.Exists(pathSection)) try { File.Delete(pathSection); } catch {}

            // 1. Export 3D view
            try
            {
                var view3D = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (view3D != null)
                {
                    uidoc.ActiveView = view3D;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);
                    uiview?.ZoomToFit();

                    var opt3D = new ImageExportOptions
                    {
                        FilePath = path3D,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(opt3D);
                }
            }
            catch {}

            // 2. Export Section view (e.g. Section 1 or Section 1-1)
            try
            {
                var sectionView = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("1-1") || v.Name.Contains("Section 1")));

                if (sectionView != null)
                {
                    uidoc.ActiveView = sectionView;
                    var uiviewSec = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == sectionView.Id);
                    uiviewSec?.ZoomToFit();

                    var optSec = new ImageExportOptions
                    {
                        FilePath = pathSection,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(optSec);
                }
            }
            catch {}

            return new {
                success = true,
                image3D = path3D,
                imageSection = pathSection
            };
        }
    }
}
