using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SlabWarningSwallower : IFailuresPreprocessor
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

    public static class CreateTang1SlabFromCad
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
                // 1. Get Level "MẶT BẰNG TẦNG 1"
                var lvlTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

                if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

                // 2. Load coordinates from JSON (or direct args)
                string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selected_slab.json";
                if (!File.Exists(jsonPath)) return new { error = "cad_selected_slab.json not found" };

                var jsonStr = File.ReadAllText(jsonPath);
                using var jdoc = JsonDocument.Parse(jsonStr);
                var elem0 = jdoc.RootElement[0];
                var rawCoords = elem0.GetProperty("raw_coords");

                List<XYZ> ptsM = new List<XYZ>();
                for (int i = 0; i < rawCoords.GetArrayLength(); i += 2)
                {
                    double xCad = rawCoords[i].GetDouble();
                    double yCad = rawCoords[i + 1].GetDouble();

                    // Transform CAD to Revit: X_revit = (xCad + 132847.0)/1000, Y_revit = (yCad + 1400405.9)/1000
                    double xRevitM = (xCad + 132847.0) / 1000.0;
                    double yRevitM = (yCad + 1400405.9) / 1000.0;

                    ptsM.Add(new XYZ(xRevitM, yRevitM, 0.0));
                }

                logs.Add($"Loaded {ptsM.Count} vertices from CAD polyline");

                // 3. Create CurveLoop in feet
                CurveLoop loop = new CurveLoop();
                for (int i = 0; i < ptsM.Count; i++)
                {
                    int j = (i + 1) % ptsM.Count;
                    XYZ p0 = new XYZ(ptsM[i].X * M2FT, ptsM[i].Y * M2FT, 0.0);
                    XYZ p1 = new XYZ(ptsM[j].X * M2FT, ptsM[j].Y * M2FT, 0.0);

                    loop.Append(Line.CreateBound(p0, p1));
                }

                // 4. Create or Get FloorType with 100mm thickness
                FloorType ft100 = null;
                string ftName = "Sàn BTCT 100mm";

                using (var tx = new Transaction(doc, "Ensure 100mm FloorType"))
                {
                    tx.Start();

                    ft100 = new FilteredElementCollector(doc)
                        .OfClass(typeof(FloorType))
                        .Cast<FloorType>()
                        .FirstOrDefault(f => f.Name.Equals(ftName, StringComparison.OrdinalIgnoreCase));

                    if (ft100 == null)
                    {
                        var baseFt = new FilteredElementCollector(doc)
                            .OfClass(typeof(FloorType))
                            .Cast<FloorType>()
                            .FirstOrDefault(f => f.Name.Equals("SAN BE TONG", StringComparison.OrdinalIgnoreCase))
                            ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().First();

                        ft100 = (FloorType)baseFt.Duplicate(ftName);
                        var cs = ft100.GetCompoundStructure();
                        int structIdx = cs.StructuralMaterialIndex;
                        if (structIdx < 0) structIdx = 0;
                        cs.SetLayerWidth(structIdx, 0.100 * M2FT); // 100mm = 0.1m
                        ft100.SetCompoundStructure(cs);
                        logs.Add($"Created FloorType: {ftName} (thickness 100mm)");
                    }
                    else
                    {
                        logs.Add($"Found existing FloorType: {ftName}");
                    }

                    tx.Commit();
                }

                // 5. Create Floor element on Tầng 1
                Floor createdFloor = null;
                using (var tx = new Transaction(doc, "Create Nền Tầng 1 Slab 100mm"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new SlabWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    createdFloor = Floor.Create(doc, new List<CurveLoop> { loop }, ft100.Id, lvlTang1.Id);

                    // Set Level Offset = 0
                    var pOffset = createdFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    if (pOffset != null && !pOffset.IsReadOnly)
                    {
                        pOffset.Set(0.0);
                    }

                    logs.Add($"Created Floor ID: {createdFloor.Id.Value}");

                    tx.Commit();
                }

                uidoc.RefreshActiveView();
                try { doc.Save(); } catch { }

                // 6. Export verification images
                string outPlanImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_slab_plan.png";
                string out3DImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_slab_3d.png";

                var planView = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
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
                    level = lvlTang1.Name,
                    verticesCount = ptsM.Count,
                    areaM2 = Math.Round(createdFloor?.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2),
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
