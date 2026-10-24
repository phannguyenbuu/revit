using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class RebuildFamilyLoadOptions : IFamilyLoadOptions
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

    public static class RebuildDoubleSwingDoorFamily
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

                using (var tx = new Transaction(famDoc, "Build Double Swing Door"))
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
                    double L = 0.900 * M2FT; // leaf length 900mm
                    double T = 0.050 * M2FT; // leaf thickness 50mm
                    double cos45 = Math.Sqrt(2.0) / 2.0;
                    double sin45 = cos45;

                    // 1. SWING ARCS (4 arcs)
                    // Arc 1: Left Exterior (swings outward into +Y)
                    // Center (-R, 0), Start (0, 0), End (-R, +R), Mid (-R + R*cos45, R*sin45)
                    var a1 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(-R, R, 0),
                        new XYZ(-R + R * cos45, R * sin45, 0)
                    );
                    var sc1 = famDoc.FamilyCreate.NewSymbolicCurve(a1, refLevelPlane);
                    if (planSwingStyle != null) sc1.Subcategory = planSwingStyle;

                    // Arc 2: Left Interior (swings inward into -Y)
                    // Center (-R, 0), Start (-R, -R), End (0, 0), Mid (-R + R*cos45, -R*sin45)
                    var a2 = Arc.Create(
                        new XYZ(-R, -R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(-R + R * cos45, -R * sin45, 0)
                    );
                    var sc2 = famDoc.FamilyCreate.NewSymbolicCurve(a2, refLevelPlane);
                    if (planSwingStyle != null) sc2.Subcategory = planSwingStyle;

                    // Arc 3: Right Exterior (swings outward into +Y)
                    // Center (+R, 0), Start (+R, +R), End (0, 0), Mid (+R - R*cos45, R*sin45)
                    var a3 = Arc.Create(
                        new XYZ(+R, R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(+R - R * cos45, R * sin45, 0)
                    );
                    var sc3 = famDoc.FamilyCreate.NewSymbolicCurve(a3, refLevelPlane);
                    if (planSwingStyle != null) sc3.Subcategory = planSwingStyle;

                    // Arc 4: Right Interior (swings inward into -Y)
                    // Center (+R, 0), Start (0, 0), End (+R, -R), Mid (+R - R*cos45, -R*sin45)
                    var a4 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(+R, -R, 0),
                        new XYZ(+R - R * cos45, -R * sin45, 0)
                    );
                    var sc4 = famDoc.FamilyCreate.NewSymbolicCurve(a4, refLevelPlane);
                    if (planSwingStyle != null) sc4.Subcategory = planSwingStyle;

                    // 2. DOOR LEAF RECTANGLES (4 leaves, each 900mm x 50mm, matching CAD)
                    // Helper action to draw leaf rectangle
                    Action<XYZ, XYZ, XYZ> addLeafRect = (hinge, dir, normal) =>
                    {
                        var p0 = hinge;
                        var p1 = hinge + dir * L;
                        var p2 = hinge + dir * L + normal * T;
                        var p3 = hinge + normal * T;

                        var l01 = famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p0, p1), refLevelPlane);
                        var l12 = famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p1, p2), refLevelPlane);
                        var l23 = famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p2, p3), refLevelPlane);
                        var l30 = famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p3, p0), refLevelPlane);

                        if (panelStyle != null)
                        {
                            l01.Subcategory = panelStyle;
                            l12.Subcategory = panelStyle;
                            l23.Subcategory = panelStyle;
                            l30.Subcategory = panelStyle;
                        }
                    };

                    // Leaf 1: Left Hinge (-R, 0), swinging into Exterior (+Y, angle +45 deg)
                    // dir = (cos45, sin45), normal = (-sin45, cos45)
                    addLeafRect(new XYZ(-R, 0, 0), new XYZ(cos45, sin45, 0), new XYZ(-sin45, cos45, 0));

                    // Leaf 2: Left Hinge (-R, 0), swinging into Interior (-Y, angle -45 deg)
                    // dir = (cos45, -sin45), normal = (sin45, cos45)
                    addLeafRect(new XYZ(-R, 0, 0), new XYZ(cos45, -sin45, 0), new XYZ(sin45, cos45, 0));

                    // Leaf 3: Right Hinge (+R, 0), swinging into Exterior (+Y, angle +135 deg)
                    // dir = (-cos45, sin45), normal = (sin45, cos45)
                    addLeafRect(new XYZ(+R, 0, 0), new XYZ(-cos45, sin45, 0), new XYZ(sin45, cos45, 0));

                    // Leaf 4: Right Hinge (+R, 0), swinging into Interior (-Y, angle -135 deg)
                    // dir = (-cos45, -sin45), normal = (-sin45, cos45)
                    addLeafRect(new XYZ(+R, 0, 0), new XYZ(-cos45, -sin45, 0), new XYZ(-sin45, cos45, 0));

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
                using (var txLoad = new Transaction(doc, "Reload Double Swing Door Family D1"))
                {
                    txLoad.Start();
                    doc.LoadFamily(rfaPath, new RebuildFamilyLoadOptions(), out loadedFam);
                    txLoad.Commit();
                }

                // Verify placed door 2364731
                var door = doc.GetElement(new ElementId(2364731L)) as FamilyInstance;
                if (door != null)
                {
                    using (var txInst = new Transaction(doc, "Update Door D1 Instance"))
                    {
                        txInst.Start();
                        var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                        if (pMark != null && pMark.AsString() != "D1") pMark.Set("D1");
                        txInst.Commit();
                    }
                }

                return new
                {
                    success = true,
                    rfaPath = rfaPath,
                    loadedFamName = loadedFam?.Name,
                    doorInstanceId = door?.Id.Value
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
