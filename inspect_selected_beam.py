import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Inspect element 2381982
query_code = """
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSelectedElement
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            long selId = 2381982L;
            var el = doc.GetElement(new ElementId(selId));
            if (el == null) return new { error = "Element not found" };

            var fi = el as FamilyInstance;
            var lc = el.Location as LocationCurve;
            var p0 = lc?.Curve.GetEndPoint(0);
            var p1 = lc?.Curve.GetEndPoint(1);

            var pars = new Dictionary<string, string>();
            foreach (Parameter p in el.Parameters)
            {
                if (p.HasValue && !string.IsNullOrEmpty(p.Definition.Name))
                {
                    string v = p.AsValueString() ?? p.AsString();
                    if (string.IsNullOrEmpty(v))
                    {
                        if (p.StorageType == StorageType.Double) v = (p.AsDouble() * FT2M).ToString("F4");
                        else if (p.StorageType == StorageType.Integer) v = p.AsInteger().ToString();
                        else if (p.StorageType == StorageType.ElementId) v = p.AsElementId().Value.ToString();
                    }
                    pars[p.Definition.Name] = v;
                }
            }

            var bb = el.get_BoundingBox(null);

            return new {
                id = el.Id.Value,
                name = el.Name,
                category = el.Category?.Name,
                levelId = el.LevelId.Value,
                p0x = p0 != null ? Math.Round(p0.X * FT2M * 1000, 2) : 0,
                p0y = p0 != null ? Math.Round(p0.Y * FT2M * 1000, 2) : 0,
                p0z = p0 != null ? Math.Round(p0.Z * FT2M * 1000, 2) : 0,
                p1x = p1 != null ? Math.Round(p1.X * FT2M * 1000, 2) : 0,
                p1y = p1 != null ? Math.Round(p1.Y * FT2M * 1000, 2) : 0,
                p1z = p1 != null ? Math.Round(p1.Z * FT2M * 1000, 2) : 0,
                bbMinX = bb != null ? Math.Round(bb.Min.X * FT2M * 1000, 2) : 0,
                bbMaxX = bb != null ? Math.Round(bb.Max.X * FT2M * 1000, 2) : 0,
                bbMinY = bb != null ? Math.Round(bb.Min.Y * FT2M * 1000, 2) : 0,
                bbMaxY = bb != null ? Math.Round(bb.Max.Y * FT2M * 1000, 2) : 0,
                bbMinZ = bb != null ? Math.Round(bb.Min.Z * FT2M, 3) : 0,
                bbMaxZ = bb != null ? Math.Round(bb.Max.Z * FT2M, 3) : 0,
                pars
            };
        }
    }
}
"""

with open(r'D:\Dropbox\_Documents\RevitAI\InspectSelectedElement.cs', 'w', encoding='utf-8') as f:
    f.write(query_code)

print("Wrote InspectSelectedElement.cs")
