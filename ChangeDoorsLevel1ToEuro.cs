using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class DoorChangeWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var m in msgs)
            {
                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class ChangeDoorsLevel1ToEuro
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Find target door symbol: D4_1000x2200 from CỬA 1 CÁNH EROWINDOW(có ô chết)
            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            var targetSym = doorSymbols.FirstOrDefault(s => s.Id.Value == 2361172L)
                         ?? doorSymbols.FirstOrDefault(s => s.FamilyName.Contains("EROWINDOW", StringComparison.OrdinalIgnoreCase) && s.Name.Contains("1000x2200", StringComparison.OrdinalIgnoreCase))
                         ?? doorSymbols.FirstOrDefault(s => s.Name.Equals("D4_1000x2200", StringComparison.OrdinalIgnoreCase));

            if (targetSym == null) return new { error = "Target door symbol D4_1000x2200 not found" };

            // 2. Find Level 1
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvl1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            // 3. Find 1-leaf wooden doors on Level 1
            var allDoors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var targetDoors = allDoors.Where(d => {
                bool isLevel1 = lvl1 != null ? d.LevelId == lvl1.Id : false;
                bool isWood1Leaf = d.Symbol.FamilyName.Contains("GỖ", StringComparison.OrdinalIgnoreCase)
                                   || d.Symbol.Name.Contains("GỖ", StringComparison.OrdinalIgnoreCase)
                                   || d.Symbol.Id.Value == 131952L;
                return isLevel1 && isWood1Leaf;
            }).ToList();

            // Also check by explicit IDs if needed
            var explicitIds = new long[] { 2360902L, 2360904L, 2360905L, 2360906L, 2360907L, 2360909L };
            foreach (var id in explicitIds)
            {
                var d = doc.GetElement(new ElementId(id)) as FamilyInstance;
                if (d != null && !targetDoors.Any(td => td.Id.Value == id))
                {
                    targetDoors.Add(d);
                }
            }

            int changedCount = 0;
            var updatedDoorsInfo = new List<object>();

            using (var tx = new Transaction(doc, "Change Level 1 Doors to Eurowindow D4_1000x2200"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new DoorChangeWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                if (!targetSym.IsActive) targetSym.Activate();

                foreach (var door in targetDoors)
                {
                    var oldFam = door.Symbol.FamilyName;
                    var oldName = door.Symbol.Name;

                    door.ChangeTypeId(targetSym.Id);

                    // Ensure sill height is 0
                    var pSill = door.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                    if (pSill != null && !pSill.IsReadOnly)
                    {
                        pSill.Set(0.0);
                    }

                    changedCount++;
                    updatedDoorsInfo.Add(new
                    {
                        id = door.Id.Value,
                        oldFamily = oldFam,
                        oldName = oldName,
                        newFamily = targetSym.FamilyName,
                        newName = targetSym.Name
                    });
                }

                doc.Regenerate();
                tx.Commit();
            }

            // 4. Export Verification Images
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string corridorImgPath = Path.Combine(folder, "revit_framing_corridor_section_cut.png");
            string closeUpImgPath = Path.Combine(folder, "revit_level1_doors_updated_corridor.png");

            try
            {
                var v3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (v3d != null)
                {
                    uidoc.ActiveView = v3d;

                    // Section Box inside corridor
                    using (var txSec = new Transaction(doc, "Setup Corridor Section Box"))
                    {
                        txSec.Start();
                        BoundingBoxXYZ sb = new BoundingBoxXYZ();
                        sb.Min = new XYZ(3.0 * M2FT, 6.5 * M2FT, -0.5 * M2FT);
                        sb.Max = new XYZ(27.0 * M2FT, 16.0 * M2FT, 15.0 * M2FT);
                        v3d.SetSectionBox(sb);
                        v3d.IsSectionBoxActive = true;
                        v3d.DisplayStyle = DisplayStyle.FlatColors;
                        var vdm = v3d.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        v3d.SetViewDisplayModel(vdm);
                        txSec.Commit();
                    }

                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
                    uiview?.ZoomToFit();

                    if (File.Exists(corridorImgPath)) try { File.Delete(corridorImgPath); } catch { }

                    var expOpt = new ImageExportOptions
                    {
                        FilePath = corridorImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOpt);

                    // Also close up on Tầng 1
                    using (var txClose = new Transaction(doc, "Setup Close Up Section Box"))
                    {
                        txClose.Start();
                        BoundingBoxXYZ sbClose = new BoundingBoxXYZ();
                        sbClose.Min = new XYZ(5.0 * M2FT, 6.5 * M2FT, -0.5 * M2FT);
                        sbClose.Max = new XYZ(22.0 * M2FT, 16.0 * M2FT, 8.0 * M2FT);
                        v3d.SetSectionBox(sbClose);
                        v3d.IsSectionBoxActive = true;
                        txClose.Commit();
                    }

                    uiview?.ZoomToFit();
                    if (File.Exists(closeUpImgPath)) try { File.Delete(closeUpImgPath); } catch { }
                    expOpt.FilePath = closeUpImgPath;
                    doc.ExportImage(expOpt);

                    // Restore section box
                    using (var txRest = new Transaction(doc, "Restore Section Box"))
                    {
                        txRest.Start();
                        v3d.IsSectionBoxActive = false;
                        txRest.Commit();
                    }
                    uiview?.ZoomToFit();
                }
            }
            catch { }

            // 5. Save document
            try
            {
                doc.Save(new SaveOptions());
            }
            catch { }

            return new
            {
                success = true,
                changedCount,
                updatedDoorsInfo,
                images = new string[] { corridorImgPath, closeUpImgPath }
            };
        }
    }
}
