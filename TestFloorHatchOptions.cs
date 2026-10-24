using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestFloorHatchOptions
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No active ViewPlan" };

                var fpe600 = doc.GetElement(new ElementId(8574L)) as FillPatternElement
                    ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "600 x 600mm");

                var e2381562 = doc.GetElement(new ElementId(2381562L));

                // 1. Get top faces and curve loops
                var optGeomModel = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
                var geomModel = e2381562?.get_Geometry(optGeomModel);
                List<PlanarFace> topFaces = new List<PlanarFace>();
                if (geomModel != null)
                {
                    foreach (var obj in geomModel)
                    {
                        if (obj is Solid s && s.Volume > 0)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && pf.FaceNormal.IsAlmostEqualTo(XYZ.BasisZ))
                                {
                                    topFaces.Add(pf);
                                }
                            }
                        }
                    }
                }

                int loopsCount = 0;
                double totalArea = 0;
                List<int> curvesPerLoop = new List<int>();
                IList<CurveLoop> validLoops = new List<CurveLoop>();
                if (topFaces.Count > 0)
                {
                    var loops = topFaces[0].GetEdgesAsCurveLoops();
                    loopsCount = loops.Count;
                    totalArea = topFaces[0].Area * 0.092903; // m2
                    foreach (var l in loops)
                    {
                        curvesPerLoop.Add(l.Count());
                        validLoops.Add(l);
                    }
                }

                // Check available FloorTypes of category OST_Floors
                var floorTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(FloorType))
                    .Cast<FloorType>()
                    .Where(ft => ft.Category != null && ft.Category.Id.Value == (long)BuiltInCategory.OST_Floors)
                    .Select(ft => new { id = ft.Id.Value, name = ft.Name })
                    .ToList();

                // Export cropped image around center of Tang 1 to see if pattern appeared!
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string testImgPath = Path.Combine(outDir, "revit_test_floor_override.png");
                
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ p1 = new XYZ(10000.0 / 304.8, 2000.0 / 304.8, 0);
                    XYZ p2 = new XYZ(20000.0 / 304.8, 12000.0 / 304.8, 0);
                    uiview.ZoomAndCenterRectangle(p1, p2);
                }

                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = testImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt);

                return new
                {
                    topFacesCount = topFaces.Count,
                    loopsCount = loopsCount,
                    curvesPerLoop = curvesPerLoop,
                    totalArea = totalArea,
                    floorTypes = floorTypes
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
