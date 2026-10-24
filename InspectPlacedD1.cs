using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectPlacedD1
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Clear any active selection
            uidoc.Selection.SetElementIds(new List<ElementId>());

            // Switch to MẶT BẰNG TẦNG 1
            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"));

            if (plan != null && uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

            // Find door 2363719
            var doorId = new ElementId(2363719L);
            var door = doc.GetElement(doorId) as FamilyInstance;
            if (door == null)
            {
                // Fallback: search for door with mark D1 or symbol D1
                var allDoors = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(d => d.Symbol != null && (d.Symbol.Name.Contains("D1") || (d.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString() == "D1")))
                    .ToList();
                door = allDoors.FirstOrDefault();
            }

            if (door == null) return new { error = "Door D1 not found in document" };

            var sym = door.Symbol;
            var fam = sym?.Family;
            var host = door.Host;
            var lp = door.Location as LocationPoint;
            var bb = door.get_BoundingBox(null);

            // Get parameters
            var paramDict = new Dictionary<string, string>();
            foreach (Parameter p in door.Parameters)
            {
                if (p.HasValue && !string.IsNullOrWhiteSpace(p.Definition?.Name))
                {
                    try { paramDict[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString(); } catch { }
                }
            }

            var typeParamDict = new Dictionary<string, string>();
            if (sym != null)
            {
                foreach (Parameter p in sym.Parameters)
                {
                    if (p.HasValue && !string.IsNullOrWhiteSpace(p.Definition?.Name))
                    {
                        try { typeParamDict[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString(); } catch { }
                    }
                }
            }

            // Zoom to target area
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == (plan != null ? plan.Id : uidoc.ActiveView.Id));
            if (uiview != null)
            {
                var minPt = new XYZ(-1.5 * M2FT, 3.5 * M2FT, 0.0);
                var maxPt = new XYZ(4.0 * M2FT, 9.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(minPt, maxPt);
            }

            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_glass_hinge_clean.png";
            try
            {
                if (File.Exists(outImgPath)) File.Delete(outImgPath);

                var expOpt = new ImageExportOptions
                {
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = "Image export error: " + ex.Message };
            }

            return new
            {
                success = true,
                doorId = door.Id.Value,
                familyName = fam?.Name,
                typeName = sym?.Name,
                host = host != null ? $"{host.Id.Value} ({host.Name})" : "None",
                loc = lp != null ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null,
                facing = new { x = door.FacingOrientation.X, y = door.FacingOrientation.Y, z = door.FacingOrientation.Z },
                hand = new { x = door.HandOrientation.X, y = door.HandOrientation.Y, z = door.HandOrientation.Z },
                bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048, z = bb.Min.Z * 0.3048 } : null,
                bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048, z = bb.Max.Z * 0.3048 } : null,
                image = outImgPath,
                typeParams = typeParamDict,
                instParams = paramDict
            };
        }
    }
}
