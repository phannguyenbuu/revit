using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateDedicated3DView
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // 1. Find ViewFamilyType for 3D
                var vft3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewFamilyType))
                    .Cast<ViewFamilyType>()
                    .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

                if (vft3D == null) return new { error = "No 3D ViewFamilyType found" };

                string viewName = "3D_K2_Truc1";
                View3D view = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => v.Name == viewName);

                using (Transaction tx = new Transaction(doc, "Create/Setup 3D_K2_Truc1 View"))
                {
                    tx.Start();

                    if (view == null)
                    {
                        view = View3D.CreateIsometric(doc, vft3D.Id);
                        view.Name = viewName;
                    }

                    // Camera: Look directly at Truc 1 bay from the outside (West side)
                    // Bay center: X = 0.55m, Y = 12.54m, Z = 6.0m
                    XYZ target = new XYZ(0.55 * M2FT, 12.54 * M2FT, 6.0 * M2FT);
                    // Eye: at X = -10.0m (outside west wall), Y = 10.0m, Z = 7.5m
                    XYZ eye = new XYZ(-10.0 * M2FT, 10.0 * M2FT, 7.5 * M2FT);
                    XYZ forward = (target - eye).Normalize();
                    XYZ right = forward.CrossProduct(XYZ.BasisZ).Normalize();
                    XYZ up = right.CrossProduct(forward).Normalize();

                    view.SetOrientation(new ViewOrientation3D(eye, up, forward));
                    view.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = view.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    view.SetViewDisplayModel(vdm);

                    // Ensure uncropped
                    view.CropBoxActive = false;
                    view.IsSectionBoxActive = false;

                    tx.Commit();
                }

                // Switch active view
                uidoc.ActiveView = view;

                // Zoom to fit K2 stack
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ pMin = new XYZ(-2.0 * M2FT, 10.5 * M2FT, -0.5 * M2FT);
                    XYZ pMax = new XYZ(3.0 * M2FT, 14.5 * M2FT, 12.5 * M2FT);
                    uiview.ZoomAndCenterRectangle(pMin, pMax);
                }

                // Select the 7 elements so they glow in Revit UI
                var k2Windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(w => w.Symbol.FamilyName == "Window_K2")
                    .Select(w => w.Id)
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
                        return Math.Abs(x - 0.55) < 0.05 && Math.Abs(y0 - 12.09375) < 0.05;
                    })
                    .Select(w => w.Id)
                    .ToList();

                var allTargetIds = k2Windows.Concat(stackWalls).ToList();
                uidoc.Selection.SetElementIds(allTargetIds);
                uidoc.RefreshActiveView();

                // Save doc
                try { doc.Save(new SaveOptions()); } catch { }

                // Export current view image
                string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_dedicated_view.png";
                if (File.Exists(outImg)) try { File.Delete(outImg); } catch { }

                var expOpt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(expOpt);

                return new
                {
                    success = true,
                    viewName,
                    selectedCount = allTargetIds.Count,
                    outImg
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
