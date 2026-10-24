using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateTamCapFromCad
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No active ViewPlan" };

                var level = view.GenLevel;
                if (level == null) return new { error = "No view level" };

                // Get FloorType BAC (ID 1196262) or default FloorType
                var ftBac = doc.GetElement(new ElementId(1196262L)) as FloorType
                    ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().FirstOrDefault(ft => ft.Name == "BAC")
                    ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().First();

                // Get WallType "gach200_xay moi" (ID 2361271)
                var wtGach200 = doc.GetElement(new ElementId(2361271L)) as WallType
                    ?? new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().FirstOrDefault(w => w.Name.Contains("gach200"))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().First();

                // Geometry from CAD selection (exact coordinates in mm):
                // Width Y: 5500 to 7700 (2200mm)
                // 5 steps:
                // Step 5 (Highest, Left): X: 37250 to 38350, Top: 0.0 mm (HeightOffset = 0.0)
                // Step 4: X: 38350 to 38650, Top: -150.0 mm (HeightOffset = -150)
                // Step 3: X: 38650 to 38950, Top: -300.0 mm (HeightOffset = -300)
                // Step 2: X: 38950 to 39250, Top: -450.0 mm (HeightOffset = -450)
                // Step 1 (Lowest, Right): X: 39250 to 39550, Top: -600.0 mm (HeightOffset = -600)

                double yMin = 5500.0 * MM_TO_FT;
                double yMax = 7700.0 * MM_TO_FT;

                var stepX = new List<(double x1, double x2, double topOffsetMm)>
                {
                    (37250.0, 38350.0, 0.0),      // Bậc 5 (cao nhất, bên trái)
                    (38350.0, 38650.0, -150.0),   // Bậc 4
                    (38650.0, 38950.0, -300.0),   // Bậc 3
                    (38950.0, 39250.0, -450.0),   // Bậc 2
                    (39250.0, 39550.0, -600.0)    // Bậc 1 (thấp nhất, bên phải)
                };

                List<long> createdFloorIds = new List<long>();
                List<long> createdWallIds = new List<long>();

                using (var tx = new Transaction(doc, "Create Tam Cap 5 Bac"))
                {
                    var failOpt = tx.GetFailureHandlingOptions();
                    failOpt.SetFailuresPreprocessor(new WarningSwallower());
                    tx.SetFailureHandlingOptions(failOpt);

                    tx.Start();

                    // 1. Create 5 Floor steps
                    foreach (var s in stepX)
                    {
                        double x1 = s.x1 * MM_TO_FT;
                        double x2 = s.x2 * MM_TO_FT;

                        var loop = new CurveLoop();
                        loop.Append(Line.CreateBound(new XYZ(x1, yMin, 0), new XYZ(x2, yMin, 0)));
                        loop.Append(Line.CreateBound(new XYZ(x2, yMin, 0), new XYZ(x2, yMax, 0)));
                        loop.Append(Line.CreateBound(new XYZ(x2, yMax, 0), new XYZ(x1, yMax, 0)));
                        loop.Append(Line.CreateBound(new XYZ(x1, yMax, 0), new XYZ(x1, yMin, 0)));

                        var floor = Floor.Create(doc, new List<CurveLoop> { loop }, ftBac.Id, level.Id);
                        
                        var pOffset = floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                        if (pOffset != null && !pOffset.IsReadOnly)
                        {
                            pOffset.Set(s.topOffsetMm * MM_TO_FT);
                        }

                        createdFloorIds.Add(floor.Id.Value);
                    }

                    // 2. Create 2 side curbs (gờ má tam cấp) as walls
                    // South curb: Y = 5400, X from 37250 to 39550
                    // North curb: Y = 7800, X from 37250 to 39550
                    double xStart = 37250.0 * MM_TO_FT;
                    double xEnd = 39550.0 * MM_TO_FT;
                    double ySouth = 5400.0 * MM_TO_FT;
                    double yNorth = 7800.0 * MM_TO_FT;

                    var cSouth = Line.CreateBound(new XYZ(xStart, ySouth, 0), new XYZ(xEnd, ySouth, 0));
                    var cNorth = Line.CreateBound(new XYZ(xStart, yNorth, 0), new XYZ(xEnd, yNorth, 0));

                    double wallHeight = 750.0 * MM_TO_FT;
                    double baseOffset = -750.0 * MM_TO_FT;

                    var wSouth = Wall.Create(doc, cSouth, wtGach200.Id, level.Id, wallHeight, baseOffset, false, false);
                    var wNorth = Wall.Create(doc, cNorth, wtGach200.Id, level.Id, wallHeight, baseOffset, false, false);

                    createdWallIds.Add(wSouth.Id.Value);
                    createdWallIds.Add(wNorth.Id.Value);

                    // 3. Adjust View Range if needed so steps below 0 are visible
                    var targetView = (view.ViewTemplateId != ElementId.InvalidElementId 
                        ? doc.GetElement(view.ViewTemplateId) as ViewPlan 
                        : null) ?? view;

                    try
                    {
                        var vr = targetView.GetViewRange();
                        double curBottom = vr.GetOffset(PlanViewPlane.BottomClipPlane) * 304.8;
                        double curDepth = vr.GetOffset(PlanViewPlane.ViewDepthPlane) * 304.8;
                        if (curBottom > -800.0) vr.SetOffset(PlanViewPlane.BottomClipPlane, -800.0 * MM_TO_FT);
                        if (curDepth > -800.0) vr.SetOffset(PlanViewPlane.ViewDepthPlane, -800.0 * MM_TO_FT);
                        targetView.SetViewRange(vr);
                    }
                    catch { }

                    tx.Commit();
                }

                // 4. Export Zoom crop around Tam Cap
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ p1 = new XYZ(35000.0 * MM_TO_FT, 3500.0 * MM_TO_FT, 0);
                    XYZ p2 = new XYZ(41000.0 * MM_TO_FT, 9500.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p1, p2);
                }

                string imgZoom = Path.Combine(outDir, "revit_zoom_tam_cap_5bac.png");
                var optZoom = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = imgZoom,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1800,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(optZoom);

                // Full plan view
                if (uiview != null)
                {
                    XYZ pAll1 = new XYZ(-2000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                    XYZ pAll2 = new XYZ(41000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(pAll1, pAll2);
                }

                string planImg = Path.Combine(outDir, "revit_tang1_with_tam_cap.png");
                var optPlan = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = planImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 3000,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(optPlan);

                return new
                {
                    success = true,
                    createdFloorIds = createdFloorIds,
                    createdWallIds = createdWallIds,
                    zoomImage = "revit_zoom_tam_cap_5bac.png",
                    planImage = "revit_tang1_with_tam_cap.png"
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
