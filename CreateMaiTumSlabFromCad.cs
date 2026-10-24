using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class MaiTumWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var m in msgs)
            {
                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class CreateMaiTumSlabFromCad
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            List<string> logs = new List<string>();

            try
            {
                // 1. Identify Level MẶT BẰNG MÁI (+17.200m)
                var allLevels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();

                Level targetLevel = doc.GetElement(new ElementId(1209118L)) as Level
                    ?? allLevels.FirstOrDefault(l => Math.Abs(l.Elevation * FT2M - 17.2) < 0.2)
                    ?? allLevels.FirstOrDefault(l => l.Name.Contains("MÁI", StringComparison.OrdinalIgnoreCase) && !l.Name.Contains("ÁP", StringComparison.OrdinalIgnoreCase))
                    ?? allLevels.Last();

                logs.Add($"Selected target level: '{targetLevel.Name}' (Id: {targetLevel.Id.Value}, Elev: {targetLevel.Elevation * FT2M:F3}m)");

                // 2. Define Outer Boundary (4 vertices, CCW, 50mm rounded, 100% orthogonal)
                // Width = 3900mm (X: 29550 -> 33450), Height = 7300mm (Y: 7700 -> 15000)
                var outerPtsMm = new List<XYZ>
                {
                    new XYZ(29550.0,  7700.0, 0.0), // V0: góc dưới trái (Trục 9 - C)
                    new XYZ(33450.0,  7700.0, 0.0), // V1: góc dưới phải (Trục 10 - C)
                    new XYZ(33450.0, 15000.0, 0.0), // V2: góc trên phải (Trục 10 - E)
                    new XYZ(29550.0, 15000.0, 0.0)  // V3: góc trên trái (Trục 9 - E)
                };

                // 3. Define Inner Hole Boundary (4 vertices, CCW, 50mm rounded, 100% orthogonal)
                // Width = 1100mm (X: 30950 -> 32050), Height = 3400mm (Y: 9700 -> 13100)
                var holePtsMm = new List<XYZ>
                {
                    new XYZ(30950.0,  9700.0, 0.0), // H0: góc dưới trái lỗ mở
                    new XYZ(32050.0,  9700.0, 0.0), // H1: góc dưới phải lỗ mở
                    new XYZ(32050.0, 13100.0, 0.0), // H2: góc trên phải lỗ mở
                    new XYZ(30950.0, 13100.0, 0.0)  // H3: góc trên trái lỗ mở
                };

                // Build CurveLoops
                CurveLoop outerLoop = new CurveLoop();
                for (int i = 0; i < outerPtsMm.Count; i++)
                {
                    int j = (i + 1) % outerPtsMm.Count;
                    XYZ p0 = new XYZ((outerPtsMm[i].X / 1000.0) * M2FT, (outerPtsMm[i].Y / 1000.0) * M2FT, 0.0);
                    XYZ p1 = new XYZ((outerPtsMm[j].X / 1000.0) * M2FT, (outerPtsMm[j].Y / 1000.0) * M2FT, 0.0);
                    outerLoop.Append(Line.CreateBound(p0, p1));
                }

                if (!outerLoop.IsCounterclockwise(XYZ.BasisZ))
                {
                    outerLoop.Flip();
                }

                CurveLoop holeLoop = new CurveLoop();
                for (int i = 0; i < holePtsMm.Count; i++)
                {
                    int j = (i + 1) % holePtsMm.Count;
                    XYZ p0 = new XYZ((holePtsMm[i].X / 1000.0) * M2FT, (holePtsMm[i].Y / 1000.0) * M2FT, 0.0);
                    XYZ p1 = new XYZ((holePtsMm[j].X / 1000.0) * M2FT, (holePtsMm[j].Y / 1000.0) * M2FT, 0.0);
                    holeLoop.Append(Line.CreateBound(p0, p1));
                }

                // FloorType 100mm
                string ftName = "Sàn BTCT 100mm";
                var ft100 = new FilteredElementCollector(doc)
                    .OfClass(typeof(FloorType))
                    .Cast<FloorType>()
                    .FirstOrDefault(f => f.Name.Equals(ftName, StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().First();

                // 4. Create Floor with Outer Loop and Hole Loop
                Floor createdFloor = null;
                using (var tx = new Transaction(doc, "Create Sàn Mái Tum BTCT 100mm Có Lỗ Giữa"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new MaiTumWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    var profile = new List<CurveLoop> { outerLoop, holeLoop };
                    try
                    {
                        createdFloor = Floor.Create(doc, profile, ft100.Id, targetLevel.Id);
                    }
                    catch (Exception ex1)
                    {
                        logs.Add($"First attempt threw: {ex1.Message}, flipping hole loop...");
                        holeLoop.Flip();
                        profile = new List<CurveLoop> { outerLoop, holeLoop };
                        createdFloor = Floor.Create(doc, profile, ft100.Id, targetLevel.Id);
                    }

                    // Set Height Offset = 0
                    var pOffset = createdFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    if (pOffset != null && !pOffset.IsReadOnly)
                    {
                        pOffset.Set(0.0);
                    }

                    logs.Add($"Created Floor ID: {createdFloor.Id.Value} on Level: {targetLevel.Name}");

                    tx.Commit();
                }

                // 5. Select the newly created floor in Revit UI
                uidoc.Selection.SetElementIds(new List<ElementId> { createdFloor.Id });
                uidoc.RefreshActiveView();
                try { doc.Save(); } catch { }

                // 6. Adjust Plan View MẶT BẰNG MÁI and Export Verification Images
                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

                ViewPlan planMai = doc.GetElement(new ElementId(1234140L)) as ViewPlan
                    ?? new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewPlan))
                        .Cast<ViewPlan>()
                        .FirstOrDefault(v => !v.IsTemplate && (v.Name.Equals("MẶT BẰNG MÁI", StringComparison.OrdinalIgnoreCase) || (v.GenLevel != null && v.GenLevel.Id == targetLevel.Id)));

                if (planMai != null)
                {
                    uidoc.ActiveView = planMai;

                    using (Transaction t = new Transaction(doc, "Adjust Plan Mai ViewRange and Crop"))
                    {
                        t.Start();

                        var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                        if (floorCat != null && planMai.CanCategoryBeHidden(floorCat.Id))
                        {
                            if (planMai.GetCategoryHidden(floorCat.Id)) planMai.SetCategoryHidden(floorCat.Id, false);
                        }

                        var vr = planMai.GetViewRange();
                        vr.SetOffset(PlanViewPlane.CutPlane, 4.0); // 1.2m
                        vr.SetOffset(PlanViewPlane.TopClipPlane, 8.0); // 2.4m
                        vr.SetOffset(PlanViewPlane.BottomClipPlane, -1.0);
                        vr.SetOffset(PlanViewPlane.ViewDepthPlane, -1.0);
                        planMai.SetViewRange(vr);

                        var bb = planMai.CropBox;
                        var tr = bb.Transform;
                        var inv = tr.Inverse;

                        // Crop around the entire roof structure to see context
                        var pMinWorld = new XYZ(-2.0 * M2FT, -2.5 * M2FT, tr.Origin.Z);
                        var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, tr.Origin.Z);

                        var pMinLocal = inv.OfPoint(pMinWorld);
                        var pMaxLocal = inv.OfPoint(pMaxWorld);

                        bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                        bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                        planMai.CropBox = bb;
                        planMai.CropBoxActive = true;
                        planMai.CropBoxVisible = false;

                        t.Commit();
                    }

                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planMai.Id);
                    uiview?.ZoomToFit();

                    string outPlanOverview = Path.Combine(brainDir, "revit_mai_tum_plan_overview.png");
                    if (File.Exists(outPlanOverview)) File.Delete(outPlanOverview);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = outPlanOverview,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOpt);

                    // Also export a close-up plan image of the tum roof
                    using (Transaction tClose = new Transaction(doc, "Crop Close to Tum Roof"))
                    {
                        tClose.Start();
                        var bbClose = planMai.CropBox;
                        var trClose = bbClose.Transform;
                        var invClose = trClose.Inverse;

                        var pMinTum = new XYZ(27.0 * M2FT, 5.5 * M2FT, trClose.Origin.Z);
                        var pMaxTum = new XYZ(36.0 * M2FT, 17.0 * M2FT, trClose.Origin.Z);

                        var pMinL = invClose.OfPoint(pMinTum);
                        var pMaxL = invClose.OfPoint(pMaxTum);

                        bbClose.Min = new XYZ(Math.Min(pMinL.X, pMaxL.X), Math.Min(pMinL.Y, pMaxL.Y), bbClose.Min.Z);
                        bbClose.Max = new XYZ(Math.Max(pMinL.X, pMaxL.X), Math.Max(pMinL.Y, pMaxL.Y), bbClose.Max.Z);

                        planMai.CropBox = bbClose;
                        tClose.Commit();
                    }

                    uiview?.ZoomToFit();

                    string outPlanClose = Path.Combine(brainDir, "revit_mai_tum_plan_closeup.png");
                    if (File.Exists(outPlanClose)) File.Delete(outPlanClose);
                    var expOptClose = new ImageExportOptions
                    {
                        FilePath = outPlanClose,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOptClose);
                }

                // 7. 3D View Export (with the new floor highlighted)
                View3D v3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("3D"));

                if (v3d != null)
                {
                    uidoc.ActiveView = v3d;
                    uidoc.Selection.SetElementIds(new List<ElementId> { createdFloor.Id });
                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
                    uiview3d?.ZoomToFit();

                    string out3dImg = Path.Combine(brainDir, "revit_mai_tum_3d_selected.png");
                    if (File.Exists(out3dImg)) File.Delete(out3dImg);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = out3dImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOpt3d);
                }

                double grossAreaM2 = Math.Round((3900.0 * 7300.0) / 1e6, 2);
                double holeAreaM2 = Math.Round((1100.0 * 3400.0) / 1e6, 2);
                double netAreaComputed = Math.Round(createdFloor?.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2);

                return new
                {
                    success = true,
                    floorId = createdFloor?.Id.Value,
                    floorType = ftName,
                    thicknessMm = 100,
                    level = targetLevel.Name,
                    elevationM = targetLevel.Elevation * FT2M,
                    netAreaM2 = netAreaComputed,
                    grossAreaM2 = grossAreaM2,
                    holeAreaM2 = holeAreaM2,
                    outerDimensions = "3.9m x 7.3m",
                    holeDimensions = "1.1m x 3.4m",
                    outerVertices = outerPtsMm.Select((p, idx) => new { idx, xMm = p.X, yMm = p.Y, xM = p.X / 1000.0, yM = p.Y / 1000.0 }).ToList(),
                    holeVertices = holePtsMm.Select((p, idx) => new { idx, xMm = p.X, yMm = p.Y, xM = p.X / 1000.0, yM = p.Y / 1000.0 }).ToList(),
                    logs
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString(), logs };
            }
        }
    }
}
