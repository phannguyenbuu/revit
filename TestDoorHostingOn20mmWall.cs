using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestDoorHostingOn20mmWall
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var level = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("1"));
            var wallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType100 = wallTypes.FirstOrDefault(wt => wt.Name == "gach100_xay moi") ?? wallTypes.First();

            var doorSymbol = doc.GetElement(new ElementId(2070933)) as FamilySymbol;
            if (doorSymbol == null)
            {
                doorSymbol = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).OfClass(typeof(FamilySymbol)).Cast<FamilySymbol>().FirstOrDefault(d => d.Name.Contains("750") || d.Name.Contains("700") || d.Name.Contains("wc"));
            }

            using (var t = new Transaction(doc, "Test 20mm Wall and Door"))
            {
                t.Start();

                var wallType20 = wallTypes.FirstOrDefault(wt => wt.Name == "Vach_Ngan_Ve_Sinh_20mm");
                if (wallType20 == null)
                {
                    wallType20 = wallType100.Duplicate("Vach_Ngan_Ve_Sinh_20mm") as WallType;
                    var cs = wallType20.GetCompoundStructure();
                    var layer = cs.GetLayers().First();
                    layer.Width = 20.0 / 304.8;
                    cs.SetLayers(new List<CompoundStructureLayer> { layer });
                    wallType20.SetCompoundStructure(cs);
                }

                // Create test wall
                XYZ p0 = new XYZ(0, 0, 0);
                XYZ p1 = new XYZ(0, 3000.0 / 304.8, 0);
                var testWall = Wall.Create(doc, Line.CreateBound(p0, p1), wallType20.Id, level.Id, 2200.0 / 304.8, 0, false, false);
                doc.Regenerate();

                if (!doorSymbol.IsActive) doorSymbol.Activate();

                XYZ doorPt = new XYZ(0, 1500.0 / 304.8, 0);
                var doorInst = doc.Create.NewFamilyInstance(doorPt, doorSymbol, testWall, level, StructuralType.NonStructural);
                doc.Regenerate();

                bool doorSuccess = doorInst != null;
                long doorId = doorInst?.Id.Value ?? 0;

                // Roll back test
                t.RollBack();

                return new {
                    success = doorSuccess,
                    doorId = doorId,
                    symbolUsed = doorSymbol?.Name,
                    familyUsed = doorSymbol?.FamilyName
                };
            }
        }
    }
}
