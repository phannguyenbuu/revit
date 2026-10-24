using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SectionCutWarningSwallower : IFailuresPreprocessor
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

    public static class SetFloorSectionCutStyle
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            List<string> logs = new List<string>();

            var floorCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Floors);
            var beamCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralFraming);
            var colCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_StructuralColumns);

            // Find solid fill pattern
            var solidPattern = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .FirstOrDefault(f => f.GetFillPattern().IsSolidFill);

            if (solidPattern == null) return new { error = "Solid fill pattern not found" };

            Color beamGrayColor = new Color(128, 128, 128);

            using (var tx = new Transaction(doc, "Set Floor Section Cut Style Matching Beam"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SectionCutWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                // 1. Update Object Styles for OST_Floors
                if (floorCat != null)
                {
                    try
                    {
                        // Match beam cut line weight = 4
                        floorCat.SetLineWeight(4, GraphicsStyleType.Cut);
                        floorCat.LineColor = new Color(0, 0, 0);
                        logs.Add("Set OST_Floors Object Style: Cut Line Weight = 4, Line Color = Black");
                    }
                    catch (Exception ex)
                    {
                        logs.Add("Error setting floorCat object style: " + ex.Message);
                    }
                }

                // 2. Also inspect and update Floor Material Cut Pattern if desired
                var sampleFloor = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .FirstOrDefault();

                if (sampleFloor != null)
                {
                    foreach (var mid in sampleFloor.GetMaterialIds(false))
                    {
                        var mat = doc.GetElement(mid) as Material;
                        if (mat != null)
                        {
                            try
                            {
                                mat.CutForegroundPatternId = solidPattern.Id;
                                mat.CutForegroundPatternColor = beamGrayColor;
                                logs.Add($"Updated floor material {mat.Name}: Cut Foreground Pattern = Solid Fill (128,128,128)");
                            }
                            catch (Exception ex)
                            {
                                logs.Add($"Could not update material {mat.Name}: {ex.Message}");
                            }
                        }
                    }
                }

                // 3. Update all Section and Detail Views
                var sectionViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .Where(v => !v.IsTemplate)
                    .ToList();

                foreach (var v in sectionViews)
                {
                    try
                    {
                        var beamOvr = v.GetCategoryOverrides(beamCat.Id);
                        var ovr = v.GetCategoryOverrides(floorCat.Id) ?? new OverrideGraphicSettings();

                        // Set Cut Line Weight = 4 (bold)
                        ovr.SetCutLineWeight(4);
                        ovr.SetCutLineColor(new Color(0, 0, 0));

                        // Set Cut Foreground Pattern = Solid Fill with color 128, 128, 128 (same as beam)
                        ovr.SetCutForegroundPatternId(solidPattern.Id);
                        ovr.SetCutForegroundPatternColor(beamGrayColor);
                        ovr.SetCutForegroundPatternVisible(true);

                        v.SetCategoryOverrides(floorCat.Id, ovr);
                        logs.Add($"Applied floor cut override in view '{v.Name}' (ID {v.Id.Value}): CutLineWeight=4, SolidFill(128,128,128)");
                    }
                    catch (Exception ex)
                    {
                        logs.Add($"Error overriding view {v.Name}: {ex.Message}");
                    }
                }

                // Optional: Attempt to join Floors and Beams to eliminate seam lines between them
                int joinedCount = 0;
                var allFloors = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .ToList();

                var allBeams = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilyInstance))
                    .OfCategory(BuiltInCategory.OST_StructuralFraming)
                    .Cast<FamilyInstance>()
                    .ToList();

                foreach (var fl in allFloors)
                {
                    var flBb = fl.get_BoundingBox(null);
                    if (flBb == null) continue;

                    var outline = new Outline(flBb.Min, flBb.Max);
                    var filter = new BoundingBoxIntersectsFilter(outline);

                    var candidateBeams = new FilteredElementCollector(doc)
                        .OfClass(typeof(FamilyInstance))
                        .OfCategory(BuiltInCategory.OST_StructuralFraming)
                        .WherePasses(filter)
                        .Cast<FamilyInstance>();

                    foreach (var bm in candidateBeams)
                    {
                        try
                        {
                            if (!JoinGeometryUtils.AreElementsJoined(doc, fl, bm))
                            {
                                JoinGeometryUtils.JoinGeometry(doc, fl, bm);
                                joinedCount++;
                            }
                        }
                        catch {}
                    }
                }
                logs.Add($"Joined {joinedCount} floor-beam intersections for seamless monolithic concrete cut");

                tx.Commit();
            }

            // 4. Export updated Section View image
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            List<string> exportedFiles = new List<string>();

            var activeSec = uidoc.ActiveView as ViewSection ?? new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSection))
                .Cast<ViewSection>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("1-1"));

            if (activeSec != null)
            {
                uidoc.ActiveView = activeSec;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == activeSec.Id);
                uiview?.ZoomToFit();

                string path = Path.Combine(outDir, "revit_section_1_1_floor_cut_updated.png");
                if (File.Exists(path)) try { File.Delete(path); } catch {}

                var opt = new ImageExportOptions
                {
                    FilePath = path,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ShadowViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3200
                };
                doc.ExportImage(opt);
                exportedFiles.Add(path);
            }

            return new {
                success = true,
                logs,
                exportedFiles
            };
        }
    }
}
