using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class LoggingLoadOptions : IFamilyLoadOptions
    {
        public bool FamilyFoundCalled = false;
        public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
        {
            FamilyFoundCalled = true;
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

    public class LoggingFailurePreprocessor : IFailuresPreprocessor
    {
        public List<string> Messages = new List<string>();
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var msg in msgs)
            {
                Messages.Add($"[{msg.GetSeverity()}] {msg.GetDescriptionText()}");
                if (msg.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(msg);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class TestLoadDetailed
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            string famPath = Path.Combine(@"D:\Dropbox\_Documents\RevitAI", "Mat_Tien_3dsMax.rfa");
            var loadOpt = new LoggingLoadOptions();
            var failProc = new LoggingFailurePreprocessor();

            Family? loadedFam = null;
            bool loadOk = false;

            using (var tx = new Transaction(doc, "Test Detailed Load"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(failProc);
                tx.SetFailureHandlingOptions(opt);

                tx.Start();
                loadOk = doc.LoadFamily(famPath, loadOpt, out loadedFam);
                tx.Commit();
            }

            return new
            {
                loadOk,
                familyFoundCalled = loadOpt.FamilyFoundCalled,
                loadedFamName = loadedFam?.Name ?? "null",
                failureMessages = failProc.Messages
            };
        }
    }
}
