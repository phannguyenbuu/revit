using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ViewExporter
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find a floor plan view
            var planViews = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                .OrderBy(v => v.Name)
                .Select(v => new { id = v.Id.Value, name = v.Name })
                .ToList();

            string targetName = args.TryGetProperty("viewName", out var vn) ? vn.GetString() ?? "" : "";
            ViewPlan targetPlan = null;
            if (!string.IsNullOrEmpty(targetName))
            {
                targetPlan = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => v.Name.Equals(targetName, StringComparison.OrdinalIgnoreCase));
            }
            if (targetPlan == null)
            {
                targetPlan = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan);
            }

            if (targetPlan != null)
            {
                string outPath = args.GetProperty("outputPath").GetString()!;
                var opts = new ImageExportOptions
                {
                    FilePath = outPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.SetOfViews,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 1920
                };
                opts.SetViewsAndSheets(new System.Collections.Generic.List<ElementId> { targetPlan.Id });

                doc.ExportImage(opts);
                return new { success = true, exportedView = targetPlan.Name, planViews = planViews };
            }

            return new { error = "No floor plan found", planViews = planViews };
        }
    }
}
