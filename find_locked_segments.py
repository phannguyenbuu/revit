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
    public static class FindLockedSegments
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var dims = new FilteredElementCollector(doc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .ToList();

            var lockedSegments = new List<object>();

            foreach (var d in dims)
            {
                if (d.Segments != null && d.Segments.Size > 0)
                {
                    int segIdx = 0;
                    foreach (DimensionSegment seg in d.Segments)
                    {
                        if (seg.IsLocked)
                        {
                            lockedSegments.Add(new
                            {
                                dimId = d.Id.Value,
                                segIndex = segIdx,
                                val = seg.Value * 0.3048 * 1000
                            });
                        }
                        segIdx++;
                    }
                }
                else
                {
                    if (d.IsLocked)
                    {
                        lockedSegments.Add(new
                        {
                            dimId = d.Id.Value,
                            segIndex = -1,
                            val = d.Value * 0.3048 * 1000
                        });
                    }
                }
            }

            return new { lockedCount = lockedSegments.Count, lockedSegments };
        }
    }
}
"""
print("FindLockedSegments ready")
