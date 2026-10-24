using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestMoveElement
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var doorId = new ElementId(2363712L);
            var door = doc?.GetElement(doorId);
            if (door == null) return new { error = "Door 2363712 not found" };

            string moveErr = null;
            string rotErr = null;

            using (var tx = new Transaction(doc, "Test Move"))
            {
                tx.Start();
                try
                {
                    var vec = new XYZ(0.550 * M2FT, 6.600 * M2FT, 0);
                    ElementTransformUtils.MoveElement(doc, doorId, vec);
                }
                catch (Exception ex)
                {
                    moveErr = ex.ToString();
                }

                try
                {
                    var pt = new XYZ(0.550 * M2FT, 6.600 * M2FT, 0);
                    var axis = Line.CreateBound(pt, pt + XYZ.BasisZ);
                    ElementTransformUtils.RotateElement(doc, doorId, axis, Math.PI / 2.0);
                }
                catch (Exception ex)
                {
                    rotErr = ex.ToString();
                }

                doc.Regenerate();
                tx.Commit();
            }

            var bb = door.get_BoundingBox(null);

            return new
            {
                moveErr,
                rotErr,
                bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048 } : null,
                bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048 } : null
            };
        }
    }
}
