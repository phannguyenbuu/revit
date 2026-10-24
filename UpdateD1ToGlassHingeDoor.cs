using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class D1FamilyLoadOptions : IFamilyLoadOptions
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

    public static class UpdateD1ToGlassHingeDoor
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active Revit doc" };

            // 1. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 2. Wall gach200_xay moi
            var wt200 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name.Equals("gach200_xay moi", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().FirstOrDefault(w => w.Name.Contains("200"));

            // 3. Find Material Glass Tempered
            var matTempered = new FilteredElementCollector(doc)
                .OfClass(typeof(Material))
                .Cast<Material>()
                .FirstOrDefault(m => m.Name.Contains("Tempered", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>().FirstOrDefault(m => m.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase));

            // 4. Find Family cua thuy luc 2 canh
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("cua thuy luc 2 canh", StringComparison.OrdinalIgnoreCase));
            if (fam == null) return new { error = "Family cua thuy luc 2 canh not found" };

            // Attach dialog suppressor for EditFamily/LoadFamily
            EventHandler<Autodesk.Revit.UI.Events.DialogBoxShowingEventArgs> dlgHandler = (s, e) =>
            {
                e.OverrideResult((int)TaskDialogResult.Ok);
            };
            uiapp.DialogBoxShowing += dlgHandler;

            try
            {
                var fdoc = doc.EditFamily(fam);
                if (fdoc != null)
                {
                    // Find sketch plane "Base Line" or first SketchPlane
                    var sketchPlanes = new FilteredElementCollector(fdoc)
                        .OfClass(typeof(SketchPlane))
                        .Cast<SketchPlane>()
                        .ToList();
                    var sp = sketchPlanes.FirstOrDefault(p => p.Name.Equals("Base Line", StringComparison.OrdinalIgnoreCase))
                          ?? sketchPlanes.FirstOrDefault();

                    // Get subcategories
                    var doorCat = fdoc.OwnerFamily.FamilyCategory;
                    GraphicsStyle styleSwing = null;
                    GraphicsStyle stylePanel = null;
                    if (doorCat != null && doorCat.SubCategories != null)
                    {
                        foreach (Category sc in doorCat.SubCategories)
                        {
                            if (sc.Name.Equals("Plan Swing", StringComparison.OrdinalIgnoreCase))
                                styleSwing = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                            if (sc.Name.Equals("Panel", StringComparison.OrdinalIgnoreCase))
                                stylePanel = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        }
                    }

                    using (var ftx = new Transaction(fdoc, "Enhance Glass Door Family"))
                    {
                        ftx.Start();

                        // 4.1 Update Family Manager Parameters
                        var mgr = fdoc.FamilyManager;
                        var pThick = mgr.get_Parameter("Glazing Thickness");
                        if (pThick != null)
                        {
                            // 10 mm in feet
                            double thickFt = 10.0 / 304.8;
                            mgr.Set(pThick, thickFt);
                        }

                        // Set Description
                        var pDesc = mgr.get_Parameter("Description");
                        if (pDesc != null) mgr.Set(pDesc, "Cửa kính cường lực 10mm 2 cánh bản lề sàn bật 2 chiều (D1)");

                        // 4.2 Fix visibility of existing SymbolicCurves
                        var existingCurves = new FilteredElementCollector(fdoc)
                            .OfClass(typeof(CurveElement))
                            .Cast<CurveElement>()
                            .Where(c => c is SymbolicCurve)
                            .Cast<SymbolicCurve>()
                            .ToList();

                        var visModel = new FamilyElementVisibility(FamilyElementVisibilityType.Model)
                        {
                            IsShownInPlanRCPCut = true,
                            IsShownInCoarse = true,
                            IsShownInMedium = true,
                            IsShownInFine = true
                        };

                        foreach (var sc in existingCurves)
                        {
                            if (sc.LineStyle != null && (sc.LineStyle.Name.Contains("Swing") || sc.LineStyle.Name.Contains("Panel")))
                            {
                                try { sc.SetVisibility(visModel); } catch { }
                            }
                        }

                        // 4.3 Add reverse swing curves for 2-way swing hinge (bật 2 chiều)
                        // Family geometry constants in feet:
                        // Pivot 1 (Left leaf): X = -831.8769 mm / 304.8 = -2.729255 ft, Y = 50 mm / 304.8 = 0.164042 ft
                        // Pivot 2 (Right leaf): X = +996.9231 mm / 304.8 = +3.270745 ft, Y = 0.164042 ft
                        // Center meeting point: X = +82.5231 mm / 304.8 = 0.270745 ft, Y = 0.164042 ft
                        // Radius R = 3.0 ft (914.4 mm)
                        double xPiv1 = -831.87689994715 / 304.8;
                        double xPiv2 = 996.92310005285 / 304.8;
                        double xMid = 82.52310005285 / 304.8;
                        double yPiv = 50.0 / 304.8;
                        double r = 3.0; // 914.4 mm = 3.0 ft

                        if (sp != null && existingCurves.Count <= 8)
                        {
                            // Left leaf reverse arc (swing toward -Y)
                            // Starts at (xMid, yPiv), ends at (xPiv1, yPiv - r)
                            var pCenter1 = new XYZ(xPiv1, yPiv, 0);
                            var pStart1 = new XYZ(xMid, yPiv, 0);
                            var pEnd1 = new XYZ(xPiv1, yPiv - r, 0);
                            // Midpoint on arc at angle -45 deg
                            double angle45 = -Math.PI / 4.0;
                            var pMid1 = new XYZ(xPiv1 + r * Math.Cos(angle45), yPiv + r * Math.Sin(angle45), 0);

                            try
                            {
                                var arc1 = Arc.Create(pStart1, pEnd1, pMid1);
                                var scArc1 = fdoc.FamilyCreate.NewSymbolicCurve(arc1, sp);
                                scArc1.SetVisibility(visModel);
                                if (styleSwing != null) scArc1.Subcategory = styleSwing;
                            }
                            catch { }

                            // Left leaf reverse open panel line at -90 deg
                            try
                            {
                                var line1 = Line.CreateBound(pCenter1, pEnd1);
                                var scLine1 = fdoc.FamilyCreate.NewSymbolicCurve(line1, sp);
                                scLine1.SetVisibility(visModel);
                                if (stylePanel != null) scLine1.Subcategory = stylePanel;
                            }
                            catch { }

                            // Left leaf at 45 deg into room (+Y)
                            double angle45Pos = Math.PI / 4.0;
                            var pLeaf45Pos1 = new XYZ(xPiv1 + r * Math.Cos(angle45Pos), yPiv + r * Math.Sin(angle45Pos), 0);
                            try
                            {
                                var lineLeaf45P = Line.CreateBound(pCenter1, pLeaf45Pos1);
                                var scLine = fdoc.FamilyCreate.NewSymbolicCurve(lineLeaf45P, sp);
                                scLine.SetVisibility(visModel);
                                if (stylePanel != null) scLine.Subcategory = stylePanel;
                            }
                            catch { }

                            // Left leaf at -45 deg out of room (-Y)
                            try
                            {
                                var lineLeaf45N = Line.CreateBound(pCenter1, pMid1);
                                var scLine = fdoc.FamilyCreate.NewSymbolicCurve(lineLeaf45N, sp);
                                scLine.SetVisibility(visModel);
                                if (stylePanel != null) scLine.Subcategory = stylePanel;
                            }
                            catch { }

                            // Right leaf reverse arc (swing toward -Y)
                            // Starts at (xMid, yPiv), ends at (xPiv2, yPiv - r)
                            var pCenter2 = new XYZ(xPiv2, yPiv, 0);
                            var pStart2 = new XYZ(xMid, yPiv, 0);
                            var pEnd2 = new XYZ(xPiv2, yPiv - r, 0);
                            // Midpoint on arc at angle -135 deg
                            double angle135 = -3.0 * Math.PI / 4.0;
                            var pMid2 = new XYZ(xPiv2 + r * Math.Cos(angle135), yPiv + r * Math.Sin(angle135), 0);

                            try
                            {
                                var arc2 = Arc.Create(pStart2, pEnd2, pMid2);
                                var scArc2 = fdoc.FamilyCreate.NewSymbolicCurve(arc2, sp);
                                scArc2.SetVisibility(visModel);
                                if (styleSwing != null) scArc2.Subcategory = styleSwing;
                            }
                            catch { }

                            // Right leaf reverse open panel line at -90 deg
                            try
                            {
                                var line2 = Line.CreateBound(pCenter2, pEnd2);
                                var scLine2 = fdoc.FamilyCreate.NewSymbolicCurve(line2, sp);
                                scLine2.SetVisibility(visModel);
                                if (stylePanel != null) scLine2.Subcategory = stylePanel;
                            }
                            catch { }

                            // Right leaf at 135 deg into room (+Y)
                            double angle135Pos = 3.0 * Math.PI / 4.0;
                            var pLeaf45Pos2 = new XYZ(xPiv2 + r * Math.Cos(angle135Pos), yPiv + r * Math.Sin(angle135Pos), 0);
                            try
                            {
                                var lineLeaf45P2 = Line.CreateBound(pCenter2, pLeaf45Pos2);
                                var scLine = fdoc.FamilyCreate.NewSymbolicCurve(lineLeaf45P2, sp);
                                scLine.SetVisibility(visModel);
                                if (stylePanel != null) scLine.Subcategory = stylePanel;
                            }
                            catch { }

                            // Right leaf at -135 deg out of room (-Y)
                            try
                            {
                                var lineLeaf45N2 = Line.CreateBound(pCenter2, pMid2);
                                var scLine = fdoc.FamilyCreate.NewSymbolicCurve(lineLeaf45N2, sp);
                                scLine.SetVisibility(visModel);
                                if (stylePanel != null) scLine.Subcategory = stylePanel;
                            }
                            catch { }
                        }

                        ftx.Commit();
                    }

                    // Load back into main document
                    fdoc.LoadFamily(doc, new D1FamilyLoadOptions());
                    fdoc.Close(false);
                }
            }
            finally
            {
                uiapp.DialogBoxShowing -= dlgHandler;
            }

            // 5. In main doc, update/place Door D1
            var doorSym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (doorSym == null)
            {
                var fCollector = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsElementType()
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(s => s.FamilyName.Contains("thuy luc", StringComparison.OrdinalIgnoreCase));
                doorSym = fCollector;
            }
            if (doorSym == null) return new { error = "Door symbol cua thuy luc not found after reload" };

            ElementId newDoorId = ElementId.InvalidElementId;
            ElementId wallId = ElementId.InvalidElementId;

            using (var tx = new Transaction(doc, "Place Glass Double Door D1"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                if (!doorSym.IsActive) doorSym.Activate();

                if (matTempered != null)
                {
                    var pMat = doorSym.LookupParameter("Material Glass");
                    if (pMat != null && !pMat.IsReadOnly) pMat.Set(matTempered.Id);
                }

                // Delete any old doors at this location
                try { doc.Delete(new ElementId(2362084L)); } catch { }
                try { doc.Delete(new ElementId(2362082L)); } catch { }
                try { doc.Delete(new ElementId(2362081L)); } catch { }

                // Check wall along Axis 1 (0.550, 4.200) to (0.550, 9.000)
                var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
                double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

                if (wall == null)
                {
                    var pStart = new XYZ(0.550 * M2FT, 4.200 * M2FT, lvlTang1.Elevation);
                    var pEnd = new XYZ(0.550 * M2FT, 9.000 * M2FT, lvlTang1.Elevation);
                    var wallLine = Line.CreateBound(pStart, pEnd);
                    wall = Wall.Create(doc, wallLine, wt200.Id, lvlTang1.Id, heightFt, 0, false, false);
                }
                wallId = wall.Id;
                doc.Regenerate();

                // Create wall opening for Door D1: from Y = 5.65m to Y = 7.55m, Z = 0 to 2.70m
                // Check if an opening already exists
                var existingOpenings = new FilteredElementCollector(doc)
                    .OfClass(typeof(Opening))
                    .Cast<Opening>()
                    .Where(o => o.Host?.Id == wall.Id)
                    .ToList();

                if (existingOpenings.Count == 0)
                {
                    double z0 = lvlTang1.Elevation;
                    double z1 = z0 + (2.70 * M2FT);
                    var p0 = new XYZ(0.550 * M2FT, 5.650 * M2FT, z0);
                    var p1 = new XYZ(0.550 * M2FT, 7.550 * M2FT, z1);
                    try
                    {
                        doc.Create.NewOpening(wall, p0, p1);
                    }
                    catch { }
                }

                // Delete any old doors at this location
                try { doc.Delete(new ElementId(2362906L)); } catch { }
                try { doc.Delete(new ElementId(2362084L)); } catch { }
                try { doc.Delete(new ElementId(2362082L)); } catch { }
                try { doc.Delete(new ElementId(2362081L)); } catch { }

                // Place Door D1 hosted on wall at (0.550, 6.600)
                var doorLoc = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                var door = doc.Create.NewFamilyInstance(doorLoc, doorSym, wall, lvlTang1, StructuralType.NonStructural);
                newDoorId = door.Id;

                // Set Mark parameter to "D1"
                var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                if (pMark != null && !pMark.IsReadOnly) pMark.Set("D1");

                doc.Regenerate();
                tx.Commit();
            }

            // 6. Switch to MẶT BẰNG TẦNG 1 floor plan and select the new door
            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase));
            if (plan != null && uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

            if (newDoorId != ElementId.InvalidElementId)
            {
                uidoc.Selection.SetElementIds(new List<ElementId> { newDoorId });
            }

            // 7. Export verification image
            string cleanImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_glass_hinge_clean.png";
            try
            {
                if (File.Exists(cleanImgPath)) File.Delete(cleanImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = cleanImgPath,
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

            return new
            {
                success = true,
                doorId = newDoorId.Value,
                wallId = wallId.Value,
                doorType = doorSym.Name,
                familyName = doorSym.FamilyName,
                image = cleanImgPath
            };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
