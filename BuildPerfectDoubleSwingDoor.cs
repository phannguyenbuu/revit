using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class PerfectDoorLoadOptions : IFamilyLoadOptions
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

    public static class BuildPerfectDoubleSwingDoor
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Door.rft";
            if (!File.Exists(templatePath)) return new { error = "Template not found" };

            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Cua_Kinh_Cuong_Luc_2Canh_Bat2Chieu.rfa";

            Document famDoc = null;
            try
            {
                famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Could not create family doc" };

                // Find Ref. Level sketch plane
                var sketchPlanes = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(SketchPlane))
                    .Cast<SketchPlane>()
                    .ToList();
                var refLevelPlane = sketchPlanes.FirstOrDefault(p => p.Name.Equals("Ref. Level", StringComparison.OrdinalIgnoreCase))
                                 ?? sketchPlanes.FirstOrDefault();

                if (refLevelPlane == null)
                {
                    var refLevel = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .FirstOrDefault();
                    if (refLevel != null)
                    {
                        var plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, refLevel.Elevation));
                        using (var txSp = new Transaction(famDoc, "Create Sketch Plane"))
                        {
                            txSp.Start();
                            refLevelPlane = SketchPlane.Create(famDoc, plane);
                            txSp.Commit();
                        }
                    }
                }

                // Subcategories
                GraphicsStyle planSwingStyle = null;
                GraphicsStyle panelStyle = null;
                GraphicsStyle frameStyle = null;
                Category glassSubCat = null;
                Category frameSubCat = null;

                var doorCat = famDoc.OwnerFamily.FamilyCategory;
                if (doorCat != null && doorCat.SubCategories != null)
                {
                    foreach (Category sc in doorCat.SubCategories)
                    {
                        if (sc.Name.Equals("Plan Swing", StringComparison.OrdinalIgnoreCase))
                            planSwingStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        else if (sc.Name.Equals("Panel", StringComparison.OrdinalIgnoreCase))
                            panelStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        else if (sc.Name.Equals("Frame/Mullion", StringComparison.OrdinalIgnoreCase))
                        {
                            frameStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                            frameSubCat = sc;
                        }
                        else if (sc.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase))
                            glassSubCat = sc;
                    }
                }

                using (var tx = new Transaction(famDoc, "Build Perfect Double Swing Door"))
                {
                    tx.Start();

                    // Set Width = 1900 mm, Height = 2700 mm
                    var fMgr = famDoc.FamilyManager;
                    var pWidth = fMgr.get_Parameter(BuiltInParameter.DOOR_WIDTH)
                              ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Width", StringComparison.OrdinalIgnoreCase));
                    if (pWidth != null) fMgr.Set(pWidth, 1.900 * M2FT);

                    var pHeight = fMgr.get_Parameter(BuiltInParameter.DOOR_HEIGHT)
                               ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Height", StringComparison.OrdinalIgnoreCase));
                    if (pHeight != null) fMgr.Set(pHeight, 2.700 * M2FT);

                    // ==========================================
                    // 1. 3D GEOMETRY (Extrusions)
                    // ==========================================
                    // Visibility setting: 3D only, invisible in Plan/RCP
                    var vis3DOnly = new FamilyElementVisibility(FamilyElementVisibilityType.Model)
                    {
                        IsShownInPlanRCPCut = false,
                        IsShownInCoarse = true,
                        IsShownInMedium = true,
                        IsShownInFine = true
                    };

                    // 1A. Door Jamb Frames (2 vertical columns at sides: 50mm wide x 100mm deep x 2700mm high)
                    // Left Jamb 3D
                    CurveLoop loopJambL = new CurveLoop();
                    double jL_x0 = -0.950 * M2FT, jL_x1 = -0.900 * M2FT;
                    double j_y0 = -0.050 * M2FT, j_y1 = 0.050 * M2FT;
                    loopJambL.Append(Line.CreateBound(new XYZ(jL_x0, j_y0, 0), new XYZ(jL_x1, j_y0, 0)));
                    loopJambL.Append(Line.CreateBound(new XYZ(jL_x1, j_y0, 0), new XYZ(jL_x1, j_y1, 0)));
                    loopJambL.Append(Line.CreateBound(new XYZ(jL_x1, j_y1, 0), new XYZ(jL_x0, j_y1, 0)));
                    loopJambL.Append(Line.CreateBound(new XYZ(jL_x0, j_y1, 0), new XYZ(jL_x0, j_y0, 0)));
                    var extJambL = famDoc.FamilyCreate.NewExtrusion(true, CreateCurveArrArray(loopJambL), refLevelPlane, 2.700 * M2FT);
                    extJambL.SetVisibility(vis3DOnly);
                    if (frameSubCat != null) extJambL.Subcategory = frameSubCat;

                    // Right Jamb 3D
                    CurveLoop loopJambR = new CurveLoop();
                    double jR_x0 = 0.900 * M2FT, jR_x1 = 0.950 * M2FT;
                    loopJambR.Append(Line.CreateBound(new XYZ(jR_x0, j_y0, 0), new XYZ(jR_x1, j_y0, 0)));
                    loopJambR.Append(Line.CreateBound(new XYZ(jR_x1, j_y0, 0), new XYZ(jR_x1, j_y1, 0)));
                    loopJambR.Append(Line.CreateBound(new XYZ(jR_x1, j_y1, 0), new XYZ(jR_x0, j_y1, 0)));
                    loopJambR.Append(Line.CreateBound(new XYZ(jR_x0, j_y1, 0), new XYZ(jR_x0, j_y0, 0)));
                    var extJambR = famDoc.FamilyCreate.NewExtrusion(true, CreateCurveArrArray(loopJambR), refLevelPlane, 2.700 * M2FT);
                    extJambR.SetVisibility(vis3DOnly);
                    if (frameSubCat != null) extJambR.Subcategory = frameSubCat;

                    // Top Frame 3D (between jambs at top: 50mm high)
                    CurveLoop loopTop = new CurveLoop();
                    loopTop.Append(Line.CreateBound(new XYZ(jL_x1, j_y0, 2.650 * M2FT), new XYZ(jR_x0, j_y0, 2.650 * M2FT)));
                    loopTop.Append(Line.CreateBound(new XYZ(jR_x0, j_y0, 2.650 * M2FT), new XYZ(jR_x0, j_y1, 2.650 * M2FT)));
                    loopTop.Append(Line.CreateBound(new XYZ(jR_x0, j_y1, 2.650 * M2FT), new XYZ(jL_x1, j_y1, 2.650 * M2FT)));
                    loopTop.Append(Line.CreateBound(new XYZ(jL_x1, j_y1, 2.650 * M2FT), new XYZ(jL_x1, j_y0, 2.650 * M2FT)));
                    var planeTop = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, 2.650 * M2FT));
                    var spTop = SketchPlane.Create(famDoc, planeTop);
                    var extTop = famDoc.FamilyCreate.NewExtrusion(true, CreateCurveArrArray(loopTop), spTop, 0.050 * M2FT);
                    extTop.SetVisibility(vis3DOnly);
                    if (frameSubCat != null) extTop.Subcategory = frameSubCat;

                    // 1B. 3D Glass Panels (10mm thick tempered glass in closed position)
                    // Left Panel
                    CurveLoop loopGlassL = new CurveLoop();
                    double gL_x0 = -0.880 * M2FT, gL_x1 = -0.005 * M2FT;
                    double g_y0 = -0.005 * M2FT, g_y1 = 0.005 * M2FT;
                    loopGlassL.Append(Line.CreateBound(new XYZ(gL_x0, g_y0, 0.060 * M2FT), new XYZ(gL_x1, g_y0, 0.060 * M2FT)));
                    loopGlassL.Append(Line.CreateBound(new XYZ(gL_x1, g_y0, 0.060 * M2FT), new XYZ(gL_x1, g_y1, 0.060 * M2FT)));
                    loopGlassL.Append(Line.CreateBound(new XYZ(gL_x1, g_y1, 0.060 * M2FT), new XYZ(gL_x0, g_y1, 0.060 * M2FT)));
                    loopGlassL.Append(Line.CreateBound(new XYZ(gL_x0, g_y1, 0.060 * M2FT), new XYZ(gL_x0, g_y0, 0.060 * M2FT)));
                    var planeGlass = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, new XYZ(0, 0, 0.060 * M2FT));
                    var spGlass = SketchPlane.Create(famDoc, planeGlass);
                    var extGlassL = famDoc.FamilyCreate.NewExtrusion(true, CreateCurveArrArray(loopGlassL), spGlass, (2.640 - 0.060) * M2FT);
                    extGlassL.SetVisibility(vis3DOnly);
                    if (glassSubCat != null) extGlassL.Subcategory = glassSubCat;

                    // Right Panel
                    CurveLoop loopGlassR = new CurveLoop();
                    double gR_x0 = 0.005 * M2FT, gR_x1 = 0.880 * M2FT;
                    loopGlassR.Append(Line.CreateBound(new XYZ(gR_x0, g_y0, 0.060 * M2FT), new XYZ(gR_x1, g_y0, 0.060 * M2FT)));
                    loopGlassR.Append(Line.CreateBound(new XYZ(gR_x1, g_y0, 0.060 * M2FT), new XYZ(gR_x1, g_y1, 0.060 * M2FT)));
                    loopGlassR.Append(Line.CreateBound(new XYZ(gR_x1, g_y1, 0.060 * M2FT), new XYZ(gR_x0, g_y1, 0.060 * M2FT)));
                    loopGlassR.Append(Line.CreateBound(new XYZ(gR_x0, g_y1, 0.060 * M2FT), new XYZ(gR_x0, g_y0, 0.060 * M2FT)));
                    var extGlassR = famDoc.FamilyCreate.NewExtrusion(true, CreateCurveArrArray(loopGlassR), spGlass, (2.640 - 0.060) * M2FT);
                    extGlassR.SetVisibility(vis3DOnly);
                    if (glassSubCat != null) extGlassR.Subcategory = glassSubCat;

                    // ==========================================
                    // 2. 2D PLAN LINEWORK (Symbolic Curves)
                    // ==========================================
                    double W = 1.900 * M2FT;
                    double R_opening = W / 2.0; // 0.950m in ft
                    double L_leaf = 0.880 * M2FT; // 880mm leaf
                    double hingeOffset = 0.880 * M2FT;
                    double t_leaf = 0.035 * M2FT; // 35mm leaf thickness
                    double ht = t_leaf / 2.0;

                    // 2A. Jambs 2D in Plan (Frame/Mullion)
                    AddRectCurves(famDoc, refLevelPlane, frameStyle, -0.950 * M2FT, -0.900 * M2FT, -0.050 * M2FT, 0.050 * M2FT);
                    AddRectCurves(famDoc, refLevelPlane, frameStyle, 0.900 * M2FT, 0.950 * M2FT, -0.050 * M2FT, 0.050 * M2FT);

                    // 2B. Floor Spring Box (Bản lề sàn) at hinges: 100mm x 50mm
                    AddRectCurves(famDoc, refLevelPlane, frameStyle, (-0.880 - 0.050) * M2FT, (-0.880 + 0.050) * M2FT, -0.025 * M2FT, 0.025 * M2FT);
                    AddRectCurves(famDoc, refLevelPlane, frameStyle, (0.880 - 0.050) * M2FT, (0.880 + 0.050) * M2FT, -0.025 * M2FT, 0.025 * M2FT);

                    // 2C. Center Closed Position Line (Plan Swing)
                    var lClosed = Line.CreateBound(new XYZ(-hingeOffset, 0, 0), new XYZ(hingeOffset, 0, 0));
                    var scClosed = famDoc.FamilyCreate.NewSymbolicCurve(lClosed, refLevelPlane);
                    if (planSwingStyle != null) scClosed.Subcategory = planSwingStyle;

                    // 2D. 4 Door Leaves at 45 Degrees with 35mm thickness
                    double cos45 = Math.Sqrt(2.0) / 2.0;
                    double sin45 = cos45;

                    // Leaf 1: Left Hinge (-hingeOffset, 0) -> Exterior (+Y) at 45 deg
                    XYZ hL = new XYZ(-hingeOffset, 0, 0);
                    XYZ u1 = new XYZ(cos45, sin45, 0);
                    XYZ n1 = new XYZ(-sin45, cos45, 0);
                    AddLeafRectangle(famDoc, refLevelPlane, panelStyle, hL, u1, n1, L_leaf, ht);

                    // Leaf 2: Left Hinge (-hingeOffset, 0) -> Interior (-Y) at -45 deg
                    XYZ u2 = new XYZ(cos45, -sin45, 0);
                    XYZ n2 = new XYZ(sin45, cos45, 0);
                    AddLeafRectangle(famDoc, refLevelPlane, panelStyle, hL, u2, n2, L_leaf, ht);

                    // Leaf 3: Right Hinge (+hingeOffset, 0) -> Exterior (+Y) at 135 deg
                    XYZ hR = new XYZ(hingeOffset, 0, 0);
                    XYZ u3 = new XYZ(-cos45, sin45, 0);
                    XYZ n3 = new XYZ(-sin45, -cos45, 0);
                    AddLeafRectangle(famDoc, refLevelPlane, panelStyle, hR, u3, n3, L_leaf, ht);

                    // Leaf 4: Right Hinge (+hingeOffset, 0) -> Interior (-Y) at -135 deg
                    XYZ u4 = new XYZ(-cos45, -sin45, 0);
                    XYZ n4 = new XYZ(sin45, -cos45, 0);
                    AddLeafRectangle(famDoc, refLevelPlane, panelStyle, hR, u4, n4, L_leaf, ht);

                    // 2E. The 4 SWING ARCS (45 degrees exact, connecting center (0,0) to leaf tips!)
                    double cos225 = Math.Cos(Math.PI / 8.0); // 22.5 deg
                    double sin225 = Math.Sin(Math.PI / 8.0);

                    // Arc 1: Left Exterior (+Y)
                    // Start at (0, 0, 0), End at hL + L_leaf * u1, Mid at hL + L_leaf * (cos22.5, sin22.5, 0)
                    XYZ arc1_start = new XYZ(0, 0, 0);
                    XYZ arc1_end = hL + L_leaf * u1;
                    XYZ arc1_mid = hL + new XYZ(L_leaf * cos225, L_leaf * sin225, 0);
                    var a1 = Arc.Create(arc1_start, arc1_end, arc1_mid);
                    var sc1 = famDoc.FamilyCreate.NewSymbolicCurve(a1, refLevelPlane);
                    if (planSwingStyle != null) sc1.Subcategory = planSwingStyle;

                    // Arc 2: Left Interior (-Y)
                    XYZ arc2_start = new XYZ(0, 0, 0);
                    XYZ arc2_end = hL + L_leaf * u2;
                    XYZ arc2_mid = hL + new XYZ(L_leaf * cos225, -L_leaf * sin225, 0);
                    var a2 = Arc.Create(arc2_start, arc2_end, arc2_mid);
                    var sc2 = famDoc.FamilyCreate.NewSymbolicCurve(a2, refLevelPlane);
                    if (planSwingStyle != null) sc2.Subcategory = planSwingStyle;

                    // Arc 3: Right Exterior (+Y)
                    XYZ arc3_start = new XYZ(0, 0, 0);
                    XYZ arc3_end = hR + L_leaf * u3;
                    XYZ arc3_mid = hR + new XYZ(-L_leaf * cos225, L_leaf * sin225, 0);
                    var a3 = Arc.Create(arc3_start, arc3_end, arc3_mid);
                    var sc3 = famDoc.FamilyCreate.NewSymbolicCurve(a3, refLevelPlane);
                    if (planSwingStyle != null) sc3.Subcategory = planSwingStyle;

                    // Arc 4: Right Interior (-Y)
                    XYZ arc4_start = new XYZ(0, 0, 0);
                    XYZ arc4_end = hR + L_leaf * u4;
                    XYZ arc4_mid = hR + new XYZ(-L_leaf * cos225, -L_leaf * sin225, 0);
                    var a4 = Arc.Create(arc4_start, arc4_end, arc4_mid);
                    var sc4 = famDoc.FamilyCreate.NewSymbolicCurve(a4, refLevelPlane);
                    if (planSwingStyle != null) sc4.Subcategory = planSwingStyle;

                    // Create Type "D1 - Kính Cường Lực 10mm 2 Cánh"
                    var newType = fMgr.NewType("D1 - Kính Cường Lực 10mm 2 Cánh");
                    fMgr.CurrentType = newType;

                    var pDesc = fMgr.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
                             ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Description", StringComparison.OrdinalIgnoreCase));
                    if (pDesc != null) fMgr.Set(pDesc, "Cửa kính cường lực 10mm 2 cánh bản lề sàn bật 2 chiều (Double Swing Door D1)");

                    tx.Commit();
                }

                // Save family to disk
                var saveOpt = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(rfaPath, saveOpt);
                famDoc.Close(false);

                // Reload family into project document
                Family loadedFam = null;
                using (var txLoad = new Transaction(doc, "Reload Perfect Double Swing Door"))
                {
                    txLoad.Start();
                    doc.LoadFamily(rfaPath, new PerfectDoorLoadOptions(), out loadedFam);
                    txLoad.Commit();
                }

                return new
                {
                    success = true,
                    rfaPath = rfaPath,
                    loadedFamName = loadedFam?.Name
                };
            }
            catch (Exception ex)
            {
                if (famDoc != null) try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }

        private static CurveArrArray CreateCurveArrArray(CurveLoop loop)
        {
            var caa = new CurveArrArray();
            var ca = new CurveArray();
            foreach (var c in loop) ca.Append(c);
            caa.Append(ca);
            return caa;
        }

        private static CurveArray ToCurveArray(CurveLoop loop)
        {
            var arr = new CurveArray();
            foreach (var c in loop) arr.Append(c);
            return arr;
        }

        private static void AddRectCurves(Document doc, SketchPlane sp, GraphicsStyle style, double x0, double x1, double y0, double y1)
        {
            var p1 = new XYZ(x0, y0, 0);
            var p2 = new XYZ(x1, y0, 0);
            var p3 = new XYZ(x1, y1, 0);
            var p4 = new XYZ(x0, y1, 0);

            var c1 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p1, p2), sp);
            var c2 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p2, p3), sp);
            var c3 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p3, p4), sp);
            var c4 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p4, p1), sp);

            if (style != null)
            {
                c1.Subcategory = style;
                c2.Subcategory = style;
                c3.Subcategory = style;
                c4.Subcategory = style;
            }
        }

        private static void AddLeafRectangle(Document doc, SketchPlane sp, GraphicsStyle style, XYZ hinge, XYZ u, XYZ n, double length, double halfThick)
        {
            XYZ p1 = hinge + halfThick * n;
            XYZ p2 = hinge + length * u + halfThick * n;
            XYZ p3 = hinge + length * u - halfThick * n;
            XYZ p4 = hinge - halfThick * n;

            var c1 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p1, p2), sp);
            var c2 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p2, p3), sp);
            var c3 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p3, p4), sp);
            var c4 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p4, p1), sp);

            if (style != null)
            {
                c1.Subcategory = style;
                c2.Subcategory = style;
                c3.Subcategory = style;
                c4.Subcategory = style;
            }
        }
    }
}
