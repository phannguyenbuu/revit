using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class PlaceStructuralColumns
    {
        private const double MetersToFeet = 1.0 / 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Temp\columns_extracted.json";
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("jsonPath", out var jp))
            {
                jsonPath = jp.GetString() ?? jsonPath;
            }

            if (!File.Exists(jsonPath)) return new { error = "Columns JSON not found: " + jsonPath };

            string jsonText = File.ReadAllText(jsonPath);
            using var jsonDoc = JsonDocument.Parse(jsonText);
            var root = jsonDoc.RootElement;
            if (root.ValueKind != JsonValueKind.Array) return new { error = "JSON is not an array" };

            // 1. Get Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            var baseLevel = levels.FirstOrDefault(l => l.Name.Contains("TRỆT")) ?? levels.FirstOrDefault();
            var topLevel = levels.FirstOrDefault(l => l.Name.Contains("01") && !l.Name.Contains("HẦM")) 
                           ?? levels.FirstOrDefault(l => l.Elevation > (baseLevel?.Elevation ?? 0));

            if (baseLevel == null || topLevel == null) return new { error = "Could not find base or top level" };

            // 2. Map available column symbols by name
            var colSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .ToList();

            var symbolDict = new Dictionary<string, FamilySymbol>(StringComparer.OrdinalIgnoreCase);
            foreach (var s in colSymbols)
            {
                if (!s.IsActive)
                {
                    using (var txSym = new Transaction(doc, "Activate Symbol"))
                    {
                        txSym.Start();
                        s.Activate();
                        txSym.Commit();
                    }
                }
                symbolDict[s.Name] = s;
                // Also store normalized name without spaces e.g. "1100x1100mm"
                string norm = s.Name.Replace(" ", "").ToLowerInvariant();
                symbolDict[norm] = s;
            }

            // 3. Batch create columns
            int createdCount = 0;
            var errors = new List<string>();

            using (var tx = new Transaction(doc, "Draw Structural Columns from AutoCAD"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                opts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                foreach (var el in root.EnumerateArray())
                {
                    try
                    {
                        int w = (int)Math.Round(el.GetProperty("width_mm").GetDouble());
                        int h = (int)Math.Round(el.GetProperty("height_mm").GetDouble());
                        double rx = el.GetProperty("rvt_x").GetDouble() * MetersToFeet;
                        double ry = el.GetProperty("rvt_y").GetDouble() * MetersToFeet;

                        string exactName = $"{w} x {h}mm";
                        string normName = $"{w}x{h}mm".ToLowerInvariant();

                        FamilySymbol? targetSym = null;
                        if (symbolDict.TryGetValue(exactName, out targetSym) || symbolDict.TryGetValue(normName, out targetSym))
                        {
                            // Found direct match
                        }
                        else
                        {
                            // Try flipped
                            string flipName = $"{h} x {w}mm";
                            string flipNorm = $"{h}x{w}mm".ToLowerInvariant();
                            symbolDict.TryGetValue(flipName, out targetSym);
                            if (targetSym == null) symbolDict.TryGetValue(flipNorm, out targetSym);
                        }

                        if (targetSym == null)
                        {
                            targetSym = colSymbols.FirstOrDefault();
                        }

                        if (targetSym == null)
                        {
                            errors.Add($"No column symbol available for size {w}x{h}");
                            continue;
                        }

                        XYZ loc = new XYZ(rx, ry, baseLevel.Elevation);
                        FamilyInstance instance = doc.Create.NewFamilyInstance(loc, targetSym, baseLevel, StructuralType.Column);

                        if (instance != null)
                        {
                            // Set Base Level and Top Level
                            var pBase = instance.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                            if (pBase != null && !pBase.IsReadOnly) pBase.Set(baseLevel.Id);

                            var pTop = instance.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                            if (pTop != null && !pTop.IsReadOnly) pTop.Set(topLevel.Id);

                            var pBaseOffset = instance.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM) ?? instance.LookupParameter("Base Offset");
                            if (pBaseOffset != null && !pBaseOffset.IsReadOnly) pBaseOffset.Set(0.0);

                            var pTopOffset = instance.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM) ?? instance.LookupParameter("Top Offset");
                            if (pTopOffset != null && !pTopOffset.IsReadOnly) pTopOffset.Set(0.0);

                            createdCount++;
                        }
                    }
                    catch (Exception ex)
                    {
                        errors.Add(ex.Message);
                    }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                totalInput = root.GetArrayLength(),
                columnsCreated = createdCount,
                baseLevel = baseLevel.Name,
                topLevel = topLevel.Name,
                errorsCount = errors.Count,
                firstErrors = errors.Take(5).ToList()
            };
        }
    }
}
