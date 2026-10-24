using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportSelectedViewsToDwg
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            var views = new List<View>();

            foreach (var id in selIds)
            {
                var v = doc.GetElement(id) as View;
                if (v != null && !v.IsTemplate && (v is ViewPlan || v is ViewSection || v is ViewDrafting))
                {
                    views.Add(v);
                }
            }

            // Fallback if selection was lost: standard 7 floor plans
            if (views.Count == 0)
            {
                long[] defaultIds = new long[] { 312L, 695L, 1727632L, 2409349L, 931687L, 2370740L, 1234140L };
                foreach (var did in defaultIds)
                {
                    var v = doc.GetElement(new ElementId(did)) as View;
                    if (v != null) views.Add(v);
                }
            }

            // Sort views naturally by Name
            views = views.OrderBy(v => v.Name).ToList();

            string exportFolder = Path.Combine(@"D:\Dropbox\_Documents\RevitAI", "DWG_Export_Individual");
            if (!Directory.Exists(exportFolder))
            {
                Directory.CreateDirectory(exportFolder);
            }
            else
            {
                // Clean existing dwg files in folder
                foreach (var oldFile in Directory.GetFiles(exportFolder, "*.dwg"))
                {
                    try { File.Delete(oldFile); } catch { }
                }
            }

            var opt = new DWGExportOptions();
            opt.FileVersion = ACADVersion.R2018;
            opt.TargetUnit = ExportUnit.Millimeter;
            opt.MergedViews = true;
            opt.Colors = ExportColorMode.TrueColor;
            opt.HideScopeBox = true;
            opt.HideUnreferenceViewTags = true;

            var exportedFiles = new List<object>();

            for (int i = 0; i < views.Count; i++)
            {
                var v = views[i];
                // Clean safe filename: e.g. "01_Mat_Bang_Tang_1"
                string safeName = $"{i + 1:D2}_{v.Name}";
                foreach (char c in Path.GetInvalidFileNameChars())
                {
                    safeName = safeName.Replace(c, '_');
                }

                var vList = new List<ElementId> { v.Id };
                bool ok = doc.Export(exportFolder, safeName, vList, opt);

                // Find the exported file
                string expectedFile = Path.Combine(exportFolder, safeName + ".dwg");
                if (!File.Exists(expectedFile))
                {
                    // Revit might append the view name if not named exactly
                    var matches = Directory.GetFiles(exportFolder, safeName + "*.dwg");
                    if (matches.Length > 0) expectedFile = matches[0];
                }

                exportedFiles.Add(new
                {
                    order = i + 1,
                    viewId = v.Id.Value,
                    viewName = v.Name,
                    success = ok,
                    filePath = File.Exists(expectedFile) ? expectedFile : null,
                    fileSizeKb = File.Exists(expectedFile) ? new FileInfo(expectedFile).Length / 1024.0 : 0
                });
            }

            // Keep the views selected in Project Browser
            uidoc.Selection.SetElementIds(views.Select(v => v.Id).ToList());

            return new
            {
                success = true,
                count = exportedFiles.Count,
                exportFolder,
                exportedFiles
            };
        }
    }
}
