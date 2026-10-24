using System;
using System.IO;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestExportOneViewDwg
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var view = doc.GetElement(new ElementId(312L)) as View;
            if (view == null) return new { error = "View 312 not found" };

            string outDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Desktop", "RevitDwgExportTest");
            if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

            var opt = new DWGExportOptions();
            opt.FileVersion = ACADVersion.R2018;
            opt.TargetUnit = ExportUnit.Millimeter;
            opt.MergedViews = true;
            opt.Colors = ExportColorMode.TrueColor;

            var viewIds = new List<ElementId> { view.Id };
            string baseFileName = "Test_Tang1";

            bool success = doc.Export(outDir, baseFileName, viewIds, opt);

            var files = Directory.GetFiles(outDir);

            return new
            {
                success,
                outDir,
                files
            };
        }
    }
}
