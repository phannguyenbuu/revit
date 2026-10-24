using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class ColumnFamilyLoadOption : IFamilyLoadOptions
    {
        public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
        {
            overwriteParameterValues = true;
            return true;
        }

        public bool OnSharedFamilyFound(Family sharedFamily, bool familyInUse, out FamilySource source, out bool overwriteParameterValues)
        {
            source = FamilySource.Family;
            overwriteParameterValues = true;
            return true;
        }
    }

    public static class CreateColumnFamily
    {
        private const double MetersToFeet = 1.0 / 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Structural Column.rft";
            if (!File.Exists(templatePath))
            {
                templatePath = @"C:\ProgramData\Autodesk\RVT 2027\Family Templates\English\Metric Structural Column.rft";
            }
            if (!File.Exists(templatePath)) return new { error = "Template not found" };

            string outputRfa = @"D:\Dropbox\_Documents\RevitAI\Concrete-Rectangular-Column.rfa";

            // 10 distinct types to create
            var typeDefs = new (string name, double widthMm, double depthMm)[]
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

            Document famDoc = app.NewFamilyDocument(templatePath);
            if (famDoc == null) return new { error = "Failed to create family document" };

            try
            {
                var famMgr = famDoc.FamilyManager;
                FamilyParameter? widthParam = null;
                FamilyParameter? depthParam = null;

                foreach (FamilyParameter p in famMgr.Parameters)
                {
                    if (p.Definition.Name.Equals("Width", StringComparison.OrdinalIgnoreCase)) widthParam = p;
                    if (p.Definition.Name.Equals("Depth", StringComparison.OrdinalIgnoreCase)) depthParam = p;
                }

                if (widthParam == null || depthParam == null)
                {
                    famDoc.Close(false);
                    return new { error = "Width or Depth parameter not found in template" };
                }

                using (var tx = new Transaction(famDoc, "Create Column Types"))
                {
                    tx.Start();
                    foreach (var td in typeDefs)
                    {
                        var t = famMgr.NewType(td.name);
                        famMgr.Set(widthParam, (td.widthMm / 1000.0) * MetersToFeet);
                        famMgr.Set(depthParam, (td.depthMm / 1000.0) * MetersToFeet);
                    }
                    tx.Commit();
                }

                var saveOpts = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(outputRfa, saveOpts);

                // Load family into project
                Family loadedFamily = famDoc.LoadFamily(doc, new ColumnFamilyLoadOption());
                famDoc.Close(false);

                // Activate symbols in project
                var symbols = new List<string>();
                if (loadedFamily != null)
                {
                    using (var tx = new Transaction(doc, "Activate Column Symbols"))
                    {
                        tx.Start();
                        foreach (ElementId symId in loadedFamily.GetFamilySymbolIds())
                        {
                            var sym = doc.GetElement(symId) as FamilySymbol;
                            if (sym != null)
                            {
                                if (!sym.IsActive) sym.Activate();
                                symbols.Add(sym.Name);
                            }
                        }
                        tx.Commit();
                    }
                }

                return new
                {
                    success = true,
                    familyName = loadedFamily?.Name ?? "Concrete-Rectangular-Column",
                    symbolsCount = symbols.Count,
                    symbols = symbols,
                    rfaPath = outputRfa
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
