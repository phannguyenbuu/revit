using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpBridge
{
    public static class IfcToRfaConverter
    {
        public static object ConvertIfcDirectoryToRfa(UIApplication uiapp, string ifcDir, string? outputDir = null, string? templatePath = null)
        {
            if (string.IsNullOrWhiteSpace(ifcDir) || !Directory.Exists(ifcDir))
            {
                return new { error = $"Directory not found: {ifcDir}" };
            }

            outputDir ??= ifcDir;
            Directory.CreateDirectory(outputDir);

            if (string.IsNullOrWhiteSpace(templatePath) || !File.Exists(templatePath))
            {
                templatePath = @"C:\ProgramData\Autodesk\RVT 2027\Family Templates\English\Metric Generic Model.rft";
            }

            if (!File.Exists(templatePath))
            {
                return new { error = $"Family template not found: {templatePath}" };
            }

            var ifcFiles = Directory.GetFiles(ifcDir, "*.ifc");
            if (ifcFiles.Length == 0)
            {
                return new { message = "No .ifc files found in " + ifcDir, count = 0 };
            }

            var results = new List<object>();

            foreach (var ifcFile in ifcFiles)
            {
                string fileName = Path.GetFileNameWithoutExtension(ifcFile);
                string outputRfa = Path.Combine(outputDir, fileName + ".rfa");
                
                try
                {
                    var res = ConvertSingleIfcToRfa(uiapp, ifcFile, outputRfa, templatePath);
                    results.Add(res);
                }
                catch (Exception ex)
                {
                    results.Add(new { file = Path.GetFileName(ifcFile), success = false, error = ex.ToString() });
                }
            }

            return new { success = true, total = ifcFiles.Length, results };
        }

        public static object ConvertSingleIfcToRfa(UIApplication uiapp, string ifcFile, string outputRfa, string templatePath)
        {
            var app = uiapp.Application;
            string fileName = Path.GetFileNameWithoutExtension(ifcFile);
            string tempDir = Path.Combine(Path.GetTempPath(), "RevitIfcToRfa_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDir);

            Document? ifcDoc = null;
            Document? famDoc = null;

            try
            {
                // 1. Open the IFC file into a Revit project document
                ifcDoc = app.OpenIFCDocument(ifcFile);
                if (ifcDoc == null)
                {
                    return new { file = Path.GetFileName(ifcFile), success = false, error = "Failed to open IFC document." };
                }

                // Find a 3D view in the IFC document
                View3D? view3d = new FilteredElementCollector(ifcDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

                if (view3d == null)
                {
                    using (var tx = new Transaction(ifcDoc, "Create 3D View"))
                    {
                        tx.Start();
                        var viewFamilyType = new FilteredElementCollector(ifcDoc)
                            .OfClass(typeof(ViewFamilyType))
                            .Cast<ViewFamilyType>()
                            .FirstOrDefault(x => x.ViewFamily == ViewFamily.ThreeDimensional);
                        if (viewFamilyType != null)
                        {
                            view3d = View3D.CreateIsometric(ifcDoc, viewFamilyType.Id);
                        }
                        tx.Commit();
                    }
                }

                if (view3d == null)
                {
                    return new { file = Path.GetFileName(ifcFile), success = false, error = "Cannot find or create 3D view in IFC document." };
                }

                // 2. Export 3D View to SAT & DWG
                var viewIds = new List<ElementId> { view3d.Id };
                string satBaseName = "geom_" + fileName;
                
                var satExport = new SATExportOptions();
                ifcDoc.Export(tempDir, satBaseName, viewIds, satExport);

                var dwgExport = new DWGExportOptions
                {
                    FileVersion = ACADVersion.R2018,
                    ExportOfSolids = SolidGeometry.ACIS
                };
                ifcDoc.Export(tempDir, satBaseName, viewIds, dwgExport);

                // Collect any exported SAT or DWG
                string[] satFiles = Directory.GetFiles(tempDir, "*.sat");
                string satPath = satFiles.Length > 0 ? satFiles[0] : "";
                string[] dwgFiles = Directory.GetFiles(tempDir, "*.dwg");
                string dwgPath = dwgFiles.Length > 0 ? dwgFiles[0] : "";

                // Close IFC doc to save memory
                try { ifcDoc.Close(false); } catch { }
                ifcDoc = null;

                // 3. Create new Family Document from template
                famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null)
                {
                    return new { file = Path.GetFileName(ifcFile), success = false, error = "Failed to create new family document from template." };
                }

                // Set Category to Speciality Equipment or Generic Model
                using (var tx = new Transaction(famDoc, "Set Family Category"))
                {
                    tx.Start();
                    var category = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_SpecialityEquipment) 
                                   ?? famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                    if (category != null)
                    {
                        famDoc.OwnerFamily.FamilyCategory = category;
                    }
                    tx.Commit();
                }

                int solidCount = 0;

                // 4. Try importing SAT solids via ShapeImporter
                if (!string.IsNullOrEmpty(satPath) && File.Exists(satPath))
                {
                    try
                    {
                        using (var tx = new Transaction(famDoc, "Import SAT Solids"))
                        {
                            tx.Start();
                            var shapeImporter = new ShapeImporter();
                            var geomObjs = shapeImporter.Convert(famDoc, satPath);
                            if (geomObjs != null)
                            {
                                foreach (var obj in geomObjs)
                                {
                                    if (obj is Solid solid && solid.Volume > 1e-6)
                                    {
                                        FreeFormElement.Create(famDoc, solid);
                                        solidCount++;
                                    }
                                }
                            }
                            tx.Commit();
                        }
                    }
                    catch (Exception satEx)
                    {
                        System.Diagnostics.Debug.WriteLine("SAT import failed: " + satEx.Message);
                    }
                }

                // 5. Fallback: If no solids imported, import DWG into the family view
                if (solidCount == 0 && !string.IsNullOrEmpty(dwgPath) && File.Exists(dwgPath))
                {
                    View? targetView = famDoc.ActiveView ?? new FilteredElementCollector(famDoc)
                        .OfClass(typeof(View))
                        .Cast<View>()
                        .FirstOrDefault(v => !v.IsTemplate && (v.ViewType == ViewType.ThreeD || v.ViewType == ViewType.FloorPlan));

                    if (targetView != null)
                    {
                        using (var tx = new Transaction(famDoc, "Import DWG Geometry"))
                        {
                            tx.Start();
                            var dwgImport = new DWGImportOptions
                            {
                                Placement = ImportPlacement.Origin,
                                Unit = ImportUnit.Default,
                                AutoCorrectAlmostVHLines = true
                            };
                            if (famDoc.Import(dwgPath, dwgImport, targetView, out ElementId importedId))
                            {
                                solidCount = 1;
                            }
                            tx.Commit();
                        }
                    }
                }

                // 6. Save Family as .rfa
                var saveOptions = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(outputRfa, saveOptions);
                famDoc.Close(false);
                famDoc = null;

                return new
                {
                    file = Path.GetFileName(ifcFile),
                    rfa = outputRfa,
                    success = true,
                    solidCount
                };
            }
            finally
            {
                if (famDoc != null) { try { famDoc.Close(false); } catch { } }
                if (ifcDoc != null) { try { ifcDoc.Close(false); } catch { } }

                // Clean up temp dir
                try
                {
                    if (Directory.Exists(tempDir))
                    {
                        Directory.Delete(tempDir, true);
                    }
                }
                catch { }

                // Clean up any .ifc.RVT created next to the IFC file
                try
                {
                    string rvtNextToIfc = ifcFile + ".RVT";
                    if (File.Exists(rvtNextToIfc)) File.Delete(rvtNextToIfc);
                    string logNextToIfc = ifcFile + ".log.html";
                    if (File.Exists(logNextToIfc)) File.Delete(logNextToIfc);
                }
                catch { }
            }
        }
    }
}
