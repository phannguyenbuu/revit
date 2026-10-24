using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class TestImportMaxWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var msg in msgs)
            {
                if (msg.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(msg);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class TestImportMaxFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\max_selection_test.dwg";
            string dxfPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\max_selection.dxf";
            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            string testFamPath = @"D:\Dropbox\_Documents\RevitAI\Test_Sanh_Import.rfa";

            var app = uiapp.Application;
            List<string> logs = new List<string>();

            try
            {
                var famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Cannot create family document" };

                View targetView = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate)
                    ?? (View)famDoc.ActiveView
                    ?? new FilteredElementCollector(famDoc).OfClass(typeof(View)).Cast<View>().FirstOrDefault(v => !v.IsTemplate);

                ElementId importedId = ElementId.InvalidElementId;
                string usedFile = File.Exists(dwgPath) ? dwgPath : dxfPath;
                logs.Add("Using file: " + usedFile);

                using (var tx = new Transaction(famDoc, "Import Test DWG"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new TestImportMaxWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    var dwgOpt = new DWGImportOptions
                    {
                        Placement = ImportPlacement.Origin,
                        Unit = ImportUnit.Millimeter,
                        ColorMode = ImportColorMode.Preserved,
                        AutoCorrectAlmostVHLines = false,
                        ThisViewOnly = false
                    };

                    bool success = famDoc.Import(usedFile, dwgOpt, targetView, out importedId);
                    logs.Add($"Import returned: {success}, importedId: {importedId.Value}");

                    tx.Commit();
                }

                var impElem = famDoc.GetElement(importedId) as ImportInstance;
                BoundingBoxXYZ bb = impElem?.get_BoundingBox(null);
                double minX = bb != null ? bb.Min.X * 304.8 : 0;
                double maxX = bb != null ? bb.Max.X * 304.8 : 0;
                double minY = bb != null ? bb.Min.Y * 304.8 : 0;
                double maxY = bb != null ? bb.Max.Y * 304.8 : 0;
                double minZ = bb != null ? bb.Min.Z * 304.8 : 0;
                double maxZ = bb != null ? bb.Max.Z * 304.8 : 0;

                logs.Add($"BBox mm: X[{minX:F1}, {maxX:F1}], Y[{minY:F1}, {maxY:F1}], Z[{minZ:F1}, {maxZ:F1}]");

                famDoc.SaveAs(testFamPath, new SaveAsOptions { OverwriteExistingFile = true });
                famDoc.Close(false);
                logs.Add("Saved test family to: " + testFamPath);

                return new
                {
                    success = true,
                    importedId = importedId.Value,
                    bbox = new { minX, maxX, minY, maxY, minZ, maxZ },
                    logs
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString(), logs };
            }
        }
    }
}
