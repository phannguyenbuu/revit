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
    public class TangTumWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failures = failuresAccessor.GetFailureMessages();
            foreach (var f in failures)
            {
                if (f.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(f);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class BuildTangTumModel
    {
        private const double M2FT = 3.2808398950131235;
        private static double M(double meters) => meters / 0.3048;
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Levels
            Level levelTum = doc.GetElement(new ElementId(2360635L)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TUM") || Math.Abs(ToM(l.Elevation) - 14.4) < 0.1);

            Level levelMai = doc.GetElement(new ElementId(1209118L)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("MÁI") || Math.Abs(ToM(l.Elevation) - 17.2) < 0.1);

            if (levelTum == null) return new { error = "Level Tầng Tum (14.4m) not found" };

            double wallHeight_m = levelMai != null ? (ToM(levelMai.Elevation) - ToM(levelTum.Elevation)) : 2.80;
            if (wallHeight_m <= 0.5) wallHeight_m = 2.80;

            // 2. Wall Type (200mm)
            var allWallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType200 = allWallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi") 
                ?? allWallTypes.FirstOrDefault(w => Math.Abs(w.Width - M(0.20)) < 0.05)
                ?? allWallTypes.FirstOrDefault(w => w.Width > 0.6);

            if (wallType200 == null) return new { error = "WallType 200mm not found" };

            // 3. Door Symbol D4
            var allDoorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            var symD4 = allDoorSymbols.FirstOrDefault(s => s.Name == "D4_1000x2200")
                ?? allDoorSymbols.FirstOrDefault(s => s.Name.Contains("D4") || s.Name.Contains("1000"));

            if (symD4 == null) return new { error = "Door Symbol D4_1000x2200 not found" };

            using (Transaction t = new Transaction(doc, "Activate D4 Symbol"))
            {
                t.Start();
                if (!symD4.IsActive) symD4.Activate();
                t.Commit();
            }

            // 4. Clean existing walls on Level Tum
            var existingTumWalls = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Walls)
                .WhereElementIsNotElementType()
                .Cast<Wall>()
                .Where(w => w.LevelId == levelTum.Id)
                .Select(w => w.Id)
                .ToList();

            if (existingTumWalls.Count > 0)
            {
                using (Transaction t = new Transaction(doc, "Clean Existing Tum Walls"))
                {
                    t.Start();
                    doc.Delete(existingTumWalls);
                    t.Commit();
                }
            }

            // 5. Create 4 walls
            // Room coordinates based on Trục 9 (X=29.65), Trục 10 (X=33.35), Trục C (Y=7.80), Trục E (Y=14.90)
            var wallDefs = new[]
            {
                new { Name = "Wall_North_E", X1 = 29.650, Y1 = 14.900, X2 = 33.350, Y2 = 14.900, IsHost = false },
                new { Name = "Wall_East_10",  X1 = 33.350, Y1 = 14.900, X2 = 33.350, Y2 = 7.800,  IsHost = false },
                new { Name = "Wall_South_C", X1 = 33.350, Y1 = 7.800,  X2 = 29.650, Y2 = 7.800,  IsHost = true  },
                new { Name = "Wall_West_9",   X1 = 29.650, Y1 = 7.800,  X2 = 29.650, Y2 = 14.900, IsHost = false }
            };

            var createdWallIds = new List<ElementId>();
            Wall hostWallSouth = null;

            using (Transaction t = new Transaction(doc, "Create Tang Tum 4 Walls"))
            {
                var prep = new TangTumWarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                foreach (var wd in wallDefs)
                {
                    XYZ p1 = new XYZ(M(wd.X1), M(wd.Y1), levelTum.Elevation);
                    XYZ p2 = new XYZ(M(wd.X2), M(wd.Y2), levelTum.Elevation);
                    Line line = Line.CreateBound(p1, p2);

                    Wall wall = Wall.Create(doc, line, wallType200.Id, levelTum.Id, M(wallHeight_m), 0.0, false, false);
                    wall.LookupParameter("Comments")?.Set(wd.Name);

                    if (levelMai != null)
                    {
                        var pTop = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                        if (pTop != null && !pTop.IsReadOnly) pTop.Set(levelMai.Id);
                    }
                    var pTopOff = wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                    if (pTopOff != null && !pTopOff.IsReadOnly) pTopOff.Set(0.0);

                    var pBaseOff = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                    if (pBaseOff != null && !pBaseOff.IsReadOnly) pBaseOff.Set(0.0);

                    createdWallIds.Add(wall.Id);
                    if (wd.IsHost) hostWallSouth = wall;
                }

                doc.Regenerate();
                t.Commit();
            }

            // 6. Create Door D4 on Wall_South_C
            FamilyInstance createdDoor = null;
            if (hostWallSouth != null)
            {
                using (Transaction t = new Transaction(doc, "Place Door D4"))
                {
                    var prep = new TangTumWarningSwallower();
                    var opt = t.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(prep);
                    t.SetFailureHandlingOptions(opt);

                    t.Start();

                    double doorX = 32.650;
                    double doorY = 7.800;
                    XYZ doorLoc = new XYZ(M(doorX), M(doorY), levelTum.Elevation);

                    createdDoor = doc.Create.NewFamilyInstance(doorLoc, symD4, hostWallSouth, levelTum, StructuralType.NonStructural);
                    if (createdDoor != null)
                    {
                        createdDoor.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("D4");
                        createdDoor.LookupParameter("Comments")?.Set("D4_TANG_TUM");
                        createdDoor.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(0.0);

                        doc.Regenerate();
                        // In CAD, the door opens outwards to South (Y < 7.80)
                        if (createdDoor.FacingOrientation.Y > 0)
                        {
                            createdDoor.flipFacing();
                        }
                    }

                    t.Commit();
                }
            }

            // 7. Extend columns E9 and E10 to Level Mái
            using (Transaction t = new Transaction(doc, "Extend Columns E9 and E10"))
            {
                var prep = new TangTumWarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                var cols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .ToList();

                foreach (var col in cols)
                {
                    var bb = col.get_BoundingBox(null);
                    if (bb == null) continue;
                    double cx = ToM((bb.Min.X + bb.Max.X) / 2.0);
                    double cy = ToM((bb.Min.Y + bb.Max.Y) / 2.0);

                    bool isE9 = Math.Abs(cx - 29.65) < 0.25 && Math.Abs(cy - 14.90) < 0.25;
                    bool isE10 = Math.Abs(cx - 33.35) < 0.25 && Math.Abs(cy - 14.90) < 0.25;

                    if ((isE9 || isE10) && levelMai != null)
                    {
                        var pTop = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        var pTopOff = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                        if (pTop != null && !pTop.IsReadOnly) pTop.Set(levelMai.Id);
                        if (pTopOff != null && !pTopOff.IsReadOnly) pTopOff.Set(0.0);
                    }
                }

                t.Commit();
            }

            // 8. Find or create Floor Plan for Tầng Tum
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(outDir, "plan_tang_tum.png");
            string plan3dImgPath = Path.Combine(outDir, "revit_3d_tang1234_with_tum.jpg");

            ViewPlan planTum = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.GenLevel?.Id == levelTum.Id && v.ViewType == ViewType.FloorPlan);

            if (planTum == null)
            {
                var viewFamilyType = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewFamilyType))
                    .Cast<ViewFamilyType>()
                    .FirstOrDefault(vft => vft.ViewFamily == ViewFamily.FloorPlan);

                if (viewFamilyType != null)
                {
                    using (Transaction tv = new Transaction(doc, "Create Tang Tum View"))
                    {
                        tv.Start();
                        planTum = ViewPlan.Create(doc, viewFamilyType.Id, levelTum.Id);
                        try { planTum.Name = "MẶT BẰNG TẦNG TUM"; } catch { }
                        tv.Commit();
                    }
                }
            }

            if (planTum != null)
            {
                uidoc.ActiveView = planTum;

                using (Transaction t = new Transaction(doc, "Setup Tum View and Text"))
                {
                    t.Start();

                    var cats = new[] { BuiltInCategory.OST_Grids, BuiltInCategory.OST_Walls, BuiltInCategory.OST_Doors, BuiltInCategory.OST_Stairs, BuiltInCategory.OST_StructuralColumns };
                    foreach (var cat in cats)
                    {
                        var cId = new ElementId(cat);
                        if (planTum.CanCategoryBeHidden(cId) && planTum.GetCategoryHidden(cId))
                        {
                            planTum.SetCategoryHidden(cId, false);
                        }
                    }

                    // Add Text Notes
                    var textTypes = new FilteredElementCollector(doc).OfClass(typeof(TextNoteType)).Cast<TextNoteType>().ToList();
                    var textType = textTypes.FirstOrDefault(t2 => t2.Name.Contains("2.0") || t2.Name.Contains("2.5")) ?? textTypes.FirstOrDefault();
                    if (textType != null)
                    {
                        var optText = new TextNoteOptions(textType.Id);
                        XYZ textPos = new XYZ(M(32.555), M(8.147), levelTum.Elevation);
                        TextNote.Create(doc, planTum.Id, textPos, "D4", optText);

                        XYZ textPosRoom = new XYZ(M(31.500), M(11.500), levelTum.Elevation);
                        TextNote.Create(doc, planTum.Id, textPosRoom, "TẦNG TUM", optText);
                    }

                    t.Commit();
                }

                // Zoom to Tum room
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTum.Id);
                uiview?.ZoomAndCenterRectangle(new XYZ(M(24.0), M(4.0), 0), new XYZ(M(38.0), M(17.0), 0));

                try
                {
                    if (File.Exists(planImgPath)) File.Delete(planImgPath);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = planImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3200
                    };
                    doc.ExportImage(expOpt);
                }
                catch { }
            }

            // 9. Export 3D view
            var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name == "{3D}")
                ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

            if (view3d != null)
            {
                uidoc.ActiveView = view3d;
                var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                uiview3d?.ZoomToFit();

                try
                {
                    if (File.Exists(plan3dImgPath)) File.Delete(plan3dImgPath);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = plan3dImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt3d);
                }
                catch { }
            }

            // 10. Save Document
            bool saved = false;
            try
            {
                doc.Save();
                saved = true;
            }
            catch { }

            return new
            {
                status = "SUCCESS",
                createdWalls = createdWallIds.Count,
                wallIds = createdWallIds.Select(id => id.Value).ToList(),
                doorId = createdDoor?.Id.Value,
                doorMark = "D4",
                doorLocation = new { x = 32.650, y = 7.800, z = 14.400 },
                planImgPath,
                plan3dImgPath,
                docSaved = saved
            };
        }
    }
}
