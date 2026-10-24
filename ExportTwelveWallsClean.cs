using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportTwelveWallsClean
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Deselect
            uidoc.Selection.SetElementIds(new List<ElementId>());

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(31.5 * M2FT, -0.8 * M2FT, 0.0);
                XYZ pMax = new XYZ(37.5 * M2FT, 1.2 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            string outImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_12walls100_clean.png";
            if (File.Exists(outImgPath)) { try { File.Delete(outImgPath); } catch { } }

            try
            {
                var expOpt = new ImageExportOptions
                {
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2500
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = ex.Message };
            }

            return new
            {
                success = true,
                exported = outImgPath
            };
        }
    }
}
