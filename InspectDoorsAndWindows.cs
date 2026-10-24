using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorsAndWindows
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            // Collect all doors
            var doors = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .OfCategory(BuiltInCategory.OST_Doors)
                .Cast<FamilyInstance>()
                .ToList();

            // Collect all windows
            var windows = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .ToList();

            var doorTypes = doors.Select(d => d.Symbol).DistinctBy(s => s.Id.Value).Select(s => DescribeSymbol(s, doc)).ToList();
            var windowTypes = windows.Select(w => w.Symbol).DistinctBy(s => s.Id.Value).Select(s => DescribeSymbol(s, doc)).ToList();

            var sampleDoors = doors.Take(5).Select(d => DescribeInstance(d, doc)).ToList();
            var sampleWindows = windows.Take(5).Select(w => DescribeInstance(w, doc)).ToList();

            return new
            {
                doorCount = doors.Count,
                windowCount = windows.Count,
                doorTypes = doorTypes,
                windowTypes = windowTypes,
                sampleDoors = sampleDoors,
                sampleWindows = sampleWindows
            };
        }

        private static object DescribeSymbol(FamilySymbol s, Document doc)
        {
            var pList = new List<object>();
            foreach (Parameter p in s.Parameters)
            {
                if (p.HasValue && (p.StorageType == StorageType.Double || p.StorageType == StorageType.String))
                {
                    string name = p.Definition.Name;
                    if (name.Contains("Width", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Height", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Frame", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Inset", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Offset", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Rough", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Depth", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Reveal", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Thick", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Kích thước", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Khung", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Bề dày", StringComparison.OrdinalIgnoreCase))
                    {
                        string val = p.StorageType == StorageType.Double ? $"{p.AsDouble() * 304.8:F1} mm" : p.AsString();
                        pList.Add(new { name = name, value = val, isReadOnly = p.IsReadOnly });
                    }
                }
            }

            return new
            {
                symbolId = s.Id.Value,
                familyName = s.FamilyName,
                symbolName = s.Name,
                parameters = pList
            };
        }

        private static object DescribeInstance(FamilyInstance inst, Document doc)
        {
            var pList = new List<object>();
            foreach (Parameter p in inst.Parameters)
            {
                if (p.HasValue && (p.StorageType == StorageType.Double || p.StorageType == StorageType.String))
                {
                    string name = p.Definition.Name;
                    if (name.Contains("Inset", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Offset", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Depth", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Reveal", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Sill", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Frame", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Position", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Vị trí", StringComparison.OrdinalIgnoreCase) ||
                        name.Contains("Lọt lòng", StringComparison.OrdinalIgnoreCase))
                    {
                        string val = p.StorageType == StorageType.Double ? $"{p.AsDouble() * 304.8:F1} mm" : p.AsString();
                        pList.Add(new { name = name, value = val, isReadOnly = p.IsReadOnly });
                    }
                }
            }

            var hostWall = inst.Host as Wall;
            double wallThick = hostWall != null ? hostWall.Width * 304.8 : 0;

            return new
            {
                instanceId = inst.Id.Value,
                familyName = inst.Symbol?.FamilyName,
                symbolName = inst.Name,
                hostWallId = hostWall?.Id.Value,
                hostWallThickMm = wallThick,
                handFlipped = inst.HandFlipped,
                facingFlipped = inst.FacingFlipped,
                parameters = pList
            };
        }
    }
}
