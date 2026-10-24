using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportWestFacade
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var view3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3D == null) return new { error = "No 3D view" };

                // Target: Truc 1 bay center
                XYZ target = new XYZ(0.55 * M2FT, 12.54 * M2FT, 6.0 * M2FT);
                // Eye: Looking towards Truc 1 from West-Southwest
                XYZ eye = new XYZ(-12.0 * M2FT, 8.0 * M2FT, 9.0 * M2FT);
                XYZ forward = (target - eye).Normalize();
                XYZ right = forward.CrossProduct(XYZ.BasisZ).Normalize();
                XYZ up = right.CrossProduct(forward).Normalize();

                using (var tx = new Transaction(doc, "Orient 3D to West Facade"))
                {
                    tx.Start();
                    view3D.SetOrientation(new ViewOrientation3D(eye, up, forward));
                    view3D.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = view3D.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    view3D.SetViewDisplayModel(vdm);
                    tx.Commit();
                }

                uidoc.ActiveView = view3D;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == view3D.Id);
                uiview?.ZoomToFit();

                string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_west_facade.png";
                if (File.Exists(outPath)) try { File.Delete(outPath); } catch { }

                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt);

                // Also export direct West Elevation view if exists
                var westView = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("West") || v.Name.Contains("Tây")));

                string outWestElev = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_west_elevation.png";
                if (westView != null)
                {
                    if (File.Exists(outWestElev)) try { File.Delete(outWestElev); } catch { }
                    var optElev = new ImageExportOptions
                    {
                        ExportRange = ExportRange.SetOfViews,
                        FilePath = outWestElev,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        PixelSize = 2500,
                        ZoomType = ZoomFitType.FitToPage
                    };
                    optElev.SetViewsAndSheets(new List<ElementId> { westView.Id });
                    doc.ExportImage(optElev);
                }

                return new { success = true, outPath, outWestElev, westViewName = westView?.Name };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
