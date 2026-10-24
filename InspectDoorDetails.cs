using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var ids = new long[] { 2360905, 2361259, 2361275, 2361460 };
            var list = ids.Select(id => {
                var el = doc.GetElement(new ElementId(id)) as FamilyInstance;
                if (el == null) return null;
                var pt = (el.Location as LocationPoint)?.Point;
                var rot = (el.Location as LocationPoint)?.Rotation;
                var hand = el.HandOrientation;
                var face = el.FacingOrientation;
                var host = el.Host;
                return new {
                    id = el.Id.Value,
                    sym = el.Symbol.Name,
                    fam = el.Symbol.FamilyName,
                    pt = pt != null ? new { x = pt.X * 304.8, y = pt.Y * 304.8, z = pt.Z * 304.8 } : null,
                    rot = rot,
                    hand = new { x = hand.X, y = hand.Y },
                    face = new { x = face.X, y = face.Y },
                    hostId = host?.Id.Value,
                    hostName = host?.Name
                };
            }).Where(x => x != null).ToList();

            return list;
        }
    }
}
