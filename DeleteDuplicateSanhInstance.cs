using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DeleteDuplicateSanhInstance
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var deletedIds = new List<long>();
            using (var tx = new Transaction(doc, "Delete Duplicate Sanh_Chinh_3dsMax"))
            {
                tx.Start();
                var e = doc.GetElement(new ElementId(2385103L));
                if (e != null)
                {
                    doc.Delete(e.Id);
                    deletedIds.Add(2385103L);
                }
                tx.Commit();
            }

            // Export verification image
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path3D = Path.Combine(outDir, "revit_facade_no_duplicate.png");
            if (File.Exists(path3D)) try { File.Delete(path3D); } catch {}

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

            return new { success = true, deletedIds, image = path3D };
        }
    }
}
