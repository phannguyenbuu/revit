using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAndFixStairPath
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"));

            if (plan == null) return new { error = "View not found" };

            var stairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .ToList();

            var paths = new FilteredElementCollector(doc, plan.Id)
                .OfCategory(BuiltInCategory.OST_StairsPaths)
                .WhereElementIsNotElementType()
                .Cast<StairsPath>()
                .ToList();

            var pathInfo = paths.Select(p => new {
                id = p.Id.Value,
                stairId = p.StairsId.HostElementId.Value
            }).ToList();

            // Find StairsPathType
            var pathType = new FilteredElementCollector(doc)
                .OfClass(typeof(StairsPathType))
                .Cast<StairsPathType>()
                .FirstOrDefault();

            int addedPaths = 0;
            using (Transaction t = new Transaction(doc, "Ensure StairsPath for all stairs"))
            {
                t.Start();
                foreach (var st in stairs)
                {
                    bool hasPath = paths.Any(p => p.StairsId.HostElementId == st.Id);
                    if (!hasPath && pathType != null)
                    {
                        try
                        {
                            var linkElemId = new LinkElementId(st.Id);
                            StairsPath.Create(doc, linkElemId, pathType.Id, plan.Id);
                            addedPaths++;
                        }
                        catch { }
                    }
                }
                t.Commit();
            }

            // Export clean unselected image of bay 9-10
            uidoc.ActiveView = plan;
            uidoc.Selection.SetElementIds(new List<ElementId>());

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string stair910CleanImg = Path.Combine(folder, "stair_bay_9_10_clean.png");
            string bothStairsCleanImg = Path.Combine(folder, "both_stairs_clean.png");

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == plan.Id);

            // Bay 9-10 close up
            uiview?.ZoomAndCenterRectangle(new XYZ(29.0 * M2FT, 9.5 * M2FT, 0.0), new XYZ(34.0 * M2FT, 15.6 * M2FT, 0.0));
            try
            {
                if (File.Exists(stair910CleanImg)) File.Delete(stair910CleanImg);
                var expOpt = new ImageExportOptions
                {
                    FilePath = stair910CleanImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            // Both stairs zoomed to upper half of building (Y from 7.0 to 16.0, X from 2.0 to 36.0)
            uiview?.ZoomAndCenterRectangle(new XYZ(2.0 * M2FT, 6.5 * M2FT, 0.0), new XYZ(36.0 * M2FT, 16.5 * M2FT, 0.0));
            try
            {
                if (File.Exists(bothStairsCleanImg)) File.Delete(bothStairsCleanImg);
                var expOpt = new ImageExportOptions
                {
                    FilePath = bothStairsCleanImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3500
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new {
                stairsCount = stairs.Count,
                stairs = stairs.Select(s => s.Id.Value).ToList(),
                existingPaths = pathInfo,
                addedPaths,
                stair910Image = stair910CleanImg,
                bothStairsImage = bothStairsCleanImg
            };
        }
    }
}
