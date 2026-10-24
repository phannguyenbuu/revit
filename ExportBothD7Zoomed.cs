using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportBothD7Zoomed
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

            var d1 = doc.GetElement(new ElementId(2360900L)) as FamilyInstance;
            var d2 = doc.GetElement(new ElementId(2360910L)) as FamilyInstance;

            // Zoom D1
            var loc1 = (d1.Location as LocationPoint).Point;
            double w = 2500.0 / 304.8;
            uiview?.ZoomAndCenterRectangle(new XYZ(loc1.X - w, loc1.Y - w, 0), new XYZ(loc1.X + w, loc1.Y + w, 0));

            var opt1 = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = Path.Combine(outDir, "revit_d7_1_zoom.png"),
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(opt1);

            // Zoom D2
            var loc2 = (d2.Location as LocationPoint).Point;
            uiview?.ZoomAndCenterRectangle(new XYZ(loc2.X - w, loc2.Y - w, 0), new XYZ(loc2.X + w, loc2.Y + w, 0));

            var opt2 = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = Path.Combine(outDir, "revit_d7_2_zoom.png"),
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(opt2);

            return new
            {
                success = true,
                d1_img = "revit_d7_1_zoom.png",
                d2_img = "revit_d7_2_zoom.png",
                d1 = new {
                    hand = new { x = d1.HandOrientation.X, y = d1.HandOrientation.Y },
                    face = new { x = d1.FacingOrientation.X, y = d1.FacingOrientation.Y },
                    handFlipped = d1.HandFlipped,
                    facingFlipped = d1.FacingFlipped
                },
                d2 = new {
                    hand = new { x = d2.HandOrientation.X, y = d2.HandOrientation.Y },
                    face = new { x = d2.FacingOrientation.X, y = d2.FacingOrientation.Y },
                    handFlipped = d2.HandFlipped,
                    facingFlipped = d2.FacingFlipped
                }
            };
        }
    }
}
