using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportFramingVerification
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
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

                // 1. Export Overview (all elements, section box disabled)
                using (var tx = new Transaction(doc, "Overview Settings"))
                {
                    tx.Start();
                    v3d.IsSectionBoxActive = false;
                    v3d.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = v3d.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    v3d.SetViewDisplayModel(vdm);
                    tx.Commit();
                }

                uidoc.Selection.SetElementIds(new List<ElementId>());
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
                uiview?.ZoomToFit();

                string imgOverview = Path.Combine(brainDir, "revit_framing_all_floors_3d.png");
                if (File.Exists(imgOverview)) try { File.Delete(imgOverview); } catch { }

                var expOpt = new ImageExportOptions
                {
                    FilePath = imgOverview,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560
                };
                doc.ExportImage(expOpt);

                // 2. Export Cross-Section Cut (Cutting bays 5-11, showing interior columns, beams, slabs & walls)
                // Crop from X = -2m to 20m, Y = -2m to 16m, Z = -1m to 18m
                using (var txSec = new Transaction(doc, "Section Box Cut"))
                {
                    txSec.Start();
                    BoundingBoxXYZ sb = new BoundingBoxXYZ();
                    sb.Min = new XYZ(-2.0 * M2FT, -2.0 * M2FT, -1.0 * M2FT);
                    sb.Max = new XYZ(20.0 * M2FT, 16.0 * M2FT, 18.5 * M2FT);
                    v3d.SetSectionBox(sb);
                    v3d.IsSectionBoxActive = true;
                    txSec.Commit();
                }

                uiview?.ZoomToFit();

                string imgSection = Path.Combine(brainDir, "revit_framing_section_cut_bays1_6.png");
                if (File.Exists(imgSection)) try { File.Delete(imgSection); } catch { }

                expOpt.FilePath = imgSection;
                doc.ExportImage(expOpt);

                // 3. Close-up on Beam-Slab-Wall intersection at Level 2 (Bay 2-3)
                using (var txClose = new Transaction(doc, "Close Up Section"))
                {
                    txClose.Start();
                    BoundingBoxXYZ sb = new BoundingBoxXYZ();
                    sb.Min = new XYZ(2.0 * M2FT, -1.0 * M2FT, 1.0 * M2FT);
                    sb.Max = new XYZ(10.0 * M2FT, 9.0 * M2FT, 8.5 * M2FT);
                    v3d.SetSectionBox(sb);
                    v3d.IsSectionBoxActive = true;
                    txClose.Commit();
                }

                uiview?.ZoomToFit();

                string imgClose = Path.Combine(brainDir, "revit_beam_slab_wall_joint_detail.png");
                if (File.Exists(imgClose)) try { File.Delete(imgClose); } catch { }

                expOpt.FilePath = imgClose;
                doc.ExportImage(expOpt);

                // Restore section box to off
                using (var txRestore = new Transaction(doc, "Restore Section Box"))
                {
                    txRestore.Start();
                    v3d.IsSectionBoxActive = false;
                    txRestore.Commit();
                }

                uiview?.ZoomToFit();
                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    images = new string[] { imgOverview, imgSection, imgClose }
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
