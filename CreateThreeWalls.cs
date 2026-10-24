using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateThreeWalls
    {
        private const double M2FT = 3.2808398950131235; // 1 meter to feet
        private const double MM2FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            // 1. Get or create 200mm wall type
            WallType? wallType200 = null;
            using (var tx = new Transaction(doc, "Ensure 200mm Wall Type"))
            {
                tx.Start();
                wallType200 = new FilteredElementCollector(doc)
                    .OfClass(typeof(WallType))
                    .Cast<WallType>()
                    .FirstOrDefault(w => w.Name == "gach200_xay moi" || w.Name == "gach200" || w.Name == "Tường 200");

                if (wallType200 == null)
                {
                    var baseType = new FilteredElementCollector(doc)
                        .OfClass(typeof(WallType))
                        .Cast<WallType>()
                        .FirstOrDefault(w => w.Name == "gach250_xay moi" || w.Name == "gach250_xay cu")
                        ?? new FilteredElementCollector(doc)
                            .OfClass(typeof(WallType))
                            .Cast<WallType>()
                            .FirstOrDefault(w => w.Kind == WallKind.Basic);

                    if (baseType != null)
                    {
                        wallType200 = baseType.Duplicate("gach200_xay moi") as WallType;
                        if (wallType200 != null)
                        {
                            var cs = wallType200.GetCompoundStructure();
                            var layers = cs.GetLayers();
                            // If 3 layers (Finish1, Structure, Finish2)
                            if (layers.Count == 3)
                            {
                                layers[0].Width = 15.0 * MM2FT; // 15mm
                                layers[1].Width = 170.0 * MM2FT; // 170mm
                                layers[2].Width = 15.0 * MM2FT; // 15mm
                            }
                            else if (layers.Count > 0)
                            {
                                layers[0].Width = 200.0 * MM2FT;
                            }
                            cs.SetLayers(layers);
                            wallType200.SetCompoundStructure(cs);
                        }
                    }
                }
                tx.Commit();
            }

            if (wallType200 == null) return new { error = "Failed to create/find 200mm wall type" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));

            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Wall Centerlines in Revit coordinates (Meters)
            // Cad origin shift: X_rvt = X_cad + 132847.0, Y_rvt = Y_cad + 1400405.9
            // Entity 0 (Left Horiz): (-107059.5, -1387206.0) -> (-106097.0, -1387206.0) => (25.7875, 13.2000) to (26.7500, 13.2000)
            // Entity 1 (Right Horiz): (-106097.0, -1387206.0) -> (-105409.5, -1387206.0) => (26.7500, 13.2000) to (27.4375, 13.2000)
            // Entity 4 (Vertical): (-106097.0, -1392505.9) -> (-106097.0, -1387206.0) => (26.7500, 7.9000) to (26.7500, 13.2000)

            var wallDefs = new List<(string name, XYZ p1, XYZ p2)>
            {
                (
                    "Wall_200_Horiz_Left",
                    new XYZ(25.7875 * M2FT, 13.2000 * M2FT, 0.0),
                    new XYZ(26.7500 * M2FT, 13.2000 * M2FT, 0.0)
                ),
                (
                    "Wall_200_Horiz_Right",
                    new XYZ(26.7500 * M2FT, 13.2000 * M2FT, 0.0),
                    new XYZ(27.4375 * M2FT, 13.2000 * M2FT, 0.0)
                ),
                (
                    "Wall_200_Vertical",
                    new XYZ(26.7500 * M2FT, 7.9000 * M2FT, 0.0),
                    new XYZ(26.7500 * M2FT, 13.2000 * M2FT, 0.0)
                )
            };

            var createdWalls = new List<object>();

            using (var tx = new Transaction(doc, "Create 3 Wall 200 Instances"))
            {
                tx.Start();
                foreach (var wdef in wallDefs)
                {
                    var line = Line.CreateBound(wdef.p1, wdef.p2);
                    double heightFt = 3.6 * M2FT; // Default height to Tầng 2

                    Wall wall;
                    if (lvlTang2 != null)
                    {
                        wall = Wall.Create(doc, line, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                        // Set top constraint to Tầng 2
                        var topParam = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                        if (topParam != null && !topParam.IsReadOnly)
                        {
                            topParam.Set(lvlTang2.Id);
                        }
                    }
                    else
                    {
                        wall = Wall.Create(doc, line, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    }

                    createdWalls.Add(new
                    {
                        name = wdef.name,
                        wallId = wall.Id.Value,
                        lengthM = line.Length * 0.3048,
                        start = new { x = wdef.p1.X * 0.3048, y = wdef.p1.Y * 0.3048 },
                        end = new { x = wdef.p2.X * 0.3048, y = wdef.p2.Y * 0.3048 }
                    });
                }
                tx.Commit();
            }

            return new
            {
                success = true,
                wallType = wallType200.Name,
                createdWalls = createdWalls
            };
        }
    }
}
