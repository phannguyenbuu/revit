using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixStackElevation
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

                // Find Tầng 1 (elevation = 0)
                var lvlTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => Math.Abs(l.Elevation) < 0.01)
                    ?? doc.GetElement(new ElementId(311)) as Level;

                if (lvlTang1 == null) return new { error = "Level Tang 1 not found" };

                var bbBefore = elem.get_BoundingBox(null);
                double minZBefore = bbBefore.Min.Z * FT2M;

                using (Transaction tx = new Transaction(doc, "Adjust Stack Elevation to +0.000"))
                {
                    tx.Start();

                    // If hosted on San Vuon (-0.75m), move up by (0 - minZBefore)
                    double deltaZM = 0.0 - minZBefore;
                    if (Math.Abs(deltaZM) > 0.001)
                    {
                        ElementTransformUtils.MoveElement(doc, elem.Id, new XYZ(0, 0, deltaZM * M2FT));
                    }

                    // Try to re-assign Level parameter if available
                    var lvlParam = elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM);
                    if (lvlParam != null && !lvlParam.IsReadOnly)
                    {
                        try { lvlParam.Set(lvlTang1.Id); } catch { }
                    }

                    tx.Commit();
                }

                // Check bounding box after move
                var bbAfter = elem.get_BoundingBox(null);
                double minZAfter = bbAfter.Min.Z * FT2M;
                double maxZAfter = bbAfter.Max.Z * FT2M;

                // Update section box of "3D - K2 Facade"
                string boxViewName = "3D - K2 Facade";
                View3D boxView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => v.Name == boxViewName);

                if (boxView != null)
                {
                    using (Transaction tx = new Transaction(doc, "Update Section Box"))
                    {
                        tx.Start();
                        BoundingBoxXYZ sb = new BoundingBoxXYZ();
                        sb.Min = new XYZ(-1.0 * M2FT, 10.5 * M2FT, -0.5 * M2FT);
                        sb.Max = new XYZ(2.5 * M2FT, 14.5 * M2FT, 13.5 * M2FT);
                        boxView.SetSectionBox(sb);
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
                }

                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    minZBefore,
                    minZAfter,
                    maxZAfter,
                    expectedMinZ = 0.0,
                    expectedMaxZ = 11.35
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
