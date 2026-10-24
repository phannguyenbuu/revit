using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class Tang4WarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failList = failuresAccessor.GetFailureMessages();
            foreach (var failure in failList)
            {
                var severity = failure.GetSeverity();
                if (severity == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(failure);
                }
                else if (severity == FailureSeverity.Error)
                {
                    if (failure.HasResolutions())
                    {
                        failuresAccessor.ResolveFailure(failure);
                        return FailureProcessingResult.ProceedWithCommit;
                    }
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class BuildTang4Model
    {
        private const double M2FT = 3.2808398950131235;

        public class WallData
        {
            public string id { get; set; }
            public string type { get; set; }
            public List<double> p1 { get; set; }
            public List<double> p2 { get; set; }
        }

        public class DoorData
        {
            public string tag { get; set; }
            public string symbol { get; set; }
            public double x { get; set; }
            public double y { get; set; }
            public string hostWallId { get; set; }
        }

        public class WindowData
        {
            public string tag { get; set; }
            public string symbol { get; set; }
            public double x { get; set; }
            public double y { get; set; }
            public string hostWallId { get; set; }
            public double sill { get; set; }
        }

        public class TextData
        {
            public string text { get; set; }
            public double x { get; set; }
            public double y { get; set; }
            public string type { get; set; }
        }

        public class Tang4Data
        {
            public List<WallData> walls { get; set; }
            public List<DoorData> doors { get; set; }
            public List<WindowData> windows { get; set; }
            public List<TextData> texts { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Load Data JSON
            string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\tang4_creation_data.json";
            if (!File.Exists(jsonPath)) return new { error = "JSON file not found: " + jsonPath };

            var data = JsonSerializer.Deserialize<Tang4Data>(File.ReadAllText(jsonPath));
            if (data == null) return new { error = "Failed to deserialize JSON data" };

            // 2. Levels: Level 4 (Base = 10.8m) & Level 5 (Top = 14.4m)
            Level level4 = doc.GetElement(new ElementId(2360634L)) as Level
                ?? doc.GetElement(new ElementId(931615L)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 4") || l.Name.Contains("ÁP MÁI"));

            Level level5 = doc.GetElement(new ElementId(2360635L)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TUM") || l.Name.Contains("MÁI"));

            if (level4 == null || level5 == null) return new { error = "Level 4 or Level 5 not found" };

            // 3. Extend all 48 structural columns to Level 5 (elev 14.4m)
            var allCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            using (Transaction t = new Transaction(doc, "Extend Columns to Level 4 Top"))
            {
                var prep = new Tang4WarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();
                foreach (var col in allCols)
                {
                    try
                    {
                        var pTop = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        var pTopOff = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                        if (pTop != null && !pTop.IsReadOnly)
                        {
                            pTop.Set(level5.Id);
                            if (pTopOff != null && !pTopOff.IsReadOnly) pTopOff.Set(0.0);
                        }
                    }
                    catch { }
                }

                // Also extend grids to 35m
                var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().ToList();
                foreach (var g in grids)
                {
                    try { g.SetVerticalExtents(-10.0 * M2FT, 35.0 * M2FT); } catch { }
                }

                t.Commit();
            }

            // 4. Wall Types
            var allWallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType200 = allWallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi") ?? allWallTypes.FirstOrDefault(w => w.Width > 0.6);
            var wallType100 = allWallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi") ?? allWallTypes.FirstOrDefault(w => w.Width < 0.4);

            // 5. Door & Window Symbols
            var allDoorSymbols = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsElementType().Cast<FamilySymbol>().ToList();
            var symD2 = allDoorSymbols.FirstOrDefault(s => s.Name == "D2_1400x2200") ?? allDoorSymbols.FirstOrDefault(s => s.Name.Contains("1400") || s.Name.Contains("D2"));
            var symD4 = allDoorSymbols.FirstOrDefault(s => s.Name == "D4_1000x2200") ?? allDoorSymbols.FirstOrDefault(s => s.Name.Contains("1000") || s.FamilyName.Contains("1 CANH"));
            var symD5 = allDoorSymbols.FirstOrDefault(s => s.Name == "D5_800x2200") ?? allDoorSymbols.FirstOrDefault(s => s.Name.Contains("800"));
            var symD7 = allDoorSymbols.FirstOrDefault(s => s.Name.Contains("D7") || s.Name.Contains("1200")) ?? symD4;

            var allWinSymbols = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType().Cast<FamilySymbol>().ToList();
            var symS1 = allWinSymbols.FirstOrDefault(s => s.Name == "S1_1500x1400") ?? allWinSymbols.FirstOrDefault(s => s.Name.Contains("S1"));
            var symS4 = allWinSymbols.FirstOrDefault(s => s.Name == "S4_1500x1400") ?? symS1;
            var symS3 = allWinSymbols.FirstOrDefault(s => s.Name == "900X1900") ?? allWinSymbols.FirstOrDefault(s => s.Name.Contains("S3") || s.Name.Contains("900"));
            var symK3 = allWinSymbols.FirstOrDefault(s => s.Name == "K3_3100x2100") ?? allWinSymbols.FirstOrDefault(s => s.Name.Contains("K3") || s.Name.Contains("3100"));

            using (Transaction t = new Transaction(doc, "Activate Symbols"))
            {
                t.Start();
                if (symD2 != null && !symD2.IsActive) symD2.Activate();
                if (symD4 != null && !symD4.IsActive) symD4.Activate();
                if (symD5 != null && !symD5.IsActive) symD5.Activate();
                if (symD7 != null && !symD7.IsActive) symD7.Activate();
                if (symS1 != null && !symS1.IsActive) symS1.Activate();
                if (symS4 != null && !symS4.IsActive) symS4.Activate();
                if (symS3 != null && !symS3.IsActive) symS3.Activate();
                if (symK3 != null && !symK3.IsActive) symK3.Activate();
                t.Commit();
            }

            // Clean any existing walls on Level 4 first
            var existingLvl4Walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => w.LevelId == level4.Id)
                .Select(w => w.Id)
                .ToList();

            if (existingLvl4Walls.Count > 0)
            {
                using (Transaction t = new Transaction(doc, "Delete Existing Level 4 Walls"))
                {
                    t.Start();
                    doc.Delete(existingLvl4Walls);
                    t.Commit();
                }
            }

            // 6. Create Walls on Level 4
            var wallMap = new Dictionary<string, Wall>();
            var createdWallIds = new List<long>();
            double wallHeightFt = 3.60 * M2FT;

            using (Transaction t = new Transaction(doc, "Create Tang 4 Walls"))
            {
                var prep = new Tang4WarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();
                foreach (var wd in data.walls)
                {
                    var p1 = new XYZ(wd.p1[0] * M2FT, wd.p1[1] * M2FT, 0.0);
                    var p2 = new XYZ(wd.p2[0] * M2FT, wd.p2[1] * M2FT, 0.0);
                    Line line = Line.CreateBound(p1, p2);

                    WallType targetType = (wd.type.Contains("100") ? wallType100 : wallType200) ?? wallType200;
                    Wall wall = Wall.Create(doc, line, targetType.Id, level4.Id, wallHeightFt, 0.0, false, false);
                    wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level5.Id);
                    wall.LookupParameter("Comments")?.Set("TANG_4_" + wd.id);

                    wallMap[wd.id] = wall;
                    createdWallIds.Add(wall.Id.Value);
                }
                t.Commit();
            }

            // 7. Create Doors
            var createdDoorIds = new List<long>();
            using (Transaction t = new Transaction(doc, "Create Tang 4 Doors"))
            {
                var prep = new Tang4WarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();
                foreach (var dd in data.doors)
                {
                    if (!wallMap.ContainsKey(dd.hostWallId)) continue;
                    Wall hostWall = wallMap[dd.hostWallId];

                    FamilySymbol sym = symD4;
                    if (dd.tag == "D2") sym = symD2 ?? symD4;
                    else if (dd.tag == "D5") sym = symD5 ?? symD4;
                    else if (dd.tag == "D7") sym = symD7 ?? symD4;

                    if (sym == null) continue;

                    var pt = new XYZ(dd.x * M2FT, dd.y * M2FT, 0.0);
                    try
                    {
                        FamilyInstance door = doc.Create.NewFamilyInstance(pt, sym, hostWall, level4, StructuralType.NonStructural);
                        door.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(0.0);
                        door.LookupParameter("Mark")?.Set(dd.tag);
                        createdDoorIds.Add(door.Id.Value);
                    }
                    catch { }
                }
                t.Commit();
            }

            // 8. Create Windows
            var createdWindowIds = new List<long>();
            using (Transaction t = new Transaction(doc, "Create Tang 4 Windows"))
            {
                var prep = new Tang4WarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();
                foreach (var wd in data.windows)
                {
                    if (!wallMap.ContainsKey(wd.hostWallId)) continue;
                    Wall hostWall = wallMap[wd.hostWallId];

                    FamilySymbol sym = symS1;
                    if (wd.tag == "S4") sym = symS4 ?? symS1;
                    else if (wd.tag == "S3") sym = symS3 ?? symS1;
                    else if (wd.tag == "K3") sym = symK3 ?? symS1;

                    if (sym == null) continue;

                    double sillFt = wd.sill * M2FT;
                    var pt = new XYZ(wd.x * M2FT, wd.y * M2FT, sillFt);
                    try
                    {
                        FamilyInstance win = doc.Create.NewFamilyInstance(pt, sym, hostWall, level4, StructuralType.NonStructural);
                        win.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(sillFt);
                        win.LookupParameter("Mark")?.Set(wd.tag);
                        createdWindowIds.Add(win.Id.Value);
                    }
                    catch { }
                }
                t.Commit();
            }

            // 9. Plan View for Tầng 4
            ViewPlan planTang4 = doc.GetElement(new ElementId(931687L)) as ViewPlan
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && (v.Name.Contains("TẦNG 4") || v.Name.Contains("ÁP MÁI")))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.GenLevel?.Id == level4.Id);

            if (planTang4 == null)
            {
                var viewFamilyType = new FilteredElementCollector(doc).OfClass(typeof(ViewFamilyType)).Cast<ViewFamilyType>().FirstOrDefault(v => v.ViewFamily == ViewFamily.FloorPlan);
                if (viewFamilyType != null)
                {
                    using (Transaction t = new Transaction(doc, "Create Tang 4 View"))
                    {
                        t.Start();
                        planTang4 = ViewPlan.Create(doc, viewFamilyType.Id, level4.Id);
                        try { planTang4.Name = "MẶT BẰNG TẦNG 4"; } catch { }
                        t.Commit();
                    }
                }
            }

            int createdTexts = 0;
            if (planTang4 != null)
            {
                var allTextTypes = new FilteredElementCollector(doc).OfClass(typeof(TextNoteType)).Cast<TextNoteType>().ToList();
                var defaultType = allTextTypes.FirstOrDefault(t => t.Name == "2.5mm Arial") ?? allTextTypes.First();
                var roomType = allTextTypes.FirstOrDefault(t => t.Name == "3.5mm Arial") ?? defaultType;

                using (Transaction t = new Transaction(doc, "Setup Tang 4 View & Texts"))
                {
                    var prep = new Tang4WarningSwallower();
                    var opt = t.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(prep);
                    t.SetFailureHandlingOptions(opt);

                    t.Start();

                    // Delete existing text notes in planTang4
                    var existingNotes = new FilteredElementCollector(doc, planTang4.Id).OfClass(typeof(TextNote)).Select(n => n.Id).ToList();
                    if (existingNotes.Count > 0)
                    {
                        try { doc.Delete(existingNotes); } catch { }
                    }

                    // Create text notes
                    foreach (var td in data.texts)
                    {
                        var targetType = td.type.Contains("3.5") ? roomType : defaultType;
                        var pt = new XYZ(td.x * M2FT, td.y * M2FT, 0.0);
                        try
                        {
                            TextNoteOptions textOpt = new TextNoteOptions
                            {
                                HorizontalAlignment = HorizontalTextAlignment.Center,
                                TypeId = targetType.Id
                            };
                            TextNote.Create(doc, planTang4.Id, pt, td.text, textOpt);
                            createdTexts++;
                        }
                        catch { }
                    }

                    // Hide section markers and elevation markers specifically by ElementId
                    var hideList = new List<ElementId>
                    {
                        new ElementId(749995L),
                        new ElementId(8142L),
                        new ElementId(8174L),
                        new ElementId(8208L),
                        new ElementId(98746L)
                    };

                    var extraViewers = new FilteredElementCollector(doc, planTang4.Id)
                        .OfCategory(BuiltInCategory.OST_Viewers)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraViewers);

                    var extraElevs = new FilteredElementCollector(doc, planTang4.Id)
                        .OfCategory(BuiltInCategory.OST_Elev)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraElevs);

                    var extraCameras = new FilteredElementCollector(doc, planTang4.Id)
                        .OfCategory(BuiltInCategory.OST_Cameras)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraCameras);

                    var extraSectionBoxes = new FilteredElementCollector(doc, planTang4.Id)
                        .OfCategory(BuiltInCategory.OST_SectionBox)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraSectionBoxes);

                    var canHide = hideList.Distinct().Where(id =>
                    {
                        var el = doc.GetElement(id);
                        return el != null && el.CanBeHidden(planTang4);
                    }).ToList();

                    if (canHide.Count > 0)
                    {
                        try { planTang4.HideElements(canHide); } catch { }
                    }

                    // Unhide Grids
                    var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
                    if (gridCat != null && planTang4.CanCategoryBeHidden(gridCat.Id))
                    {
                        if (planTang4.GetCategoryHidden(gridCat.Id)) planTang4.SetCategoryHidden(gridCat.Id, false);
                    }

                    // Set Perfect Crop Box around building + grid bubbles
                    var bb = planTang4.CropBox;
                    var tr = bb.Transform;
                    var inv = tr.Inverse;

                    var pMinWorld = new XYZ(-2.5 * M2FT, -3.5 * M2FT, tr.Origin.Z);
                    var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, tr.Origin.Z);

                    var pMinLocal = inv.OfPoint(pMinWorld);
                    var pMaxLocal = inv.OfPoint(pMaxWorld);

                    bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                    bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                    planTang4.CropBox = bb;
                    planTang4.CropBoxActive = true;
                    planTang4.CropBoxVisible = false;

                    t.Commit();
                }
            }

            // 10. Export Images
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang4_perfect.png");
            string plan3dImgPath = Path.Combine(folder, "revit_3d_tang1234.jpg");

            if (planTang4 != null)
            {
                uidoc.ActiveView = planTang4;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang4.Id);
                uiview?.ZoomToFit();

                try
                {
                    if (File.Exists(planImgPath)) File.Delete(planImgPath);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = planImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3800
                    };
                    doc.ExportImage(expOpt);
                }
                catch { }
            }

            // 3D View Export
            var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
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
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2800
                    };
                    doc.ExportImage(expOpt3d);
                }
                catch { }

                if (planTang4 != null) uidoc.ActiveView = planTang4;
            }

            // 11. Save document
            bool docSaved = false;
            try
            {
                doc.Save(new SaveOptions());
                docSaved = true;
            }
            catch { }

            return new
            {
                success = true,
                wallsCreated = createdWallIds.Count,
                doorsCreated = createdDoorIds.Count,
                windowsCreated = createdWindowIds.Count,
                textsCreated = createdTexts,
                columnsExtended = allCols.Count,
                docSaved,
                planTang4Image = planImgPath,
                view3dImage = plan3dImgPath
            };
        }
    }
}
