using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SyncWarningSwallower : IFailuresPreprocessor
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

    public class SyncFamilyLoadOptions : IFamilyLoadOptions
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

    public static class Sync3dsMaxToRevitFamily
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double FT2MM = 304.8;

        /// <summary>
        /// Nạp hình học từ file trung gian (.sat hoặc .dwg) vào Family Document.
        /// Ưu tiên chuyển đổi sang FreeFormElement (B-Rep Solid chuẩn Revit) để hỗ trợ cắt lát 2D và mặt cắt.
        /// </summary>
        private static (int ffeCount, int impCount) ImportGeometryIntoFamily(Document famDoc, string filePath)
        {
            // 1. Dọn dẹp các đối tượng cũ nếu có
            var existingFfes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(FreeFormElement))
                .Cast<FreeFormElement>()
                .ToList();

            foreach (var f in existingFfes)
            {
                try { famDoc.Delete(f.Id); } catch { }
            }

            var existingImports = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .ToList();

            foreach (var imp in existingImports)
            {
                try
                {
                    imp.Pinned = false;
                    famDoc.Delete(imp.Id);
                }
                catch { }
            }

            // 2. Chuẩn bị vật liệu trắng mặt phẳng, nét đen sắc nét
            var whiteMat = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Material))
                .Cast<Material>()
                .FirstOrDefault(m => m.Name.Contains("Đồng Bộ") || m.Name.Contains("Trắng"));

            if (whiteMat == null)
            {
                var matId = Material.Create(famDoc, "Vật liệu Đồng Bộ (Trắng)");
                whiteMat = (Material)famDoc.GetElement(matId);
                whiteMat.Color = new Color(255, 255, 255);
            }

            View3D? famView3D = new FilteredElementCollector(famDoc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            View targetView = (View?)famView3D ?? famDoc.ActiveView ?? new FilteredElementCollector(famDoc).OfClass(typeof(View)).Cast<View>().FirstOrDefault(v => !v.IsTemplate);

            bool isSat = filePath.EndsWith(".sat", StringComparison.OrdinalIgnoreCase);
            ElementId importedId = ElementId.InvalidElementId;
            List<FreeFormElement> createdFfes = new List<FreeFormElement>();

            if (isSat)
            {
                var satOpt = new SATImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Millimeter,
                    ColorMode = ImportColorMode.BlackAndWhite,
                    ThisViewOnly = false
                };
                importedId = famDoc.Import(filePath, satOpt, targetView);
            }
            else
            {
                var dwgOpt = new DWGImportOptions
                {
                    Placement = ImportPlacement.Origin,
                    Unit = ImportUnit.Millimeter,
                    ColorMode = ImportColorMode.BlackAndWhite,
                    AutoCorrectAlmostVHLines = false,
                    ThisViewOnly = false
                };
                famDoc.Import(filePath, dwgOpt, targetView, out importedId);
            }

            if (importedId != ElementId.InvalidElementId)
            {
                var impElem = famDoc.GetElement(importedId) as ImportInstance;
                if (impElem != null)
                {
                    if (isSat)
                    {
                        var geom = impElem.get_Geometry(new Options { ComputeReferences = true, DetailLevel = ViewDetailLevel.Fine });
                        List<Solid> solids = new List<Solid>();

                        Action<GeometryElement> collectSolids = null;
                        collectSolids = (gElem) =>
                        {
                            if (gElem == null) return;
                            foreach (var gObj in gElem)
                            {
                                if (gObj is Solid s && s.Volume > 1e-6)
                                {
                                    solids.Add(s);
                                }
                                else if (gObj is GeometryInstance gi)
                                {
                                    collectSolids(gi.GetInstanceGeometry());
                                }
                            }
                        };

                        collectSolids(geom);

                        foreach (var s in solids)
                        {
                            try
                            {
                                FreeFormElement ffe = FreeFormElement.Create(famDoc, s);
                                if (ffe != null)
                                {
                                    var matParam = ffe.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM);
                                    if (matParam != null && !matParam.IsReadOnly && whiteMat != null)
                                    {
                                        matParam.Set(whiteMat.Id);
                                    }
                                    createdFfes.Add(ffe);
                                }
                            }
                            catch { }
                        }

                        // Nếu đã chuyển đổi thành công sang FreeFormElement Solid nguyên bản, xóa ImportInstance tạm
                        if (createdFfes.Count > 0)
                        {
                            try
                            {
                                impElem.Pinned = false;
                                famDoc.Delete(importedId);
                                importedId = ElementId.InvalidElementId;
                            }
                            catch { }
                        }
                    }

                    // Fallback cho DWG hoặc trường hợp SAT không tạo được Solid
                    if (importedId != ElementId.InvalidElementId)
                    {
                        var importCat = famDoc.Settings.Categories.Cast<Category>()
                            .FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));

                        if (importCat != null)
                        {
                            foreach (Category sub in importCat.SubCategories)
                            {
                                sub.Material = whiteMat;
                                sub.LineColor = new Color(0, 0, 0);
                            }
                        }
                    }
                }
            }

            if (famView3D != null)
            {
                famView3D.DisplayStyle = DisplayStyle.FlatColors;
                var vdm = famView3D.GetViewDisplayModel();
                vdm.SmoothEdges = true;
                famView3D.SetViewDisplayModel(vdm);
            }

            int finalFfeCount = new FilteredElementCollector(famDoc).OfClass(typeof(FreeFormElement)).Count();
            int finalImpCount = new FilteredElementCollector(famDoc).OfClass(typeof(ImportInstance)).Count();
            return (finalFfeCount, finalImpCount);
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            string tempDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp";
            string defaultSat = Path.Combine(tempDir, "Sync_3dsMax_To_Revit.sat");
            string defaultDwg = Path.Combine(tempDir, "Sync_3dsMax_To_Revit.dwg");
            string filePath = File.Exists(defaultSat) ? defaultSat : defaultDwg;
            string maxObjName = "3dsMax_Object";
            bool checkOnly = false;
            bool createNewFamily = false;
            string newFamilyName = "";

            var targetArgs = args.ValueKind == JsonValueKind.Object && args.TryGetProperty("args", out var innerArgs) && innerArgs.ValueKind == JsonValueKind.Object ? innerArgs : args;

            if (targetArgs.ValueKind == JsonValueKind.Object)
            {
                if (targetArgs.TryGetProperty("checkOnly", out var pCheck)) checkOnly = pCheck.GetBoolean();
                else if (args.TryGetProperty("checkOnly", out var pCheck2)) checkOnly = pCheck2.GetBoolean();

                if (targetArgs.TryGetProperty("createNewFamily", out var pCreate)) createNewFamily = pCreate.GetBoolean();
                else if (args.TryGetProperty("createNewFamily", out var pCreate2)) createNewFamily = pCreate2.GetBoolean();

                if (targetArgs.TryGetProperty("newFamilyName", out var pNewName)) newFamilyName = pNewName.GetString() ?? "";
                else if (args.TryGetProperty("newFamilyName", out var pNewName2)) newFamilyName = pNewName2.GetString() ?? "";

                if (targetArgs.TryGetProperty("filePath", out var pFile)) filePath = pFile.GetString() ?? filePath;
                else if (args.TryGetProperty("filePath", out var pFile2)) filePath = pFile2.GetString() ?? filePath;
                else if (targetArgs.TryGetProperty("satPath", out var pSat)) filePath = pSat.GetString() ?? filePath;
                else if (args.TryGetProperty("satPath", out var pSat2)) filePath = pSat2.GetString() ?? filePath;
                else if (targetArgs.TryGetProperty("dwgPath", out var pDwg)) filePath = pDwg.GetString() ?? filePath;
                else if (args.TryGetProperty("dwgPath", out var pDwg2)) filePath = pDwg2.GetString() ?? filePath;

                if (targetArgs.TryGetProperty("maxObjectName", out var pName)) maxObjName = pName.GetString() ?? maxObjName;
                else if (args.TryGetProperty("maxObjectName", out var pName2)) maxObjName = pName2.GetString() ?? maxObjName;
            }

            // 1. Chế độ kiểm tra nhanh Selection (checkOnly)
            if (checkOnly)
            {
                var checkSelIds = uidoc.Selection.GetElementIds();
                if (checkSelIds == null || checkSelIds.Count == 0)
                {
                    return new
                    {
                        success = true,
                        hasSelection = false,
                        isEditableFamily = false,
                        message = "Chưa chọn đối tượng nào trong Revit."
                    };
                }

                FamilyInstance? checkInst = null;
                foreach (var id in checkSelIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem is FamilyInstance fi && fi.Symbol?.Family != null && fi.Symbol.Family.IsEditable)
                    {
                        checkInst = fi;
                        break;
                    }
                }

                if (checkInst != null)
                {
                    return new
                    {
                        success = true,
                        hasSelection = true,
                        isEditableFamily = true,
                        instanceId = checkInst.Id.Value,
                        familyName = checkInst.Symbol.Family.Name,
                        category = checkInst.Category?.Name ?? "Family"
                    };
                }
                else
                {
                    var firstElem = doc.GetElement(checkSelIds.First());
                    return new
                    {
                        success = true,
                        hasSelection = true,
                        isEditableFamily = false,
                        elementId = checkSelIds.First().Value,
                        category = firstElem?.Category?.Name ?? "Đối tượng",
                        message = "Đối tượng đang chọn không phải là Family có thể chỉnh sửa (.rfa)."
                    };
                }
            }

            // 2. Chế độ TẠO MỚI FAMILY (createNewFamily == true)
            if (createNewFamily)
            {
                if (!File.Exists(filePath))
                {
                    return new { success = false, error = "Không tìm thấy file hình học xuất từ 3ds Max: " + filePath };
                }

                string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
                if (!File.Exists(templatePath))
                {
                    string baseDir = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates";
                    if (Directory.Exists(baseDir))
                    {
                        var found = Directory.GetFiles(baseDir, "*Metric Generic Model*.rft", SearchOption.AllDirectories)
                            .FirstOrDefault(f => !f.Contains("based") && !f.Contains("Adaptive"));
                        if (found != null) templatePath = found;
                    }
                }

                if (!File.Exists(templatePath))
                {
                    return new { success = false, error = "Không tìm thấy file Family Template 'Metric Generic Model.rft'!" };
                }

                Document newFamDoc = app.NewFamilyDocument(templatePath);
                if (newFamDoc == null)
                {
                    return new { success = false, error = "Không thể tạo tài liệu Family mới từ template!" };
                }

                try
                {
                    (int ffeCount, int impCount) importCounts = (0, 0);
                    using (var tx = new Transaction(newFamDoc, "Import 3dsMax Geometry into New Family"))
                    {
                        var opt = tx.GetFailureHandlingOptions();
                        opt.SetFailuresPreprocessor(new SyncWarningSwallower());
                        tx.SetFailureHandlingOptions(opt);
                        tx.Start();

                        var cat = newFamDoc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
                        if (cat != null) newFamDoc.OwnerFamily.FamilyCategory = cat;

                        var cutVoidParam = newFamDoc.OwnerFamily.get_Parameter(BuiltInParameter.FAMILY_ALLOW_CUT_WITH_VOIDS);
                        if (cutVoidParam != null && !cutVoidParam.IsReadOnly)
                        {
                            cutVoidParam.Set(1);
                        }

                        importCounts = ImportGeometryIntoFamily(newFamDoc, filePath);

                        tx.Commit();
                    }

                    string safeFamName = string.IsNullOrWhiteSpace(newFamilyName) ? $"Family_{maxObjName}" : newFamilyName.Trim();
                    foreach (char c in Path.GetInvalidFileNameChars())
                    {
                        safeFamName = safeFamName.Replace(c, '_');
                    }
                    string rfaDir = @"D:\Dropbox\_Documents\RevitAI";
                    string rfaPath = Path.Combine(rfaDir, $"{safeFamName}.rfa");

                    var saveOpt = new SaveAsOptions { OverwriteExistingFile = true };
                    newFamDoc.SaveAs(rfaPath, saveOpt);

                    Family loadedFam = newFamDoc.LoadFamily(doc, new SyncFamilyLoadOptions());
                    newFamDoc.Close(false);

                    long newInstId = -1;
                    if (loadedFam != null)
                    {
                        using (var tx = new Transaction(doc, $"Place New Family {safeFamName}"))
                        {
                            var opt = tx.GetFailureHandlingOptions();
                            opt.SetFailuresPreprocessor(new SyncWarningSwallower());
                            tx.SetFailureHandlingOptions(opt);
                            tx.Start();

                            var symbolId = loadedFam.GetFamilySymbolIds().FirstOrDefault();
                            if (symbolId != null)
                            {
                                var symbol = doc.GetElement(symbolId) as FamilySymbol;
                                if (symbol != null)
                                {
                                    if (!symbol.IsActive) symbol.Activate();

                                    XYZ placePt = XYZ.Zero;
                                    Level? targetLevel = null;

                                    if (uidoc.ActiveView is ViewPlan vp && vp.GenLevel != null)
                                    {
                                        targetLevel = vp.GenLevel;
                                    }
                                    else
                                    {
                                        targetLevel = new FilteredElementCollector(doc)
                                            .OfClass(typeof(Level))
                                            .Cast<Level>()
                                            .OrderBy(l => l.Elevation)
                                            .FirstOrDefault();
                                    }

                                    FamilyInstance newInst;
                                    try
                                    {
                                        if (targetLevel != null)
                                            newInst = doc.Create.NewFamilyInstance(placePt, symbol, targetLevel, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                                        else
                                            newInst = doc.Create.NewFamilyInstance(placePt, symbol, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                                    }
                                    catch
                                    {
                                        newInst = doc.Create.NewFamilyInstance(placePt, symbol, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                                    }

                                    newInstId = newInst.Id.Value;
                                    doc.Regenerate();

                                    var activeV3d = uidoc.ActiveView as View3D;
                                    if (activeV3d != null)
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
                                        activeV3d.SetElementOverrides(newInst.Id, ogs);
                                    }

                                    tx.Commit();
                                    uidoc.Selection.SetElementIds(new List<ElementId> { newInst.Id });
                                }
                            }
                        }
                    }

                    bool isSat = filePath.EndsWith(".sat", StringComparison.OrdinalIgnoreCase);
                    return new
                    {
                        success = true,
                        isNewFamily = true,
                        maxObjectName = maxObjName,
                        revitFamilyName = safeFamName,
                        instanceId = newInstId,
                        rfaPath,
                        filePath,
                        format = isSat ? "SAT (FreeFormElement Solid)" : "DWG",
                        freeFormCount = importCounts.ffeCount,
                        importInstanceCount = importCounts.impCount
                    };
                }
                catch (Exception ex)
                {
                    try { newFamDoc.Close(false); } catch {}
                    return new { success = false, error = "Lỗi khi tạo Family mới: " + ex.Message };
                }
            }

            // 3. Chế độ CẬP NHẬT FAMILY HIỆN CÓ
            if (!File.Exists(filePath))
            {
                return new { success = false, error = "Không tìm thấy file hình học xuất từ 3ds Max: " + filePath };
            }

            var selIds = uidoc.Selection.GetElementIds();
            if (selIds == null || selIds.Count == 0)
            {
                return new
                {
                    success = false,
                    needCreateNew = true,
                    hasSelection = false,
                    isEditableFamily = false,
                    error = "Không có đối tượng nào đang được chọn trong Revit."
                };
            }

            FamilyInstance? targetInst = null;
            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem is FamilyInstance fi && fi.Symbol?.Family != null && fi.Symbol.Family.IsEditable)
                {
                    targetInst = fi;
                    break;
                }
            }

            if (targetInst == null)
            {
                var firstElem = doc.GetElement(selIds.First());
                string catName = firstElem?.Category?.Name ?? "Đối tượng";
                return new
                {
                    success = false,
                    needCreateNew = true,
                    hasSelection = true,
                    isEditableFamily = false,
                    elementId = selIds.First().Value,
                    category = catName,
                    error = $"Đối tượng bạn đang chọn (ID: {selIds.First().Value} - {catName}) không phải là một Family có thể chỉnh sửa (.rfa)."
                };
            }

            var fam = targetInst.Symbol.Family;
            string famName = fam.Name;
            var lp = targetInst.Location as LocationPoint;
            XYZ origin = lp != null ? lp.Point : XYZ.Zero;
            double rotation = lp != null ? lp.Rotation : 0.0;
            var targetInstId = targetInst.Id;

            // 2. Edit existing Family directly
            Document famDoc = doc.EditFamily(fam);
            if (famDoc == null)
            {
                return new { success = false, error = "Không thể mở family để cập nhật: " + famName };
            }

            try
            {
                (int ffeCount, int impCount) updateCounts = (0, 0);
                using (var tx = new Transaction(famDoc, "Update 3dsMax Geometry into Family"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new SyncWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    var cutVoidParam = famDoc.OwnerFamily.get_Parameter(BuiltInParameter.FAMILY_ALLOW_CUT_WITH_VOIDS);
                    if (cutVoidParam != null && !cutVoidParam.IsReadOnly)
                    {
                        cutVoidParam.Set(1);
                    }

                    updateCounts = ImportGeometryIntoFamily(famDoc, filePath);

                    tx.Commit();
                }

                // 3. Load family back into document with SyncFamilyLoadOptions
                Family loadedFam = famDoc.LoadFamily(doc, new SyncFamilyLoadOptions());
            }
            finally
            {
                famDoc.Close(false);
            }

            // 4. Regenerate and update graphics
            using (var tx = new Transaction(doc, $"Regen {famName}"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SyncWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();
                doc.Regenerate();

                var activeV3d = uidoc.ActiveView as View3D;
                if (activeV3d != null && targetInst != null)
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
                    activeV3d.SetElementOverrides(targetInst.Id, ogs);
                }
                tx.Commit();
            }

            // Reselect the instance
            try
            {
                uidoc.Selection.SetElementIds(new List<ElementId> { targetInstId });
            }
            catch {}

            bool isSatFile = filePath.EndsWith(".sat", StringComparison.OrdinalIgnoreCase);
            return new
            {
                success = true,
                maxObjectName = maxObjName,
                revitFamilyName = famName,
                instanceId = targetInstId.Value,
                filePath,
                format = isSatFile ? "SAT (FreeFormElement Solid)" : "DWG"
            };
        }
    }
}
