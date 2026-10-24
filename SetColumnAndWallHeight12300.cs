using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetColumnAndWallHeight12300
    {
        private const double FT2M = 0.3048;
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            double targetHeightMm = 12300.0;
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("heightMm", out var hProp))
            {
                targetHeightMm = hProp.GetDouble();
            }
            double targetHeightFt = targetHeightMm / 304.8;

            // Target walls identified from user selection and Axis 11 pillar box
            var targetWallIds = new List<long>
            {
                2379828L, 2379825L, 2379826L, 2379827L,
                2361336L, 2379829L, 2379830L, 2379822L
            };

            // Include any currently selected walls or columns
            var currentSel = uidoc.Selection.GetElementIds();
            foreach (var id in currentSel)
            {
                var elem = doc.GetElement(id);
                if (elem is Wall && !targetWallIds.Contains(id.Value))
                {
                    targetWallIds.Add(id.Value);
                }
            }

            var updatedWalls = new List<object>();
            var updatedCols = new List<object>();
            var finalSelectionIds = new List<ElementId>();

            // Find levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang4 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 4", StringComparison.OrdinalIgnoreCase));
            var lvlApMai = levels.FirstOrDefault(l => l.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase)) ?? lvlTang4;

            using (var tx = new Transaction(doc, "Set Column and Walls Height to 12300mm"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new GenericWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                // 1. UPDATE WALLS TO 12300 MM
                foreach (var wid in targetWallIds)
                {
                    var elem = doc.GetElement(new ElementId(wid));
                    if (elem is not Wall wall) continue;

                    // Top Constraint -> Unconnected
                    var pTop = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                    if (pTop != null && !pTop.IsReadOnly)
                    {
                        pTop.Set(ElementId.InvalidElementId);
                    }

                    // Height -> 12300 mm
                    var pHeight = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    if (pHeight != null && !pHeight.IsReadOnly)
                    {
                        pHeight.Set(targetHeightFt);
                    }

                    // Base offset -> 0
                    var pBaseOff = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                    if (pBaseOff != null && !pBaseOff.IsReadOnly)
                    {
                        pBaseOff.Set(0.0);
                    }

                    doc.Regenerate();

                    double curH = (pHeight?.AsDouble() ?? 0) * 304.8;
                    updatedWalls.Add(new
                    {
                        id = wall.Id.Value,
                        wallType = wall.WallType.Name,
                        heightMm = Math.Round(curH, 1)
                    });
                    finalSelectionIds.Add(wall.Id);
                }

                // 2. UPDATE COLUMN STACK AT (37150, 100) TO REACH 12300 MM
                // Check if segment on Tang 4 exists at (37150, 100)
                var existingColsAtPos = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(c => {
                        var lp = c.Location as LocationPoint;
                        if (lp == null) return false;
                        double x = lp.Point.X * FT2M * 1000;
                        double y = lp.Point.Y * FT2M * 1000;
                        return Math.Abs(x - 37150) < 100 && Math.Abs(y - 100) < 100;
                    })
                    .ToList();

                FamilyInstance? colTang4 = null;
                FamilySymbol? colSymbol = null;

                foreach (var c in existingColsAtPos)
                {
                    colSymbol = c.Symbol;
                    var pBase = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    if (pBase != null && lvlTang4 != null && pBase.AsElementId() == lvlTang4.Id)
                    {
                        colTang4 = c;
                    }
                }

                if (colTang4 != null)
                {
                    // Update existing Tang 4 column top offset
                    var pTop = colTang4.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    var pTopOff = colTang4.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                    if (lvlApMai != null && pTop != null && !pTop.IsReadOnly) pTop.Set(lvlApMai.Id);
                    if (pTopOff != null && !pTopOff.IsReadOnly) pTopOff.Set(1.5 * M2FT); // 1500mm -> reaches +12.300m
                    doc.Regenerate();

                    updatedCols.Add(new
                    {
                        id = colTang4.Id.Value,
                        action = "updated_tang4_column",
                        baseLevel = lvlTang4?.Name,
                        topLevel = lvlApMai?.Name,
                        topOffsetMm = 1500.0,
                        topElevationM = 12.3
                    });
                    finalSelectionIds.Add(colTang4.Id);
                }
                else if (colSymbol != null && lvlTang4 != null && lvlApMai != null)
                {
                    // Create the Tang 4 column segment reaching +12.300m (12300 mm total height)
                    var pt = new XYZ(37150 / 1000.0 * M2FT, 100 / 1000.0 * M2FT, lvlTang4.Elevation);
                    var newCol = doc.Create.NewFamilyInstance(pt, colSymbol, lvlTang4, StructuralType.Column);

                    var pBase = newCol.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    var pTop = newCol.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    var pBaseOff = newCol.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                    var pTopOff = newCol.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                    if (pBase != null && !pBase.IsReadOnly) pBase.Set(lvlTang4.Id);
                    if (pTop != null && !pTop.IsReadOnly) pTop.Set(lvlApMai.Id);
                    if (pBaseOff != null && !pBaseOff.IsReadOnly) pBaseOff.Set(0.0);
                    if (pTopOff != null && !pTopOff.IsReadOnly) pTopOff.Set(1.5 * M2FT); // 1500 mm offset

                    doc.Regenerate();

                    updatedCols.Add(new
                    {
                        id = newCol.Id.Value,
                        action = "created_tang4_column_segment_to_12300",
                        baseLevel = lvlTang4.Name,
                        topLevel = lvlApMai.Name,
                        topOffsetMm = 1500.0,
                        topElevationM = 12.3
                    });
                    finalSelectionIds.Add(newCol.Id);
                }

                // Also add existing column segment 2379835 to selection
                var baseCol = doc.GetElement(new ElementId(2379835L));
                if (baseCol != null)
                {
                    finalSelectionIds.Add(baseCol.Id);
                    updatedCols.Add(new
                    {
                        id = 2379835L,
                        action = "base_column_part_of_stack",
                        baseLevel = "MẶT BẰNG TẦNG 1",
                        stackTopElevationM = 12.3
                    });
                }

                tx.Commit();
            }

            // Set selection in Revit so user sees them highlighted
            try
            {
                uidoc.Selection.SetElementIds(finalSelectionIds);
            }
            catch { }

            // Export 3D image
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\46315a5a-177a-46ef-beb3-de86d38f2956";
            string outImg = Path.Combine(folder, "revit_column_walls_height_12300.png");
            if (File.Exists(outImg)) { try { File.Delete(outImg); } catch { } }

            try
            {
                var view3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview?.ZoomToFit();

                    var expOpts = new ImageExportOptions
                    {
                        FilePath = outImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpts);
                }
            }
            catch { }

            return new
            {
                success = true,
                targetHeightMm,
                updatedWallsCount = updatedWalls.Count,
                updatedWalls,
                updatedCols,
                image = outImg
            };
        }
    }
}
