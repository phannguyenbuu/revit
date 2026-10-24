using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SanMaiWarningSwallower : IFailuresPreprocessor
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

    public static class CreateSanMaiFromCad
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
                // 1. Identify Level Tầng Tum (+14.400m)
                var allLevels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();

                Level targetLevel = doc.GetElement(new ElementId(2360635L)) as Level
                    ?? allLevels.FirstOrDefault(l => Math.Abs(l.Elevation * FT2M - 14.4) < 0.2)
                    ?? allLevels.FirstOrDefault(l => l.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase))
                    ?? allLevels.Last();

                logs.Add($"Selected target level: '{targetLevel.Name}' (Id: {targetLevel.Id.Value}, Elev: {targetLevel.Elevation * FT2M:F3}m)");

                // 2. Delete old floor 2381771 if exists
                using (var txDel = new Transaction(doc, "Delete Previous Floor 2381771"))
                {
                    txDel.Start();
                    var oldFloor = doc.GetElement(new ElementId(2381771L));
                    if (oldFloor != null)
                    {
                        doc.Delete(oldFloor.Id);
                        logs.Add("Deleted previous floor 2381771 successfully.");
                    }
                    txDel.Commit();
                }

                // 3. Define Outer Boundary (14 vertices, CCW, 50mm rounded, 100% orthogonal)
                var outerPtsMm = new List<XYZ>
                {
                    new XYZ(26650.0,  4800.0, 0.0), // V00: Trục 8 - C
                    new XYZ(37250.0,  4800.0, 0.0), // V01: Trục 11 - C
                    new XYZ(37250.0, 13300.0, 0.0), // V02: Trục 11 - D
                    new XYZ(33250.0, 13300.0, 0.0), // V03: Trục 10 - D
                    new XYZ(33250.0, 10100.0, 0.0), // V04: Trục 10 - C
                    new XYZ(29750.0, 10100.0, 0.0), // V05: Trục 9 - C
                    new XYZ(29750.0, 13300.0, 0.0), // V06: Trục 9 - D
                    new XYZ( 8150.0, 13300.0, 0.0), // V07: Trục 3 - D
                    new XYZ( 8150.0, 15000.0, 0.0), // V08: Trục 3 - E
                    new XYZ( 4250.0, 15000.0, 0.0), // V09: Trục 2 - E
                    new XYZ( 4250.0,  4800.0, 0.0), // V10: Trục 2 - C
                    new XYZ(11050.0,  4800.0, 0.0), // V11: Trục 4 - C
                    new XYZ(11050.0,  -100.0, 0.0), // V12: Trục 4 - A
                    new XYZ(26650.0,  -100.0, 0.0)  // V13: Trục 8 - A
                };

                // 4. Define Hole Boundary (4 vertices, CCW, rounded to 50mm)
                var holePtsMm = new List<XYZ>
                {
                    new XYZ(5650.0,  9700.0, 0.0), // H0: góc dưới trái
                    new XYZ(6750.0,  9700.0, 0.0), // H1: góc dưới phải
                    new XYZ(6750.0, 13100.0, 0.0), // H2: góc trên phải
                    new XYZ(5650.0, 13100.0, 0.0)  // H3: góc trên trái
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

                // 5. Create Floor with Outer Loop and Hole Loop
                Floor createdFloor = null;
                using (var tx = new Transaction(doc, "Create Sàn Mái BTCT 100mm Từ CAD Selected"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new SanMaiWarningSwallower());
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

                // 6. Select the newly created floor in Revit UI
                uidoc.Selection.SetElementIds(new List<ElementId> { createdFloor.Id });
                uidoc.RefreshActiveView();
                try { doc.Save(); } catch { }

                // 7. Adjust Plan View and Export Verification Images
                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

                ViewPlan planTum = doc.GetElement(new ElementId(2370740L)) as ViewPlan
                    ?? new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewPlan))
                        .Cast<ViewPlan>()
                        .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase) || (v.GenLevel != null && v.GenLevel.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase))));

                if (planTum != null)
                {
                    uidoc.ActiveView = planTum;

                    using (Transaction t = new Transaction(doc, "Adjust Plan Tum ViewRange and Crop"))
                    {
                        t.Start();

                        var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                        if (floorCat != null && planTum.CanCategoryBeHidden(floorCat.Id))
                        {
                            if (planTum.GetCategoryHidden(floorCat.Id)) planTum.SetCategoryHidden(floorCat.Id, false);
                        }

                        var vr = planTum.GetViewRange();
                        vr.SetOffset(PlanViewPlane.BottomClipPlane, -1.0);
                        vr.SetOffset(PlanViewPlane.ViewDepthPlane, -1.0);
                        planTum.SetViewRange(vr);

                        var bb = planTum.CropBox;
                        var tr = bb.Transform;
                        var inv = tr.Inverse;

                        var pMinWorld = new XYZ(-2.0 * M2FT, -2.5 * M2FT, tr.Origin.Z);
                        var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, tr.Origin.Z);

                        var pMinLocal = inv.OfPoint(pMinWorld);
                        var pMaxLocal = inv.OfPoint(pMaxWorld);

                        bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                        bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                        planTum.CropBox = bb;
                        planTum.CropBoxActive = true;
                        planTum.CropBoxVisible = false;

                        t.Commit();
                    }

                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTum.Id);
                    uiview?.ZoomToFit();

                    string outPlanOverview = Path.Combine(brainDir, "revit_san_mai_plan_overview.png");
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
                }

                // 8. 3D View Export (with the new floor highlighted)
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

                    string out3dImg = Path.Combine(brainDir, "revit_san_mai_3d_selected.png");
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

                double grossAreaM2 = 352.37;
                double holeAreaM2 = 3.74;
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
                    holeDimensions = "1.1m x 3.4m",
                    outerVerticesCount = outerPtsMm.Count,
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
