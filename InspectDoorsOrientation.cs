using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorsOrientation
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            long[] ids = new long[] { 2360910, 2368986, 2369731, 2369959, 2370737 };
            var list = new List<object>();

            foreach (var id in ids)
            {
                var d = doc.GetElement(new ElementId(id)) as FamilyInstance;
                if (d == null) continue;

                var lp = d.Location as LocationPoint;
                var facing = d.FacingOrientation;
                var hand = d.HandOrientation;

                list.Add(new
                {
                    id = d.Id.Value,
                    level = doc.GetElement(d.LevelId)?.Name,
                    family = d.Symbol.FamilyName,
                    type = d.Symbol.Name,
                    x = lp != null ? Math.Round(lp.Point.X * FT_TO_MM, 1) : 0,
                    y = lp != null ? Math.Round(lp.Point.Y * FT_TO_MM, 1) : 0,
                    z = lp != null ? Math.Round(lp.Point.Z * FT_TO_MM, 1) : 0,
                    facingFlipped = d.FacingFlipped,
                    handFlipped = d.HandFlipped,
                    canFlipFacing = d.CanFlipFacing,
                    canFlipHand = d.CanFlipHand,
                    facingDir = facing != null ? $"({facing.X:F2}, {facing.Y:F2}, {facing.Z:F2})" : "",
                    handDir = hand != null ? $"({hand.X:F2}, {hand.Y:F2}, {hand.Z:F2})" : "",
                    hostWallId = d.Host?.Id.Value,
                    mark = d.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString()
                });
            }

            return new { doors = list };
        }
    }
}
