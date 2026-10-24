using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestLoadFamilyResult
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            string famPath = Path.Combine(@"D:\Dropbox\_Documents\RevitAI", "Mat_Tien_3dsMax.rfa");
            if (!File.Exists(famPath)) return new { error = "File not found" };

            Family? loadedFam = null;
            bool loadOk = false;
            string loadError = "";

            using (var tx = new Transaction(doc, "Test Load Family"))
            {
                tx.Start();
                try
                {
                    loadOk = doc.LoadFamily(famPath, new SyncFamilyLoadOptions(), out loadedFam);
                }
                catch (Exception ex)
                {
                    loadError = ex.Message;
                }
                tx.RollBack();
            }

            return new
            {
                famPath,
                loadOk,
                loadedFamName = loadedFam?.Name ?? "null",
                loadError
            };
        }
    }
}
