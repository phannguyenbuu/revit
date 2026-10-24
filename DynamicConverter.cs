using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class WarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            failuresAccessor.DeleteAllWarnings();
            return FailureProcessingResult.Continue;
        }
    }

    public static class Script
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string dxfPath = args.GetProperty("dxfPath").GetString()!;
            string rfaPath = args.GetProperty("rfaPath").GetString()!;
            string templatePath = args.TryGetProperty("templatePath", out var tp) ? tp.GetString()! : @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            if (!File.Exists(templatePath))
            {
                templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            }

            var app = uiapp.Application;
            var famDoc = app.NewFamilyDocument(templatePath);

            View? targetView = famDoc.ActiveView ?? new FilteredElementCollector(famDoc)
                .OfClass(typeof(View))
                .Cast<View>()
                .FirstOrDefault(v => !v.IsTemplate && (v.ViewType == ViewType.ThreeD || v.ViewType == ViewType.FloorPlan));

            if (targetView == null)
            {
                famDoc.Close(false);
                return new { error = "No view found in family document" };
            }

            using (var tx = new Transaction(famDoc, "Import DXF Mesh"))
            {
                var failOpts = tx.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new WarningSwallower());
                failOpts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(failOpts);

                tx.Start();
                var cat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_SpecialityEquipment) 
                          ?? famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                if (cat != null) famDoc.OwnerFamily.FamilyCategory = cat;

                var opt = new DWGImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Default,
                    ColorMode = ImportColorMode.Preserved,
                    AutoCorrectAlmostVHLines = false
                };

                famDoc.Import(dxfPath, opt, targetView, out ElementId importedId);
                tx.Commit();
            }

            famDoc.SaveAs(rfaPath, new SaveAsOptions { OverwriteExistingFile = true });
            famDoc.Close(false);

            return new { success = true, rfa = rfaPath };
        }
        public static object InspectAndExport(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            string outputDir = args.GetProperty("outputDir").GetString()!;
            string baseName = args.GetProperty("baseName").GetString()!;
            Directory.CreateDirectory(outputDir);

            // Find views
            var view3D = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            var viewIds = new System.Collections.Generic.List<ElementId>();
            if (view3D != null) viewIds.Add(view3D.Id);

            // Export SAT
            bool satOk = false;
            string satError = "";
            try
            {
                var satOpts = new SATExportOptions();
                if (viewIds.Count > 0)
                {
                    satOk = doc.Export(outputDir, baseName, viewIds, satOpts);
                }
            }
            catch (Exception ex)
            {
                satError = ex.Message;
            }

            // Export DWG
            bool dwgOk = false;
            string dwgError = "";
            try
            {
                var dwgOpts = new DWGExportOptions
                {
                    FileVersion = ACADVersion.R2018,
                    ExportOfSolids = SolidGeometry.ACIS
                };
                if (viewIds.Count > 0)
                {
                    dwgOk = doc.Export(outputDir, baseName, viewIds, dwgOpts);
                }
            }
            catch (Exception ex)
            {
                dwgError = ex.Message;
            }

            // Get all user elements (non-system internal)
            var userElements = new FilteredElementCollector(doc)
                .WhereElementIsNotElementType()
                .Select(e => new
                {
                    id = e.Id.Value,
                    name = e.Name,
                    type = e.GetType().Name,
                    category = e.Category?.Name
                })
                .ToList();

            return new
            {
                title = doc.Title,
                path = doc.PathName,
                isFamily = doc.IsFamilyDocument,
                view3D = view3D?.Name,
                satOk,
                satError,
                dwgOk,
                dwgError,
                outputDir,
                elements = userElements
            };
        }

        public static object InspectFamily(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var materials = new FilteredElementCollector(doc)
                .OfClass(typeof(Material))
                .Cast<Material>()
                .Select(m => new
                {
                    id = m.Id.Value,
                    name = m.Name,
                    color = m.Color != null ? $"RGB({m.Color.Red},{m.Color.Green},{m.Color.Blue})" : null,
                    transparency = m.Transparency
                })
                .ToList();

            var forms = new FilteredElementCollector(doc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f =>
                {
                    var matParam = f.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM);
                    var matId = matParam?.AsElementId();
                    var mat = matId != null && matId != ElementId.InvalidElementId ? doc.GetElement(matId) as Material : null;
                    var bbox = f.get_BoundingBox(null);
                    return new
                    {
                        id = f.Id.Value,
                        name = f.Name,
                        formType = f.GetType().Name,
                        isSolid = f.IsSolid,
                        subCategory = f.Subcategory?.Name,
                        materialId = matId?.Value,
                        materialName = mat?.Name,
                        materialColor = mat?.Color != null ? $"RGB({mat.Color.Red},{mat.Color.Green},{mat.Color.Blue})" : null,
                        bboxMin = bbox != null ? new { x = Math.Round(bbox.Min.X * 304.8, 1), y = Math.Round(bbox.Min.Y * 304.8, 1), z = Math.Round(bbox.Min.Z * 304.8, 1) } : null,
                        bboxMax = bbox != null ? new { x = Math.Round(bbox.Max.X * 304.8, 1), y = Math.Round(bbox.Max.Y * 304.8, 1), z = Math.Round(bbox.Max.Z * 304.8, 1) } : null
                    };
                })
                .ToList();

            var familyParams = new System.Collections.Generic.List<object>();
            if (doc.IsFamilyDocument)
            {
                var fm = doc.FamilyManager;
                foreach (FamilyParameter fp in fm.Parameters)
                {
                    familyParams.Add(new
                    {
                        name = fp.Definition.Name,
                        storageType = fp.StorageType.ToString(),
                        formula = fp.Formula,
                        isDeterminedByFormula = fp.IsDeterminedByFormula
                    });
                }
            }

            var subCats = new System.Collections.Generic.List<object>();
            if (doc.IsFamilyDocument && doc.OwnerFamily?.FamilyCategory != null)
            {
                foreach (Category sub in doc.OwnerFamily.FamilyCategory.SubCategories)
                {
                    subCats.Add(new
                    {
                        name = sub.Name,
                        material = sub.Material?.Name,
                        lineColor = sub.LineColor != null ? $"RGB({sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue})" : null
                    });
                }
            }

            return new
            {
                title = doc.Title,
                materials,
                forms,
                familyParams,
                subCats
            };
        }

        public static object InspectSavedFamily(UIApplication uiapp, JsonElement args)
        {
            string rfaPath = args.GetProperty("rfaPath").GetString()!;
            var app = uiapp.Application;
            var doc = app.OpenDocumentFile(rfaPath);
            var subCats = new System.Collections.Generic.List<object>();
            if (doc.OwnerFamily?.FamilyCategory != null)
            {
                foreach (Category sub in doc.OwnerFamily.FamilyCategory.SubCategories)
                {
                    subCats.Add(new
                    {
                        name = sub.Name,
                        material = sub.Material?.Name,
                        lineColor = sub.LineColor != null ? $"RGB({sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue})" : null
                    });
                }
            }
            var importInstances = new FilteredElementCollector(doc).OfClass(typeof(ImportInstance)).Cast<ImportInstance>().ToList();
            var firstImport = importInstances.FirstOrDefault();
            var bbox = firstImport?.get_BoundingBox(null);
            var mats = new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>().Select(m => new { name = m.Name, color = m.Color != null ? $"RGB({m.Color.Red},{m.Color.Green},{m.Color.Blue})" : null }).ToList();
            
            var result = new
            {
                rfa = rfaPath,
                revitVersion = $"{app.VersionNumber} ({app.VersionName})",
                familyCategory = doc.OwnerFamily?.FamilyCategory?.Name,
                importsCount = importInstances.Count,
                bboxMm = bbox != null ? new
                {
                    minX = Math.Round(bbox.Min.X * 304.8, 1),
                    minY = Math.Round(bbox.Min.Y * 304.8, 1),
                    minZ = Math.Round(bbox.Min.Z * 304.8, 1),
                    maxX = Math.Round(bbox.Max.X * 304.8, 1),
                    maxY = Math.Round(bbox.Max.Y * 304.8, 1),
                    maxZ = Math.Round(bbox.Max.Z * 304.8, 1),
                    widthX = Math.Round((bbox.Max.X - bbox.Min.X) * 304.8, 1),
                    depthY = Math.Round((bbox.Max.Y - bbox.Min.Y) * 304.8, 1),
                    heightZ = Math.Round((bbox.Max.Z - bbox.Min.Z) * 304.8, 1)
                } : null,
                materialsCount = mats.Count
            };
            doc.Close(false);
            return result;
        }
    }
}
