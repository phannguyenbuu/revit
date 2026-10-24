using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportHallwaySection
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var v3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

            if (v3d == null) return new { error = "No {3D} view" };

            uidoc.ActiveView = v3d;

            // Section Box cutting through Y = 6.5m (inside corridor) looking towards Trục D (Y = 13.1m)
            // X: [3m, 27m], Y: [6.5m, 16m], Z: [0m, 15m]
            using (var tx = new Transaction(doc, "Corridor Longitudinal Section Cut"))
            {
                tx.Start();
                BoundingBoxXYZ sb = new BoundingBoxXYZ();
                sb.Min = new XYZ(3.0 * M2FT, 6.5 * M2FT, -0.5 * M2FT);
                sb.Max = new XYZ(27.0 * M2FT, 16.0 * M2FT, 15.0 * M2FT);
                v3d.SetSectionBox(sb);
                v3d.IsSectionBoxActive = true;
                v3d.DisplayStyle = DisplayStyle.FlatColors;
                var vdm = v3d.GetViewDisplayModel();
                vdm.SmoothEdges = true;
                v3d.SetViewDisplayModel(vdm);
                tx.Commit();
            }

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
            uiview?.ZoomToFit();

            string imgPath = Path.Combine(brainDir, "revit_framing_corridor_section_cut.png");
            if (File.Exists(imgPath)) try { File.Delete(imgPath); } catch { }

            var expOpt = new ImageExportOptions
            {
                FilePath = imgPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2560
            };
            doc.ExportImage(expOpt);

            // Restore section box to off
            using (var txRestore = new Transaction(doc, "Restore Section Box"))
            {
                txRestore.Start();
                v3d.IsSectionBoxActive = false;
                txRestore.Commit();
            }
            uiview?.ZoomToFit();

            return new { success = true, imgPath };
        }
    }
}
