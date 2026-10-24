using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorZRange
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var door = doc.GetElement(new ElementId(2362082L)) as FamilyInstance;
            if (door == null) return new { error = "Door 2362082 not found" };

            var bbox = door.get_BoundingBox(null);
            var view = doc.ActiveView as ViewPlan;
            var vr = view?.GetViewRange();

            return new
            {
                doorBbox = bbox != null ? new
                {
                    minZ = bbox.Min.Z * 0.3048,
                    maxZ = bbox.Max.Z * 0.3048,
                    minX = bbox.Min.X * 0.3048,
                    maxX = bbox.Max.X * 0.3048,
                    minY = bbox.Min.Y * 0.3048,
                    maxY = bbox.Max.Y * 0.3048
                } : null,
                viewRange = vr != null ? new
                {
                    cutPlaneOffset = vr.GetOffset(PlanViewPlane.CutPlane) * 0.3048,
                    bottomOffset = vr.GetOffset(PlanViewPlane.BottomClipPlane) * 0.3048,
                    topOffset = vr.GetOffset(PlanViewPlane.TopClipPlane) * 0.3048
                } : null
            };
        }
    }
}
