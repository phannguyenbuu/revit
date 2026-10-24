using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportUnifiedStackView
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active Revit doc" };

                // 1. Find Window_K2_Stack instance
                var stackInst = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .FirstOrDefault(f => f.Symbol.FamilyName == "Window_K2_Stack");

                if (stackInst == null) return new { error = "Window_K2_Stack instance not found" };

                // Select the single unified instance in UI
                uidoc.Selection.SetElementIds(new List<ElementId> { stackInst.Id });

                // 2. Setup 3D Section Box view "3D - K2 Facade"
                string boxViewName = "3D - K2 Facade";
                View3D boxView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => v.Name == boxViewName);

                var vft3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewFamilyType))
                    .Cast<ViewFamilyType>()
                    .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

                using (Transaction tx = new Transaction(doc, "Setup Unified Stack 3D View"))
                {
                    tx.Start();
                    if (boxView == null)
                    {
                        boxView = View3D.CreateIsometric(doc, vft3D.Id);
                        boxView.Name = boxViewName;
                    }

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

                uidoc.ActiveView = boxView;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == boxView.Id);
                uiview?.ZoomToFit();
                uidoc.RefreshActiveView();

                string outBoxImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_unified_stack_3d.png";
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

                // 3. Export West Facade Elevation to see the full elevation
                var westView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View))
                    .Cast<View>()
                    .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("West") || v.Name.Contains("Tây") || v.Name == "Elevations - West"));

                string outWestImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_k2_unified_stack_west.png";
                if (westView != null)
                {
                    if (File.Exists(outWestImg)) try { File.Delete(outWestImg); } catch { }
                    uidoc.ActiveView = westView;
                    var uiWest = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == westView.Id);
                    uiWest?.ZoomToFit();
                    uidoc.RefreshActiveView();

                    var expWest = new ImageExportOptions
                    {
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        FilePath = outWestImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        PixelSize = 2500,
                        ZoomType = ZoomFitType.FitToPage
                    };
                    doc.ExportImage(expWest);
                }

                // Restore active view back to 3D boxView
                uidoc.ActiveView = boxView;

                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    instanceId = stackInst.Id.Value,
                    familyName = stackInst.Symbol.FamilyName,
                    typeName = stackInst.Symbol.Name,
                    outBoxImg,
                    outWestImg
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
