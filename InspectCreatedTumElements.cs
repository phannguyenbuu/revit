using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCreatedTumElements
    {
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var ids = new long[] { 2370733, 2370734, 2370735, 2370736, 2370737 };
            var elements = new List<object>();

            foreach (var idVal in ids)
            {
                var elem = doc.GetElement(new ElementId(idVal));
                if (elem == null)
                {
                    elements.Add(new { id = idVal, status = "NOT_FOUND" });
                    continue;
                }

                var bb = elem.get_BoundingBox(null);
                elements.Add(new
                {
                    id = elem.Id.Value,
                    name = elem.Name,
                    category = elem.Category?.Name,
                    min = bb != null ? new { x = Math.Round(ToM(bb.Min.X), 2), y = Math.Round(ToM(bb.Min.Y), 2), z = Math.Round(ToM(bb.Min.Z), 2) } : null,
                    max = bb != null ? new { x = Math.Round(ToM(bb.Max.X), 2), y = Math.Round(ToM(bb.Max.Y), 2), z = Math.Round(ToM(bb.Max.Z), 2) } : null,
                    comments = elem.LookupParameter("Comments")?.AsString()
                });
            }

            // Export 3D view with ExportRange.CurrentView and ZoomToFit
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string plan3dImgPath = Path.Combine(outDir, "revit_3d_tang1234_with_tum.jpg");

            var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name == "{3D}")
                ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

            if (view3d != null)
            {
                uidoc.ActiveView = view3d;
                var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                uiview3d?.ZoomToFit();

                if (File.Exists(plan3dImgPath)) File.Delete(plan3dImgPath);
                var expOpt3d = new ImageExportOptions
                {
                    FilePath = plan3dImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt3d);
            }

            // Floor Plan for Tầng Tum
            string planImgPath = Path.Combine(outDir, "plan_tang_tum.png");
            var planTum = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("TUM") || v.GenLevel?.Name.Contains("TUM") == true));

            if (planTum != null)
            {
                uidoc.ActiveView = planTum;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTum.Id);
                uiview?.ZoomToFit();

                if (File.Exists(planImgPath)) File.Delete(planImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3200
                };
                doc.ExportImage(expOpt);
            }

            return new { elements, plan3dImgPath, planImgPath, tumPlanName = planTum?.Name };
        }
    }
}
