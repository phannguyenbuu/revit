import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

script = """
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectEndWalls
    {
        private const double FT2M = 0.3048;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var walls = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Walls)
                .WhereElementIsNotElementType()
                .Cast<Wall>()
                .Select(w => {
                    var lc = w.Location as LocationCurve;
                    if (lc == null) return null;
                    var c = lc.Curve;
                    var p0 = c.GetEndPoint(0) * FT2M * 1000;
                    var p1 = c.GetEndPoint(1) * FT2M * 1000;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        p0x = Math.Round(p0.X, 1),
                        p0y = Math.Round(p0.Y, 1),
                        p1x = Math.Round(p1.X, 1),
                        p1y = Math.Round(p1.Y, 1)
                    };
                })
                .Where(w => w != null && (w.p0x < 1000 || w.p1x < 1000 || w.p0x > 36000 || w.p1x > 36000))
                .Take(20)
                .ToList();

            return new { walls };
        }
    }
}
"""

print("End walls script ready")
