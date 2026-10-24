using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetSelectedWallsHeight13350
    {
        private const double FT2MM = 304.8;
        private const double MM2FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document in Revit" };

            // 1. Get selected walls or fallback
            var selIds = uidoc.Selection.GetElementIds().ToList();
            var wallIds = new List<ElementId>();

            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem is Wall)
                {
                    wallIds.Add(id);
                }
            }

            if (wallIds.Count == 0)
            {
                var fallbackIds = new long[] { 2361558L, 2361559L, 2361560L, 2361561L, 2378823L, 2378824L, 2378825L, 2378826L };
                foreach (var fid in fallbackIds)
                {
                    var elem = doc.GetElement(new ElementId(fid));
                    if (elem is Wall)
                    {
                        wallIds.Add(elem.Id);
                    }
                }
            }

            double targetHeightMm = 13350.0;
            double targetHeightFt = targetHeightMm * MM2FT;

            var wallResults = new List<object>();

            using (var tx = new Transaction(doc, "Set Selected Walls Height to 13350mm"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new GenericWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                foreach (var id in wallIds)
                {
                    var wall = doc.GetElement(id) as Wall;
                    if (wall == null) continue;

                    var pTop = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                    if (pTop != null && !pTop.IsReadOnly)
                    {
                        pTop.Set(ElementId.InvalidElementId);
                    }

                    var pHeight = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    if (pHeight != null && !pHeight.IsReadOnly)
                    {
                        pHeight.Set(targetHeightFt);
                    }

                    var pBaseOff = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                    if (pBaseOff != null && !pBaseOff.IsReadOnly)
                    {
                        pBaseOff.Set(0.0);
                    }

                    doc.Regenerate();

                    var bb = wall.get_BoundingBox(null);
                    double curHeight = pHeight?.AsDouble() * FT2MM ?? 0.0;

                    wallResults.Add(new
                    {
                        id = wall.Id.Value,
                        name = wall.Name,
                        wallType = wall.WallType.Name,
                        heightMm = Math.Round(curHeight, 1),
                        bboxMinZ = bb != null ? Math.Round(bb.Min.Z * FT2MM, 1) : 0,
                        bboxMaxZ = bb != null ? Math.Round(bb.Max.Z * FT2MM, 1) : 0
                    });
                }

                tx.Commit();
            }

            // Restore selection of the modified walls
            try
            {
                uidoc.Selection.SetElementIds(wallIds);
            }
            catch { }

            // Export images
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var exportedFiles = new List<string>();

            try
            {
                var view3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (view3D != null)
                {
                    try { uidoc.ActiveView = view3D; } catch { }
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);
                    uiview?.ZoomToFit();

                    string path3D = Path.Combine(outDir, "revit_walls_13350_overview_3d.png");
                    if (File.Exists(path3D)) try { File.Delete(path3D); } catch { }

                    var opt3D = new ImageExportOptions
                    {
                        FilePath = path3D,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(opt3D);
                    exportedFiles.Add(path3D);
                }
            }
            catch (Exception ex)
            {
                wallResults.Add(new { exportError = ex.Message });
            }

            return new
            {
                success = true,
                targetHeightMm,
                modifiedWallsCount = wallResults.Count,
                walls = wallResults,
                exportedFiles
            };
        }
    }
}
