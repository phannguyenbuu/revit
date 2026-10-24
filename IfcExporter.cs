using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class IfcExporter
    {
        public static object ExportToIfc(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine";
            string rvtPath = Path.Combine(outDir, "foundation_export.rvt");
            string rfaPath = Path.Combine(outDir, "Infartsskylt_recolor.rfa");
            string revitVer = app.VersionNumber;
            string templatePath = $@"C:\ProgramData\Autodesk\RVT {revitVer}\Templates\English\DefaultMetric.rte";

            var results = new Dictionary<string, object>();

            // Setup IFC 2x3 options
            var ifcOpt = new IFCExportOptions
            {
                FileVersion = IFCVersion.IFC2x3CV2,
                ExportBaseQuantities = true,
                WallAndColumnSplitting = false
            };

            // 1. Export foundation_export.rvt
            try
            {
                var rvtDoc = app.OpenDocumentFile(rvtPath);
                string rvtBaseName = "foundation_export";
                
                // Check if {3D} view exists
                var view3d = new FilteredElementCollector(rvtDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name == "{3D}")
                    ?? new FilteredElementCollector(rvtDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    ifcOpt.FilterViewId = view3d.Id;
                }

                using (var tx = new Transaction(rvtDoc, "Export IFC"))
                {
                    tx.Start();
                    rvtDoc.Export(outDir, rvtBaseName, ifcOpt);
                    tx.Commit();
                }
                rvtDoc.Close(false);

                // Handle double extension if created
                FixIfcExtensions(outDir, rvtBaseName);

                string expectedIfc = Path.Combine(outDir, rvtBaseName + ".ifc");
                var fi = new FileInfo(expectedIfc);
                results["foundation_export.rvt"] = new
                {
                    success = fi.Exists,
                    path = expectedIfc,
                    sizeBytes = fi.Exists ? fi.Length : 0,
                    lastModified = fi.Exists ? fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss") : null
                };
            }
            catch (Exception ex)
            {
                results["foundation_export.rvt"] = new
                {
                    success = false,
                    error = ex.ToString()
                };
            }

            // 2. Export Infartsskylt_recolor.rfa
            try
            {
                Document projDoc;
                if (File.Exists(templatePath))
                {
                    projDoc = app.NewProjectDocument(templatePath);
                }
                else
                {
                    projDoc = app.NewProjectDocument(UnitSystem.Metric);
                }

                string rfaBaseName = "Infartsskylt_recolor";

                using (var tx = new Transaction(projDoc, "Load and Place Family"))
                {
                    tx.Start();
                    bool loaded = projDoc.LoadFamily(rfaPath, out Family family);
                    if (family == null)
                    {
                        family = new FilteredElementCollector(projDoc)
                            .OfClass(typeof(Family))
                            .Cast<Family>()
                            .FirstOrDefault(f => f.Name == rfaBaseName);
                    }

                    if (family == null)
                    {
                        throw new InvalidOperationException("Failed to load family into project document.");
                    }

                    var symbolId = family.GetFamilySymbolIds().FirstOrDefault();
                    if (symbolId == null)
                    {
                        throw new InvalidOperationException("No symbols found in loaded family.");
                    }

                    var symbol = (FamilySymbol)projDoc.GetElement(symbolId);
                    if (!symbol.IsActive)
                    {
                        symbol.Activate();
                    }
                    projDoc.Regenerate();

                    var level = new FilteredElementCollector(projDoc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .FirstOrDefault();

                    FamilyInstance inst;
                    if (level != null)
                    {
                        inst = projDoc.Create.NewFamilyInstance(XYZ.Zero, symbol, level, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    }
                    else
                    {
                        inst = projDoc.Create.NewFamilyInstance(XYZ.Zero, symbol, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    }

                    tx.Commit();
                }

                // Find 3D view in projDoc
                var projView3d = new FilteredElementCollector(projDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

                if (projView3d == null)
                {
                    using (var tx = new Transaction(projDoc, "Create 3D View"))
                    {
                        tx.Start();
                        var vft = new FilteredElementCollector(projDoc)
                            .OfClass(typeof(ViewFamilyType))
                            .Cast<ViewFamilyType>()
                            .FirstOrDefault(x => x.ViewFamily == ViewFamily.ThreeDimensional);
                        if (vft != null)
                        {
                            projView3d = View3D.CreateIsometric(projDoc, vft.Id);
                        }
                        tx.Commit();
                    }
                }

                var rfaIfcOpt = new IFCExportOptions
                {
                    FileVersion = IFCVersion.IFC2x3CV2,
                    ExportBaseQuantities = true,
                    WallAndColumnSplitting = false
                };
                if (projView3d != null)
                {
                    rfaIfcOpt.FilterViewId = projView3d.Id;
                }

                using (var tx = new Transaction(projDoc, "Export IFC"))
                {
                    tx.Start();
                    projDoc.Export(outDir, rfaBaseName, rfaIfcOpt);
                    tx.Commit();
                }
                projDoc.Close(false);

                // Handle double extension if created
                FixIfcExtensions(outDir, rfaBaseName);

                string expectedIfc = Path.Combine(outDir, rfaBaseName + ".ifc");
                var fi = new FileInfo(expectedIfc);
                results["Infartsskylt_recolor.rfa"] = new
                {
                    success = fi.Exists,
                    path = expectedIfc,
                    sizeBytes = fi.Exists ? fi.Length : 0,
                    lastModified = fi.Exists ? fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss") : null
                };
            }
            catch (Exception ex)
            {
                results["Infartsskylt_recolor.rfa"] = new
                {
                    success = false,
                    error = ex.ToString()
                };
            }

            return results;
        }

        private static void FixIfcExtensions(string dir, string baseName)
        {
            string doubleExt = Path.Combine(dir, baseName + ".ifc.ifc");
            string singleExt = Path.Combine(dir, baseName + ".ifc");
            if (File.Exists(doubleExt))
            {
                if (File.Exists(singleExt))
                {
                    File.Delete(singleExt);
                }
                File.Move(doubleExt, singleExt);
            }
        }
    }
}
