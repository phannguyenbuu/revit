using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class RebuildDoubleSwingDoorClean
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
                var doorCat = famDoc.OwnerFamily.FamilyCategory;
                if (doorCat != null && doorCat.SubCategories != null)
                {
                    foreach (Category sc in doorCat.SubCategories)
                    {
                        if (sc.Name.Equals("Plan Swing", StringComparison.OrdinalIgnoreCase))
                            planSwingStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                        if (sc.Name.Equals("Panel", StringComparison.OrdinalIgnoreCase))
                            panelStyle = sc.GetGraphicsStyle(GraphicsStyleType.Projection);
                    }
                }

                using (var tx = new Transaction(famDoc, "Build Double Swing Door Clean"))
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

                    double W = 1.900 * M2FT;
                    double R = W / 2.0; // 0.950m in ft
                    double cos45 = Math.Sqrt(2.0) / 2.0;
                    double sin45 = cos45;

                    // 1. SWING ARCS (4 arcs, clean thin lines)
                    // Arc 1: Left Exterior (swings outward into +Y)
                    var a1 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(-R, R, 0),
                        new XYZ(-R + R * cos45, R * sin45, 0)
                    );
                    var sc1 = famDoc.FamilyCreate.NewSymbolicCurve(a1, refLevelPlane);
                    if (planSwingStyle != null) sc1.Subcategory = planSwingStyle;

                    // Arc 2: Left Interior (swings inward into -Y)
                    var a2 = Arc.Create(
                        new XYZ(-R, -R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(-R + R * cos45, -R * sin45, 0)
                    );
                    var sc2 = famDoc.FamilyCreate.NewSymbolicCurve(a2, refLevelPlane);
                    if (planSwingStyle != null) sc2.Subcategory = planSwingStyle;

                    // Arc 3: Right Exterior (swings outward into +Y)
                    var a3 = Arc.Create(
                        new XYZ(+R, R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(+R - R * cos45, R * sin45, 0)
                    );
                    var sc3 = famDoc.FamilyCreate.NewSymbolicCurve(a3, refLevelPlane);
                    if (planSwingStyle != null) sc3.Subcategory = planSwingStyle;

                    // Arc 4: Right Interior (swings inward into -Y)
                    var a4 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(+R, -R, 0),
                        new XYZ(+R - R * cos45, -R * sin45, 0)
                    );
                    var sc4 = famDoc.FamilyCreate.NewSymbolicCurve(a4, refLevelPlane);
                    if (planSwingStyle != null) sc4.Subcategory = planSwingStyle;

                    // 2. CLEAN SINGLE-LINE LEAVES AT 45 DEG (Matching professional architectural standards)
                    // Leaf 1: Left Hinge (-R, 0) -> Exterior (+Y)
                    var l1 = Line.CreateBound(
                        new XYZ(-R, 0, 0),
                        new XYZ(-R + R * cos45, R * sin45, 0)
                    );
                    var scl1 = famDoc.FamilyCreate.NewSymbolicCurve(l1, refLevelPlane);
                    if (panelStyle != null) scl1.Subcategory = panelStyle;

                    // Leaf 2: Left Hinge (-R, 0) -> Interior (-Y)
                    var l2 = Line.CreateBound(
                        new XYZ(-R, 0, 0),
                        new XYZ(-R + R * cos45, -R * sin45, 0)
                    );
                    var scl2 = famDoc.FamilyCreate.NewSymbolicCurve(l2, refLevelPlane);
                    if (panelStyle != null) scl2.Subcategory = panelStyle;

                    // Leaf 3: Right Hinge (+R, 0) -> Exterior (+Y)
                    var l3 = Line.CreateBound(
                        new XYZ(+R, 0, 0),
                        new XYZ(+R - R * cos45, R * sin45, 0)
                    );
                    var scl3 = famDoc.FamilyCreate.NewSymbolicCurve(l3, refLevelPlane);
                    if (panelStyle != null) scl3.Subcategory = panelStyle;

                    // Leaf 4: Right Hinge (+R, 0) -> Interior (-Y)
                    var l4 = Line.CreateBound(
                        new XYZ(+R, 0, 0),
                        new XYZ(+R - R * cos45, -R * sin45, 0)
                    );
                    var scl4 = famDoc.FamilyCreate.NewSymbolicCurve(l4, refLevelPlane);
                    if (panelStyle != null) scl4.Subcategory = panelStyle;

                    // Center closed line (dotted / thin line for door closed position)
                    var lClosed = Line.CreateBound(
                        new XYZ(-R, 0, 0),
                        new XYZ(+R, 0, 0)
                    );
                    var scClosed = famDoc.FamilyCreate.NewSymbolicCurve(lClosed, refLevelPlane);
                    if (planSwingStyle != null) scClosed.Subcategory = planSwingStyle;

                    // Create Type "D1 - Kính Cường Lực 10mm 2 Cánh"
                    var newType = fMgr.NewType("D1 - Kính Cường Lực 10mm 2 Cánh");
                    fMgr.CurrentType = newType;

                    var pDesc = fMgr.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
                             ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Description", StringComparison.OrdinalIgnoreCase));
                    if (pDesc != null) fMgr.Set(pDesc, "Cửa kính cường lực 10mm 2 cánh bản lề sàn bật 2 chiều (D1)");

                    tx.Commit();
                }

                // Save family to disk
                var saveOpt = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(rfaPath, saveOpt);
                famDoc.Close(false);

                // Reload family into project document
                Family loadedFam = null;
                using (var txLoad = new Transaction(doc, "Reload Double Swing Door Clean"))
                {
                    txLoad.Start();
                    doc.LoadFamily(rfaPath, new RebuildFamilyLoadOptions(), out loadedFam);
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
    }
}
