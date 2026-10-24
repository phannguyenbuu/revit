using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
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

    public static class RebuildWindowFamily
    {
        private const double MM = 1.0 / 304.8;

        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string backupPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            string fixedPath = @"D:\Dropbox\_Documents\RevitAI\CUA SO 2 CANH NHOM KINH O O THOANG.rfa";

            if (!File.Exists(backupPath))
                return new { error = "Backup file not found: " + backupPath };

            // Copy backup to fixedPath
            File.Copy(backupPath, fixedPath, true);

            var famDoc = app.Application.OpenDocumentFile(fixedPath);
            if (famDoc == null)
                return new { error = "Cannot open family document headless" };

            try
            {
                // Collect materials and subcategories from old extrusions
                ElementId alumMatId = ElementId.InvalidElementId;
                ElementId glassMatId = ElementId.InvalidElementId;
                Category frameSubCat = null;
                Category glassSubCat = null;

                var oldExtIds = new List<ElementId>();
                foreach (var ext in new FilteredElementCollector(famDoc).OfClass(typeof(Extrusion)).Cast<Extrusion>().ToList())
                {
                    if (ext.Subcategory?.Name == "Frame/Mullion")
                    {
                        alumMatId = ext.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.AsElementId() ?? alumMatId;
                        frameSubCat = ext.Subcategory;
                    }
                    else if (ext.Subcategory?.Name == "Glass")
                    {
                        glassMatId = ext.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.AsElementId() ?? glassMatId;
                        glassSubCat = ext.Subcategory;
                    }
                    oldExtIds.Add(ext.Id);
                }

                // Delete old 2D model/symbolic lines related to jambs/glass
                var oldCurveIds = new List<ElementId>();
                foreach (var ce in new FilteredElementCollector(famDoc).OfClass(typeof(CurveElement)).Cast<CurveElement>().ToList())
                {
                    string sub = (ce as SymbolicCurve)?.Subcategory?.Name ?? ce.LineStyle?.Name ?? "";
                    if (sub == "Plan Swing" || sub == "Glass")
                    {
                        oldCurveIds.Add(ce.Id);
                    }
                }

                using (var t = new Transaction(famDoc, "Rebuild Window Geometry"))
                {
                    t.Start();

                    // Delete old extrusions and 2D curves
                    foreach (var id in oldExtIds) famDoc.Delete(id);
                    foreach (var id in oldCurveIds) famDoc.Delete(id);

                    // Find ReferencePlane 'Exterior'
                    var rpExt = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(ReferencePlane))
                        .Cast<ReferencePlane>()
                        .FirstOrDefault(r => r.Name == "Exterior");

                    if (rpExt == null)
                        throw new Exception("ReferencePlane 'Exterior' not found in family");

                    double yPlane = rpExt.BubbleEnd.Y;
                    var extSketchPlane = SketchPlane.Create(famDoc, rpExt.GetReference());

                    // 1. OUTER FRAME EXTRUSION
                    // Outer rect: [-750, 750] x [750, 2550]
                    // Inner rect: [-725, 725] x [775, 2525]
                    // Depth: 76mm, centered at Y=0 -> Start = 37mm, End = 113mm from Exterior (Y=75mm)
                    var frameProfile = new CurveArrArray();
                    var outerLoop = MakeRectangleLoop(-750 * MM, 750 * MM, yPlane, 750 * MM, 2550 * MM);
                    var innerLoop = MakeRectangleLoop(-725 * MM, 725 * MM, yPlane, 775 * MM, 2525 * MM);
                    frameProfile.Append(outerLoop);
                    frameProfile.Append(innerLoop);

                    var extFrame = famDoc.FamilyCreate.NewExtrusion(true, frameProfile, extSketchPlane, 113 * MM);
                    extFrame.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM)?.Set(37 * MM);
                    if (alumMatId != ElementId.InvalidElementId)
                        extFrame.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.Set(alumMatId);
                    if (frameSubCat != null) extFrame.Subcategory = frameSubCat;

                    // 2. LEFT SASH EXTRUSION
                    // Outer rect: [-725, 0] x [775, 2525]
                    // Inner hole: [-649, -76] x [851, 2449]
                    // Depth: 25mm, centered at Y=0 -> Start = 62.5mm, End = 87.5mm
                    var leftSashProfile = new CurveArrArray();
                    var leftOuter = MakeRectangleLoop(-725 * MM, 0, yPlane, 775 * MM, 2525 * MM);
                    var leftInner = MakeRectangleLoop(-649 * MM, -76 * MM, yPlane, 851 * MM, 2449 * MM);
                    leftSashProfile.Append(leftOuter);
                    leftSashProfile.Append(leftInner);

                    var extLeftSash = famDoc.FamilyCreate.NewExtrusion(true, leftSashProfile, extSketchPlane, 87.5 * MM);
                    extLeftSash.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM)?.Set(62.5 * MM);
                    if (alumMatId != ElementId.InvalidElementId)
                        extLeftSash.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.Set(alumMatId);
                    if (frameSubCat != null) extLeftSash.Subcategory = frameSubCat;

                    // 3. RIGHT SASH EXTRUSION
                    // Outer rect: [0, 725] x [775, 2525]
                    // Inner hole: [76, 649] x [851, 2449]
                    var rightSashProfile = new CurveArrArray();
                    var rightOuter = MakeRectangleLoop(0, 725 * MM, yPlane, 775 * MM, 2525 * MM);
                    var rightInner = MakeRectangleLoop(76 * MM, 649 * MM, yPlane, 851 * MM, 2449 * MM);
                    rightSashProfile.Append(rightOuter);
                    rightSashProfile.Append(rightInner);

                    var extRightSash = famDoc.FamilyCreate.NewExtrusion(true, rightSashProfile, extSketchPlane, 87.5 * MM);
                    extRightSash.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM)?.Set(62.5 * MM);
                    if (alumMatId != ElementId.InvalidElementId)
                        extRightSash.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.Set(alumMatId);
                    if (frameSubCat != null) extRightSash.Subcategory = frameSubCat;

                    // 4. GLASS EXTRUSION
                    // Left pane: [-649, -76] x [851, 2449]
                    // Right pane: [76, 649] x [851, 2449]
                    // Depth: 5mm, centered at Y=0 -> Start = 72.5mm, End = 77.5mm
                    var glassProfile = new CurveArrArray();
                    var leftGlass = MakeRectangleLoop(-649 * MM, -76 * MM, yPlane, 851 * MM, 2449 * MM);
                    var rightGlass = MakeRectangleLoop(76 * MM, 649 * MM, yPlane, 851 * MM, 2449 * MM);
                    glassProfile.Append(leftGlass);
                    glassProfile.Append(rightGlass);

                    var extGlass = famDoc.FamilyCreate.NewExtrusion(true, glassProfile, extSketchPlane, 77.5 * MM);
                    extGlass.get_Parameter(BuiltInParameter.EXTRUSION_START_PARAM)?.Set(72.5 * MM);
                    if (glassMatId != ElementId.InvalidElementId)
                        extGlass.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.Set(glassMatId);
                    if (glassSubCat != null) extGlass.Subcategory = glassSubCat;

                    t.Commit();
                }

                famDoc.Save();
                famDoc.Close(false);

                // Now reload family into active project document!
                var projectDoc = app.ActiveUIDocument?.Document;
                if (projectDoc != null)
                {
                    using (var pt = new Transaction(projectDoc, "Load Fixed Window Family"))
                    {
                        pt.Start();
                        projectDoc.LoadFamily(fixedPath, new CustomFamilyLoadOptions(), out Family loadedFam);
                        projectDoc.Regenerate();
                        pt.Commit();
                    }
                }

                return new
                {
                    success = true,
                    fixedPath = fixedPath,
                    message = "Family rebuilt and reloaded successfully!"
                };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }

        private static CurveArray MakeRectangleLoop(double xMin, double xMax, double yPlane, double zMin, double zMax)
        {
            var arr = new CurveArray();
            var p0 = new XYZ(xMin, yPlane, zMin);
            var p1 = new XYZ(xMax, yPlane, zMin);
            var p2 = new XYZ(xMax, yPlane, zMax);
            var p3 = new XYZ(xMin, yPlane, zMax);

            arr.Append(Line.CreateBound(p0, p1));
            arr.Append(Line.CreateBound(p1, p2));
            arr.Append(Line.CreateBound(p2, p3));
            arr.Append(Line.CreateBound(p3, p0));
            return arr;
        }
    }
}
