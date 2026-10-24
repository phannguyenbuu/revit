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
    public static class RecreateSolidColumns
    {
        private const double MetersToFeet = 1.0 / 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            string sourceRfa = @"C:\ProgramData\Autodesk\Revit Steel Connections 2027\en-UK\Family Templates\AS_EXT_COLUMN_RConcrete.rfa";
            if (!File.Exists(sourceRfa))
            {
                sourceRfa = @"C:\ProgramData\Autodesk\Revit Steel Connections 2025\en-UK\Family Templates\AS_EXT_COLUMN_RConcrete.rfa";
            }
            if (!File.Exists(sourceRfa)) return new { error = "Source RFA template not found" };

            string outputRfa = @"D:\Dropbox\_Documents\RevitAI\Concrete-Rectangular-Column.rfa";

            // 1. Delete all existing structural columns in the project
            using (var txDel = new Transaction(doc, "Delete Old Empty Columns"))
            {
                var opts = txDel.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                txDel.SetFailureHandlingOptions(opts);

                txDel.Start();
                var oldCols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    .ToElementIds();
                if (oldCols.Count > 0)
                {
                    doc.Delete(oldCols);
                }
                txDel.Commit();
            }

            // 2. Open source solid family and define all 10 types
            var typeDefs = new (string name, double bMm, double hMm)[]
            {
                ("1100 x 1100mm", 1100, 1100),
                ("1000 x 1000mm", 1000, 1000),
                ("700 x 700mm", 700, 700),
                ("600 x 600mm", 600, 600),
                ("400 x 250mm", 400, 250),
                ("1200 x 1200mm", 1200, 1200),
                ("600 x 400mm", 600, 400),
                ("400 x 600mm", 400, 600),
                ("1400 x 1600mm", 1400, 1600),
                ("250 x 400mm", 250, 400)
            };

            Document famDoc = app.OpenDocumentFile(sourceRfa);
            if (famDoc == null) return new { error = "Could not open source RFA: " + sourceRfa };

            try
            {
                var famMgr = famDoc.FamilyManager;
                FamilyParameter? bParam = null;
                FamilyParameter? hParam = null;

                foreach (FamilyParameter p in famMgr.Parameters)
                {
                    if (p.Definition.Name.Equals("b", StringComparison.OrdinalIgnoreCase)) bParam = p;
                    if (p.Definition.Name.Equals("h", StringComparison.OrdinalIgnoreCase)) hParam = p;
                }

                if (bParam == null || hParam == null)
                {
                    famDoc.Close(false);
                    return new { error = "Parameters b or h not found in source family" };
                }

                using (var txFam = new Transaction(famDoc, "Add Types to Solid Column"))
                {
                    txFam.Start();
                    foreach (var td in typeDefs)
                    {
                        var t = famMgr.NewType(td.name);
                        famMgr.Set(bParam, (td.bMm / 1000.0) * MetersToFeet);
                        famMgr.Set(hParam, (td.hMm / 1000.0) * MetersToFeet);
                    }
                    txFam.Commit();
                }

                var saveOpts = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(outputRfa, saveOpts);

                Family loadedFamily = famDoc.LoadFamily(doc, new ColumnFamilyLoadOption());
                famDoc.Close(false);

                // 3. Load & activate symbols in project
                var symbolDict = new Dictionary<string, FamilySymbol>(StringComparer.OrdinalIgnoreCase);
                using (var txSym = new Transaction(doc, "Activate Loaded Solid Symbols"))
                {
                    txSym.Start();
                    var allSymbols = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralColumns)
                        .OfClass(typeof(FamilySymbol))
                        .Cast<FamilySymbol>()
                        .ToList();

                    foreach (var sym in allSymbols)
                    {
                        if (!sym.IsActive) sym.Activate();
                        symbolDict[sym.Name] = sym;
                        symbolDict[sym.Name.Replace(" ", "").ToLowerInvariant()] = sym;
                    }
                    txSym.Commit();
                }

                // 4. Place 402 solid column instances
                string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Temp\columns_extracted.json";
                string jsonText = File.ReadAllText(jsonPath);
                using var jsonDoc = JsonDocument.Parse(jsonText);
                var root = jsonDoc.RootElement;

                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();

                var baseLevel = levels.FirstOrDefault(l => l.Name.Contains("TRỆT")) ?? levels.FirstOrDefault();
                var topLevel = levels.FirstOrDefault(l => l.Name.Contains("01") && !l.Name.Contains("HẦM")) 
                               ?? levels.FirstOrDefault(l => l.Elevation > (baseLevel?.Elevation ?? 0));

                if (baseLevel == null || topLevel == null) return new { error = "Levels not found" };

                int placedCount = 0;
                using (var txPlace = new Transaction(doc, "Place Real Solid Structural Columns"))
                {
                    var opts = txPlace.GetFailureHandlingOptions();
                    opts.SetFailuresPreprocessor(new GridWarningSwallower());
                    opts.SetClearAfterRollback(true);
                    txPlace.SetFailureHandlingOptions(opts);

                    txPlace.Start();

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
                            if (!symbolDict.TryGetValue(exactName, out targetSym) && !symbolDict.TryGetValue(normName, out targetSym))
                            {
                                string flipName = $"{h} x {w}mm";
                                string flipNorm = $"{h}x{w}mm".ToLowerInvariant();
                                symbolDict.TryGetValue(flipName, out targetSym);
                                if (targetSym == null) symbolDict.TryGetValue(flipNorm, out targetSym);
                            }

                            if (targetSym == null) targetSym = symbolDict.Values.FirstOrDefault();
                            if (targetSym == null) continue;

                            XYZ loc = new XYZ(rx, ry, baseLevel.Elevation);
                            FamilyInstance instance = doc.Create.NewFamilyInstance(loc, targetSym, baseLevel, StructuralType.Column);

                            if (instance != null)
                            {
                                var pBase = instance.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                                if (pBase != null && !pBase.IsReadOnly) pBase.Set(baseLevel.Id);

                                var pTop = instance.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                                if (pTop != null && !pTop.IsReadOnly) pTop.Set(topLevel.Id);

                                var pBaseOffset = instance.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM) ?? instance.LookupParameter("Base Offset");
                                if (pBaseOffset != null && !pBaseOffset.IsReadOnly) pBaseOffset.Set(0.0);

                                var pTopOffset = instance.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM) ?? instance.LookupParameter("Top Offset");
                                if (pTopOffset != null && !pTopOffset.IsReadOnly) pTopOffset.Set(0.0);

                                placedCount++;
                            }
                        }
                        catch { }
                    }

                    // 5. Switch active view visual style to Shaded so solids render prominently
                    var activeView = uidoc.ActiveView;
                    if (activeView != null)
                    {
                        try
                        {
                            var template = activeView.ViewTemplateId != ElementId.InvalidElementId ? doc.GetElement(activeView.ViewTemplateId) as View : null;
                            if (template != null)
                            {
                                // If template controls Model Display, adjust template
                                template.DisplayStyle = DisplayStyle.ShadingWithEdges;
                            }
                            activeView.DisplayStyle = DisplayStyle.ShadingWithEdges;
                        }
                        catch { }
                    }

                    txPlace.Commit();
                }

                // 6. Zoom to fit
                try
                {
                    foreach (var uiv in uidoc.GetOpenUIViews())
                    {
                        if (uiv.ViewId == uidoc.ActiveView.Id) uiv.ZoomToFit();
                    }
                }
                catch { }

                try { uidoc.RefreshActiveView(); } catch { }

                return new
                {
                    success = true,
                    columnsPlaced = placedCount,
                    baseLevel = baseLevel.Name,
                    topLevel = topLevel.Name,
                    family = "Concrete-Rectangular-Column (Solid)"
                };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
