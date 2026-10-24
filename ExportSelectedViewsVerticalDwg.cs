using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportSelectedViewsVerticalDwg
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null || uidoc == null) return new { success = false, message = "No active Revit document." };

            var options = args.TryGetProperty("args", out var n) && n.ValueKind == System.Text.Json.JsonValueKind.Object ? n : args;

            // 1. Identify target views from Project Browser selection or arguments
            var targetViews = new List<View>();
            var selIds = uidoc.Selection.GetElementIds();

            if (options.TryGetProperty("viewIds", out var pViewIds) && pViewIds.ValueKind == System.Text.Json.JsonValueKind.Array)
            {
                foreach (var idElem in pViewIds.EnumerateArray())
                {
                    if (idElem.TryGetInt64(out var vid))
                    {
                        var v = doc.GetElement(new ElementId(vid)) as View;
                        if (v != null && !v.IsTemplate) targetViews.Add(v);
                    }
                }
            }
            else
            {
                foreach (var id in selIds)
                {
                    var v = doc.GetElement(id) as View;
                    if (v != null && !v.IsTemplate)
                    {
                        // Exclude 3D views and schedule sheets from 2D vertical DWG export
                        if (v is ViewPlan || v is ViewSection || v is ViewDrafting || v.ViewType == ViewType.Elevation)
                        {
                            targetViews.Add(v);
                        }
                    }
                }
            }

            if (targetViews.Count == 0)
            {
                return new
                {
                    success = false,
                    message = "Không tìm thấy view nào được chọn trong Project Browser. Vui lòng giữ phím Ctrl và click chọn các view (Mặt bằng, Mặt cắt, Chi tiết) trong Project Browser rồi chạy lại."
                };
            }

            // Natural sort views by name
            targetViews = targetViews.OrderBy(v => v.Name).ToList();

            // 2. Read gap parameter (default: 6000mm)
            double gapMm = 6000.0;
            if (options.TryGetProperty("gapMm", out var pGap))
                gapMm = pGap.GetDouble();

            // 3. Prepare individual export directory
            string exportFolder = Path.Combine(@"D:\Dropbox\_Documents\RevitAI", "DWG_Export_Individual");
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

            // 4. Configure DWG Export Options
            var opt = new DWGExportOptions();
            opt.FileVersion = ACADVersion.R2018;
            opt.TargetUnit = ExportUnit.Millimeter;
            opt.MergedViews = true;
            opt.Colors = ExportColorMode.IndexColors; // Standard ACI Colors
            opt.HideScopeBox = true;
            opt.HideUnreferenceViewTags = true;

            var viewDataList = new List<ViewExportData>();

            for (int i = 0; i < targetViews.Count; i++)
            {
                var v = targetViews[i];
                string asciiBase = $"view_{i + 1:D2}";

                // Export this view
                var vList = new List<ElementId> { v.Id };
                bool ok = doc.Export(exportFolder, asciiBase, vList, opt);

                string expectedFile = Path.Combine(exportFolder, asciiBase + ".dwg");
                if (!File.Exists(expectedFile))
                {
                    var matches = Directory.GetFiles(exportFolder, asciiBase + "*.dwg");
                    if (matches.Length > 0) expectedFile = matches[0];
                }

                // Determine View Bounding Box in mm
                double xMin = 0, xMax = 38000, yMin = 0, yMax = 15000;
                if (v.CropBoxActive && v.CropBox != null)
                {
                    xMin = v.CropBox.Min.X * FT_TO_MM;
                    xMax = v.CropBox.Max.X * FT_TO_MM;
                    yMin = v.CropBox.Min.Y * FT_TO_MM;
                    yMax = v.CropBox.Max.Y * FT_TO_MM;
                }
                else
                {
                    // Compute from model elements in view
                    var collector = new FilteredElementCollector(doc, v.Id).WhereElementIsNotElementType();
                    XYZ? minPt = null, maxPt = null;
                    foreach (var el in collector)
                    {
                        var bb = el.get_BoundingBox(v);
                        if (bb != null)
                        {
                            if (minPt == null)
                            {
                                minPt = new XYZ(bb.Min.X, bb.Min.Y, bb.Min.Z);
                                maxPt = new XYZ(bb.Max.X, bb.Max.Y, bb.Max.Z);
                            }
                            else
                            {
                                minPt = new XYZ(Math.Min(minPt.X, bb.Min.X), Math.Min(minPt.Y, bb.Min.Y), Math.Min(minPt.Z, bb.Min.Z));
                                maxPt = new XYZ(Math.Max(maxPt.X, bb.Max.X), Math.Max(maxPt.Y, bb.Max.Y), Math.Max(maxPt.Z, bb.Max.Z));
                            }
                        }
                    }
                    if (minPt != null && maxPt != null)
                    {
                        xMin = minPt.X * FT_TO_MM;
                        xMax = maxPt.X * FT_TO_MM;
                        yMin = minPt.Y * FT_TO_MM;
                        yMax = maxPt.Y * FT_TO_MM;
                    }
                }

                viewDataList.Add(new ViewExportData
                {
                    Index = i + 1,
                    Id = v.Id.Value,
                    Name = v.Name,
                    FilePath = expectedFile,
                    Success = ok && File.Exists(expectedFile),
                    XMin = xMin,
                    XMax = xMax,
                    YMin = yMin,
                    YMax = yMax,
                    Width = Math.Round(xMax - xMin, 1),
                    Height = Math.Round(yMax - yMin, 1),
                    CenterX = Math.Round((xMin + xMax) * 0.5, 1)
                });
            }

            // 5. Calculate vertical assembly offsets
            // View 0 is at offset Y = 0
            // View i is placed such that its Top is gapMm below the Bottom of View i-1
            double currentBottom = 0.0;
            for (int i = 0; i < viewDataList.Count; i++)
            {
                var vd = viewDataList[i];
                if (i == 0)
                {
                    vd.YOffset = 0.0;
                    currentBottom = vd.YMin; // Bottom in master drawing
                    vd.TitleY = currentBottom - (gapMm * 0.5);
                }
                else
                {
                    // Delta Y = currentBottom - gapMm - vd.YMax
                    double deltaY = currentBottom - gapMm - vd.YMax;
                    vd.YOffset = Math.Round(deltaY, 0);
                    currentBottom = vd.YMin + deltaY;
                    vd.TitleY = Math.Round(currentBottom - (gapMm * 0.5), 0);
                }
                vd.TitleX = vd.CenterX;
            }

            // Keep user selection in Project Browser
            uidoc.Selection.SetElementIds(targetViews.Select(v => v.Id).ToList());

            return new
            {
                success = true,
                viewCount = targetViews.Count,
                gapMm,
                exportFolder,
                views = viewDataList.Select(v => new
                {
                    index = v.Index,
                    id = v.Id,
                    name = v.Name,
                    filePath = v.FilePath,
                    success = v.Success,
                    width = v.Width,
                    height = v.Height,
                    yOffset = v.YOffset,
                    titleX = v.TitleX,
                    titleY = v.TitleY
                }).ToList()
            };
        }

        private class ViewExportData
        {
            public int Index { get; set; }
            public long Id { get; set; }
            public string Name { get; set; } = "";
            public string FilePath { get; set; } = "";
            public bool Success { get; set; }
            public double XMin { get; set; }
            public double XMax { get; set; }
            public double YMin { get; set; }
            public double YMax { get; set; }
            public double Width { get; set; }
            public double Height { get; set; }
            public double CenterX { get; set; }
            public double YOffset { get; set; }
            public double TitleX { get; set; }
            public double TitleY { get; set; }
        }
    }
}
