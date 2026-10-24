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
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairs
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var stairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .Select(s => {
                    var bLvl = doc.GetElement(s.BaseLevelId) as Level;
                    var tLvl = doc.GetElement(s.TopLevelId) as Level;
                    return new {
                        id = s.Id.Value,
                        name = s.Name,
                        baseLevel = bLvl?.Name,
                        baseLevelId = s.BaseLevelId.Value,
                        topLevel = tLvl?.Name,
                        topLevelId = s.TopLevelId.Value,
                        actualRisers = s.ActualRisersNumber,
                        desiredRisers = s.DesiredRisersNumber,
                        actualRiserHeightMm = s.ActualRiserHeight * FT2M * 1000.0,
                        heightMm = s.Height * FT2M * 1000.0
                    };
                })
                .ToList();

            return new { stairsCount = stairs.Count, stairs };
        }
    }
}
"""
print("InspectStairs ready")
