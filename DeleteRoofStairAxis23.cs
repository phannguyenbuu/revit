using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DeleteRoofStairAxis23
    {
        private static double ToM(double ft) => ft * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var log = new List<string>();

                // Target stair ID: 2370488 (Stair at Axis 2-3, Z: 10.8m to 14.57m)
                ElementId stairId = new ElementId(2370488L);
                var stair = doc.GetElement(stairId) as Stairs;

                if (stair == null)
                {
                    // Fallback search: find any stair with X around 4.5..8.0 and Z > 10.0
                    stair = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_Stairs)
                        .WhereElementIsNotElementType()
                        .Cast<Stairs>()
                        .FirstOrDefault(s =>
                        {
                            var bb = s.get_BoundingBox(null);
                            if (bb == null) return false;
                            double minX = ToM(bb.Min.X);
                            double maxX = ToM(bb.Max.X);
                            double minZ = ToM(bb.Min.Z);
                            return minX >= 4.0 && maxX <= 8.5 && minZ >= 10.0;
                        });
                }

                if (stair == null)
                {
                    return new { error = "Could not find stair at roof level axis 2-3" };
                }

                log.Add($"Found target stair: ID {stair.Id.Value}, Name: {stair.Name}");

                // Find associated railings
                var associatedRailings = new List<ElementId>();
                try
                {
                    var rIds = stair.GetAssociatedRailings();
                    if (rIds != null) associatedRailings.AddRange(rIds);
                }
                catch { }

                // Also check all railings hosted on this stair
                var allRailings = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StairsRailing)
                    .WhereElementIsNotElementType()
                    .Cast<Railing>()
                    .Where(r => r.HostId == stair.Id || associatedRailings.Contains(r.Id))
                    .Select(r => r.Id)
                    .Distinct()
                    .ToList();

                log.Add($"Found {allRailings.Count} associated railings: {string.Join(", ", allRailings.Select(i => i.Value))}");

                var elementsToDelete = new List<ElementId>();
                elementsToDelete.AddRange(allRailings);
                elementsToDelete.Add(stair.Id);

                using (Transaction t = new Transaction(doc, "Xoa cau thang tang ap mai truc 2-3"))
                {
                    t.Start();
                    var deletedIds = doc.Delete(elementsToDelete);
                    log.Add($"Successfully deleted {deletedIds.Count} elements (stair and railings)");
                    t.Commit();
                }

                // Regenerate
                using (Transaction t = new Transaction(doc, "Regen after delete stair"))
                {
                    t.Start();
                    doc.Regenerate();
                    t.Commit();
                }

                // Save Document
                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                    log.Add("Saved document successfully");
                }
                catch (Exception ex)
                {
                    log.Add("doc.Save error: " + ex.Message);
                }

                // Export 3D image
                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string full3dPath = Path.Combine(folder, "revit_3d_after_delete_roof_stair.jpg");

                var view3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview3d?.ZoomToFit();

                    if (File.Exists(full3dPath)) File.Delete(full3dPath);
                    var expOpt = new ImageExportOptions
                    {
                        FilePath = full3dPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt);
                }

                return new
                {
                    success = true,
                    log,
                    docSaved,
                    full3dPath
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
