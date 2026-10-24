using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportSelectedSectionsToDwg
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
                if (v != null && !v.IsTemplate && (v is ViewSection || v is ViewPlan || v is ViewDrafting))
                {
                    views.Add(v);
                }
            }

            // Fallback if selection was lost: the 5 section views
            if (views.Count == 0)
            {
                long[] defaultIds = new long[] { 2388045L, 1894971L, 749996L, 1284099L, 1891223L };
                foreach (var did in defaultIds)
                {
                    var v = doc.GetElement(new ElementId(did)) as View;
                    if (v != null) views.Add(v);
                }
            }

            // Natural sort: 1-1, 2-2, 3-3, 4-4, 5-5
            views = views.OrderBy(v => v.Name).ToList();

            string exportFolder = Path.Combine(@"D:\Dropbox\_Documents\RevitAI", "DWG_Export_Sections");
            if (!Directory.Exists(exportFolder))
            {
                Directory.CreateDirectory(exportFolder);
            }
            else
            {
                foreach (var oldFile in Directory.GetFiles(exportFolder, "*.dwg"))
                {
                    try { File.Delete(oldFile); } catch { }
                }
            }

            var opt = new DWGExportOptions();
            opt.FileVersion = ACADVersion.R2018;
            opt.TargetUnit = ExportUnit.Millimeter;
            opt.MergedViews = true;
            opt.Colors = ExportColorMode.IndexColors;
            opt.HideScopeBox = true;
            opt.HideUnreferenceViewTags = true;

            var exportedFiles = new List<object>();

            for (int i = 0; i < views.Count; i++)
            {
                var v = views[i];
                string asciiName = $"section_{i + 1:D2}";

                var vList = new List<ElementId> { v.Id };
                bool ok = doc.Export(exportFolder, asciiName, vList, opt);

                string expectedFile = Path.Combine(exportFolder, asciiName + ".dwg");
                if (!File.Exists(expectedFile))
                {
                    var matches = Directory.GetFiles(exportFolder, asciiName + "*.dwg");
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

            // Re-select views in Project Browser
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
