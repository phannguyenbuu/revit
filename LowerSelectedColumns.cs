using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class LowerSelectedColumns
    {
        private static double ToM(double ft) => ft * 0.3048;
        private static double M2Ft(double m) => m / 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var selIds = uidoc.Selection.GetElementIds().ToList();
                if (selIds.Count == 0)
                {
                    selIds = new List<ElementId>
                    {
                        new ElementId(2361381L),
                        new ElementId(2361382L),
                        new ElementId(2361383L),
                        new ElementId(2361388L),
                        new ElementId(2361389L),
                        new ElementId(2361390L)
                    };
                }

                Level level4 = doc.GetElement(new ElementId(2360634L)) as Level
                    ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => Math.Abs(ToM(l.Elevation) - 10.8) < 0.05);

                if (level4 == null) return new { error = "Level 10.8m (Tầng 4) not found" };

                var updated = new List<object>();

                using (Transaction t = new Transaction(doc, "Ha cot xuong cao 10800"))
                {
                    t.Start();

                    foreach (var id in selIds)
                    {
                        var el = doc.GetElement(id);
                        if (el == null) continue;

                        var topLevelParam = el.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        var topOffsetParam = el.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                        if (topLevelParam != null && !topLevelParam.IsReadOnly)
                        {
                            topLevelParam.Set(level4.Id);
                        }
                        if (topOffsetParam != null && !topOffsetParam.IsReadOnly)
                        {
                            topOffsetParam.Set(0.0);
                        }

                        doc.Regenerate();

                        var bb = el.get_BoundingBox(null);
                        double zMin = bb != null ? ToM(bb.Min.Z) : 0;
                        double zMax = bb != null ? ToM(bb.Max.Z) : 0;
                        double height = zMax - zMin;

                        updated.Add(new
                        {
                            id = id.Value,
                            name = el.Name,
                            topLevel = level4.Name,
                            topElevation_m = ToM(level4.Elevation),
                            zMin,
                            zMax,
                            height_m = Math.Round(height, 3),
                            height_mm = Math.Round(height * 1000, 1)
                        });
                    }

                    t.Commit();
                }

                // Export 3D view to verify visual appearance
                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string img3dPath = Path.Combine(folder, "revit_3d_lowered_columns.jpg");

                var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview3d?.ZoomToFit();

                    if (File.Exists(img3dPath)) File.Delete(img3dPath);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = img3dPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt3d);
                }

                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                }
                catch { }

                return new
                {
                    success = true,
                    targetLevel = level4.Name,
                    targetElevation = 10800,
                    count = updated.Count,
                    updatedColumns = updated,
                    img3dPath,
                    docSaved
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
