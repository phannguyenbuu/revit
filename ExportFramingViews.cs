using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportFramingViews
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string artifactDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var vft3D = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

            if (vft3D == null) return new { error = "No 3D view family type" };

            // 1. Create or get "3D - Structural Framing" view
            string viewNameFull = "3D - He Ket Cau Dam San";
            View3D viewFull = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => v.Name == viewNameFull);

            // 2. Create or get "3D - Section Cut Framing" view
            string viewNameSec = "3D - Cat Ngang Khung Ket Cau";
            View3D viewSec = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => v.Name == viewNameSec);

            using (var tx = new Transaction(doc, "Setup Structural Framing Views"))
            {
                tx.Start();

                if (viewFull == null)
                {
                    viewFull = View3D.CreateIsometric(doc, vft3D.Id);
                    viewFull.Name = viewNameFull;
                }
                viewFull.IsSectionBoxActive = false;
                viewFull.DisplayStyle = DisplayStyle.FlatColors;
                var vdmFull = viewFull.GetViewDisplayModel();
                vdmFull.SmoothEdges = true;
                viewFull.SetViewDisplayModel(vdmFull);

                if (viewSec == null)
                {
                    viewSec = View3D.CreateIsometric(doc, vft3D.Id);
                    viewSec.Name = viewNameSec;
                }
                // Section box cutting through X: [-2m, 20m], Y: [-2m, 16m], Z: [-1m, 18m]
                BoundingBoxXYZ sb = new BoundingBoxXYZ();
                sb.Min = new XYZ(-2.0 * M2FT, -2.0 * M2FT, -1.0 * M2FT);
                sb.Max = new XYZ(20.0 * M2FT, 16.0 * M2FT, 18.0 * M2FT);
                viewSec.SetSectionBox(sb);
                viewSec.IsSectionBoxActive = true;
                viewSec.DisplayStyle = DisplayStyle.FlatColors;
                var vdmSec = viewSec.GetViewDisplayModel();
                vdmSec.SmoothEdges = true;
                viewSec.SetViewDisplayModel(vdmSec);

                tx.Commit();
            }

            var exportedFiles = new List<string>();

            // Export View 1: 3D Full Overview
            uidoc.ActiveView = viewFull;
            uidoc.Selection.SetElementIds(new List<ElementId>()); // Clear selection
            var uiviewFull = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == viewFull.Id);
            uiviewFull?.ZoomToFit();

            string fullImgPath = Path.Combine(artifactDir, "revit_framing_overview_3d.png");
            if (File.Exists(fullImgPath)) try { File.Delete(fullImgPath); } catch { }

            var expOpt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = fullImgPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(expOpt);
            exportedFiles.Add(fullImgPath);

            // Export View 2: Section Box Cut
            uidoc.ActiveView = viewSec;
            var uiviewSec = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == viewSec.Id);
            uiviewSec?.ZoomToFit();

            string secImgPath = Path.Combine(artifactDir, "revit_framing_section_cut_3d.png");
            if (File.Exists(secImgPath)) try { File.Delete(secImgPath); } catch { }

            expOpt.FilePath = secImgPath;
            doc.ExportImage(expOpt);
            exportedFiles.Add(secImgPath);

            // Save doc
            try { doc.Save(new SaveOptions()); } catch { }

            return new
            {
                success = true,
                exportedFiles
            };
        }
    }
}
