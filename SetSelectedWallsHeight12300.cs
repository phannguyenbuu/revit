using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetSelectedWallsHeight12300
    {
        private const double FT2M = 0.3048;
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Get selected elements or default to the 3 target walls
            var selIds = uidoc.Selection.GetElementIds().ToList();
            if (selIds.Count == 0)
            {
                selIds = new List<ElementId>
                {
                    new ElementId(2361585L),
                    new ElementId(2361586L),
                    new ElementId(2361587L)
                };
            }

            double targetHeightMm = 12300.0;
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("heightMm", out var hProp))
            {
                targetHeightMm = hProp.GetDouble();
            }
            double targetHeightFt = targetHeightMm / 304.8;

            var updatedWalls = new List<object>();

            using (var tx = new Transaction(doc, "Set Selected Walls Height to 12300mm"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new GenericWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                foreach (var id in selIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem is not Wall wall) continue;

                    // Set Top Constraint to Unconnected
                    var pTop = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                    if (pTop != null && !pTop.IsReadOnly)
                    {
                        pTop.Set(ElementId.InvalidElementId);
                    }

                    // Set Unconnected Height to 12300 mm
                    var pHeight = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    if (pHeight != null && !pHeight.IsReadOnly)
                    {
                        pHeight.Set(targetHeightFt);
                    }

                    // Ensure Base Offset is 0
                    var pBaseOff = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                    if (pBaseOff != null && !pBaseOff.IsReadOnly)
                    {
                        pBaseOff.Set(0.0);
                    }

                    doc.Regenerate();

                    var curHeight = pHeight?.AsDouble() * 304.8 ?? 0;
                    updatedWalls.Add(new
                    {
                        id = wall.Id.Value,
                        wallType = wall.WallType.Name,
                        unconnectedHeightMm = Math.Round(curHeight, 1)
                    });
                }

                tx.Commit();
            }

            // Keep the updated walls selected so user sees them highlighted in Revit
            try
            {
                uidoc.Selection.SetElementIds(selIds);
            }
            catch { }

            // Export verification image
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string outImg = Path.Combine(folder, "revit_walls_height_12300_selected.png");
            if (File.Exists(outImg)) { try { File.Delete(outImg); } catch { } }

            try
            {
                var view3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview?.ZoomToFit();

                    var expOpts = new ImageExportOptions
                    {
                        FilePath = outImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpts);
                }
            }
            catch { }

            return new
            {
                success = true,
                targetHeightMm,
                updatedWalls,
                image = outImg
            };
        }
    }
}
