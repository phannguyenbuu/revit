using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateRaisedPlatformAndDividerWall
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Levels
            var levels = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().ToList();
            var level1 = levels.FirstOrDefault(l => l.Name.Contains("1"));
            var level2 = levels.FirstOrDefault(l => l.Name.Contains("2"));
            if (level1 == null) return new { error = "Level 1 not found" };

            // 2. WallType 100mm
            var wallTypes = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().ToList();
            var wallType100 = wallTypes.FirstOrDefault(wt => wt.Name == "gach100_xay moi")
                           ?? wallTypes.FirstOrDefault(wt => Math.Abs(wt.Width * 304.8 - 100) < 15);
            if (wallType100 == null) return new { error = "WallType 100mm not found" };

            // 3. FloorType 200mm
            var floorTypes = new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().ToList();
            var floorTypeWc = floorTypes.FirstOrDefault(ft => ft.Name == "NỀN WC")
                           ?? floorTypes.FirstOrDefault(ft => Math.Abs((ft.get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM)?.AsDouble() ?? 0) * 304.8 - 200) < 10)
                           ?? floorTypes.FirstOrDefault();
            if (floorTypeWc == null) return new { error = "FloorType not found" };

            Wall createdWall = null;
            Floor createdFloor = null;
            var selectIds = new List<ElementId>();

            using (var t = new Transaction(doc, "Create Divider Wall and Raised Platform"))
            {
                t.Start();

                // 4. Create Divider Wall: X = 21450, Y from 7800 to 13200
                XYZ wp0 = new XYZ(21450.0 / 304.8, 7800.0 / 304.8, 0.0);
                XYZ wp1 = new XYZ(21450.0 / 304.8, 13200.0 / 304.8, 0.0);
                createdWall = Wall.Create(doc, Line.CreateBound(wp0, wp1), wallType100.Id, level1.Id, 3800.0 / 304.8, 0.0, false, false);
                if (level2 != null)
                {
                    createdWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(level2.Id);
                    createdWall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(-100.0 / 304.8);
                }
                selectIds.Add(createdWall.Id);

                // 5. Create Raised Platform (Sàn bệ xí cao 200)
                // Rectangle from CAD: [20400, 12100] to [22500, 13100]
                double x0 = 20400.0 / 304.8;
                double x1 = 22500.0 / 304.8;
                double y0 = 12100.0 / 304.8;
                double y1 = 13100.0 / 304.8;

                var loop = new CurveLoop();
                loop.Append(Line.CreateBound(new XYZ(x0, y0, 0), new XYZ(x1, y0, 0)));
                loop.Append(Line.CreateBound(new XYZ(x1, y0, 0), new XYZ(x1, y1, 0)));
                loop.Append(Line.CreateBound(new XYZ(x1, y1, 0), new XYZ(x0, y1, 0)));
                loop.Append(Line.CreateBound(new XYZ(x0, y1, 0), new XYZ(x0, y0, 0)));

                var curveLoops = new List<CurveLoop> { loop };
                createdFloor = Floor.Create(doc, curveLoops, floorTypeWc.Id, level1.Id);
                doc.Regenerate();

                // Set Height Offset From Level = 200 mm
                var offsetParam = createdFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                if (offsetParam != null && !offsetParam.IsReadOnly)
                {
                    offsetParam.Set(200.0 / 304.8);
                }
                selectIds.Add(createdFloor.Id);

                // 6. Elevate squat toilets to sit on the 200mm platform
                long[] squatIds = new long[] { 2405972, 2405973 };
                foreach (var sid in squatIds)
                {
                    var inst = doc.GetElement(new ElementId(sid)) as FamilyInstance;
                    if (inst != null)
                    {
                        var elevP = inst.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                                 ?? inst.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM);
                        if (elevP != null && !elevP.IsReadOnly)
                        {
                            elevP.Set(200.0 / 304.8);
                        }
                    }
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
                wall = new
                {
                    id = createdWall?.Id.Value,
                    type = wallType100.Name,
                    curve = "[21450, 7800] -> [21450, 13200]",
                    lengthMm = 5400
                },
                floor = new
                {
                    id = createdFloor?.Id.Value,
                    type = floorTypeWc.Name,
                    thicknessMm = 200,
                    heightOffsetMm = 200,
                    bounds = "[20400, 12100] to [22500, 13100]",
                    widthMm = 2100,
                    depthMm = 1000
                }
            };
        }
    }
}
