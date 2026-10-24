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
    public static class InspectLevelConstraints
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var dims = new FilteredElementCollector(doc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .ToList();

            var lockedDims = new List<object>();

            foreach (var d in dims)
            {
                bool isLocked = false;
                try { isLocked = d.IsLocked; } catch { }

                var refIds = new List<long>();
                try
                {
                    foreach (Reference r in d.References)
                    {
                        if (r.ElementId != ElementId.InvalidElementId)
                            refIds.Add(r.ElementId.Value);
                    }
                }
                catch { }

                if (isLocked || refIds.Contains(311L) || refIds.Contains(694L))
                {
                    lockedDims.Add(new
                    {
                        id = d.Id.Value,
                        name = d.Name,
                        isLocked = isLocked,
                        refIds = refIds,
                        val = d.Value
                    });
                }
            }

            return new { totalDims = dims.Count, lockedDims };
        }
    }
}
"""
print("InspectLevelConstraints ready")
