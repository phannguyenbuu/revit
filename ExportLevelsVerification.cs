using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportLevelsVerification
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Save document to ensure changes are persisted
            try
            {
                doc.Save(new SaveOptions());
            }
            catch (Exception ex)
            {
                // In case Save is restricted, continue to export
            }

            // 2. Query all levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevM = Math.Round(l.Elevation * FT2M, 3),
                    elevMm = (int)Math.Round(l.Elevation * FT2M * 1000.0)
                })
                .ToList();

            // 3. Export 3D images
            string artifactFolder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path3D = Path.Combine(artifactFolder, "revit_levels_final_overview_3d.png");
            string pathSec = Path.Combine(artifactFolder, "revit_levels_final_section_cut.png");

            var v3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

            if (v3d != null)
            {
                uidoc.ActiveView = v3d;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);

                // Full 3D overview
                using (var tx = new Transaction(doc, "Reset Section Box"))
                {
                    tx.Start();
                    v3d.IsSectionBoxActive = false;
                    v3d.DisplayStyle = DisplayStyle.FlatColors;
                    tx.Commit();
                }

                uiview?.ZoomToFit();
                if (File.Exists(path3D)) try { File.Delete(path3D); } catch { }

                var opt = new ImageExportOptions
                {
                    FilePath = path3D,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560
                };
                doc.ExportImage(opt);

                // Corridor Section Cut showing levels and framing
                using (var txSec = new Transaction(doc, "Section Box Cut"))
                {
                    txSec.Start();
                    BoundingBoxXYZ sb = new BoundingBoxXYZ();
                    sb.Min = new XYZ(2.0 * M2FT, 6.0 * M2FT, -1.0 * M2FT);
                    sb.Max = new XYZ(28.0 * M2FT, 16.5 * M2FT, 18.5 * M2FT);
                    v3d.SetSectionBox(sb);
                    v3d.IsSectionBoxActive = true;
                    txSec.Commit();
                }

                uiview?.ZoomToFit();
                if (File.Exists(pathSec)) try { File.Delete(pathSec); } catch { }
                opt.FilePath = pathSec;
                doc.ExportImage(opt);

                // Restore Section Box
                using (var txRest = new Transaction(doc, "Restore Section Box"))
                {
                    txRest.Start();
                    v3d.IsSectionBoxActive = false;
                    txRest.Commit();
                }
                uiview?.ZoomToFit();
            }

            return new
            {
                success = true,
                levels,
                path3D,
                pathSec
            };
        }
    }
}
