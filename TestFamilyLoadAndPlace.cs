using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SimpleFamilyLoadOptions : IFamilyLoadOptions
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

    public static class TestFamilyLoadAndPlace
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                string famPath = Path.Combine(Path.GetTempPath(), "TestWindowFamily.rfa");
                if (!File.Exists(famPath)) return new { error = "TestWindowFamily.rfa not found at " + famPath };

                Family fam = null;
                using (Transaction tx = new Transaction(doc, "Load Test Family"))
                {
                    tx.Start();
                    doc.LoadFamily(famPath, new SimpleFamilyLoadOptions(), out fam);
                    tx.Commit();
                }

                if (fam == null) return new { error = "Failed to load family" };

                FamilySymbol sym = null;
                foreach (ElementId symId in fam.GetFamilySymbolIds())
                {
                    sym = doc.GetElement(symId) as FamilySymbol;
                    if (sym != null) break;
                }

                if (sym == null) return new { error = "No symbol found in family" };

                return new
                {
                    success = true,
                    familyName = fam.Name,
                    symbolName = sym.Name,
                    category = fam.FamilyCategory?.Name
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
