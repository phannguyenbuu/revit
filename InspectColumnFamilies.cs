using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectColumnFamilies
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Check existing structural column symbols
            var structSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Select(s => new
                {
                    id = s.Id.Value,
                    familyName = s.FamilyName,
                    name = s.Name,
                    category = "StructuralColumns"
                })
                .ToList();

            // 2. Check standard architectural column symbols
            var archSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Columns)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Select(s => new
                {
                    id = s.Id.Value,
                    familyName = s.FamilyName,
                    name = s.Name,
                    category = "Columns"
                })
                .ToList();

            // 3. Check levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevationMeters = l.Elevation * 0.3048
                })
                .ToList();

            // 4. Search Revit library paths on disk for column families
            var searchPaths = new List<string>
            {
                @"C:\ProgramData\Autodesk\RVT 2025\Libraries",
                @"C:\ProgramData\Autodesk\RVT 2024\Libraries",
                @"C:\ProgramData\Autodesk\RVT 2027\Libraries",
                @"C:\ProgramData\Autodesk\Libraries"
            };

            var foundFamilyFiles = new List<string>();
            foreach (var p in searchPaths)
            {
                if (Directory.Exists(p))
                {
                    try
                    {
                        var files = Directory.GetFiles(p, "*Column*.rfa", SearchOption.AllDirectories);
                        foundFamilyFiles.AddRange(files.Take(10));
                    }
                    catch { }
                }
            }

            return new
            {
                structSymbolsCount = structSymbols.Count,
                structSymbols = structSymbols,
                archSymbolsCount = archSymbols.Count,
                archSymbols = archSymbols,
                levels = levels,
                foundLibraryFiles = foundFamilyFiles
            };
        }
    }
}
