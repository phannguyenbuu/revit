using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetFloorPlanFramingAndExport
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var viewConfigs = new List<(long id, string filename)>
            {
                (312L, "plan_tang_1_overview.png"),
                (695L, "plan_tang_2_overview.png"),
                (1727632L, "plan_tang_3_overview.png"),
                (2409349L, "plan_tang_4_overview.png"),
            };

            var catElev = doc.Settings.Categories.get_Item(BuiltInCategory.OST_ElevationMarks);

            // Building world bounds (in mm):
            // Center roughly at X = 16900, Y = 7600
            // World bounds:
            double worldMinX = -13500.0; // mm
            double worldMaxX = 47500.0;  // mm
            double worldMinY = -6500.0;  // mm
            double worldMaxY = 21500.0;  // mm

            using (var trans = new Transaction(doc, "Set Tight Uniform Floor Plan Framing"))
            {
                trans.Start();

                foreach (var item in viewConfigs)
                {
                    var v = doc.GetElement(new ElementId(item.id)) as ViewPlan;
                    if (v == null) continue;

                    if (catElev != null && v.CanCategoryBeHidden(catElev.Id))
                    {
                        v.SetCategoryHidden(catElev.Id, true);
                    }

                    // Turn off annotation crop so it doesn't stretch or outline the view
                    var pAnn = v.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE);
                    if (pAnn != null && !pAnn.IsReadOnly)
                    {
                        pAnn.Set(0);
                    }

                    v.CropBoxActive = true;
                    v.CropBoxVisible = false;

                    var curBox = v.CropBox;
                    var orig = curBox.Transform.Origin;

                    // Convert world bounds to local crop box bounds
                    double localMinX = (worldMinX - (orig.X * 304.8)) / 304.8;
                    double localMaxX = (worldMaxX - (orig.X * 304.8)) / 304.8;
                    double localMinY = (worldMinY - (orig.Y * 304.8)) / 304.8;
                    double localMaxY = (worldMaxY - (orig.Y * 304.8)) / 304.8;

                    var newBox = new BoundingBoxXYZ();
                    newBox.Transform = curBox.Transform;
                    newBox.Min = new XYZ(localMinX, localMinY, curBox.Min.Z);
                    newBox.Max = new XYZ(localMaxX, localMaxY, curBox.Max.Z);

                    v.CropBox = newBox;
                }

                trans.Commit();
            }

            // Export each floor plan
            var exported = new List<object>();
            foreach (var item in viewConfigs)
            {
                var v = doc.GetElement(new ElementId(item.id)) as View;
                if (v == null) continue;

                string filePath = Path.Combine(outDir, item.filename);

                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.SetOfViews,
                    FilePath = filePath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 3500,
                    ZoomType = ZoomFitType.FitToPage
                };
                opt.SetViewsAndSheets(new List<ElementId> { v.Id });

                try
                {
                    doc.ExportImage(opt);
                    exported.Add(new { id = item.id, name = v.Name, filePath, status = "Success" });
                }
                catch (Exception ex)
                {
                    exported.Add(new { id = item.id, name = v.Name, error = ex.Message });
                }
            }

            return new { success = true, exported };
        }
    }
}
