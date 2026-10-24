using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class FamilyLoadOptionOverride : IFamilyLoadOptions
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

    public static class RemoveWindowBars
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var log = new List<string>();

                // List of target families to modify
                string[] targetFamilyNames = new[]
                {
                    "CUA SO 2 CANH NHOM KINH O O THOANG",
                    "CUA SO2 CANH NHOM KINH CO O THOANG"
                };

                foreach (var famName in targetFamilyNames)
                {
                    var fam = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name.Equals(famName, StringComparison.OrdinalIgnoreCase));

                    if (fam == null)
                    {
                        log.Add($"Family {famName} not found");
                        continue;
                    }

                    if (!fam.IsEditable)
                    {
                        log.Add($"Family {famName} is not editable");
                        continue;
                    }

                    Document famDoc = null;
                    try
                    {
                        famDoc = doc.EditFamily(fam);
                    }
                    catch (Exception ex)
                    {
                        log.Add($"Cannot edit family {famName}: {ex.Message}");
                        continue;
                    }

                    if (famDoc == null)
                    {
                        log.Add($"famDoc is null for {famName}");
                        continue;
                    }

                    // Find horizontal bars: GenericForm with dz around 50mm and dy around 25mm
                    var forms = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(GenericForm))
                        .Cast<GenericForm>()
                        .ToList();

                    var barsToDelete = new List<ElementId>();
                    foreach (var f in forms)
                    {
                        var bb = f.get_BoundingBox(null);
                        if (bb == null) continue;

                        double dz = ToMm(bb.Max.Z - bb.Min.Z);
                        double dy = ToMm(bb.Max.Y - bb.Min.Y);

                        // Horizontal muntin bars have dz ~ 50mm and dy ~ 25mm
                        if (dz >= 35 && dz <= 65 && dy >= 15 && dy <= 40)
                        {
                            barsToDelete.Add(f.Id);
                            log.Add($"Found bar in {famName}: ID {f.Id.Value}, dz={dz:F1}mm, dy={dy:F1}mm");
                        }
                    }

                    if (barsToDelete.Count > 0)
                    {
                        using (Transaction t = new Transaction(famDoc, "Xoa song ngang cua so"))
                        {
                            t.Start();
                            famDoc.Delete(barsToDelete);
                            t.Commit();
                        }
                        log.Add($"Deleted {barsToDelete.Count} bars from {famName}");

                        // Reload family into doc
                        famDoc.LoadFamily(doc, new FamilyLoadOptionOverride());
                        log.Add($"Successfully reloaded {famName} into project");
                    }
                    else
                    {
                        log.Add($"No horizontal bars found in {famName}");
                    }

                    famDoc.Close(false);
                }

                // 2. Regenerate doc
                using (Transaction t = new Transaction(doc, "Regenerate after updating window families"))
                {
                    t.Start();
                    doc.Regenerate();
                    t.Commit();
                }

                // 3. Export images
                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string full3dPath = Path.Combine(folder, "revit_3d_no_bars.jpg");
                string closeupPath = Path.Combine(folder, "revit_window_closeup_no_bars.png");

                var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    uidoc.Selection.SetElementIds(new List<ElementId>());

                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);

                    // Export Full 3D
                    uiview3d?.ZoomToFit();
                    if (File.Exists(full3dPath)) File.Delete(full3dPath);
                    var expOptFull = new ImageExportOptions
                    {
                        FilePath = full3dPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOptFull);

                    // Find a window on Axis A (e.g. S1 window at X=13.4, Y=0 or similar) for closeup
                    var sampleWin = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_Windows)
                        .WhereElementIsNotElementType()
                        .Cast<FamilyInstance>()
                        .FirstOrDefault(w => w.Symbol.FamilyName.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

                    if (sampleWin != null && uiview3d != null)
                    {
                        var bb = sampleWin.get_BoundingBox(view3d);
                        if (bb != null)
                        {
                            XYZ center = (bb.Min + bb.Max) * 0.5;
                            double margin = 3.5; // ft ~ 1m
                            XYZ zoomMin = new XYZ(center.X - margin, center.Y - margin, center.Z - margin);
                            XYZ zoomMax = new XYZ(center.X + margin, center.Y + margin, center.Z + margin);

                            uiview3d.ZoomAndCenterRectangle(zoomMin, zoomMax);

                            if (File.Exists(closeupPath)) File.Delete(closeupPath);
                            var expOptClose = new ImageExportOptions
                            {
                                FilePath = closeupPath,
                                FitDirection = FitDirectionType.Horizontal,
                                HLRandWFViewsFileType = ImageFileType.PNG,
                                ImageResolution = ImageResolution.DPI_300,
                                ExportRange = ExportRange.CurrentView,
                                ZoomType = ZoomFitType.FitToPage,
                                PixelSize = 2500
                            };
                            doc.ExportImage(expOptClose);
                        }
                    }
                }

                // 4. Save doc
                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                }
                catch (Exception ex)
                {
                    log.Add("doc.Save error: " + ex.Message);
                }

                return new
                {
                    success = true,
                    log,
                    full3dPath,
                    closeupPath,
                    docSaved
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
