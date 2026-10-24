using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class MoveStackToZero
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var elem = doc.GetElement(new ElementId(2377860)) as FamilyInstance;
                if (elem == null) return new { error = "Element 2377860 not found" };

                var bbBefore = elem.get_BoundingBox(null);
                double minZBefore = bbBefore.Min.Z * FT2M;

                // We want minZ to be exactly 0.000m
                double deltaZ = 0.0 - minZBefore;

                using (Transaction tx = new Transaction(doc, "Align Stack Bottom to 0.000"))
                {
                    tx.Start();
                    if (Math.Abs(deltaZ) > 0.0001)
                    {
                        ElementTransformUtils.MoveElement(doc, elem.Id, new XYZ(0, 0, deltaZ * M2FT));
                    }
                    tx.Commit();
                }

                var bbAfter = elem.get_BoundingBox(null);
                double minZAfter = bbAfter.Min.Z * FT2M;
                double maxZAfter = bbAfter.Max.Z * FT2M;

                // Re-export 3D box view
                string boxViewName = "3D - K2 Facade";
                View3D boxView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => v.Name == boxViewName);

                if (boxView != null)
                {
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
                }

                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    minZBefore,
                    deltaZApplied = deltaZ,
                    minZAfter,
                    maxZAfter
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
