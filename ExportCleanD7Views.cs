using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCleanD7Views
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            // Clear selection so no blue highlight
            uidoc.Selection.SetElementIds(new List<ElementId>());

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
                FilePath = Path.Combine(outDir, "revit_d7_1_clean.png"),
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
                FilePath = Path.Combine(outDir, "revit_d7_2_clean.png"),
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(opt2);

            // Zoom to entire floor plan
            uiview?.ZoomToFit();
            var optPlan = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = Path.Combine(outDir, "revit_tang1_overview_clean.png"),
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(optPlan);

            return new { success = true };
        }
    }
}
