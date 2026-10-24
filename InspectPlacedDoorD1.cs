using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectPlacedDoorD1
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var door = doc.GetElement(new ElementId(2362082L)) as FamilyInstance;
            if (door == null) return new { error = "Door 2362082 not found" };

            var geom = door.get_Geometry(new Options { DetailLevel = ViewDetailLevel.Fine });
            int solidCount = 0;
            if (geom != null)
            {
                foreach (var gobj in geom)
                {
                    if (gobj is Solid s && s.Volume > 0) solidCount++;
                    else if (gobj is GeometryInstance gi)
                    {
                        var instGeom = gi.GetInstanceGeometry();
                        if (instGeom != null)
                        {
                            foreach (var ig in instGeom)
                            {
                                if (ig is Solid isold && isold.Volume > 0) solidCount++;
                            }
                        }
                    }
                }
            }

            return new
            {
                doorId = door.Id.Value,
                loc = door.Location is LocationPoint lp ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null,
                solidCount = solidCount
            };
        }
    }
}
