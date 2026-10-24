using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FlipD4Doors
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // Find the 3 D4 doors: Mark D4-1, D4-2, D4-3
            var d4Doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(d =>
                {
                    var mark = d.get_Parameter(BuiltInParameter.DOOR_NUMBER)?.AsString();
                    return mark == "D4-1" || mark == "D4-2" || mark == "D4-3";
                })
                .ToList();

            using (var tx = new Transaction(doc, "AI Copilot: Flip D4 Doors to South"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WallAWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                foreach (var d in d4Doors)
                {
                    // If door is facing North (+Y), flip it so it faces South (-Y)
                    if (d.FacingOrientation.Y > 0)
                    {
                        d.flipFacing();
                    }
                    // In CAD, the hinge was on the left (West side), door leaf opens to the right (East side)
                    // Let's check HandOrientation
                    if (d.HandOrientation.X < 0)
                    {
                        d.flipHand();
                    }
                }

                tx.Commit();
            }

            // Export updated image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wall_b_doors_final.png";
            try
            {
                var activeView = uidoc.ActiveView;
                var expOpt = new ImageExportOptions
                {
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560,
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                flippedCount = d4Doors.Count,
                doors = d4Doors.Select(d => new
                {
                    id = d.Id.Value,
                    mark = d.get_Parameter(BuiltInParameter.DOOR_NUMBER)?.AsString(),
                    facingY = d.FacingOrientation.Y,
                    handX = d.HandOrientation.X
                }),
                exportImage = outImgPath
            };
        }
    }
}
