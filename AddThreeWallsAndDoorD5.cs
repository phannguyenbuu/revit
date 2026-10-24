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
    public static class AddThreeWallsAndDoorD5
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Levels
            Level level2 = doc.GetElement(new ElementId(694L)) as Level;
            Level level3 = doc.GetElement(new ElementId(1727584L)) as Level;
            if (level2 == null || level3 == null) return new { error = "Levels not found" };

            // 2. Wall type
            var allWallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType100 = allWallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi") ?? allWallTypes.FirstOrDefault(w => w.Width < 0.4);
            if (wallType100 == null) return new { error = "WallType 100 not found" };

            // 3. Door Symbol D5
            var allDoorSymbols = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsElementType().Cast<FamilySymbol>().ToList();
            var symD5 = allDoorSymbols.FirstOrDefault(s => s.Name == "D5_800x2200") ?? allDoorSymbols.FirstOrDefault(s => s.Name.Contains("800"));
            if (symD5 == null) return new { error = "Door symbol D5 not found" };

            using (Transaction t = new Transaction(doc, "Activate D5 Symbol"))
            {
                t.Start();
                if (!symD5.IsActive) symD5.Activate();
                t.Commit();
            }

            // 4. Delete misplaced door 2368988 if it exists at (34.54, 9.45)
            var misplacedDoor = doc.GetElement(new ElementId(2368988L));
            if (misplacedDoor != null)
            {
                using (Transaction t = new Transaction(doc, "Delete Misplaced Door"))
                {
                    t.Start();
                    try { doc.Delete(misplacedDoor.Id); } catch { }
                    t.Commit();
                }
            }

            // 5. Delete rough wall 2368971 if it exists at X=35.0
            var oldStallWall = doc.GetElement(new ElementId(2368971L));
            if (oldStallWall != null)
            {
                using (Transaction t = new Transaction(doc, "Delete Old Rough Stall Wall"))
                {
                    t.Start();
                    try { doc.Delete(oldStallWall.Id); } catch { }
                    t.Commit();
                }
            }

            // 6. Create 3 Walls
            // Wall 1: Vertical partition wall X = 34.5965 from Y = 7.80 to Y = 9.45
            // Wall 2: Horizontal pipe chase wall Y = 8.4018 from X = 34.5965 to X = 34.9465
            // Wall 3: Vertical pipe chase wall X = 34.9465 from Y = 7.80 to Y = 8.4018
            double wallHeightFt = 3.60 * M2FT;
            Wall wall1 = null;
            Wall wall2 = null;
            Wall wall3 = null;

            using (Transaction t = new Transaction(doc, "Create 3 WC Walls"))
            {
                var prep = new Tang2WarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                // Wall 1
                Line line1 = Line.CreateBound(new XYZ(34.5965 * M2FT, 7.8000 * M2FT, 0.0), new XYZ(34.5965 * M2FT, 9.4500 * M2FT, 0.0));
                wall1 = Wall.Create(doc, line1, wallType100.Id, level2.Id, wallHeightFt, 0.0, false, false);
                wall1.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level3.Id);
                wall1.LookupParameter("Comments")?.Set("TANG_2_Wall_WC_Part_X34.60");

                // Wall 2
                Line line2 = Line.CreateBound(new XYZ(34.5965 * M2FT, 8.4018 * M2FT, 0.0), new XYZ(34.9465 * M2FT, 8.4018 * M2FT, 0.0));
                wall2 = Wall.Create(doc, line2, wallType100.Id, level2.Id, wallHeightFt, 0.0, false, false);
                wall2.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level3.Id);
                wall2.LookupParameter("Comments")?.Set("TANG_2_Wall_WC_Chase_Y8.40");

                // Wall 3
                Line line3 = Line.CreateBound(new XYZ(34.9465 * M2FT, 7.8000 * M2FT, 0.0), new XYZ(34.9465 * M2FT, 8.4018 * M2FT, 0.0));
                wall3 = Wall.Create(doc, line3, wallType100.Id, level2.Id, wallHeightFt, 0.0, false, false);
                wall3.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level3.Id);
                wall3.LookupParameter("Comments")?.Set("TANG_2_Wall_WC_Chase_X34.95");

                t.Commit();
            }

            // 7. Place Door D5 hosted on Wall 1
            FamilyInstance doorD5 = null;
            using (Transaction t = new Transaction(doc, "Place Door D5"))
            {
                var prep = new Tang2WarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                var pt = new XYZ(34.5965 * M2FT, 8.9018 * M2FT, 0.0);
                doorD5 = doc.Create.NewFamilyInstance(pt, symD5, wall1, level2, StructuralType.NonStructural);
                doorD5.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(0.0);
                doorD5.LookupParameter("Mark")?.Set("D5");

                // Ensure door faces into the room (X > 34.60)
                if (doorD5.FacingOrientation.X < 0)
                {
                    doorD5.flipFacing();
                }

                // Ensure hinge is at bottom (Y = 8.50)
                // In Revit, HandOrientation points towards the opening swing direction
                t.Commit();
            }

            // 8. Add Text Note D5 in View MẶT BẰNG TẦNG 2
            ViewPlan planTang2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
            if (planTang2 != null)
            {
                var allTextTypes = new FilteredElementCollector(doc).OfClass(typeof(TextNoteType)).Cast<TextNoteType>().ToList();
                var textType = allTextTypes.FirstOrDefault(t => t.Name == "2.5mm Arial") ?? allTextTypes.First();

                using (Transaction t = new Transaction(doc, "Add D5 TextNote"))
                {
                    t.Start();
                    try
                    {
                        var ptText = new XYZ(34.7975 * M2FT, 8.8784 * M2FT, 0.0);
                        TextNoteOptions opt = new TextNoteOptions
                        {
                            HorizontalAlignment = HorizontalTextAlignment.Center,
                            TypeId = textType.Id
                        };
                        TextNote.Create(doc, planTang2.Id, ptText, "D5", opt);
                    }
                    catch { }
                    t.Commit();
                }
            }

            // 9. Export Close-up View of WC area and full plan
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string wcImgPath = Path.Combine(folder, "wc_tang2_verified.png");
            string planImgPath = Path.Combine(folder, "plan_tang2_updated.png");

            if (planTang2 != null)
            {
                uidoc.ActiveView = planTang2;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang2.Id);

                // Zoom close-up to WC
                uiview?.ZoomAndCenterRectangle(new XYZ(32.0 * M2FT, 6.8 * M2FT, 0.0), new XYZ(37.5 * M2FT, 11.5 * M2FT, 0.0));

                try
                {
                    if (File.Exists(wcImgPath)) File.Delete(wcImgPath);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = wcImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2500
                    };
                    doc.ExportImage(expOpt);
                }
                catch { }

                // Zoom to fit full building
                uiview?.ZoomToFit();
                try
                {
                    if (File.Exists(planImgPath)) File.Delete(planImgPath);
                    var expOpt2 = new ImageExportOptions
                    {
                        FilePath = planImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3800
                    };
                    doc.ExportImage(expOpt2);
                }
                catch { }
            }

            return new
            {
                success = true,
                wall1_id = wall1?.Id.Value,
                wall2_id = wall2?.Id.Value,
                wall3_id = wall3?.Id.Value,
                doorD5_id = doorD5?.Id.Value,
                wcImgPath,
                planImgPath
            };
        }
    }
}
