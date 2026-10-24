using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class CustomFamilyLoadOptions : IFamilyLoadOptions
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

    public static class SafeInspectErowdFamily
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active doc" };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Door.rft";
            if (!File.Exists(templatePath)) return new { error = "Template not found" };

            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Cua_Kinh_Cuong_Luc_2Canh_Bat2Chieu.rfa";
            if (File.Exists(rfaPath))
            {
                try { File.Delete(rfaPath); } catch { }
            }

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
                    // Create sketch plane from level
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
                Category planSwingCat = null;
                Category panelCat = null;
                var doorCat = famDoc.OwnerFamily.FamilyCategory;
                if (doorCat != null && doorCat.SubCategories != null)
                {
                    foreach (Category sc in doorCat.SubCategories)
                    {
                        if (sc.Name.Equals("Plan Swing", StringComparison.OrdinalIgnoreCase)) planSwingCat = sc;
                        if (sc.Name.Equals("Panel", StringComparison.OrdinalIgnoreCase)) panelCat = sc;
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

                    // Door dimensions
                    double W = 1.900 * M2FT;
                    double R = W / 2.0; // 0.950m in ft
                    double cos45 = Math.Sqrt(2.0) / 2.0;

                    // Hinge points:
                    // Left hinge: (-R, 0, 0)
                    // Right hinge: (+R, 0, 0)
                    // Center point: (0, 0, 0)

                    // Arc 1: Left Exterior (swings outward into +Y)
                    // Center (-R, 0), Start (0, 0), End (-R, +R), Mid (-R + R*cos45, R*cos45)
                    var a1 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(-R, R, 0),
                        new XYZ(-R + R * cos45, R * cos45, 0)
                    );
                    var sc1 = famDoc.FamilyCreate.NewSymbolicCurve(a1, refLevelPlane);
                    if (planSwingCat != null) sc1.Subcategory = planSwingCat;

                    // Arc 2: Left Interior (swings inward into -Y)
                    // Center (-R, 0), Start (-R, -R), End (0, 0), Mid (-R + R*cos45, -R*cos45)
                    var a2 = Arc.Create(
                        new XYZ(-R, -R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(-R + R * cos45, -R * cos45, 0)
                    );
                    var sc2 = famDoc.FamilyCreate.NewSymbolicCurve(a2, refLevelPlane);
                    if (planSwingCat != null) sc2.Subcategory = planSwingCat;

                    // Arc 3: Right Exterior (swings outward into +Y)
                    // Center (+R, 0), Start (+R, +R), End (0, 0), Mid (+R - R*cos45, R*cos45)
                    var a3 = Arc.Create(
                        new XYZ(+R, R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(+R - R * cos45, R * cos45, 0)
                    );
                    var sc3 = famDoc.FamilyCreate.NewSymbolicCurve(a3, refLevelPlane);
                    if (planSwingCat != null) sc3.Subcategory = planSwingCat;

                    // Arc 4: Right Interior (swings inward into -Y)
                    // Center (+R, 0), Start (0, 0), End (+R, -R), Mid (+R - R*cos45, -R*cos45)
                    var a4 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(+R, -R, 0),
                        new XYZ(+R - R * cos45, -R * cos45, 0)
                    );
                    var sc4 = famDoc.FamilyCreate.NewSymbolicCurve(a4, refLevelPlane);
                    if (planSwingCat != null) sc4.Subcategory = planSwingCat;

                    // Leaf 1 (Left, 45 deg into Interior):
                    // Line from (-R, 0) to (-R + R*cos45, -R*cos45)
                    var l1 = Line.CreateBound(
                        new XYZ(-R, 0, 0),
                        new XYZ(-R + R * cos45, -R * cos45, 0)
                    );
                    var scl1 = famDoc.FamilyCreate.NewSymbolicCurve(l1, refLevelPlane);
                    if (panelCat != null) scl1.Subcategory = panelCat;

                    // Leaf 2 (Right, 45 deg into Interior):
                    // Line from (+R, 0) to (+R - R*cos45, -R*cos45)
                    var l2 = Line.CreateBound(
                        new XYZ(+R, 0, 0),
                        new XYZ(+R - R * cos45, -R * cos45, 0)
                    );
                    var scl2 = famDoc.FamilyCreate.NewSymbolicCurve(l2, refLevelPlane);
                    if (panelCat != null) scl2.Subcategory = panelCat;

                    // Also create a family type "D1 - KÃ­nh CÆ°á»ng Lá»±c 10mm 2 CÃ¡nh"
                    var newType = fMgr.NewType("D1 - KÃ­nh CÆ°á»ng Lá»±c 10mm 2 CÃ¡nh");
                    fMgr.CurrentType = newType;

                    var pDesc = fMgr.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
                             ?? fMgr.Parameters.Cast<FamilyParameter>().FirstOrDefault(p => p.Definition.Name.Equals("Description", StringComparison.OrdinalIgnoreCase));
                    if (pDesc != null) fMgr.Set(pDesc, "Cá»­a kÃ­nh cÆ°á»ng lá»±c 10mm 2 cÃ¡nh báº£n lá» sÃ n báº­t 2 chiá»u (D1)");

                    tx.Commit();
                }

                // Save family to disk
                var saveOpt = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(rfaPath, saveOpt);
                famDoc.Close(false);

                // Load family into project doc
                Family loadedFam = null;
                using (var txLoad = new Transaction(doc, "Load Custom Double Swing Door Family"))
                {
                    txLoad.Start();
                    doc.LoadFamily(rfaPath, new CustomFamilyLoadOptions(), out loadedFam);
                    txLoad.Commit();
                }

                return new
                {
                    success = true,
                    rfaPath,
                    loadedFamName = loadedFam?.Name,
                    loadedFamId = loadedFam?.Id.Value
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
