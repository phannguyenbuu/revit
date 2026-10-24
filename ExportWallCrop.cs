using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportWallCrop
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (viewTang1 == null) return new { error = "No Tang 1 view" };

            // Set crop box around walls: X in [24, 29], Y in [6.5, 14.5]
            using (var tx = new Transaction(doc, "Crop Tang 1 to Walls"))
            {
                tx.Start();
                viewTang1.CropBoxActive = true;
                viewTang1.CropBoxVisible = false;

                var bb = viewTang1.CropBox;
                bb.Min = new XYZ(24.0 * M2FT, 6.5 * M2FT, bb.Min.Z);
                bb.Max = new XYZ(29.0 * M2FT, 14.5 * M2FT, bb.Max.Z);
                viewTang1.CropBox = bb;

                tx.Commit();
            }

            string outPlan = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_crop_walls.png";
            if (File.Exists(outPlan)) { try { File.Delete(outPlan); } catch { } }

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.SetOfViews,
                FilePath = outPlan,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 1920,
                ZoomType = ZoomFitType.FitToPage
            };
            opt.SetViewsAndSheets(new List<ElementId> { viewTang1.Id });

            doc.ExportImage(opt);

            // Re-disable crop box so user has full view
            using (var tx = new Transaction(doc, "Reset Crop"))
            {
                tx.Start();
                viewTang1.CropBoxActive = false;
                tx.Commit();
            }

            return new
            {
                success = true,
                exported = outPlan
            };
        }
    }
}
