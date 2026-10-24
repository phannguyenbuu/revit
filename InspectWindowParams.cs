using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowParams
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2413190L)) as FamilyInstance;
            if (win == null) return new { error = "Window 2413190 not found" };

            var lp = win.Location as LocationPoint;
            var pt = lp?.Point;
            var sillHeight = win.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.AsDouble();
            var facing = win.FacingOrientation;
            var hand = win.HandOrientation;

            var host = win.Host as Wall;

            return new
            {
                success = true,
                pt = pt != null ? new { x = pt.X * FT_TO_MM, y = pt.Y * FT_TO_MM, z = pt.Z * FT_TO_MM } : null,
                facing = new { x = facing.X, y = facing.Y, z = facing.Z },
                hand = new { x = hand.X, y = hand.Y, z = hand.Z },
                sillHeightMm = sillHeight.HasValue ? Math.Round(sillHeight.Value * FT_TO_MM, 1) : -1,
                hostId = host?.Id.Value,
                hostName = host?.Name,
                isFlipped = win.FacingFlipped,
                handFlipped = win.HandFlipped
            };
        }
    }
}
