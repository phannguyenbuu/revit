using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class GainWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failureMessages = failuresAccessor.GetFailureMessages();
            foreach (var msg in failureMessages)
            {
                if (msg.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(msg);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class CreateGainWalls
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Get or create 100mm wall type "gach100_xay moi"
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();

            var wallType100 = wallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi" || w.Name == "Tường 100" || (Math.Abs(w.Width * FT2M - 0.100) < 0.005 && w.Kind == WallKind.Basic));

            using (var txType = new Transaction(doc, "AI Copilot: Prepare 100mm Wall Type"))
            {
                txType.Start();
                var opt = txType.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new GainWarningSwallower());
                txType.SetFailureHandlingOptions(opt);

                if (wallType100 == null)
                {
                    var baseWallType = wallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi")
                                    ?? wallTypes.FirstOrDefault(w => w.Kind == WallKind.Basic && w.Width * FT2M >= 0.14);

                    if (baseWallType == null)
                    {
                        txType.RollBack();
                        return new { error = "No basic wall type found to duplicate" };
                    }

                    wallType100 = baseWallType.Duplicate("gach100_xay moi") as WallType;
                    var cs = wallType100.GetCompoundStructure();
                    var layers = cs.GetLayers();

                    // If multiple layers or single layer, set total thickness to 100mm (0.100m)
                    if (layers.Count == 1)
                    {
                        layers[0].Width = 0.100 * M2FT;
                    }
                    else
                    {
                        // Keep finishes if present, adjust core
                        int coreIdx = cs.GetFirstCoreLayerIndex();
                        double finishWidth = 0.0;
                        for (int i = 0; i < layers.Count; i++)
                        {
                            if (i != coreIdx) finishWidth += layers[i].Width;
                        }
                        double targetCore = (0.100 * M2FT) - finishWidth;
                        if (targetCore > 0.02 * M2FT)
                        {
                            layers[coreIdx].Width = targetCore;
                        }
                        else
                        {
                            // Flatten to single structural layer
                            var singleLayer = layers[coreIdx];
                            singleLayer.Width = 0.100 * M2FT;
                            layers = new List<CompoundStructureLayer> { singleLayer };
                        }
                    }
                    cs.SetLayers(layers);
                    wallType100.SetCompoundStructure(cs);
                }
                txType.Commit();
            }

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Wall Lines
            // Centerline Corner:
            // X_corner = 29.3000 m
            // Y_corner = 13.75174 m
            //
            // Wall 1 (Horizontal Wall):
            // From corner (29.3000, 13.75174) to centerline of Trục 9 stair wall (29.6500, 13.75174)
            //
            // Wall 2 (Vertical Wall):
            // From corner (29.3000, 13.75174) to centerline of Wall C (29.3000, 13.2000)

            double zFt = lvlTang1.Elevation;

            XYZ ptCorner = new XYZ(29.3000 * M2FT, 13.75174 * M2FT, zFt);
            XYZ ptEast = new XYZ(29.6500 * M2FT, 13.75174 * M2FT, zFt);
            XYZ ptSouth = new XYZ(29.3000 * M2FT, 13.2000 * M2FT, zFt);

            Line lineH = Line.CreateBound(ptCorner, ptEast);
            Line lineV = Line.CreateBound(ptSouth, ptCorner);

            Wall wallH = null;
            Wall wallV = null;

            using (var tx = new Transaction(doc, "AI Copilot: Create Hộp Gain 100 Walls"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new GainWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

                // Create Horizontal Wall
                wallH = Wall.Create(doc, lineH, wallType100.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    wallH.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    wallH.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }

                // Create Vertical Wall
                wallV = Wall.Create(doc, lineV, wallType100.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    wallV.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    wallV.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }

                tx.Commit();
            }

            // 4. Export verification image of active view
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_gain_walls_result.png";
            try
            {
                var activeView = uidoc.ActiveView;
                var expOpt = new ImageExportOptions
                {
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560,
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                wallType = wallType100.Name,
                widthMm = wallType100.Width * FT2M * 1000.0,
                wallH = new
                {
                    id = wallH?.Id.Value,
                    lengthM = lineH.Length * FT2M,
                    start = new { x = ptCorner.X * FT2M, y = ptCorner.Y * FT2M },
                    end = new { x = ptEast.X * FT2M, y = ptEast.Y * FT2M }
                },
                wallV = new
                {
                    id = wallV?.Id.Value,
                    lengthM = lineV.Length * FT2M,
                    start = new { x = ptSouth.X * FT2M, y = ptSouth.Y * FT2M },
                    end = new { x = ptCorner.X * FT2M, y = ptCorner.Y * FT2M }
                },
                exportImage = outImgPath
            };
        }
    }
}
