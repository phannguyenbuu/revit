using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class XiXomLoadOption : IFamilyLoadOptions
    {
        public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
        {
            overwriteParameterValues = true;
            return true;
        }
        public bool OnSharedFamilyFound(Family sharedFamily, bool familyInUse, out FamilySource source, out bool overwriteParameterValues)
        {
            source = FamilySource.Family;
            overwriteParameterValues = true;
            return true;
        }
    }

    public static class CreateWallsAndSquatToilets
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Find Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var level1 = levels.FirstOrDefault(l => l.Name.Contains("1"));
            var level2 = levels.FirstOrDefault(l => l.Name.Contains("2"));

            if (level1 == null) return new { error = "Level 1 not found" };

            // 2. Find WallType: 100mm
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();

            var wallType100 = wallTypes.FirstOrDefault(wt => wt.Name == "gach100_xay moi")
                           ?? wallTypes.FirstOrDefault(wt => Math.Abs(wt.Width * 304.8 - 100) < 15);

            if (wallType100 == null) return new { error = "WallType 100mm not found" };

            // 3. Load or Get Xi_Xom family
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Xi_Xom.rfa";
            FamilySymbol xixomSymbol = null;

            using (var tLoad = new Transaction(doc, "Load Xi_Xom Family"))
            {
                tLoad.Start();

                var fam = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name == "Xi_Xom");

                if (fam == null && File.Exists(rfaPath))
                {
                    Family loadedFam = null;
                    doc.LoadFamily(rfaPath, new XiXomLoadOption(), out loadedFam);
                    fam = loadedFam;
                }

                if (fam != null)
                {
                    var symbolId = fam.GetFamilySymbolIds().FirstOrDefault();
                    if (symbolId != null)
                    {
                        xixomSymbol = doc.GetElement(symbolId) as FamilySymbol;
                        if (xixomSymbol != null && !xixomSymbol.IsActive)
                        {
                            xixomSymbol.Activate();
                        }
                    }
                }

                tLoad.Commit();
            }

            var createdWalls = new List<object>();
            var createdToilets = new List<object>();
            var selectIds = new List<ElementId>();

            // 4. Create Walls and Squat Toilets
            using (var t = new Transaction(doc, "Create Cubicle Walls and Squat Toilets"))
            {
                t.Start();

                // Wall 1 (Right cubicle front partition): X from 21500 to 23000, Y = 12050
                XYZ w1_p0 = new XYZ(21500.0 / 304.8, 12050.0 / 304.8, 0.0);
                XYZ w1_p1 = new XYZ(23000.0 / 304.8, 12050.0 / 304.8, 0.0);
                Line line1 = Line.CreateBound(w1_p0, w1_p1);
                var wall1 = Wall.Create(doc, line1, wallType100.Id, level1.Id, 3800.0 / 304.8, 0.0, false, false);
                if (level2 != null)
                {
                    wall1.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level2.Id);
                    wall1.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(-100.0 / 304.8);
                }
                createdWalls.Add(new { id = wall1.Id.Value, length = 1500, p0 = "[21500, 12050]", p1 = "[23000, 12050]" });
                selectIds.Add(wall1.Id);

                // Wall 2 (Left cubicle front partition): X from 19900 to 21400, Y = 12050
                XYZ w2_p0 = new XYZ(19900.0 / 304.8, 12050.0 / 304.8, 0.0);
                XYZ w2_p1 = new XYZ(21400.0 / 304.8, 12050.0 / 304.8, 0.0);
                Line line2 = Line.CreateBound(w2_p0, w2_p1);
                var wall2 = Wall.Create(doc, line2, wallType100.Id, level1.Id, 3800.0 / 304.8, 0.0, false, false);
                if (level2 != null)
                {
                    wall2.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level2.Id);
                    wall2.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(-100.0 / 304.8);
                }
                createdWalls.Add(new { id = wall2.Id.Value, length = 1500, p0 = "[19900, 12050]", p1 = "[21400, 12050]" });
                selectIds.Add(wall2.Id);

                // Place Squat Toilets if symbol available
                if (xixomSymbol != null)
                {
                    // Toilet 1 (Right cubicle, handle 44C67A): pt = [21700, 12600], rot = 270 deg (facing East +X)
                    XYZ t1_pt = new XYZ(21700.0 / 304.8, 12600.0 / 304.8, 0.0);
                    var inst1 = doc.Create.NewFamilyInstance(t1_pt, xixomSymbol, level1, StructuralType.NonStructural);
                    doc.Regenerate();
                    var axis1 = Line.CreateBound(t1_pt, t1_pt + XYZ.BasisZ);
                    ElementTransformUtils.RotateElement(doc, inst1.Id, axis1, 270.0 * Math.PI / 180.0);
                    createdToilets.Add(new { id = inst1.Id.Value, pt = "[21700, 12600]", rotDeg = 270.0, cubicle = "Right" });
                    selectIds.Add(inst1.Id);

                    // Toilet 2 (Left cubicle, handle 44C680): pt = [21200, 12600], rot = 90 deg (facing West -X)
                    XYZ t2_pt = new XYZ(21200.0 / 304.8, 12600.0 / 304.8, 0.0);
                    var inst2 = doc.Create.NewFamilyInstance(t2_pt, xixomSymbol, level1, StructuralType.NonStructural);
                    doc.Regenerate();
                    var axis2 = Line.CreateBound(t2_pt, t2_pt + XYZ.BasisZ);
                    ElementTransformUtils.RotateElement(doc, inst2.Id, axis2, 90.0 * Math.PI / 180.0);
                    createdToilets.Add(new { id = inst2.Id.Value, pt = "[21200, 12600]", rotDeg = 90.0, cubicle = "Left" });
                    selectIds.Add(inst2.Id);
                }

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
                toilets = createdToilets
            };
        }
    }
}
