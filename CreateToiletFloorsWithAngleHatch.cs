using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateToiletFloorsWithAngleHatch
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No active document or view" };

            // 1. Get Level 1 (ID 311)
            var level1 = doc.GetElement(new ElementId(311)) as Level;
            if (level1 == null) return new { error = "Level 1 not found" };

            // 2. Get FloorType "NỀN WC" (ID 107061)
            var floorType = doc.GetElement(new ElementId(107061)) as FloorType;
            if (floorType == null)
            {
                floorType = new FilteredElementCollector(doc)
                    .OfClass(typeof(FloorType))
                    .Cast<FloorType>()
                    .FirstOrDefault(ft => ft.Name == "NỀN WC");
            }
            if (floorType == null) return new { error = "FloorType NỀN WC not found" };

            // 3. Ensure ANGLE fill pattern exists and is assigned to Material "WC"
            var modelAnglePattern = FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "ANGLE");
            var draftAnglePattern = FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Drafting, "ANGLE");

            using (var t = new Transaction(doc, "Ensure ANGLE pattern and material finish"))
            {
                t.Start();

                if (modelAnglePattern == null)
                {
                    double spacing = 250.0 / 304.8;
                    var fp = new FillPattern("ANGLE", FillPatternTarget.Model, FillPatternHostOrientation.ToHost, Math.PI / 4.0, spacing, spacing);
                    modelAnglePattern = FillPatternElement.Create(doc, fp);
                }

                if (draftAnglePattern == null)
                {
                    double draftSpacing = 2.5 / 304.8;
                    var fpDraft = new FillPattern("ANGLE", FillPatternTarget.Drafting, FillPatternHostOrientation.ToHost, Math.PI / 4.0, draftSpacing, draftSpacing);
                    draftAnglePattern = FillPatternElement.Create(doc, fpDraft);
                }

                // Assign to Material WC (ID 107066)
                var matWc = doc.GetElement(new ElementId(107066)) as Material;
                if (matWc != null && modelAnglePattern != null)
                {
                    matWc.SurfaceForegroundPatternId = modelAnglePattern.Id;
                    matWc.SurfaceForegroundPatternColor = new Color(128, 128, 128); // Clean soft grey hatch
                }

                t.Commit();
            }

            // 4. Coordinates of 4 floors from AutoCAD selection (in mm, will convert to ft)
            // Polyline 0: Buồng xí xổm (West)
            var poly0 = new List<(double x, double y)>
            {
                (19900.0, 12100.0),
                (23000.0, 12100.0),
                (23000.0, 13100.0),
                (19900.0, 13100.0)
            };

            // Polyline 1: WC NAM
            var poly1 = new List<(double x, double y)>
            {
                (33450.0, 13100.872),
                (37050.0, 13100.872),
                (37050.0, 9501.740),
                (33450.0, 9501.740)
            };

            // Polyline 2: WC NỮ
            var poly2 = new List<(double x, double y)>
            {
                (34650.0, 9401.740),
                (37050.0, 9401.740),
                (37050.0, 7902.610),
                (35000.0, 7902.610),
                (35000.0, 8451.740),
                (34650.0, 8451.740)
            };

            // Polyline 3: WC KHUYẾT TẬT
            var poly3 = new List<(double x, double y)>
            {
                (37050.0, 5300.872),
                (34650.0, 5300.872),
                (34650.0, 101.740),
                (37050.0, 101.740)
            };

            var floorPolys = new List<List<(double x, double y)>> { poly0, poly1, poly2, poly3 };
            var floorNames = new string[] { "Sàn Xí Xổm", "Sàn WC NAM", "Sàn WC NỮ", "Sàn WC Khuyết Tật" };

            var createdFloors = new List<object>();

            using (var t = new Transaction(doc, "Create Toilet Floors from CAD"))
            {
                t.Start();

                for (int pIdx = 0; pIdx < floorPolys.Count; pIdx++)
                {
                    var pts = floorPolys[pIdx];
                    var loop = new CurveLoop();

                    for (int i = 0; i < pts.Count; i++)
                    {
                        var p1 = new XYZ(pts[i].x / 304.8, pts[i].y / 304.8, 0);
                        var nextIdx = (i + 1) % pts.Count;
                        var p2 = new XYZ(pts[nextIdx].x / 304.8, pts[nextIdx].y / 304.8, 0);

                        loop.Append(Line.CreateBound(p1, p2));
                    }

                    var floor = Floor.Create(doc, new List<CurveLoop> { loop }, floorType.Id, level1.Id);

                    // Set height offset to -30 mm (-0.030 m)
                    var offsetParam = floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    if (offsetParam != null && !offsetParam.IsReadOnly)
                    {
                        offsetParam.Set(-30.0 / 304.8);
                    }

                    createdFloors.Add(new
                    {
                        id = floor.Id.Value,
                        name = floorNames[pIdx],
                        typeName = floorType.Name,
                        offsetMm = -30.0
                    });
                }

                // 5. Create threshold drop tags (TextNote "▼ -0.030") at door thresholds
                var textTypeId = new ElementId(361); // 2.5mm Arial
                var tagText = "▼ -0.030";

                var thresholdPoints = new List<(double x, double y, string desc)>
                {
                    (33950.0, 9450.0, "Ngạch cửa WC NAM"),
                    (34600.0, 8900.0, "Ngạch cửa WC NỮ"),
                    (35150.0, 3450.0, "Ngạch cửa WC Khuyết Tật"),
                    (20750.0, 7800.0, "Ngạch cửa Buồng Xí Xổm"),
                    (20750.0, 12050.0, "Ngạch cửa Vách Ngăn Xí Xổm")
                };

                var createdTags = new List<object>();

                foreach (var tp in thresholdPoints)
                {
                    var origin = new XYZ(tp.x / 304.8, tp.y / 304.8, 0);
                    var note = TextNote.Create(doc, view.Id, origin, tagText, textTypeId);
                    note.HorizontalAlignment = HorizontalTextAlignment.Center;

                    createdTags.Add(new
                    {
                        id = note.Id.Value,
                        desc = tp.desc,
                        x = tp.x,
                        y = tp.y,
                        text = tagText
                    });
                }

                t.Commit();

                return new
                {
                    status = "success",
                    floors = createdFloors,
                    tags = createdTags
                };
            }
        }
    }
}
