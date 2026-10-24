using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ConvertCadTextsAndDeleteImport
    {
        private const double M2FT = 3.2808398950131235;

        public class TextItem
        {
            public string text { get; set; }
            public double x { get; set; }
            public double y { get; set; }
            public string typeName { get; set; }
            public string cat { get; set; }
            public string layer { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Find View MẶT BẰNG TẦNG 1
            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"));

            if (plan == null) return new { error = "View MẶT BẰNG TẦNG 1 not found" };

            // 2. Read texts from JSON
            string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\all_revit_texts_to_create.json";
            if (!File.Exists(jsonPath)) return new { error = "JSON file not found: " + jsonPath };

            string jsonContent = File.ReadAllText(jsonPath);
            var items = JsonSerializer.Deserialize<List<TextItem>>(jsonContent);
            if (items == null || items.Count == 0) return new { error = "No text items in JSON" };

            // 3. Find TextNoteTypes
            var allTextTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .ToList();

            var defaultType = allTextTypes.FirstOrDefault(t => t.Name == "2.5mm Arial") ?? allTextTypes.First();
            var roomType = allTextTypes.FirstOrDefault(t => t.Name == "3.5mm Arial") ?? defaultType;
            var dimType = allTextTypes.FirstOrDefault(t => t.Name == "2.0mm Arial") ?? defaultType;

            int createdCount = 0;
            int deletedImportsCount = 0;
            var createdIds = new List<long>();

            using (Transaction t = new Transaction(doc, "Convert CAD Texts and Delete Import"))
            {
                t.Start();

                // Create TextNotes
                foreach (var item in items)
                {
                    try
                    {
                        var targetType = defaultType;
                        if (item.cat == "Room" || item.typeName == "3.5mm Arial")
                            targetType = roomType;
                        else if (item.cat == "Dimension" || item.typeName == "2.0mm Arial")
                            targetType = dimType;

                        XYZ pos = new XYZ(item.x * M2FT, item.y * M2FT, 0.0);
                        var tn = TextNote.Create(doc, plan.Id, pos, item.text, targetType.Id);
                        if (tn != null)
                        {
                            createdCount++;
                            createdIds.Add(tn.Id.Value);
                        }
                    }
                    catch { }
                }

                // Delete ImportInstances in MẶT BẰNG TẦNG 1
                var importsToDelete = new FilteredElementCollector(doc, plan.Id)
                    .OfClass(typeof(ImportInstance))
                    .Cast<ImportInstance>()
                    .ToList();

                foreach (var imp in importsToDelete)
                {
                    try
                    {
                        if (imp.Pinned) imp.Pinned = false;
                        var typeId = imp.GetTypeId();
                        doc.Delete(imp.Id);
                        deletedImportsCount++;

                        // Also remove CADLinkType if possible
                        try
                        {
                            if (typeId != ElementId.InvalidElementId)
                            {
                                doc.Delete(typeId);
                            }
                        }
                        catch { }
                    }
                    catch { }
                }

                t.Commit();
            }

            // Export verification images
            uidoc.ActiveView = plan;
            uidoc.Selection.SetElementIds(new List<ElementId>());

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang1_clean_with_texts.png");
            string stairImgPath = Path.Combine(folder, "stair_clean_with_texts.png");

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == plan.Id);

            // Full plan view
            uiview?.ZoomAndCenterRectangle(new XYZ(-5.0 * M2FT, -3.0 * M2FT, 0.0), new XYZ(42.0 * M2FT, 17.0 * M2FT, 0.0));
            try
            {
                if (File.Exists(planImgPath)) File.Delete(planImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3500
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            // Stair close-up
            uiview?.ZoomAndCenterRectangle(new XYZ(3.8 * M2FT, 9.5 * M2FT, 0.0), new XYZ(8.8 * M2FT, 15.6 * M2FT, 0.0));
            try
            {
                if (File.Exists(stairImgPath)) File.Delete(stairImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = stairImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new {
                success = true,
                createdTextsCount = createdCount,
                deletedImportsCount = deletedImportsCount,
                fullPlanImage = planImgPath,
                stairImage = stairImgPath
            };
        }
    }
}
