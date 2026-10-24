using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCuaThuyLucLinesAndSolids
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            // Find any placed instance or check symbol geometry
            var geom = sym.get_Geometry(new Options { DetailLevel = ViewDetailLevel.Fine });
            int curveCount = 0;
            int solidCount = 0;
            string details = "";

            if (geom != null)
            {
                foreach (var g in geom)
                {
                    if (g is Solid s && s.Volume > 0)
                    {
                        solidCount++;
                        var bb = s.GetBoundingBox();
                        details += $"Solid Vol={s.Volume:F3} BBox=[({bb.Min.X*304.8:F0},{bb.Min.Y*304.8:F0},{bb.Min.Z*304.8:F0}) to ({bb.Max.X*304.8:F0},{bb.Max.Y*304.8:F0},{bb.Max.Z*304.8:F0})]; ";
                    }
                    else if (g is Curve c)
                    {
                        curveCount++;
                    }
                }
            }

            return new
            {
                symName = sym.Name,
                solidCount = solidCount,
                curveCount = curveCount,
                details = details
            };
        }
    }
}
