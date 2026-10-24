using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCurrent3DViewExact
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
                    .FirstOrDefault(v => !v.IsTemplate && v.Name == "{3D}");

                if (view3D == null) return new { error = "No {3D} view" };

                // Create a dedicated Section Box view named "3D - K2 Facade"
                var vft3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewFamilyType))
                    .Cast<ViewFamilyType>()
                    .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

                string boxViewName = "3D - K2 Facade";
                View3D boxView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => v.Name == boxViewName);

                using (Transaction tx = new Transaction(doc, "Setup 3D - K2 Facade View"))
                {
                    tx.Start();

                    if (boxView == null)
                    {
                        boxView = View3D.CreateIsometric(doc, vft3D.Id);
                        boxView.Name = boxViewName;
                    }

                    // Section box framing the K2 bay on Truc 1
                    // X: [-1.0m, 2.5m], Y: [10.5m, 14.5m], Z: [-0.5m, 13.0m]
                    BoundingBoxXYZ sb = new BoundingBoxXYZ();
                    sb.Min = new XYZ(-1.0 * M2FT, 10.5 * M2FT, -0.5 * M2FT);
                    sb.Max = new XYZ(2.5 * M2FT, 14.5 * M2FT, 13.0 * M2FT);

                    boxView.SetSectionBox(sb);
                    boxView.IsSectionBoxActive = true;
                    boxView.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = boxView.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    boxView.SetViewDisplayModel(vdm);

                    tx.Commit();
                }

                // Switch UI to boxView
                uidoc.ActiveView = boxView;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == boxView.Id);
                uiview?.ZoomToFit();

                // Select the 7 elements
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

                // Export image of this Section Box view
                string outBoxImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_sectionbox_3d.png";
                if (File.Exists(outBoxImg)) try { File.Delete(outBoxImg); } catch { }

                var expOpt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outBoxImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(expOpt);

                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    boxViewName,
                    selectedCount = allTargetIds.Count,
                    outBoxImg
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
