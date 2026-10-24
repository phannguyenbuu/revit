using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SanhFamilyWarningSwallower : IFailuresPreprocessor
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

    public class SanhFamilyLoadOptions : IFamilyLoadOptions
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

    public static class CreateSanhChinhFamily
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active project document" };

            string dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Sanh_Chinh_Layered.dwg";
            if (!File.Exists(dwgPath))
            {
                dwgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Sanh_Chinh_Origin.dwg";
            }
            if (!File.Exists(dwgPath))
            {
                return new { error = "DWG file not found: " + dwgPath };
            }

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa";

            List<string> logs = new List<string>();

            try
            {
                // 1. Create new Family Document
                var famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Failed to create family doc" };

                View3D view3D = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

                View targetView = (View)view3D ?? famDoc.ActiveView ?? new FilteredElementCollector(famDoc).OfClass(typeof(View)).Cast<View>().FirstOrDefault(v => !v.IsTemplate);

                // Transaction 1: Set category and import DWG
                ElementId importedId = ElementId.InvalidElementId;
                using (var tx = new Transaction(famDoc, "Import Sanh Chinh DWG"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new SanhFamilyWarningSwallower());
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

                // Transaction 2: Configure Materials & Subcategories
                List<string> assignedSubCats = new List<string>();
                using (var tx = new Transaction(famDoc, "Configure Sanh Materials"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new SanhFamilyWarningSwallower());
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

                    // Set consistent colors display style
                    if (view3D != null)
                    {
                        view3D.DisplayStyle = DisplayStyle.FlatColors;
                        var vdm = view3D.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        view3D.SetViewDisplayModel(vdm);
                    }

                    tx.Commit();
                }

                // Check bounding box
                var impElem = famDoc.GetElement(importedId) as ImportInstance;
                var bb = impElem?.get_BoundingBox(null);
                double minX = bb != null ? bb.Min.X * FT2MM : 0;
                double maxX = bb != null ? bb.Max.X * FT2MM : 0;
                double minY = bb != null ? bb.Min.Y * FT2MM : 0;
                double maxY = bb != null ? bb.Max.Y * FT2MM : 0;
                double minZ = bb != null ? bb.Min.Z * FT2MM : 0;
                double maxZ = bb != null ? bb.Max.Z * FT2MM : 0;

                // Save family
                famDoc.SaveAs(famPath, new SaveAsOptions { OverwriteExistingFile = true });
                logs.Add("Saved family to: " + famPath);

                // 2. Load Family into Revit Project
                Family loadedFam = null;
                using (var tx = new Transaction(doc, "Load Sanh_Chinh_3dsMax Family"))
                {
                    tx.Start();
                    doc.LoadFamily(famPath, new SanhFamilyLoadOptions(), out loadedFam);
                    tx.Commit();
                }

                if (loadedFam == null)
                {
                    loadedFam = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name == "Sanh_Chinh_3dsMax");
                }

                FamilySymbol loadedSymbol = null;
                if (loadedFam != null)
                {
                    foreach (ElementId sid in loadedFam.GetFamilySymbolIds())
                    {
                        loadedSymbol = doc.GetElement(sid) as FamilySymbol;
                        if (loadedSymbol != null) break;
                    }

                    if (loadedSymbol != null && !loadedSymbol.IsActive)
                    {
                        using (var tx = new Transaction(doc, "Activate Sanh_Chinh_3dsMax Symbol"))
                        {
                            tx.Start();
                            loadedSymbol.Activate();
                            tx.Commit();
                        }
                    }
                }

                famDoc.Close(false);

                return new
                {
                    success = true,
                    familyName = "Sanh_Chinh_3dsMax",
                    familyPath = famPath,
                    isLoadedInProject = loadedFam != null,
                    symbolName = loadedSymbol?.Name,
                    bboxMm = new
                    {
                        widthY = Math.Round(maxY - minY, 1),
                        depthX = Math.Round(maxX - minX, 1),
                        heightZ = Math.Round(maxZ - minZ, 1),
                        minX = Math.Round(minX, 1),
                        maxX = Math.Round(maxX, 1),
                        minY = Math.Round(minY, 1),
                        maxY = Math.Round(maxY, 1),
                        minZ = Math.Round(minZ, 1),
                        maxZ = Math.Round(maxZ, 1)
                    },
                    assignedSubCategories = assignedSubCats,
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
