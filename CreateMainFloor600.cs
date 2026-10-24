using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateMainFloor600
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No active ViewPlan" };

                var fpe600 = doc.GetElement(new ElementId(8574L)) as FillPatternElement
                    ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "600 x 600mm");

                var e2381562 = doc.GetElement(new ElementId(2381562L));
                if (e2381562 == null) return new { error = "Element 2381562 not found" };

                // Get top face curve loops from 2381562
                var optGeomModel = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
                var geomModel = e2381562.get_Geometry(optGeomModel);
                PlanarFace? topFace = null;
                if (geomModel != null)
                {
                    foreach (var obj in geomModel)
                    {
                        if (obj is Solid s && s.Volume > 0)
                        {
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && pf.FaceNormal.IsAlmostEqualTo(XYZ.BasisZ))
                                {
                                    topFace = pf;
                                    break;
                                }
                            }
                            if (topFace != null) break;
                        }
                    }
                }

                if (topFace == null) return new { error = "Could not find top face on slab" };

                var loops = topFace.GetEdgesAsCurveLoops();
                if (loops.Count == 0) return new { error = "No curve loops found" };

                // Get FloorType "NỀN COS 0.00 2"
                var ft600 = doc.GetElement(new ElementId(1185251L)) as FloorType;
                if (ft600 == null)
                {
                    ft600 = new FilteredElementCollector(doc)
                        .OfClass(typeof(FloorType))
                        .Cast<FloorType>()
                        .FirstOrDefault(ft => ft.Name == "NỀN COS 0.00 2");
                }

                if (ft600 == null) return new { error = "FloorType NỀN COS 0.00 2 not found" };

                // Ensure material has 600x600 pattern
                long createdFloorId = 0;

                using (var tx = new Transaction(doc, "Create Main Floor 600x600"))
                {
                    var failOpt = tx.GetFailureHandlingOptions();
                    failOpt.SetFailuresPreprocessor(new WarningSwallower());
                    tx.SetFailureHandlingOptions(failOpt);

                    tx.Start();

                    // Update material 6-LAT GACH NHA 06
                    var mat = doc.GetElement(new ElementId(1714807L)) as Material
                        ?? new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>()
                            .FirstOrDefault(m => m.Name.Contains("6-LAT GACH"));

                    if (mat != null && fpe600 != null)
                    {
                        mat.SurfaceForegroundPatternId = fpe600.Id;
                        mat.SurfaceForegroundPatternColor = new Color(140, 140, 140);
                    }

                    // Create Floor
                    var newFloor = Floor.Create(doc, loops, ft600.Id, view.GenLevel.Id);
                    createdFloorId = newFloor.Id.Value;

                    // Set height offset to 0
                    var pOffset = newFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    if (pOffset != null && !pOffset.IsReadOnly)
                    {
                        pOffset.Set(0.0);
                    }

                    tx.Commit();
                }

                // Export verification image
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ p1 = new XYZ(-2000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                    XYZ p2 = new XYZ(39000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p1, p2);
                }

                string planImgPath = Path.Combine(outDir, "revit_tang1_floor_600_hatch_and_tags.png");
                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 3000,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt);

                return new
                {
                    success = true,
                    createdFloorId = createdFloorId,
                    pattern = "600 x 600mm",
                    image = "revit_tang1_floor_600_hatch_and_tags.png"
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
