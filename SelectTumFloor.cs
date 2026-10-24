using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SelectTumFloor
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active Revit document" };

                // Floor ID 2381771
                ElementId targetId = new ElementId(2381771);
                var floor = doc.GetElement(targetId) as Floor;

                // Fallback: highest elevation floor if specific ID not found
                if (floor == null)
                {
                    floor = new FilteredElementCollector(doc)
                        .OfClass(typeof(Floor))
                        .Cast<Floor>()
                        .OrderByDescending(f => (doc.GetElement(f.LevelId) as Level)?.Elevation ?? 0)
                        .FirstOrDefault();
                    if (floor != null) targetId = floor.Id;
                }

                if (floor == null) return new { error = "Could not find floor element" };

                // Set selection in Revit UI
                var selList = new List<ElementId> { targetId };
                uidoc.Selection.SetElementIds(selList);

                // Show elements in UI
                uidoc.ShowElements(selList);
                uidoc.RefreshActiveView();

                var lvl = doc.GetElement(floor.LevelId) as Level;
                var areaM2 = Math.Round(floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2);

                // Export current active view to show user the selection highlight
                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string selImg = Path.Combine(brainDir, "revit_tum_slab_selected.png");
                if (File.Exists(selImg)) File.Delete(selImg);

                var expOpt = new ImageExportOptions
                {
                    FilePath = selImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 1920
                };
                doc.ExportImage(expOpt);

                return new
                {
                    success = true,
                    selectedElementId = targetId.Value,
                    level = lvl?.Name,
                    elevationM = (lvl?.Elevation ?? 0) * FT2M,
                    netAreaM2 = areaM2,
                    activeView = uidoc.ActiveView?.Name
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
