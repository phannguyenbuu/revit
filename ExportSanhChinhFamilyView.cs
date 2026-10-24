using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportSanhChinhFamilyView
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa";
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_sanh_chinh_family_3d.png";

            var app = uiapp.Application;
            var famDoc = app.OpenDocumentFile(famPath);
            if (famDoc == null) return new { error = "Cannot open family file" };

            try
            {
                View3D view3D = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

                if (view3D == null)
                {
                    famDoc.Close(false);
                    return new { error = "No 3D view in family" };
                }

                using (var tx = new Transaction(famDoc, "Set View Colors and Camera"))
                {
                    tx.Start();
                    view3D.DisplayStyle = DisplayStyle.FlatColors;
                    var vdm = view3D.GetViewDisplayModel();
                    vdm.SmoothEdges = true;
                    view3D.SetViewDisplayModel(vdm);

                    // Setup nice isometric view looking at the porch from front-left
                    double M2FT = 1.0 / 0.3048;
                    XYZ target = new XYZ(-1.0 * M2FT, 0.0 * M2FT, 2.0 * M2FT);
                    XYZ eye = new XYZ(-18.0 * M2FT, -18.0 * M2FT, 12.0 * M2FT);
                    XYZ forward = (target - eye).Normalize();
                    XYZ right = forward.CrossProduct(XYZ.BasisZ).Normalize();
                    XYZ up = right.CrossProduct(forward).Normalize();

                    view3D.SetOrientation(new ViewOrientation3D(eye, up, forward));

                    tx.Commit();
                }

                if (File.Exists(outImgPath)) File.Delete(outImgPath);

                var expOpt = new ImageExportOptions
                {
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.SetOfViews,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 1920
                };
                expOpt.SetViewsAndSheets(new List<ElementId> { view3D.Id });

                famDoc.ExportImage(expOpt);
                famDoc.Close(false);

                // Check actual output path (Revit appends view name)
                string finalPath = outImgPath;
                if (!File.Exists(finalPath))
                {
                    string dir = Path.GetDirectoryName(outImgPath);
                    string baseName = Path.GetFileNameWithoutExtension(outImgPath);
                    var candidates = Directory.GetFiles(dir, baseName + "*");
                    if (candidates.Length > 0) finalPath = candidates[0];
                }

                return new
                {
                    success = true,
                    imagePath = finalPath,
                    exists = File.Exists(finalPath)
                };
            }
            catch (Exception ex)
            {
                famDoc.Close(false);
                return new { error = ex.ToString() };
            }
        }
    }
}
