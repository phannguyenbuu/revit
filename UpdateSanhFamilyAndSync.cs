using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SanhFamilyWarningSwallower2 : IFailuresPreprocessor
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

    public class SanhFamilyLoadOptions2 : IFamilyLoadOptions
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

    public static class UpdateSanhFamilyAndSync
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            string dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Sanh_Chinh_Layered.dwg";
            if (!File.Exists(dwgPath)) return new { error = "DWG file not found: " + dwgPath };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa";

            List<string> logs = new List<string>();

            // 1. Create new Family Document
            var famDoc = app.NewFamilyDocument(templatePath);
            if (famDoc == null) return new { error = "Failed to create family doc" };

            View3D view3D = new FilteredElementCollector(famDoc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            View targetView = (View)view3D ?? famDoc.ActiveView ?? new FilteredElementCollector(famDoc).OfClass(typeof(View)).Cast<View>().FirstOrDefault(v => !v.IsTemplate);

            // Import DWG
            ElementId importedId = ElementId.InvalidElementId;
            using (var tx = new Transaction(famDoc, "Import Sanh Chinh DWG"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SanhFamilyWarningSwallower2());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                var cat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                if (cat != null) famDoc.OwnerFamily.FamilyCategory = cat;

                var dwgOpt = new DWGImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Millimeter,
                    ColorMode = ImportColorMode.Preserved,
                    AutoCorrectAlmostVHLines = false,
                    ThisViewOnly = false
                };

                famDoc.Import(dwgPath, dwgOpt, targetView, out importedId);
                logs.Add($"Imported DWG, id: {importedId.Value}");

                tx.Commit();
            }

            // Configure Materials & Subcategories
            List<string> assignedSubCats = new List<string>();
            using (var tx = new Transaction(famDoc, "Configure Sanh Materials"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SanhFamilyWarningSwallower2());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                Material GetOrCreateMaterial(string matName, byte r, byte g, byte b)
                {
                    var existing = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Material))
                        .Cast<Material>()
                        .FirstOrDefault(m => m.Name.Equals(matName, StringComparison.OrdinalIgnoreCase));
                    if (existing != null) return existing;

                    var id = Material.Create(famDoc, matName);
                    var mat = (Material)famDoc.GetElement(id);
                    mat.Color = new Color(r, g, b);
                    return mat;
                }

                var matCot = GetOrCreateMaterial("Vật liệu Cột Sảnh (Đá Granite)", 50, 50, 55);
                var matMai = GetOrCreateMaterial("Vật liệu Mái Sảnh (Bê tông trắng)", 235, 235, 235);
                var matSan = GetOrCreateMaterial("Vật liệu Sàn Sảnh (Gạch lát)", 190, 185, 175);
                var matBac = GetOrCreateMaterial("Vật liệu Bậc Tam Cấp (Đá bậc)", 150, 145, 140);

                var importCat = famDoc.Settings.Categories
                    .Cast<Category>()
                    .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                if (importCat != null)
                {
                    foreach (Category sub in importCat.SubCategories)
                    {
                        string sn = sub.Name.ToUpperInvariant();
                        if (sn.Contains("COT"))
                        {
                            sub.Material = matCot;
                            sub.LineColor = new Color(50, 50, 55);
                            assignedSubCats.Add($"{sub.Name} -> {matCot.Name}");
                        }
                        else if (sn.Contains("MAI"))
                        {
                            sub.Material = matMai;
                            sub.LineColor = new Color(180, 180, 180);
                            assignedSubCats.Add($"{sub.Name} -> {matMai.Name}");
                        }
                        else if (sn.Contains("BAC"))
                        {
                            sub.Material = matBac;
                            sub.LineColor = new Color(120, 115, 110);
                            assignedSubCats.Add($"{sub.Name} -> {matBac.Name}");
                        }
                        else if (sn.Contains("SAN"))
                        {
                            sub.Material = matSan;
                            sub.LineColor = new Color(160, 155, 145);
                            assignedSubCats.Add($"{sub.Name} -> {matSan.Name}");
                        }
                    }
                }

                if (view3D != null)
                {
                    view3D.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = view3D.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    view3D.SetViewDisplayModel(vdm);
                }

                tx.Commit();
            }

            // Save Family
            famDoc.SaveAs(famPath, new SaveAsOptions { OverwriteExistingFile = true });
            logs.Add("Saved updated family to: " + famPath);
            famDoc.Close(false);

            // 2. Load and overwrite in project
            Family loadedFam = null;
            using (var tx = new Transaction(doc, "Reload Sanh_Chinh_3dsMax Family"))
            {
                tx.Start();
                doc.LoadFamily(famPath, new SanhFamilyLoadOptions2(), out loadedFam);
                tx.Commit();
            }

            // 3. Ensure instance is placed and oriented correctly
            var existingInst = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .FirstOrDefault(fi => fi.Symbol?.Family?.Name == "Sanh_Chinh_3dsMax");

            if (existingInst == null)
            {
                var famInDoc = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name == "Sanh_Chinh_3dsMax");

                FamilySymbol sym = null;
                if (famInDoc != null)
                {
                    sym = doc.GetElement(famInDoc.GetFamilySymbolIds().First()) as FamilySymbol;
                }

                if (sym != null)
                {
                    var level1 = new FilteredElementCollector(doc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .FirstOrDefault(l => Math.Abs(l.Elevation) < 0.01);

                    using (var tx = new Transaction(doc, "Place Sanh Instance"))
                    {
                        tx.Start();
                        if (!sym.IsActive) sym.Activate();
                        XYZ targetPt = new XYZ(550.0 * MM2FT, 6600.0 * MM2FT, 0.0);
                        existingInst = doc.Create.NewFamilyInstance(targetPt, sym, level1, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                        tx.Commit();
                    }
                }
            }

            var bb = existingInst?.get_BoundingBox(null);
            var locPt = (existingInst?.Location as LocationPoint)?.Point;

            return new
            {
                success = true,
                instanceId = existingInst?.Id.Value,
                location = locPt != null ? new { x = Math.Round(locPt.X * FT2MM, 1), y = Math.Round(locPt.Y * FT2MM, 1), z = Math.Round(locPt.Z * FT2MM, 1) } : null,
                boundingBox = bb != null ? new {
                    min = new { x = Math.Round(bb.Min.X * FT2MM, 1), y = Math.Round(bb.Min.Y * FT2MM, 1), z = Math.Round(bb.Min.Z * FT2MM, 1) },
                    max = new { x = Math.Round(bb.Max.X * FT2MM, 1), y = Math.Round(bb.Max.Y * FT2MM, 1), z = Math.Round(bb.Max.Z * FT2MM, 1) }
                } : null,
                assignedSubCategories = assignedSubCats,
                logs
            };
        }
    }
}
