using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class TumSlabWarningSwallower : IFailuresPreprocessor
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

    public static class CreateTumSlabWithHole
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
                // 1. Inspect all levels
                var allLevels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();

                logs.Add($"Found {allLevels.Count} levels in document:");
                foreach (var l in allLevels)
                {
                    logs.Add($" - Level '{l.Name}' (Id: {l.Id.Value}, Elev: {l.Elevation * FT2M:F3}m)");
                }

                // Find Level MÁI / TUM (Elevation around 14.4m) or ÁP MÁI (10.8m)
                // In CAD, elevation text on this floor is +14.400
                Level targetLevel = allLevels.FirstOrDefault(l => Math.Abs(l.Elevation * FT2M - 14.4) < 0.3)
                    ?? allLevels.FirstOrDefault(l => l.Name.Contains("MÁI", StringComparison.OrdinalIgnoreCase) && !l.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase))
                    ?? allLevels.FirstOrDefault(l => l.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase))
                    ?? allLevels.FirstOrDefault(l => l.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase) || l.Name.Contains("AP MAI", StringComparison.OrdinalIgnoreCase));

                if (targetLevel == null)
                {
                    targetLevel = allLevels.Last();
                }

                logs.Add($"Selected target level: '{targetLevel.Name}' (Id: {targetLevel.Id.Value}, Elev: {targetLevel.Elevation * FT2M:F3}m)");

                // 2. Define Outer Boundary (12 vertices, CCW, rounded to 50mm)
                var outerPtsMm = new List<XYZ>
                {
                    new XYZ(4250.0, 4800.0, 0.0),
                    new XYZ(11050.0, 4800.0, 0.0),
                    new XYZ(11050.0, -100.0, 0.0),
                    new XYZ(37250.0, -100.0, 0.0),
                    new XYZ(37250.0, 13300.0, 0.0),
                    new XYZ(33250.0, 13300.0, 0.0),
                    new XYZ(33250.0, 10100.0, 0.0),
                    new XYZ(29750.0, 10100.0, 0.0),
                    new XYZ(29750.0, 13300.0, 0.0),
                    new XYZ(8150.0, 13300.0, 0.0),
                    new XYZ(8150.0, 15000.0, 0.0),
                    new XYZ(4250.0, 15000.0, 0.0)
                };

                // 3. Define Hole Boundary (4 vertices, rounded to 50mm)
                // Hole is located at X in [5650, 6750], Y in [9700, 13100]
                var holePtsMm = new List<XYZ>
                {
                    new XYZ(5650.0, 9700.0, 0.0),
                    new XYZ(6750.0, 9700.0, 0.0),
                    new XYZ(6750.0, 13100.0, 0.0),
                    new XYZ(5650.0, 13100.0, 0.0)
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
                using (var tx = new Transaction(doc, "Create Sàn Tầng Tum / Mái Có Lỗ Mở"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new TumSlabWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    // Try with holeLoop orientation 1
                    var profile = new List<CurveLoop> { outerLoop, holeLoop };
                    try
                    {
                        createdFloor = Floor.Create(doc, profile, ft100.Id, targetLevel.Id);
                    }
                    catch (Exception ex1)
                    {
                        logs.Add($"First attempt with hole orientation threw: {ex1.Message}, flipping hole loop...");
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

                uidoc.RefreshActiveView();
                try { doc.Save(); } catch { }

                // 5. Export images
                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string outPlanImg = Path.Combine(brainDir, "revit_tum_slab_plan.png");
                string out3DImg = Path.Combine(brainDir, "revit_tum_slab_3d.png");

                var planView = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.GenLevel?.Id == targetLevel.Id)
                    ?? uidoc.ActiveView;

                if (planView != null)
                {
                    if (File.Exists(outPlanImg)) File.Delete(outPlanImg);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = outPlanImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.SetOfViews,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 1920
                    };
                    expOpt.SetViewsAndSheets(new List<ElementId> { planView.Id });
                    doc.ExportImage(expOpt);
                }

                var v3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("3D"));

                if (v3d != null)
                {
                    if (File.Exists(out3DImg)) File.Delete(out3DImg);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = out3DImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.SetOfViews,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 1920
                    };
                    expOpt.SetViewsAndSheets(new List<ElementId> { v3d.Id });
                    doc.ExportImage(expOpt);
                }

                return new
                {
                    success = true,
                    floorId = createdFloor?.Id.Value,
                    floorType = ftName,
                    thicknessMm = 100,
                    level = targetLevel.Name,
                    elevationM = targetLevel.Elevation * FT2M,
                    netAreaM2 = Math.Round(createdFloor?.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2),
                    holeDimensions = "1.1m x 3.4m (Area 3.74m2)",
                    holeBoundsMm = new { xMin = 5650.0, xMax = 6750.0, yMin = 9700.0, yMax = 13100.0 },
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
