using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateTamCapArrow
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Find TextNoteType
            var textTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .Select(t => new { id = t.Id.Value, name = t.Name })
                .ToList();

            var textType = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .FirstOrDefault(t => t.Name.Contains("2.5") || t.Name.Contains("Arial"))
                ?? new FilteredElementCollector(doc).OfClass(typeof(TextNoteType)).Cast<TextNoteType>().First();

            var createdIds = new List<long>();

            using (var tx = new Transaction(doc, "Create Tam Cap Arrow"))
            {
                tx.Start();

                double yTim = 6600.0 * MM_TO_FT;
                double xStart = 39400.0 * MM_TO_FT; // Start on low step (right)
                double xEnd = 37500.0 * MM_TO_FT;   // End on high step (left)

                // 1. Shaft line
                var shaft = Line.CreateBound(new XYZ(xStart, yTim, 0), new XYZ(xEnd, yTim, 0));
                var cShaft = doc.Create.NewDetailCurve(view, shaft);
                createdIds.Add(cShaft.Id.Value);

                // 2. Start circle (R = 75mm)
                double rCircle = 75.0 * MM_TO_FT;
                var circleCenter = new XYZ(xStart, yTim, 0);
                // In Revit, a full circle must be 2 arcs
                var arc1 = Arc.Create(new XYZ(xStart - rCircle, yTim, 0), new XYZ(xStart + rCircle, yTim, 0), new XYZ(xStart, yTim + rCircle, 0));
                var arc2 = Arc.Create(new XYZ(xStart + rCircle, yTim, 0), new XYZ(xStart - rCircle, yTim, 0), new XYZ(xStart, yTim - rCircle, 0));
                var cArc1 = doc.Create.NewDetailCurve(view, arc1);
                var cArc2 = doc.Create.NewDetailCurve(view, arc2);
                createdIds.Add(cArc1.Id.Value);
                createdIds.Add(cArc2.Id.Value);

                // 3. Arrowhead pointing LEFT at xEnd
                // Top barb: from (xEnd, yTim) to (xEnd + 200mm, yTim + 100mm)
                double barbLenX = 220.0 * MM_TO_FT;
                double barbLenY = 90.0 * MM_TO_FT;
                var barbTop = Line.CreateBound(new XYZ(xEnd, yTim, 0), new XYZ(xEnd + barbLenX, yTim + barbLenY, 0));
                var barbBottom = Line.CreateBound(new XYZ(xEnd, yTim, 0), new XYZ(xEnd + barbLenX, yTim - barbLenY, 0));
                var cBarb1 = doc.Create.NewDetailCurve(view, barbTop);
                var cBarb2 = doc.Create.NewDetailCurve(view, barbBottom);
                createdIds.Add(cBarb1.Id.Value);
                createdIds.Add(cBarb2.Id.Value);

                // 4. TextNote "LÊN" above arrow shaft
                var textPt = new XYZ(38450.0 * MM_TO_FT, (6600.0 + 150.0) * MM_TO_FT, 0);
                var textOpt = new TextNoteOptions
                {
                    TypeId = textType.Id,
                    HorizontalAlignment = HorizontalTextAlignment.Center
                };
                var note = TextNote.Create(doc, view.Id, textPt, "LÊN", textOpt);
                if (note != null) createdIds.Add(note.Id.Value);

                tx.Commit();
            }

            return new {
                status = "Success",
                createdCount = createdIds.Count,
                createdIds,
                textTypeName = textType.Name,
                availableTextTypes = textTypes
            };
        }
    }
}
