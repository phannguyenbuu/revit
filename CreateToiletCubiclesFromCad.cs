using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class CubicleWarningSwallower : IFailuresPreprocessor
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
                else
                {
                    try { failuresAccessor.ResolveFailure(msg); } catch {}
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class CreateToiletCubiclesFromCad
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Level 1
            var level = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("1"));
            if (level == null) return new { error = "Level 1 not found" };

            // 2. WallType 20mm
            var wallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType20 = wallTypes.FirstOrDefault(wt => wt.Name == "Vach_Ngan_Ve_Sinh_20mm");
            var wallTypeBase = wallTypes.FirstOrDefault(wt => wt.Name == "gach100_xay moi") ?? wallTypes.First();

            // 3. Toilet Symbol (xi bet 2 - 540 x 360mm)
            var toiletSymbol = doc.GetElement(new ElementId((long)820673)) as FamilySymbol;
            if (toiletSymbol == null)
            {
                toiletSymbol = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_PlumbingFixtures)
                    .OfClass(typeof(FamilySymbol))
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(fs => fs.FamilyName == "xi bet 2" || fs.Name.Contains("540 x 360"));
            }
            if (toiletSymbol == null) return new { error = "Toilet symbol 820673 (xi bet 2) not found" };

            // 4. Door Symbol: use cua nhom wc duplicated to 750x2000
            var baseDoorSymbol = doc.GetElement(new ElementId((long)112212)) as FamilySymbol;
            if (baseDoorSymbol == null)
            {
                baseDoorSymbol = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .OfClass(typeof(FamilySymbol))
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(fs => fs.FamilyName == "cua nhom wc");
            }
            if (baseDoorSymbol == null) return new { error = "Base door symbol (cua nhom wc) not found" };

            var createdWalls = new List<object>();
            var createdDoors = new List<object>();
            var createdToilets = new List<object>();
            var selectIds = new List<ElementId>();

            using (var t = new Transaction(doc, "Create Toilet Cubicles and Doors from CAD"))
            {
                var swallower = new CubicleWarningSwallower();
                var options = t.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(swallower);
                t.SetFailureHandlingOptions(options);

                t.Start();

                // Setup 20mm Wall Type
                if (wallType20 == null)
                {
                    wallType20 = wallTypeBase.Duplicate("Vach_Ngan_Ve_Sinh_20mm") as WallType;
                    var cs = wallType20.GetCompoundStructure();
                    var layer = cs.GetLayers().First();
                    layer.Width = 20.0 / 304.8;
                    cs.SetLayers(new List<CompoundStructureLayer> { layer });
                    wallType20.SetCompoundStructure(cs);
                }

                // Setup 750x2000 Door Type
                var doorSymbol = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .OfClass(typeof(FamilySymbol))
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(fs => fs.FamilyName == "cua nhom wc" && fs.Name == "Đ2_750x2000");

                if (doorSymbol == null)
                {
                    doorSymbol = baseDoorSymbol.Duplicate("Đ2_750x2000") as FamilySymbol;
                    var widthP = doorSymbol.get_Parameter(BuiltInParameter.DOOR_WIDTH);
                    if (widthP != null && !widthP.IsReadOnly) widthP.Set(750.0 / 304.8);
                    var heightP = doorSymbol.get_Parameter(BuiltInParameter.DOOR_HEIGHT);
                    if (heightP != null && !heightP.IsReadOnly) heightP.Set(2000.0 / 304.8);
                }

                if (!toiletSymbol.IsActive) toiletSymbol.Activate();
                if (!doorSymbol.IsActive) doorSymbol.Activate();
                doc.Regenerate();

                double wallHeightFt = 2000.0 / 304.8;

                // --- 1. WALL 1 (Nam / South): X from 35260 to 37050, Y = 10912.1 ---
                XYZ w1_p0 = new XYZ(35260.0 / 304.8, 10912.1 / 304.8, 0.0);
                XYZ w1_p1 = new XYZ(37050.0 / 304.8, 10912.1 / 304.8, 0.0);
                var wall1 = Wall.Create(doc, Line.CreateBound(w1_p0, w1_p1), wallType20.Id, level.Id, wallHeightFt, 0.0, false, false);
                selectIds.Add(wall1.Id);
                createdWalls.Add(new { id = wall1.Id.Value, name = "South Wall", lengthMm = 1790.0 });

                // --- 2. WALL 2 (Giữa / Middle): X from 35260 to 37050, Y = 11992.4 ---
                XYZ w2_p0 = new XYZ(35260.0 / 304.8, 11992.4 / 304.8, 0.0);
                XYZ w2_p1 = new XYZ(37050.0 / 304.8, 11992.4 / 304.8, 0.0);
                var wall2 = Wall.Create(doc, Line.CreateBound(w2_p0, w2_p1), wallType20.Id, level.Id, wallHeightFt, 0.0, false, false);
                selectIds.Add(wall2.Id);
                createdWalls.Add(new { id = wall2.Id.Value, name = "Middle Wall", lengthMm = 1790.0 });

                // --- 3. WALL 3 (Trước / Front): X = 35260, Y from 10912.1 to 13102.6 ---
                XYZ w3_p0 = new XYZ(35260.0 / 304.8, 10912.1 / 304.8, 0.0);
                XYZ w3_p1 = new XYZ(35260.0 / 304.8, 13102.6 / 304.8, 0.0);
                var wall3 = Wall.Create(doc, Line.CreateBound(w3_p0, w3_p1), wallType20.Id, level.Id, wallHeightFt, 0.0, false, false);
                selectIds.Add(wall3.Id);
                createdWalls.Add(new { id = wall3.Id.Value, name = "Front Wall", lengthMm = 2190.5 });

                doc.Regenerate();

                // --- 4. DOOR 1 (Buồng Nam): hosted on Wall 3, center at Y = 11527.2 ---
                XYZ d1_pt = new XYZ(35260.0 / 304.8, 11527.2 / 304.8, 0.0);
                var door1 = doc.Create.NewFamilyInstance(d1_pt, doorSymbol, wall3, level, StructuralType.NonStructural);
                doc.Regenerate();

                // Ensure door1 faces INWARD into stall (+X)
                if (door1.FacingOrientation.X < 0)
                {
                    door1.flipFacing();
                    doc.Regenerate();
                }
                // Check hand orientation (swing towards South: -Y)
                if (door1.HandOrientation.Y > 0)
                {
                    door1.flipHand();
                    doc.Regenerate();
                }
                selectIds.Add(door1.Id);
                createdDoors.Add(new { id = door1.Id.Value, stall = "South", ptMm = "[35260, 11527.2]", widthMm = 750 });

                // --- 5. DOOR 2 (Buồng Bắc): hosted on Wall 3, center at Y = 12577.5 ---
                XYZ d2_pt = new XYZ(35260.0 / 304.8, 12577.5 / 304.8, 0.0);
                var door2 = doc.Create.NewFamilyInstance(d2_pt, doorSymbol, wall3, level, StructuralType.NonStructural);
                doc.Regenerate();

                // Ensure door2 faces INWARD into stall (+X)
                if (door2.FacingOrientation.X < 0)
                {
                    door2.flipFacing();
                    doc.Regenerate();
                }
                // Check hand orientation (swing towards Middle: -Y)
                if (door2.HandOrientation.Y > 0)
                {
                    door2.flipHand();
                    doc.Regenerate();
                }
                selectIds.Add(door2.Id);
                createdDoors.Add(new { id = door2.Id.Value, stall = "North", ptMm = "[35260, 12577.5]", widthMm = 750 });

                // --- 6. TOILET 1 (Buồng Nam): X = 37050, Y = 11327.3, Rot = 270 deg ---
                XYZ t1_pt = new XYZ(37050.0 / 304.8, 11327.3 / 304.8, 0.0);
                var toilet1 = doc.Create.NewFamilyInstance(t1_pt, toiletSymbol, level, StructuralType.NonStructural);
                doc.Regenerate();
                var axis1 = Line.CreateBound(t1_pt, t1_pt + XYZ.BasisZ);
                ElementTransformUtils.RotateElement(doc, toilet1.Id, axis1, 270.0 * Math.PI / 180.0);
                selectIds.Add(toilet1.Id);
                createdToilets.Add(new { id = toilet1.Id.Value, stall = "South", ptMm = "[37050, 11327.3]", rotDeg = 270.0 });

                // --- 7. TOILET 2 (Buồng Bắc): X = 37050, Y = 12602.5, Rot = 270 deg ---
                XYZ t2_pt = new XYZ(37050.0 / 304.8, 12602.5 / 304.8, 0.0);
                var toilet2 = doc.Create.NewFamilyInstance(t2_pt, toiletSymbol, level, StructuralType.NonStructural);
                doc.Regenerate();
                var axis2 = Line.CreateBound(t2_pt, t2_pt + XYZ.BasisZ);
                ElementTransformUtils.RotateElement(doc, toilet2.Id, axis2, 270.0 * Math.PI / 180.0);
                selectIds.Add(toilet2.Id);
                createdToilets.Add(new { id = toilet2.Id.Value, stall = "North", ptMm = "[37050, 12602.5]", rotDeg = 270.0 });

                t.Commit();
            }

            if (selectIds.Count > 0)
            {
                try { uidoc.Selection.SetElementIds(selectIds); } catch { }
            }

            return new
            {
                success = true,
                walls = createdWalls,
                doors = createdDoors,
                toilets = createdToilets,
                totalCreated = selectIds.Count
            };
        }

        public static object ExportZoom(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            long[] ids = new long[] { 2406169, 2406170, 2406171, 2406172, 2406175, 2406176, 2406177 };
            var elemIds = ids.Select(id => new ElementId(id)).ToList();

            double minX = (34500.0) / 304.8;
            double maxX = (37600.0) / 304.8;
            double minY = (10500.0) / 304.8;
            double maxY = (13500.0) / 304.8;

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
            if (uiview != null)
            {
                XYZ p1 = new XYZ(minX, minY, 0);
                XYZ p2 = new XYZ(maxX, maxY, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }

            try
            {
                uidoc.Selection.SetElementIds(elemIds);
            }
            catch { }

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wc_nam_cubicles_zoom.png";

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                PixelSize = 2048,
                ShadowViewsFileType = ImageFileType.PNG,
                ZoomType = ZoomFitType.FitToPage
            };

            doc.ExportImage(opt);

            string actualPath = outPath;
            if (!File.Exists(actualPath))
            {
                string dir = Path.GetDirectoryName(outPath)!;
                string baseName = Path.GetFileNameWithoutExtension(outPath);
                var files = Directory.GetFiles(dir, baseName + "*.png");
                if (files.Length > 0) actualPath = files[0];
            }

            return new { success = true, path = actualPath };
        }
    }
}
