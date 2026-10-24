using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateNineWalls
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            // 1. Get 200mm wall type
            var wallType200 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach200_xay moi" || w.Name == "gach200" || w.Name == "Tường 200");

            if (wallType200 == null)
            {
                return new { error = "Wall type gach200_xay moi not found" };
            }

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));

            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Remove existing Wall 7 (Wall_200_Vertical ID 2360872) if present to avoid duplication
            using (var tx = new Transaction(doc, "Clean Prior Vertical Wall 7"))
            {
                tx.Start();
                var priorV7 = doc.GetElement(new ElementId(2360872));
                if (priorV7 != null)
                {
                    doc.Delete(priorV7.Id);
                }
                tx.Commit();
            }

            // 4. The 9 parallel vertical walls definitions
            // X coordinates and Y spans in Revit meters:
            var wallsDef = new List<(string name, double x, double y1, double y2)>
            {
                ("Wall_200_V1_X4.35",   4.3500,  7.6991, 14.9991),
                ("Wall_200_V2_X8.05",   8.0500,  7.6991, 14.9991),
                ("Wall_200_V3_X15.25", 15.2500,  7.7000, 13.3000),
                ("Wall_200_V4_X18.85", 18.8500,  7.6991, 13.2000),
                ("Wall_200_V5_X21.45", 21.4500,  7.9000, 13.2000),
                ("Wall_200_V6_X24.05", 24.0500,  7.9000, 13.2000),
                ("Wall_200_V7_X26.75", 26.7500,  7.9000, 13.2000),
                ("Wall_200_V8_X29.65", 29.6500,  7.9009, 14.8000),
                ("Wall_200_V9_X33.35", 33.3500,  7.9009, 14.8000)
            };

            var createdWalls = new List<object>();
            var createdIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create 9 Parallel Walls 200"))
            {
                tx.Start();
                double heightFt = 3.6 * M2FT;

                foreach (var wdef in wallsDef)
                {
                    var p1 = new XYZ(wdef.x * M2FT, wdef.y1 * M2FT, 0.0);
                    var p2 = new XYZ(wdef.x * M2FT, wdef.y2 * M2FT, 0.0);
                    var line = Line.CreateBound(p1, p2);

                    Wall wall = Wall.Create(doc, line, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    if (lvlTang2 != null)
                    {
                        var topParam = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                        if (topParam != null && !topParam.IsReadOnly)
                        {
                            topParam.Set(lvlTang2.Id);
                        }
                    }

                    createdIds.Add(wall.Id);
                    createdWalls.Add(new
                    {
                        name = wdef.name,
                        id = wall.Id.Value,
                        xM = wdef.x,
                        yStartM = wdef.y1,
                        yEndM = wdef.y2,
                        lengthM = (wdef.y2 - wdef.y1)
                    });
                }

                tx.Commit();
            }

            // 5. Select all 9 walls and show them in active view
            try
            {
                var viewTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

                if (viewTang1 != null)
                {
                    uidoc.ActiveView = viewTang1;
                }
                uidoc.Selection.SetElementIds(createdIds);
                uidoc.ShowElements(createdIds);
            }
            catch { }

            return new
            {
                success = true,
                wallType = wallType200.Name,
                totalCreated = createdWalls.Count,
                walls = createdWalls
            };
        }
    }
}
