using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportSanhChinhVerification
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            List<string> exportedFiles = new List<string>();

            var v3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

            if (v3d == null) return new { error = "{3D} view not found" };

            uidoc.ActiveView = v3d;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);

            // 1. Overview image with section box turned off
            using (var tx = new Transaction(doc, "Prepare Overview View"))
            {
                tx.Start();
                v3d.IsSectionBoxActive = false;
                v3d.DisplayStyle = DisplayStyle.FlatColors;
                v3d.DetailLevel = ViewDetailLevel.Fine;

                var genericCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                if (genericCat != null)
                {
                    try { v3d.SetCategoryHidden(genericCat.Id, false); } catch {}
                }

                try
                {
                    var vdm = v3d.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    v3d.SetViewDisplayModel(vdm);
                }
                catch {}

                tx.Commit();
            }

            uiview?.ZoomToFit();

            string pathOverview = Path.Combine(outDir, "revit_overview_with_sanh_3d.png");
            if (File.Exists(pathOverview)) try { File.Delete(pathOverview); } catch {}

            var opt = new ImageExportOptions
            {
                FilePath = pathOverview,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ShadowViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2560
            };
            doc.ExportImage(opt);
            exportedFiles.Add(pathOverview);

            // 2. Focused Section Box on the Entrance Porch & Columns
            // Instance placed at (0.55m, 6.6m, 0.0m)
            // Bounds: X [-6.5m to 2.5m], Y [0.0m to 12.0m], Z [-1.5m to 6.0m]
            using (var txBox = new Transaction(doc, "Porch Section Box"))
            {
                txBox.Start();
                BoundingBoxXYZ sb = new BoundingBoxXYZ();
                sb.Min = new XYZ(-7.5 * M2FT, 0.5 * M2FT, -1.0 * M2FT);
                sb.Max = new XYZ(4.0 * M2FT, 12.5 * M2FT, 6.5 * M2FT);
                v3d.SetSectionBox(sb);
                v3d.IsSectionBoxActive = true;
                txBox.Commit();
            }

            uiview?.ZoomToFit();

            string pathCloseup = Path.Combine(outDir, "revit_sanh_chinh_closeup_3d.png");
            if (File.Exists(pathCloseup)) try { File.Delete(pathCloseup); } catch {}

            opt.FilePath = pathCloseup;
            doc.ExportImage(opt);
            exportedFiles.Add(pathCloseup);

            // Reset Section Box back to inactive
            using (var txReset = new Transaction(doc, "Reset View"))
            {
                txReset.Start();
                v3d.IsSectionBoxActive = false;
                txReset.Commit();
            }
            uiview?.ZoomToFit();

            return new
            {
                success = true,
                exportedFiles
            };
        }
    }
}
