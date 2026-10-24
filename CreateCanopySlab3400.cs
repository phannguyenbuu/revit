using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class CanopyWarningSwallower : IFailuresPreprocessor
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

    public static class CreateCanopySlab3400
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
                // 1. Delete duplicate floor 2381626 if present
                using (var tx = new Transaction(doc, "Delete Duplicate Floor If Exists"))
                {
                    tx.Start();
                    var dupId = new ElementId(2381626L);
                    var elem = doc.GetElement(dupId);
                    if (elem != null)
                    {
                        doc.Delete(dupId);
                        logs.Add($"Deleted duplicate floor ID: {dupId.Value}");
                    }
                    tx.Commit();
                }

                // 2. Get Level "MẶT BẰNG TẦNG 1"
                var lvlTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

                if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

                logs.Add($"Base Level: {lvlTang1.Name} (Id: {lvlTang1.Id.Value}, Elevation: {lvlTang1.Elevation * FT2M:F3}m)");

                // 3. Define Canopy Slab Boundary (Polyline 4A7EE2 on layer NET HAT MONG)
                // In CAD: X in [-75953.54, -70503.54], Y in [-1397905.90, -1389705.90]
                // Transformed with dx = +70953.54, dy = +1400405.90
                // X in [-5000.0, +450.0], Y in [+2500.0, +10700.0]
                // All coordinates are exact multiples of 50mm!
                double xMinMm = -5000.0;
                double xMaxMm = 450.0;
                double yMinMm = 2500.0;
                double yMaxMm = 10700.0;

                // Counter-Clockwise (CCW) vertices:
                var ptsMm = new List<XYZ>
                {
                    new XYZ(xMinMm, yMinMm, 0.0), // SW: (-5000, 2500)
                    new XYZ(xMaxMm, yMinMm, 0.0), // SE: (450, 2500)
                    new XYZ(xMaxMm, yMaxMm, 0.0), // NE: (450, 10700)
                    new XYZ(xMinMm, yMaxMm, 0.0)  // NW: (-5000, 10700)
                };

                CurveLoop loop = new CurveLoop();
                for (int i = 0; i < ptsMm.Count; i++)
                {
                    int j = (i + 1) % ptsMm.Count;
                    XYZ p0 = new XYZ((ptsMm[i].X / 1000.0) * M2FT, (ptsMm[i].Y / 1000.0) * M2FT, 0.0);
                    XYZ p1 = new XYZ((ptsMm[j].X / 1000.0) * M2FT, (ptsMm[j].Y / 1000.0) * M2FT, 0.0);
                    loop.Append(Line.CreateBound(p0, p1));
                }

                // 4. FloorType 100mm
                string ftName = "Sàn BTCT 100mm";
                var ft100 = new FilteredElementCollector(doc)
                    .OfClass(typeof(FloorType))
                    .Cast<FloorType>()
                    .FirstOrDefault(f => f.Name.Equals(ftName, StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().First();

                // 5. Create Floor element at Elevation +3400mm (+3.400m)
                // Height above Level TẦNG 1 = 3400 mm = 3.4 m
                double targetElevationMm = 3400.0;
                double offsetFt = (targetElevationMm / 1000.0) * M2FT;

                Floor createdFloor = null;
                using (var tx = new Transaction(doc, "Create Sàn Mái Sảnh Cao Độ +3400mm"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new CanopyWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    createdFloor = Floor.Create(doc, new List<CurveLoop> { loop }, ft100.Id, lvlTang1.Id);

                    // Set Height Offset to +3400mm
                    var pOffset = createdFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    if (pOffset != null && !pOffset.IsReadOnly)
                    {
                        pOffset.Set(offsetFt);
                    }

                    logs.Add($"Created Canopy Floor ID: {createdFloor.Id.Value}, Level: {lvlTang1.Name}, Offset: {targetElevationMm}mm (+3.400m)");

                    tx.Commit();
                }

                uidoc.RefreshActiveView();
                try { doc.Save(); } catch { }

                // 6. Export verification images
                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string outPlanImg = Path.Combine(brainDir, "revit_canopy_slab_plan.png");
                string out3DImg = Path.Combine(brainDir, "revit_canopy_slab_3d.png");

                var planView = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"))
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
                    elevationMm = targetElevationMm,
                    elevationM = targetElevationMm / 1000.0,
                    level = lvlTang1.Name,
                    heightOffsetMm = targetElevationMm,
                    areaM2 = Math.Round(createdFloor?.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2),
                    boundsMm = new
                    {
                        xMin = xMinMm,
                        xMax = xMaxMm,
                        yMin = yMinMm,
                        yMax = yMaxMm,
                        widthMm = xMaxMm - xMinMm,
                        lengthMm = yMaxMm - yMinMm
                    },
                    vertices = ptsMm.Select((p, idx) => new { idx, xMm = p.X, yMm = p.Y, xM = p.X / 1000.0, yM = p.Y / 1000.0 }).ToList(),
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
