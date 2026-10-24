using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class OverwriteFamilyLoadOptions : IFamilyLoadOptions
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

    public static class UpdateWindowK2StackWithPlanSymbol
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var app = uiapp.Application;
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                string famPath = @"D:\Dropbox\_Documents\RevitAI\Window_K2_Stack.rfa";
                if (!File.Exists(famPath)) return new { error = "Family file not found: " + famPath };

                Document famDoc = app.OpenDocumentFile(famPath);
                if (famDoc == null) return new { error = "Could not open family document" };

                List<string> logs = new List<string>();

                using (Transaction tx = new Transaction(famDoc, "Add 2D Plan Symbolic Lines and Configure Visibility"))
                {
                    tx.Start();

                    // Find Ref. Level / Reference Plane for Plan View
                    var refLevel = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .FirstOrDefault();

                    SketchPlane skPlane = null;
                    if (refLevel != null)
                    {
                        skPlane = SketchPlane.Create(famDoc, refLevel.Id);
                    }
                    else
                    {
                        Plane plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero);
                        skPlane = SketchPlane.Create(famDoc, plane);
                    }

                    // 1. Configure 3D FreeFormElements visibility:
                    // Hide 3D solids in Plan/RCP when cut so they don't obscure the 2D window cut symbol
                    var ffes = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(FreeFormElement))
                        .Cast<FreeFormElement>()
                        .ToList();

                    foreach (var ffe in ffes)
                    {
                        var fev = new FamilyElementVisibility(FamilyElementVisibilityType.Model)
                        {
                            IsShownInPlanRCPCut = false,
                            IsShownInFrontBack = true,
                            IsShownInLeftRight = true,
                            IsShownInCoarse = true,
                            IsShownInMedium = true,
                            IsShownInFine = true
                        };
                        ffe.SetVisibility(fev);
                    }
                    logs.Add($"Set IsShownInPlanRCPCut=false for {ffes.Count} 3D solids");

                    // 2. Subcategories and GraphicsStyles for 2D Symbolic Lines
                    var winCat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows);
                    GraphicsStyle frameCutStyle = null;
                    GraphicsStyle glassCutStyle = null;

                    if (winCat != null && winCat.SubCategories != null)
                    {
                        foreach (Category sc in winCat.SubCategories)
                        {
                            if (sc.Name.Contains("Frame") || sc.Name.Contains("Khung"))
                            {
                                frameCutStyle = sc.GetGraphicsStyle(GraphicsStyleType.Cut) ?? sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                            }
                            if (sc.Name.Contains("Glass") || sc.Name.Contains("Kính"))
                            {
                                glassCutStyle = sc.GetGraphicsStyle(GraphicsStyleType.Cut) ?? sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                            }
                        }
                    }

                    // 3. Draw 2D Symbolic Lines:
                    // Width 900mm: X in [-450, 450] mm
                    // Wall thickness 200mm: Y in [-100, 100] mm
                    // Frame thickness 100mm: Y in [-50, 50] mm
                    // Glass pane at Y in [-5, 5] mm, X in [-328.75, 328.75] mm
                    double xMin = -450.0 * MM2FT;
                    double xMax = 450.0 * MM2FT;
                    double yWallMin = -100.0 * MM2FT;
                    double yWallMax = 100.0 * MM2FT;
                    double yFrameMin = -50.0 * MM2FT;
                    double yFrameMax = 50.0 * MM2FT;
                    double xGlassMin = -328.75 * MM2FT;
                    double xGlassMax = 328.75 * MM2FT;
                    double yGlass1 = -5.0 * MM2FT;
                    double yGlass2 = 5.0 * MM2FT;

                    void AddSymLine(XYZ p1, XYZ p2, GraphicsStyle style)
                    {
                        Line line = Line.CreateBound(p1, p2);
                        SymbolicCurve sc = famDoc.FamilyCreate.NewSymbolicCurve(line, skPlane);
                        if (style != null) sc.Subcategory = style;
                    }

                    // A. Wall opening jambs (2 bên mép tường)
                    AddSymLine(new XYZ(xMin, yWallMin, 0), new XYZ(xMin, yWallMax, 0), null);
                    AddSymLine(new XYZ(xMax, yWallMin, 0), new XYZ(xMax, yWallMax, 0), null);

                    // B. Wall sill lines (2 gờ bậu tường trong và ngoài)
                    AddSymLine(new XYZ(xMin, yWallMin, 0), new XYZ(xMax, yWallMin, 0), null);
                    AddSymLine(new XYZ(xMin, yWallMax, 0), new XYZ(xMax, yWallMax, 0), null);

                    // C. Window frame cut lines (2 đường nét khung nhôm)
                    AddSymLine(new XYZ(xMin, yFrameMin, 0), new XYZ(xMax, yFrameMin, 0), frameCutStyle);
                    AddSymLine(new XYZ(xMin, yFrameMax, 0), new XYZ(xMax, yFrameMax, 0), frameCutStyle);

                    // D. Glass pane double lines (2 đường nét kính ở giữa)
                    AddSymLine(new XYZ(xGlassMin, yGlass1, 0), new XYZ(xGlassMax, yGlass1, 0), glassCutStyle);
                    AddSymLine(new XYZ(xGlassMin, yGlass2, 0), new XYZ(xGlassMax, yGlass2, 0), glassCutStyle);

                    // E. Window sash frame edges
                    AddSymLine(new XYZ(xGlassMin, yFrameMin, 0), new XYZ(xGlassMin, yFrameMax, 0), frameCutStyle);
                    AddSymLine(new XYZ(xGlassMax, yFrameMin, 0), new XYZ(xGlassMax, yFrameMax, 0), frameCutStyle);

                    logs.Add("Added 10 2D Symbolic Curves for architectural plan cut symbol");

                    tx.Commit();
                }

                famDoc.Save();
                famDoc.Close(false);
                logs.Add("Saved updated family file");

                // 4. Reload into Project Document
                Family famReloaded = null;
                using (Transaction tx = new Transaction(doc, "Reload Window_K2_Stack with 2D Plan Symbol"))
                {
                    tx.Start();
                    doc.LoadFamily(famPath, new OverwriteFamilyLoadOptions(), out famReloaded);
                    tx.Commit();
                }
                logs.Add("Reloaded family into project document");

                // 5. Switch to Floor Plan and Refresh
                var plan = doc.GetElement(new ElementId(312)) as ViewPlan;
                if (plan != null)
                {
                    uidoc.ActiveView = plan;

                    // Ensure View Range cut plane is 1800mm and Top is 2200mm
                    using (Transaction tx = new Transaction(doc, "Verify View Range"))
                    {
                        tx.Start();
                        var vr = plan.GetViewRange();
                        vr.SetOffset(PlanViewPlane.TopClipPlane, 2.2 * M2FT);
                        vr.SetOffset(PlanViewPlane.CutPlane, 1.8 * M2FT);
                        plan.SetViewRange(vr);
                        tx.Commit();
                    }

                    // Zoom to bay showing stack 2378322 or 2377860
                    XYZ pMin = new XYZ(0.5 * M2FT, 12.0 * M2FT, 0);
                    XYZ pMax = new XYZ(3.0 * M2FT, 14.5 * M2FT, 0);
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == plan.Id);
                    uiview?.ZoomAndCenterRectangle(pMin, pMax);
                    uidoc.RefreshActiveView();
                }

                // 6. Export image to verify
                string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_k2_symbolic_plan.png";
                if (File.Exists(outImg)) try { File.Delete(outImg); } catch { }

                var expOpt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(expOpt);

                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    outImg,
                    logs
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
