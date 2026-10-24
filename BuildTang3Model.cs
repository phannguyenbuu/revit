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
    public class Tang3WarningSwallower : IFailuresPreprocessor
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

    public static class BuildTang3Model
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

        public class Tang3Data
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
            string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\tang3_creation_data.json";
            if (!File.Exists(jsonPath)) return new { error = "JSON file not found: " + jsonPath };

            var data = JsonSerializer.Deserialize<Tang3Data>(File.ReadAllText(jsonPath));
            if (data == null) return new { error = "Failed to deserialize JSON data" };

            // 2. Levels
            Level level3 = doc.GetElement(new ElementId(1727584)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 3") || l.Name.Contains("TANG 3"));
            Level level4 = doc.GetElement(new ElementId(2360634)) as Level
                ?? doc.GetElement(new ElementId(931615)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 4") || l.Name.Contains("ÁP MÁI"));

            if (level3 == null || level4 == null) return new { error = "Level 3 or 4 not found" };

            // 3. Wall Types
            var allWallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType200 = allWallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi") ?? allWallTypes.FirstOrDefault(w => w.Width > 0.6);
            var wallType100 = allWallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi") ?? allWallTypes.FirstOrDefault(w => w.Width < 0.4);

            // 4. Door & Window Symbols
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

            // Activate symbols
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

            // Clean any existing walls on Level 3 first
            var existingLvl3Walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => w.LevelId == level3.Id)
                .Select(w => w.Id)
                .ToList();

            if (existingLvl3Walls.Count > 0)
            {
                using (Transaction t = new Transaction(doc, "Delete Existing Level 3 Walls"))
                {
                    t.Start();
                    doc.Delete(existingLvl3Walls);
                    t.Commit();
                }
            }

            // 5. Create Walls
            var wallMap = new Dictionary<string, Wall>();
            var createdWallIds = new List<long>();
            double wallHeightFt = 3.60 * M2FT;

            using (Transaction t = new Transaction(doc, "Create Tang 3 Walls"))
            {
                var prep = new Tang3WarningSwallower();
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
                    Wall wall = Wall.Create(doc, line, targetType.Id, level3.Id, wallHeightFt, 0.0, false, false);
                    wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level4.Id);
                    wall.LookupParameter("Comments")?.Set("TANG_3_" + wd.id);

                    wallMap[wd.id] = wall;
                    createdWallIds.Add(wall.Id.Value);
                }
                t.Commit();
            }

            // 6. Create Doors
            var createdDoorIds = new List<long>();
            using (Transaction t = new Transaction(doc, "Create Tang 3 Doors"))
            {
                var prep = new Tang3WarningSwallower();
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
                        FamilyInstance door = doc.Create.NewFamilyInstance(pt, sym, hostWall, level3, StructuralType.NonStructural);
                        door.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(0.0);
                        door.LookupParameter("Mark")?.Set(dd.tag);
                        createdDoorIds.Add(door.Id.Value);
                    }
                    catch { }
                }
                t.Commit();
            }

            // 7. Create Windows
            var createdWindowIds = new List<long>();
            using (Transaction t = new Transaction(doc, "Create Tang 3 Windows"))
            {
                var prep = new Tang3WarningSwallower();
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
                        FamilyInstance win = doc.Create.NewFamilyInstance(pt, sym, hostWall, level3, StructuralType.NonStructural);
                        win.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(sillFt);
                        win.LookupParameter("Mark")?.Set(wd.tag);
                        createdWindowIds.Add(win.Id.Value);
                    }
                    catch { }
                }
                t.Commit();
            }

            // 8. Create Text Notes in View MẶT BẰNG TẦNG 3
            var planTang3 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Equals("MẶT BẰNG TẦNG 3", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.GenLevel?.Id == level3.Id);

            int createdTexts = 0;
            if (planTang3 != null)
            {
                var allTextTypes = new FilteredElementCollector(doc).OfClass(typeof(TextNoteType)).Cast<TextNoteType>().ToList();
                var defaultType = allTextTypes.FirstOrDefault(t => t.Name == "2.5mm Arial") ?? allTextTypes.First();
                var roomType = allTextTypes.FirstOrDefault(t => t.Name == "3.5mm Arial") ?? defaultType;

                // Clean existing text notes in planTang3 first
                var existingNotes = new FilteredElementCollector(doc, planTang3.Id)
                    .OfClass(typeof(TextNote))
                    .Cast<TextNote>()
                    .Select(n => n.Id)
                    .ToList();

                using (Transaction t = new Transaction(doc, "Create Tang 3 TextNotes"))
                {
                    var prep = new Tang3WarningSwallower();
                    var opt = t.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(prep);
                    t.SetFailureHandlingOptions(opt);

                    t.Start();
                    if (existingNotes.Count > 0)
                    {
                        try { doc.Delete(existingNotes); } catch { }
                    }

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
                            TextNote.Create(doc, planTang3.Id, pt, td.text, textOpt);
                            createdTexts++;
                        }
                        catch { }
                    }

                    // Set Crop Box around the building + grid bubbles
                    var bb = planTang3.CropBox;
                    if (bb != null)
                    {
                        bb.Min = new XYZ(-3.5 * M2FT, -4.5 * M2FT, bb.Min.Z);
                        bb.Max = new XYZ(41.0 * M2FT, 17.5 * M2FT, bb.Max.Z);
                        planTang3.CropBox = bb;
                    }
                    planTang3.CropBoxActive = true;
                    planTang3.CropBoxVisible = false;

                    t.Commit();
                }
            }

            // 9. Export Verification Images
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang3_clean.png");
            string plan3dImgPath = Path.Combine(folder, "revit_3d_tang123.jpg");

            if (planTang3 != null)
            {
                uidoc.ActiveView = planTang3;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang3.Id);
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
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
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
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                uiview?.ZoomToFit();

                try
                {
                    if (File.Exists(plan3dImgPath)) File.Delete(plan3dImgPath);
                    var opt = new ImageExportOptions
                    {
                        ExportRange = ExportRange.SetOfViews,
                        FilePath = plan3dImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        PixelSize = 1920,
                        ZoomType = ZoomFitType.FitToPage
                    };
                    opt.SetViewsAndSheets(new List<ElementId> { view3d.Id });
                    doc.ExportImage(opt);
                }
                catch { }

                // Switch back to Tang 3 plan
                if (planTang3 != null) uidoc.ActiveView = planTang3;
            }

            return new
            {
                success = true,
                wallsCreated = createdWallIds.Count,
                doorsCreated = createdDoorIds.Count,
                windowsCreated = createdWindowIds.Count,
                textsCreated = createdTexts,
                planTang3Image = planImgPath,
                view3dImage = plan3dImgPath
            };
        }
    }
}
