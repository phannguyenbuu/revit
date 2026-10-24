using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Export3DTumHoleDetail
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            View3D v3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("3D"));

            if (v3d == null) return new { error = "No 3D view" };

            uidoc.ActiveView = v3d;

            // 1. Create a focused section box around the hole & roof tum
            BoundingBoxXYZ origBox = null;
            bool origActive = v3d.IsSectionBoxActive;
            if (origActive) origBox = v3d.GetSectionBox();

            string out3dClose = Path.Combine(brainDir, "revit_tum_slab_hole_3d_close.png");

            using (Transaction t = new Transaction(doc, "Section Box on Tum Hole"))
            {
                t.Start();

                var box = new BoundingBoxXYZ();
                // Hole is at X in [5.65m, 6.75m], Y in [9.7m, 13.1m], Z = 14.4m
                // Focus box around X: 1m to 14m, Y: 5m to 18m, Z: 9m to 18m
                box.Min = new XYZ(1.0 * M2FT, 5.0 * M2FT, 9.5 * M2FT);
                box.Max = new XYZ(14.0 * M2FT, 17.0 * M2FT, 17.5 * M2FT);

                v3d.SetSectionBox(box);
                v3d.IsSectionBoxActive = true;

                t.Commit();
            }

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
            uiview?.ZoomToFit();

            if (File.Exists(out3dClose)) File.Delete(out3dClose);
            var expOpt = new ImageExportOptions
            {
                FilePath = out3dClose,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2560
            };
            doc.ExportImage(expOpt);

            // Restore original section box
            using (Transaction t2 = new Transaction(doc, "Restore Section Box"))
            {
                t2.Start();
                if (origActive && origBox != null)
                {
                    v3d.SetSectionBox(origBox);
                    v3d.IsSectionBoxActive = true;
                }
                else
                {
                    v3d.IsSectionBoxActive = false;
                }
                t2.Commit();
            }

            uiview?.ZoomToFit();

            return new { success = true };
        }
    }
}
