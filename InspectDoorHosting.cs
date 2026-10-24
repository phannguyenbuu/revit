using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorHosting
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var door = doc.GetElement(new ElementId(2362081L)) as FamilyInstance;
            if (door == null) return new { error = "Door 2362081 not found" };

            var bbox = door.get_BoundingBox(doc.ActiveView);

            return new
            {
                doorId = door.Id.Value,
                hostId = door.Host?.Id.Value,
                symbol = door.Symbol.Name,
                family = door.Symbol.FamilyName,
                placementType = door.Symbol.Family.FamilyPlacementType.ToString(),
                bbox = bbox != null ? new
                {
                    min = new { x = bbox.Min.X * 0.3048, y = bbox.Min.Y * 0.3048, z = bbox.Min.Z * 0.3048 },
                    max = new { x = bbox.Max.X * 0.3048, y = bbox.Max.Y * 0.3048, z = bbox.Max.Z * 0.3048 }
                } : null
            };
        }
    }
}
