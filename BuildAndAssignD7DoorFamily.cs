using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class D7FamilyLoadOptions : IFamilyLoadOptions
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

    public static class BuildAndAssignD7DoorFamily
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Door.rft";
            if (!File.Exists(templatePath)) return new { error = $"Template not found: {templatePath}" };

            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Cua_Chong_Chay_D7_1Canh.rfa";

            Document? famDoc = null;
            try
            {
                famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Could not create family document" };

                // Get Ref. Level sketch plane
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
                        using var txSp = new Transaction(famDoc, "Create Sketch Plane");
                        txSp.Start();
                        refLevelPlane = SketchPlane.Create(famDoc, plane);
                        txSp.Commit();
                    }
                }

                if (refLevelPlane == null) return new { error = "Cannot find or create Ref. Level sketch plane" };

                // Subcategories
                Category? planSwingCat = null;
                Category? panelCat = null;
                Category? frameCat = null;
                GraphicsStyle? planSwingStyle = null;
                GraphicsStyle? panelStyle = null;
                GraphicsStyle? frameStyle = null;

                var doorCat = famDoc.OwnerFamily.FamilyCategory;
                if (doorCat != null && doorCat.SubCategories != null)
                {
                    foreach (Category sc in doorCat.SubCategories)
                    {
                        if (sc.Name.Equals("Plan Swing", StringComparison.OrdinalIgnoreCase))
                        {
                            planSwingCat = sc;
                            planSwingStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        }
                        else if (sc.Name.Equals("Panel", StringComparison.OrdinalIgnoreCase))
                        {
                            panelCat = sc;
                            panelStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        }
                        else if (sc.Name.Equals("Frame/Mullion", StringComparison.OrdinalIgnoreCase))
                        {
                            frameCat = sc;
                            frameStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        }
                    }
                }

                // Geometry dimensions (in feet)
                double W = 1200.0 * MM_TO_FT;
                double H = 2200.0 * MM_TO_FT;
                double frameThick = 50.0 * MM_TO_FT;   // 50mm jamb width
                double frameDepth = 200.0 * MM_TO_FT;  // 200mm frame depth for 200mm wall
                double leafThick = 45.0 * MM_TO_FT;    // 45mm door leaf thickness
                double clearWidth = W - 2.0 * frameThick; // 1100mm leaf length

                using (var tx = new Transaction(famDoc, "Build Fire Door D7"))
                {
                    tx.Start();

                    var fMgr = famDoc.FamilyManager;

                    // Set Width and Height parameters
                    var pWidth = fMgr.get_Parameter(BuiltInParameter.DOOR_WIDTH)
                              ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Width", StringComparison.OrdinalIgnoreCase));
                    if (pWidth != null) fMgr.Set(pWidth, W);

                    var pHeight = fMgr.get_Parameter(BuiltInParameter.DOOR_HEIGHT)
                               ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Height", StringComparison.OrdinalIgnoreCase));
                    if (pHeight != null) fMgr.Set(pHeight, H);

                    // Add / Set Description and Fire Rating
                    var pDesc = fMgr.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
                             ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Description", StringComparison.OrdinalIgnoreCase));
                    if (pDesc != null) fMgr.Set(pDesc, "Cửa thép chống cháy 1 cánh D7 (EI 70) - Góc mở 30%");

                    var pFire = fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Fire Rating", StringComparison.OrdinalIgnoreCase));
                    if (pFire != null) fMgr.Set(pFire, "EI 70 (70 phút)");

                    // 1. 3D SOLIDS
                    // Left Jamb: [-W/2, -frameDepth/2] to [-W/2 + frameThick, frameDepth/2], Z: [0, H]
                    var leftJamb = CreateBoxExtrusion(famDoc, refLevelPlane,
                        new XYZ(-W / 2.0, -frameDepth / 2.0, 0),
                        new XYZ(-W / 2.0 + frameThick, frameDepth / 2.0, 0),
                        H, frameCat);

                    // Right Jamb: [W/2 - frameThick, -frameDepth/2] to [W/2, frameDepth/2], Z: [0, H]
                    var rightJamb = CreateBoxExtrusion(famDoc, refLevelPlane,
                        new XYZ(W / 2.0 - frameThick, -frameDepth / 2.0, 0),
                        new XYZ(W / 2.0, frameDepth / 2.0, 0),
                        H, frameCat);

                    // Header: [-W/2 + frameThick, -frameDepth/2] to [W/2 - frameThick, frameDepth/2], Z: [H - frameThick, H]
                    var header = CreateBoxExtrusion(famDoc, refLevelPlane,
                        new XYZ(-W / 2.0 + frameThick, -frameDepth / 2.0, 0),
                        new XYZ(W / 2.0 - frameThick, frameDepth / 2.0, 0),
                        H, frameCat);
                    header.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM)?.Set(H - frameThick);
                    header.get_Parameter(BuiltInParameter.EXTRUSION_END_PARAM)?.Set(H);

                    // 3D Door Leaf (Closed position): Z: [0, H - frameThick]
                    // Located flush with exterior face of frame
                    var leaf3D = CreateBoxExtrusion(famDoc, refLevelPlane,
                        new XYZ(-W / 2.0 + frameThick, frameDepth / 2.0 - leafThick, 0),
                        new XYZ(W / 2.0 - frameThick, frameDepth / 2.0, 0),
                        H - frameThick, panelCat);

                    // Set 3D leaf visibility: Hide in Plan/RCP Cut so 2D swing shows cleanly!
                    var leafVis = new FamilyElementVisibility(FamilyElementVisibilityType.Model)
                    {
                        IsShownInPlanRCPCut = false,
                        IsShownInFine = true,
                        IsShownInMedium = true,
                        IsShownInCoarse = true
                    };
                    leaf3D.SetVisibility(leafVis);

                    // 2. 2D SYMBOLIC LINES ON REF. LEVEL (Plan Representation)
                    // Hinge Point: at Left jamb inner corner, exterior face
                    var hinge = new XYZ(-W / 2.0 + frameThick, frameDepth / 2.0, 0);

                    // Leaf vector at 30 degrees open angle
                    double rad30 = 30.0 * Math.PI / 180.0;
                    double cos30 = Math.Cos(rad30);
                    double sin30 = Math.Sin(rad30);
                    var uDir = new XYZ(cos30, sin30, 0); // Along leaf
                    var nDir = new XYZ(-sin30, cos30, 0); // Normal into exterior

                    // 2D Leaf Rectangle (4 lines, subcategory Panel)
                    var p0 = hinge;
                    var p1 = hinge + uDir * clearWidth;
                    var p2 = p1 + nDir * leafThick;
                    var p3 = p0 + nDir * leafThick;
                    AddRectSymbolic(famDoc, refLevelPlane, p0, p1, p2, p3, panelStyle);

                    // 2D Swing Arc (30 degree circular arc from closed to 30 deg open)
                    // Closed position end point
                    var pClosed = hinge + new XYZ(clearWidth, 0, 0);
                    // Midpoint at 15 degrees
                    double rad15 = 15.0 * Math.PI / 180.0;
                    var pMid = hinge + new XYZ(Math.Cos(rad15) * clearWidth, Math.Sin(rad15) * clearWidth, 0);
                    // Open position end point (p1)
                    var pOpen = p1;

                    var swingArc = Arc.Create(pClosed, pOpen, pMid);
                    var scArc = famDoc.FamilyCreate.NewSymbolicCurve(swingArc, refLevelPlane);
                    if (planSwingStyle != null) scArc.Subcategory = planSwingStyle;

                    // 2D Jamb Rectangles
                    // Left jamb 2D
                    var jL0 = new XYZ(-W / 2.0, -frameDepth / 2.0, 0);
                    var jL1 = new XYZ(-W / 2.0 + frameThick, -frameDepth / 2.0, 0);
                    var jL2 = new XYZ(-W / 2.0 + frameThick, frameDepth / 2.0, 0);
                    var jL3 = new XYZ(-W / 2.0, frameDepth / 2.0, 0);
                    AddRectSymbolic(famDoc, refLevelPlane, jL0, jL1, jL2, jL3, frameStyle);

                    // Right jamb 2D
                    var jR0 = new XYZ(W / 2.0 - frameThick, -frameDepth / 2.0, 0);
                    var jR1 = new XYZ(W / 2.0, -frameDepth / 2.0, 0);
                    var jR2 = new XYZ(W / 2.0, frameDepth / 2.0, 0);
                    var jR3 = new XYZ(W / 2.0 - frameThick, frameDepth / 2.0, 0);
                    AddRectSymbolic(famDoc, refLevelPlane, jR0, jR1, jR2, jR3, frameStyle);

                    // Create Type 1: D7_1200x2200
                    var type1 = fMgr.NewType("D7_1200x2200");
                    fMgr.CurrentType = type1;

                    // Create Type 2: D7_1200x2400
                    var type2 = fMgr.NewType("D7_1200x2400");
                    fMgr.CurrentType = type2;
                    if (pHeight != null) fMgr.Set(pHeight, 2400.0 * MM_TO_FT);

                    // Switch back to D7_1200x2200 as current
                    fMgr.CurrentType = type1;

                    tx.Commit();
                }

                // Save family to disk
                var saveOpt = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(rfaPath, saveOpt);
                famDoc.Close(false);
                famDoc = null;

                // Load family into Project
                Family loadedFam;
                using (var txLoad = new Transaction(doc, "Load Family Cua_Chong_Chay_D7_1Canh"))
                {
                    txLoad.Start();
                    doc.LoadFamily(rfaPath, new D7FamilyLoadOptions(), out loadedFam);
                    txLoad.Commit();
                }

                if (loadedFam == null)
                {
                    loadedFam = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name == "Cua_Chong_Chay_D7_1Canh");
                }

                if (loadedFam == null) return new { error = "Family loadedFam is null after load" };

                // Get Symbol "D7_1200x2200"
                FamilySymbol? targetSymbol = null;
                foreach (ElementId symId in loadedFam.GetFamilySymbolIds())
                {
                    var sym = doc.GetElement(symId) as FamilySymbol;
                    if (sym != null && sym.Name.Contains("1200x2200"))
                    {
                        targetSymbol = sym;
                        break;
                    }
                }
                if (targetSymbol == null)
                {
                    targetSymbol = doc.GetElement(loadedFam.GetFamilySymbolIds().First()) as FamilySymbol;
                }

                if (targetSymbol == null) return new { error = "No symbol found in loaded family" };

                // Activate symbol
                using (var txAct = new Transaction(doc, "Activate Symbol D7"))
                {
                    txAct.Start();
                    if (!targetSymbol.IsActive) targetSymbol.Activate();
                    txAct.Commit();
                }

                // Now update Door 1 (2360900) and Door 2 (2360910)
                var updatedDoors = new List<object>();
                long[] targetIds = new long[] { 2360900, 2360910 };

                using (var txAssign = new Transaction(doc, "Assign D7 Fire Door to Selected Doors"))
                {
                    txAssign.Start();

                    foreach (long id in targetIds)
                    {
                        var door = doc.GetElement(new ElementId(id)) as FamilyInstance;
                        if (door == null) continue;

                        door.ChangeTypeId(targetSymbol.Id);

                        // Ensure Mark parameter
                        var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                        string markVal = id == 2360900 ? "D7-1" : "D7-2";
                        if (pMark != null) pMark.Set(markVal);

                        var loc = (door.Location as LocationPoint)?.Point;
                        updatedDoors.Add(new
                        {
                            id = door.Id.Value,
                            mark = markVal,
                            familyName = door.Symbol.FamilyName,
                            typeName = door.Symbol.Name,
                            x = loc != null ? loc.X * 304.8 : 0,
                            y = loc != null ? loc.Y * 304.8 : 0
                        });
                    }

                    txAssign.Commit();
                }

                return new
                {
                    success = true,
                    familyName = loadedFam.Name,
                    symbolName = targetSymbol.Name,
                    updatedDoors = updatedDoors
                };
            }
            catch (Exception ex)
            {
                if (famDoc != null) try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }

        private static Extrusion CreateBoxExtrusion(Document doc, SketchPlane sp, XYZ pMin, XYZ pMax, double height, Category? subCat)
        {
            var ca = new CurveArray();
            var p0 = new XYZ(pMin.X, pMin.Y, 0);
            var p1 = new XYZ(pMax.X, pMin.Y, 0);
            var p2 = new XYZ(pMax.X, pMax.Y, 0);
            var p3 = new XYZ(pMin.X, pMax.Y, 0);

            ca.Append(Line.CreateBound(p0, p1));
            ca.Append(Line.CreateBound(p1, p2));
            ca.Append(Line.CreateBound(p2, p3));
            ca.Append(Line.CreateBound(p3, p0));

            var caa = new CurveArrArray();
            caa.Append(ca);

            var ext = doc.FamilyCreate.NewExtrusion(true, caa, sp, height);
            if (subCat != null) ext.Subcategory = subCat;
            return ext;
        }

        private static void AddRectSymbolic(Document doc, SketchPlane sp, XYZ p0, XYZ p1, XYZ p2, XYZ p3, GraphicsStyle? style)
        {
            var l01 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p0, p1), sp);
            var l12 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p1, p2), sp);
            var l23 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p2, p3), sp);
            var l30 = doc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p3, p0), sp);

            if (style != null)
            {
                l01.Subcategory = style;
                l12.Subcategory = style;
                l23.Subcategory = style;
                l30.Subcategory = style;
            }
        }
    }
}
