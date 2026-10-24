using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestWallAndDoorRefs
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var dimType = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .FirstOrDefault(dt => dt.Name == "Linear Dimension Style")
                ?? new FilteredElementCollector(doc).OfClass(typeof(DimensionType)).Cast<DimensionType>().First();

            try
            {
                // Test 1: Wall Side Faces
                var walls = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Take(5)
                    .ToList();

                var wallFaceResults = new List<object>();
                foreach (var w in walls)
                {
                    var extFaces = HostObjectUtils.GetSideFaces(w, ShellLayerType.Exterior);
                    var intFaces = HostObjectUtils.GetSideFaces(w, ShellLayerType.Interior);
                    wallFaceResults.Add(new {
                        id = w.Id.Value,
                        name = w.Name,
                        extCount = extFaces.Count,
                        intCount = intFaces.Count
                    });
                }

                // Test 2: FamilyInstance References (Door / Window)
                var door = new FilteredElementCollector(doc, view.Id)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .Cast<FamilyInstance>()
                    .FirstOrDefault();

                var doorRefTypes = new List<string>();
                if (door != null)
                {
                    foreach (FamilyInstanceReferenceType rt in Enum.GetValues(typeof(FamilyInstanceReferenceType)))
                    {
                        var refs = door.GetReferences(rt);
                        if (refs != null && refs.Count > 0)
                        {
                            doorRefTypes.Add($"{rt}: {refs.Count}");
                        }
                    }
                }

                // Test 3: Can we dim between Grid 1 and Exterior face of a wall?
                long testDimId = 0;
                var g1 = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().FirstOrDefault(g => g.Name == "1");
                var southWall = new FilteredElementCollector(doc, view.Id).OfClass(typeof(Wall)).Cast<Wall>().FirstOrDefault(w => w.Name.Contains("gach200"));
                if (g1 != null && southWall != null)
                {
                    var extFaces = HostObjectUtils.GetSideFaces(southWall, ShellLayerType.Exterior);
                    if (extFaces.Count > 0)
                    {
                        using (var tx = new Transaction(doc, "Test Wall Dim"))
                        {
                            tx.Start();
                            var refArr = new ReferenceArray();
                            refArr.Append(new Reference(g1));
                            refArr.Append(extFaces[0]);

                            var line = Line.CreateBound(
                                new XYZ(0, -1500.0 * MM_TO_FT, 0),
                                new XYZ(5000.0 * MM_TO_FT, -1500.0 * MM_TO_FT, 0)
                            );
                            try
                            {
                                var d = doc.Create.NewDimension(view, line, refArr, dimType);
                                if (d != null) testDimId = d.Id.Value;
                            }
                            catch (Exception dex)
                            {
                                return new { wallFaceResults, doorRefTypes, dimError = dex.Message };
                            }
                            tx.RollBack();
                        }
                    }
                }

                return new {
                    wallFaceResults,
                    doorRefTypes,
                    testDimId
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
