import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

code = """
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllLevels
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new {
                    id = l.Id.Value,
                    name = l.Name,
                    elevationM = Math.Round(l.Elevation * FT2M, 4),
                    elevationMm = Math.Round(l.Elevation * FT2M * 1000.0, 1)
                })
                .ToList();

            return new { levels };
        }
    }
}
"""
print("Code ready")
