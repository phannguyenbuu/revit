using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportDoorsD7Zoom
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = doc?.ActiveView;
            if (view == null) return new { error = "No active view" };

            var d1 = doc.GetElement(new ElementId(2360900L)) as FamilyInstance;
            var d2 = doc.GetElement(new ElementId(2360910L)) as FamilyInstance;

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            // Export full plan first
            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = Path.Combine(outDir, "revit_doors_d7_current_view.png"),
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(opt);

            return new
            {
                success = true,
                d1_info = new {
                    id = d1?.Id.Value,
                    sym = d1?.Symbol.Name,
                    fam = d1?.Symbol.FamilyName,
                    handFlipped = d1?.HandFlipped,
                    facingFlipped = d1?.FacingFlipped
                },
                d2_info = new {
                    id = d2?.Id.Value,
                    sym = d2?.Symbol.Name,
                    fam = d2?.Symbol.FamilyName,
                    handFlipped = d2?.HandFlipped,
                    facingFlipped = d2?.FacingFlipped
                }
            };
        }
    }
}
