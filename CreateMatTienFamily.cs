using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class MatTienWarningSwallower : IFailuresPreprocessor
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

    public class MatTienFamilyLoadOptions : IFamilyLoadOptions
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

    public static class CreateMatTienFamily
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double FT2MM = 304.8;
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active project document" };

            string dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Mat_Tien_Layered.dwg";
            if (!File.Exists(dwgPath))
            {
                dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Mat_Tien_Facade.dwg";
            }
            if (!File.Exists(dwgPath))
            {
                return new { error = "DWG file not found: " + dwgPath };
            }

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Mat_Tien_3dsMax.rfa";

            List<string> logs = new List<string>();
            List<string> exportedFiles = new List<string>();
            try
            {
                // =========================================================================
                // 1. Create New Family Document & Import DWG
                // =========================================================================
            var famDoc = app.NewFamilyDocument(templatePath);
            if (famDoc == null) return new { error = "Failed to create family document" };

            View3D famView3D = new FilteredElementCollector(famDoc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            View targetView = (View)famView3D ?? famDoc.ActiveView ?? new FilteredElementCollector(famDoc).OfClass(typeof(View)).Cast<View>().FirstOrDefault(v => !v.IsTemplate);

            ElementId importedId = ElementId.InvalidElementId;
            using (var tx = new Transaction(famDoc, "Import Mat Tien DWG"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new MatTienWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                var cat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                if (cat != null) famDoc.OwnerFamily.FamilyCategory = cat;

                var dwgOpt = new DWGImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Millimeter,
                    ColorMode = ImportColorMode.BlackAndWhite,
                    AutoCorrectAlmostVHLines = false,
                    ThisViewOnly = false
                };

                famDoc.Import(dwgPath, dwgOpt, targetView, out importedId);
                logs.Add($"Imported DWG into family, element ID: {importedId.Value}");

                tx.Commit();
            }

            // Configure Materials & Subcategories in Family
            using (var tx = new Transaction(famDoc, "Configure Mat Tien Materials"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new MatTienWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                Material whiteMat = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .FirstOrDefault(m => m.Name.Equals("Vật liệu Mặt Tiền (Trắng)", StringComparison.OrdinalIgnoreCase));

                if (whiteMat == null)
                {
                    var matId = Material.Create(famDoc, "Vật liệu Mặt Tiền (Trắng)");
                    whiteMat = (Material)famDoc.GetElement(matId);
                    whiteMat.Color = new Color(255, 255, 255);
                    whiteMat.Transparency = 0;
                    whiteMat.Shininess = 0;
                    whiteMat.Smoothness = 0;
                }

                var importCat = famDoc.Settings.Categories.Cast<Category>()
                    .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                if (importCat != null)
                {
                    foreach (Category sub in importCat.SubCategories)
                    {
                        sub.Material = whiteMat;
                        sub.LineColor = new Color(0, 0, 0);
                        logs.Add($"Fam subcategory {sub.Name} -> White face, Black line");
                    }
                }

                if (famView3D != null)
                {
                    famView3D.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = famView3D.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    famView3D.SetViewDisplayModel(vdm);
                }

                tx.Commit();
            }

            // Check Bounding Box
            var impElem = famDoc.GetElement(importedId) as ImportInstance;
            var bb = impElem?.get_BoundingBox(null);
            double minX = bb != null ? bb.Min.X * FT2MM : 0;
            double maxX = bb != null ? bb.Max.X * FT2MM : 0;
            double minY = bb != null ? bb.Min.Y * FT2MM : 0;
            double maxY = bb != null ? bb.Max.Y * FT2MM : 0;
            double minZ = bb != null ? bb.Min.Z * FT2MM : 0;
            double maxZ = bb != null ? bb.Max.Z * FT2MM : 0;
            logs.Add($"Family BBox: X[{minX:F1}..{maxX:F1}], Y[{minY:F1}..{maxY:F1}], Z[{minZ:F1}..{maxZ:F1}]");

            // Save Family
            famDoc.SaveAs(famPath, new SaveAsOptions { OverwriteExistingFile = true });
            famDoc.Close(false);
            logs.Add("Saved family to: " + famPath);

            // =========================================================================
            // 2. Load Family into Active Project & Place Instance
            // =========================================================================
            ElementId placedInstId = ElementId.InvalidElementId;
            using (var tx = new Transaction(doc, "Load & Place Mat Tien Family"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new MatTienWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                // First delete existing instances and record origin
                XYZ origin = new XYZ(550.0 * MM2FT, 6600.0 * MM2FT, 0.0);
                var existingInsts = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilyInstance))
                    .Cast<FamilyInstance>()
                    .Where(fi => {
                        try { return fi.Symbol != null && fi.Symbol.Family != null && fi.Symbol.Family.Name.Equals("Mat_Tien_3dsMax", StringComparison.OrdinalIgnoreCase); }
                        catch { return false; }
                    })
                    .ToList();

                if (existingInsts.Count > 0)
                {
                    var lp = existingInsts[0].Location as LocationPoint;
                    if (lp != null) origin = lp.Point;
                    foreach (var oldInst in existingInsts)
                    {
                        try
                        {
                            doc.Delete(oldInst.Id);
                            logs.Add($"Deleted existing Mat Tien instance: {oldInst.Id.Value}");
                        }
                        catch {}
                    }
                }

                Family loadedFam = null;
                bool loadOk = doc.LoadFamily(famPath, new MatTienFamilyLoadOptions(), out loadedFam);
                if (loadedFam == null)
                {
                    loadedFam = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name.Equals("Mat_Tien_3dsMax", StringComparison.OrdinalIgnoreCase));
                }

                if (loadedFam == null)
                {
                    tx.RollBack();
                    return new { error = "Failed to load Mat_Tien_3dsMax family into project", logs };
                }

                var symIds = loadedFam.GetFamilySymbolIds();
                if (symIds.Count == 0)
                {
                    tx.RollBack();
                    return new { error = "Mat_Tien_3dsMax has no symbols", logs };
                }

                var sym = doc.GetElement(symIds.First()) as FamilySymbol;
                if (!sym.IsActive) sym.Activate();
                doc.Regenerate();

                // Place new instance
                var newInst = doc.Create.NewFamilyInstance(origin, sym, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                placedInstId = newInst.Id;
                logs.Add($"Placed new Mat Tien instance: ID {placedInstId.Value} at ({origin.X * FT2MM:F1}, {origin.Y * FT2MM:F1}, {origin.Z * FT2MM:F1}) mm");

                // Project Categories configuration for Mat Tien
                Material whiteMatProj = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .FirstOrDefault(m => m.Name.Equals("Vật liệu Tường Trắng (Sảnh)", StringComparison.OrdinalIgnoreCase)
                                      || m.Name.Equals("Vật liệu Mặt Tiền (Trắng)", StringComparison.OrdinalIgnoreCase));

                if (whiteMatProj == null)
                {
                    var id = Material.Create(doc, "Vật liệu Mặt Tiền (Trắng)");
                    whiteMatProj = (Material)doc.GetElement(id);
                    whiteMatProj.Color = new Color(255, 255, 255);
                }

                void ProcessProjCat(Category c)
                {
                    if (c == null) return;
                    if (c.Name.IndexOf("Mat_Tien", StringComparison.OrdinalIgnoreCase) >= 0
                        || c.Name.IndexOf("Gach", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        try
                        {
                            c.LineColor = new Color(0, 0, 0);
                            c.Material = whiteMatProj;
                            logs.Add($"Updated proj cat: {c.Name} -> White face, Black line");
                        }
                        catch {}
                    }
                    foreach (Category sub in c.SubCategories) ProcessProjCat(sub);
                }

                foreach (Category c in doc.Settings.Categories)
                {
                    if (c.Name.IndexOf("Import", StringComparison.OrdinalIgnoreCase) >= 0
                        || c.Name.IndexOf("Generic", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        ProcessProjCat(c);
                    }
                }

                // Apply view override for 3D view
                var v3d = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (v3d != null && newInst != null)
                {
                    var solidPattern = new FilteredElementCollector(doc)
                        .OfClass(typeof(FillPatternElement))
                        .Cast<FillPatternElement>()
                        .FirstOrDefault(f => f.GetFillPattern().IsSolidFill);

                    var ogs = new OverrideGraphicSettings();
                    ogs.SetProjectionLineColor(new Color(0, 0, 0));
                    ogs.SetProjectionLineWeight(1);
                    if (solidPattern != null)
                    {
                        ogs.SetSurfaceForegroundPatternId(solidPattern.Id);
                        ogs.SetSurfaceForegroundPatternColor(new Color(255, 255, 255));
                        ogs.SetSurfaceForegroundPatternVisible(true);
                    }
                    v3d.SetElementOverrides(newInst.Id, ogs);
                    logs.Add($"Applied view override on Mat Tien instance {newInst.Id.Value}");
                }

                tx.Commit();
            }

            // =========================================================================
            // 3. Export Verification Images
            // =========================================================================
            try
            {
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var view3D = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (view3D != null)
                {
                    try
                    {
                        if (uidoc.ActiveView.Id != view3D.Id)
                        {
                            uidoc.ActiveView = view3D;
                        }
                    }
                    catch (Exception exSwitch)
                    {
                        logs.Add($"View switch note: {exSwitch.Message}");
                    }

                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);

                    // 1. Overview image with section box turned OFF
                    using (var txNoBox = new Transaction(doc, "Overview Section Box Off"))
                    {
                        txNoBox.Start();
                        view3D.IsSectionBoxActive = false;
                        view3D.DisplayStyle = DisplayStyle.FlatColors;
                        view3D.DetailLevel = ViewDetailLevel.Fine;
                        var vdm = view3D.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        view3D.SetViewDisplayModel(vdm);
                        txNoBox.Commit();
                    }

                    uiview?.ZoomToFit();

                    string pathOverview = Path.Combine(outDir, "revit_mattien_overview_3d.png");
                    if (File.Exists(pathOverview)) try { File.Delete(pathOverview); } catch {}

                    var opt = new ImageExportOptions
                    {
                        FilePath = pathOverview,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(opt);
                    exportedFiles.Add(pathOverview);

                    // 2. Focused Section Box on Front Facade (Axis 1)
                    using (var txBox = new Transaction(doc, "Facade Section Box"))
                    {
                        txBox.Start();
                        BoundingBoxXYZ sb = new BoundingBoxXYZ();
                        sb.Min = new XYZ(-7.5 * M2FT, -1.0 * M2FT, -1.0 * M2FT);
                        sb.Max = new XYZ(5.0 * M2FT, 14.5 * M2FT, 19.0 * M2FT);
                        view3D.SetSectionBox(sb);
                        view3D.IsSectionBoxActive = true;
                        txBox.Commit();
                    }

                    uiview?.ZoomToFit();

                    string pathCloseup = Path.Combine(outDir, "revit_mattien_closeup_3d.png");
                    if (File.Exists(pathCloseup)) try { File.Delete(pathCloseup); } catch {}

                    opt.FilePath = pathCloseup;
                    doc.ExportImage(opt);
                    exportedFiles.Add(pathCloseup);

                    // Restore section box to off
                    using (var txRestore = new Transaction(doc, "Restore Section Box Off"))
                    {
                        txRestore.Start();
                        view3D.IsSectionBoxActive = false;
                        txRestore.Commit();
                    }
                }
            }
            catch (Exception exExp)
            {
                logs.Add($"Export image warning: {exExp.Message}");
            }

            return new {
                success = true,
                placedInstanceId = placedInstId.Value,
                logs,
                exportedFiles
            };
        }
        catch (Exception ex)
        {
            return new {
                success = false,
                error = ex.Message,
                stackTrace = ex.StackTrace,
                logs
            };
        }
    }
}
}
