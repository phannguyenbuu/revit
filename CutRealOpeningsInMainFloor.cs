using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CutRealOpeningsInMainFloor
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

                var mainFloor = doc.GetElement(new ElementId(2407783L)) as Floor
                    ?? new FilteredElementCollector(doc, view.Id)
                        .OfClass(typeof(Floor))
                        .Cast<Floor>()
                        .FirstOrDefault(f => f.FloorType.Name == "NỀN COS 0.00 2");

                if (mainFloor == null) return new { error = "Main floor not found" };

                // Get WC floors
                long[] wcFloorIds = new long[] { 2406060L, 2406290L, 2406297L, 2406304L, 2406313L };
                var wcFloors = wcFloorIds.Select(id => doc.GetElement(new ElementId(id)) as Floor).Where(f => f != null).ToList();

                int openingsCreated = 0;
                List<string> logs = new List<string>();

                using (var tx = new Transaction(doc, "Create Real Floor Openings for WC"))
                {
                    var failOpt = tx.GetFailureHandlingOptions();
                    failOpt.SetFailuresPreprocessor(new WarningSwallower());
                    tx.SetFailureHandlingOptions(failOpt);

                    tx.Start();

                    // Unjoin first if joined
                    foreach (var wcf in wcFloors)
                    {
                        if (JoinGeometryUtils.AreElementsJoined(doc, mainFloor, wcf))
                        {
                            JoinGeometryUtils.UnjoinGeometry(doc, mainFloor, wcf);
                        }

                        // Get top face of wcf
                        var opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
                        var geom = wcf.get_Geometry(opt);
                        PlanarFace? topFace = null;
                        if (geom != null)
                        {
                            foreach (var obj in geom)
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
                                }
                            }
                        }

                        if (topFace != null)
                        {
                            var loops = topFace.GetEdgesAsCurveLoops();
                            foreach (var loop in loops)
                            {
                                var ca = new CurveArray();
                                foreach (var c in loop) ca.Append(c);
                                try
                                {
                                    doc.Create.NewOpening(mainFloor, ca, true);
                                    openingsCreated++;
                                    logs.Add($"Opening created for WC Floor {wcf.Id.Value}");
                                }
                                catch (Exception ex)
                                {
                                    logs.Add($"Opening failed for {wcf.Id.Value}: {ex.Message}");
                                }
                            }
                        }
                        else
                        {
                            logs.Add($"No top face for {wcf.Id.Value}");
                        }
                    }

                    tx.Commit();
                }

                // Export Zoom 2
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ p3 = new XYZ(31000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0);
                    XYZ p4 = new XYZ(38500.0 * MM_TO_FT, 14500.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p3, p4);
                }

                string img2 = Path.Combine(outDir, "revit_zoom_wc_angle_verified.png");
                var opt2 = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = img2,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1800,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt2);

                // Reset view to full plan and export
                if (uiview != null)
                {
                    XYZ pAll1 = new XYZ(-2000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                    XYZ pAll2 = new XYZ(39000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(pAll1, pAll2);
                }

                string planImg = Path.Combine(outDir, "revit_tang1_floor_final_verified.png");
                var optPlan = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = planImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 3000,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(optPlan);

                return new
                {
                    success = true,
                    openingsCreated = openingsCreated,
                    logs = logs,
                    zoomWcImage = "revit_zoom_wc_angle_verified.png",
                    planImage = "revit_tang1_floor_final_verified.png"
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
