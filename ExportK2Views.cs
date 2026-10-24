using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportK2Views
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                // 1. Save doc
                try
                {
                    doc.Save(new SaveOptions());
                }
                catch { }

                // 2. Find 3D View
                var view3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3D == null) return new { error = "No 3D view" };

                using (var tx = new Transaction(doc, "Set 3D View Style"))
                {
                    tx.Start();
                    view3D.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = view3D.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    view3D.SetViewDisplayModel(vdm);
                    tx.Commit();
                }

                uidoc.ActiveView = view3D;

                string outFull3D = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_full_3d.png";
                string outCloseup = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_closeup_3d.png";

                if (File.Exists(outFull3D)) try { File.Delete(outFull3D); } catch { }
                if (File.Exists(outCloseup)) try { File.Delete(outCloseup); } catch { }

                // Full 3D Export
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == view3D.Id);
                uiview?.ZoomToFit();

                var optFull = new ImageExportOptions
                {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = outFull3D,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                optFull.SetViewsAndSheets(new List<ElementId> { view3D.Id });
                doc.ExportImage(optFull);

                // Close-up Export: Zoom to Truc 1 Stack
                // Stack bounds in meters: X[0.0, 1.5], Y[11.5, 13.5], Z[0.0, 12.0]
                XYZ pMin = new XYZ(-1.0 * M2FT, 11.0 * M2FT, 0.0 * M2FT);
                XYZ pMax = new XYZ(2.0 * M2FT, 14.0 * M2FT, 12.0 * M2FT);
                uiview?.ZoomAndCenterRectangle(pMin, pMax);

                var optClose = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outCloseup,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(optClose);

                // Find the 3 placed windows and 4 stacked walls to get their exact status
                var k2Windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(w => w.Symbol.FamilyName == "Window_K2")
                    .Select(w =>
                    {
                        var loc = (w.Location as LocationPoint)?.Point;
                        return new
                        {
                            id = w.Id.Value,
                            mark = w.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                            x = loc != null ? Math.Round(loc.X / M2FT, 3) : 0,
                            y = loc != null ? Math.Round(loc.Y / M2FT, 3) : 0,
                            z = loc != null ? Math.Round(loc.Z / M2FT, 3) : 0
                        };
                    })
                    .ToList();

                var stackWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var lc = (w.Location as LocationCurve)?.Curve;
                        if (lc == null) return false;
                        double x = lc.GetEndPoint(0).X / M2FT;
                        double y0 = lc.GetEndPoint(0).Y / M2FT;
                        double y1 = lc.GetEndPoint(1).Y / M2FT;
                        return Math.Abs(x - 0.55) < 0.05 && Math.Abs(Math.Min(y0, y1) - 12.09375) < 0.05;
                    })
                    .Select(w =>
                    {
                        var baseOffset = w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() ?? 0;
                        var height = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() ?? 0;
                        return new
                        {
                            id = w.Id.Value,
                            typeName = w.WallType.Name,
                            baseOffsetM = Math.Round(baseOffset / M2FT, 3),
                            heightM = Math.Round(height / M2FT, 3),
                            topM = Math.Round((baseOffset + height) / M2FT, 3)
                        };
                    })
                    .OrderBy(w => w.baseOffsetM)
                    .ToList();

                return new
                {
                    success = true,
                    outFull3D,
                    outCloseup,
                    k2Windows,
                    stackWalls
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
