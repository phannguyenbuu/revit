using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Visual;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ColorChanger
    {
        public static object ApplyPdfColors(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            // Colors extracted from FK2025_Infart_1050x700_med HRP+FP.pdf:
            // 1. Lidl Blue (Board background, logo box, logo letters L,D,L): RGB(0, 91, 162) [#005BA2]
            // 2. Lidl Red (Logo ring border, letter 'i' and dot): RGB(237, 28, 36) [#ED1C24]
            // 3. Lidl Yellow (Logo circular disc): RGB(255, 242, 0) [#FFF200]
            // 4. White (Symbols: Arrow, P, Stroller, Wheelchair, Logo outline): RGB(255, 255, 255) [#FFFFFF]
            // 5. Lidl Dark Blue (Circle behind arrow): RGB(0, 47, 103) [#002F67]

            var colorLidlBlue = new Color(0, 91, 162);
            var colorLidlRed = new Color(237, 28, 36);
            var colorLidlYellow = new Color(255, 242, 0);
            var colorWhite = new Color(255, 255, 255);
            var colorDarkBlue = new Color(0, 47, 103);

            var report = new List<string>();

            using (var tx = new Transaction(doc, "Update Colors per FK2025 PDF"))
            {
                tx.Start();

                var allMaterials = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .ToList();

                // 1. Update Dark grey (Sign board background) -> Lidl Blue
                var matDarkGrey = allMaterials.FirstOrDefault(m => m.Name.Equals("Dark grey", StringComparison.OrdinalIgnoreCase));
                if (matDarkGrey != null)
                {
                    matDarkGrey.Color = colorLidlBlue;
                    UpdateAppearanceColor(doc, matDarkGrey, 0, 91, 162);
                    report.Add($"Updated 'Dark grey' (Sign Board) -> RGB(0, 91, 162) [Lidl Blue]");
                }

                // 2. Update Blue (Logo background & letters L, D, L) -> Lidl Blue
                var matBlue = allMaterials.FirstOrDefault(m => m.Name.Equals("Blue", StringComparison.OrdinalIgnoreCase));
                if (matBlue != null)
                {
                    matBlue.Color = colorLidlBlue;
                    UpdateAppearanceColor(doc, matBlue, 0, 91, 162);
                    report.Add($"Updated 'Blue' (Logo Box & Letters) -> RGB(0, 91, 162) [Lidl Blue]");
                }

                // 3. Update Red (Logo ring & 'i') -> Lidl Red
                var matRed = allMaterials.FirstOrDefault(m => m.Name.Equals("Red", StringComparison.OrdinalIgnoreCase));
                if (matRed != null)
                {
                    matRed.Color = colorLidlRed;
                    UpdateAppearanceColor(doc, matRed, 237, 28, 36);
                    report.Add($"Updated 'Red' (Logo Ring & i) -> RGB(237, 28, 36) [Lidl Red]");
                }

                // 4. Update yellow (Logo disc) -> Lidl Yellow
                var matYellow = allMaterials.FirstOrDefault(m => m.Name.Equals("yellow", StringComparison.OrdinalIgnoreCase));
                if (matYellow != null)
                {
                    matYellow.Color = colorLidlYellow;
                    UpdateAppearanceColor(doc, matYellow, 255, 242, 0);
                    report.Add($"Updated 'yellow' (Logo Disc) -> RGB(255, 242, 0) [Lidl Yellow]");
                }

                // 5. Update White / VIT -> RGB(255, 255, 255)
                var matWhite = allMaterials.FirstOrDefault(m => m.Name.Equals("White", StringComparison.OrdinalIgnoreCase));
                if (matWhite != null)
                {
                    matWhite.Color = colorWhite;
                    UpdateAppearanceColor(doc, matWhite, 255, 255, 255);
                    report.Add($"Updated 'White' (Symbols & Border) -> RGB(255, 255, 255)");
                }

                var matVit = allMaterials.FirstOrDefault(m => m.Name.Equals("VIT", StringComparison.OrdinalIgnoreCase));
                if (matVit != null)
                {
                    matVit.Color = colorWhite;
                    UpdateAppearanceColor(doc, matVit, 255, 255, 255);
                    report.Add($"Updated 'VIT' (Inner Core) -> RGB(255, 255, 255)");
                }

                // 6. Also create or ensure a dedicated "Lidl Dark Blue" material exists for the arrow circle if needed
                var matDarkBlue = allMaterials.FirstOrDefault(m => m.Name.Equals("Lidl Dark Blue", StringComparison.OrdinalIgnoreCase));
                if (matDarkBlue == null)
                {
                    var id = Material.Create(doc, "Lidl Dark Blue");
                    matDarkBlue = doc.GetElement(id) as Material;
                    if (matDarkBlue != null)
                    {
                        matDarkBlue.Color = colorDarkBlue;
                        report.Add($"Created new material 'Lidl Dark Blue' -> RGB(0, 47, 103)");
                    }
                }
                else
                {
                    matDarkBlue.Color = colorDarkBlue;
                    UpdateAppearanceColor(doc, matDarkBlue, 0, 47, 103);
                    report.Add($"Updated 'Lidl Dark Blue' -> RGB(0, 47, 103)");
                }

                tx.Commit();
            }

            // Also refresh active view
            try
            {
                uiapp.ActiveUIDocument?.RefreshActiveView();
            }
            catch { }

            return new
            {
                success = true,
                doc = doc.Title,
                changes = report
            };
        }

        private static void UpdateAppearanceColor(Document doc, Material mat, byte r, byte g, byte b)
        {
            if (mat.AppearanceAssetId == ElementId.InvalidElementId) return;

            try
            {
                using (var editScope = new AppearanceAssetEditScope(doc))
                {
                    Asset asset = editScope.Start(mat.AppearanceAssetId);
                    var col = new Color(r, g, b);

                    // Try standard properties
                    var prop = asset.FindByName("generic_diffuse") as AssetPropertyDoubleArray4d;
                    if (prop != null)
                    {
                        prop.SetValueAsColor(col);
                    }
                    else
                    {
                        for (int i = 0; i < asset.Size; i++)
                        {
                            var p = asset[i];
                            if (p is AssetPropertyDoubleArray4d colProp &&
                                (p.Name.ToLower().Contains("color") || p.Name.ToLower().Contains("diffuse")))
                            {
                                try { colProp.SetValueAsColor(col); } catch { }
                            }
                        }
                    }

                    editScope.Commit(true);
                }
            }
            catch
            {
                // Appearance asset edit might throw for some asset schemas; non-fatal
            }
        }

        public static object ExportViewImage(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView;
            if (doc == null || view == null) return new { error = "No doc or view" };

            string outPath = args.GetProperty("outputPath").GetString()!;
            var opts = new ImageExportOptions
            {
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 1920
            };

            doc.ExportImage(opts);
            return new { success = true, path = outPath };
        }
    }
}
