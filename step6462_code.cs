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
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Door.rft";
            if (!File.Exists(templatePath)) return new { error = "Template not found" };

            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Cua_Kinh_Cuong_Luc_2Canh_Bat2Chieu.rfa";
            if (File.Exists(rfaPath))
            {
                try { File.Delete(rfaPath); } catch { }
            }

            Document famDoc = null;
            Family loadedFam = null;

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

                    // Door dimensions
                    double W = 1.900 * M2FT;
                    double R = W / 2.0; // 0.950m in ft
                    double cos45 = Math.Sqrt(2.0) / 2.0;

                    // Arc 1: Left Exterior (swings outward into +Y)
                    var a1 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(-R, R, 0),
                        new XYZ(-R + R * cos45, R * cos45, 0)
                    );
                    var sc1 = famDoc.FamilyCreate.NewSymbolicCurve(a1, refLevelPlane);
                    if (planSwingStyle != null) sc1.Subcategory = planSwingStyle;

                    // Arc 2: Left Interior (swings inward into -Y)
                    var a2 = Arc.Create(
                        new XYZ(-R, -R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(-R + R * cos45, -R * cos45, 0)
                    );
                    var sc2 = famDoc.FamilyCreate.NewSymbolicCurve(a2, refLevelPlane);
                    if (planSwingStyle != null) sc2.Subcategory = planSwingStyle;

                    // Arc 3: Right Exterior (swings outward into +Y)
                    var a3 = Arc.Create(
                        new XYZ(+R, R, 0),
                        new XYZ(0, 0, 0),
                        new XYZ(+R - R * cos45, R * cos45, 0)
                    );
                    var sc3 = famDoc.FamilyCreate.NewSymbolicCurve(a3, refLevelPlane);
                    if (planSwingStyle != null) sc3.Subcategory = planSwingStyle;

                    // Arc 4: Right Interior (swings inward into -Y)
                    var a4 = Arc.Create(
                        new XYZ(0, 0, 0),
                        new XYZ(+R, -R, 0),
                        new XYZ(+R - R * cos45, -R * cos45, 0)
                    );
                    var sc4 = famDoc.FamilyCreate.NewSymbolicCurve(a4, refLevelPlane);
                    if (planSwingStyle != null) sc4.Subcategory = planSwingStyle;

                    // Leaf 1 (Left, 45 deg into Interior):
                    var l1 = Line.CreateBound(
                        new XYZ(-R, 0, 0),
                        new XYZ(-R + R * cos45, -R * cos45, 0)
                    );
                    var scl1 = famDoc.FamilyCreate.NewSymbolicCurve(l1, refLevelPlane);
                    if (panelStyle != null) scl1.Subcategory = panelStyle;

                    // Leaf 2 (Right, 45 deg into Interior):
                    var l2 = Line.CreateBound(
                        new XYZ(+R, 0, 0),
                        new XYZ(+R - R * cos45, -R * cos45, 0)
                    );
                    var scl2 = famDoc.FamilyCreate.NewSymbolicCurve(l2, refLevelPlane);
                    if (panelStyle != null) scl2.Subcategory = panelStyle;

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
                using (var txLoad = new Transaction(doc, "Load Double Swing Door Family"))
                {
                    txLoad.Start();
                    doc.LoadFamily(rfaPath, new CustomFamilyLoadOptions(), out loadedFam);
                    txLoad.Commit();
                }
            }
            catch (Exception ex)
            {
                if (famDoc != null) try { famDoc.Close(false); } catch { }
                return new { error = "Family creation/loading error: " + ex.ToString() };
            }

            if (loadedFam == null)
            {
                // Find existing family if already loaded
                loadedFam = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.Contains("Bat2Chieu") || f.Name.Contains("Cua_Kinh_Cuong_Luc"));
            }

            if (loadedFam == null) return new { error = "Could not find loaded family in doc" };

            // Find Symbol
            FamilySymbol targetSym = null;
            foreach (var sid in loadedFam.GetFamilySymbolIds())
            {
                var s = doc.GetElement(sid) as FamilySymbol;
                if (s != null)
                {
                    targetSym = s;
                    break;
                }
            }
            if (targetSym == null) return new { error = "No symbol found in loaded family" };

            // Place door on wall 2362083
            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            if (wall == null) return new { error = "Wall 2362083 not found" };

            var levels = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("Táº¦NG 1", StringComparison.OrdinalIgnoreCase));

            ElementId newDoorId = ElementId.InvalidElementId;

            using (var txPlace = new Transaction(doc, "Place Double Swing D1 Door"))
            {
                var opts = txPlace.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                txPlace.SetFailureHandlingOptions(opts);

                txPlace.Start();

                if (!targetSym.IsActive) targetSym.Activate();

                // Delete previous door 2363719
                try { doc.Delete(new ElementId(2363719L)); } catch { }
                try { doc.Delete(new ElementId(2362084L)); } catch { }

                // Place new door instance hosted on Wall 2362083
                var doorLoc = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                var door = doc.Create.NewFamilyInstance(doorLoc, targetSym, wall, lvlTang1, StructuralType.NonStructural);
                newDoorId = door.Id;

                var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                if (pMark != null && !pMark.IsReadOnly) pMark.Set("D1");

                doc.Regenerate();
                txPlace.Commit();
            }

            var placedDoor = doc.GetElement(newDoorId) as FamilyInstance;

            // Clear selection and switch view to Máº¶T Báº°NG Táº¦NG 1
            uidoc.Selection.SetElementIds(new List<ElementId>());

            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("Máº¶T Báº°NG Táº¦NG 1", StringComparison.OrdinalIgnoreCase));

            if (plan != null && uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

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
            catch { }

            // Save active document
            try
            {
                doc.Save(new SaveOptions());
            }
            catch { }

            return new
            {
                success = true,
                family = loadedFam?.Name,
                symbol = targetSym?.Name,
                doorId = newDoorId.Value,
                facing = placedDoor != null ? new { x = placedDoor.FacingOrientation.X, y = placedDoor.FacingOrientation.Y } : null,
                hand = placedDoor != null ? new { x = placedDoor.HandOrientation.X, y = placedDoor.HandOrientation.Y } : null,
                image = outImgPath
            };
        }
    }
}
