using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class TestFamilyOption : IFamilyLoadOptions
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

    public static class TestCreateFamily
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var app = uiapp.Application;
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Plumbing Fixture.rft";
            if (!File.Exists(templatePath))
            {
                templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
            }

            var famDoc = app.NewFamilyDocument(templatePath);
            if (famDoc == null) return new { error = "Failed to create family document" };

            try
            {
                using (var t = new Transaction(famDoc, "Create Xi Xom Geometry"))
                {
                    t.Start();

                    // Find Ref. Level sketch plane
                    var level = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .FirstOrDefault();

                    var sketchPlane = SketchPlane.Create(famDoc, level.Id);

                    // Create outer profile for extrusion
                    // 550mm wide x 600mm long, corners beveled
                    double scale = 0.96 / 304.8;
                    var pts = new XYZ[]
                    {
                        new XYZ(200 * scale, 0, 0),
                        new XYZ(275 * scale, 75 * scale, 0),
                        new XYZ(275 * scale, 525 * scale, 0),
                        new XYZ(200 * scale, 600 * scale, 0),
                        new XYZ(-200 * scale, 600 * scale, 0),
                        new XYZ(-275 * scale, 525 * scale, 0),
                        new XYZ(-275 * scale, 75 * scale, 0),
                        new XYZ(-200 * scale, 0, 0)
                    };

                    CurveArrArray curveArrArr = new CurveArrArray();
                    CurveArray curveArr = new CurveArray();
                    for (int i = 0; i < pts.Length; i++)
                    {
                        var p1 = pts[i];
                        var p2 = pts[(i + 1) % pts.Length];
                        curveArr.Append(Line.CreateBound(p1, p2));
                    }
                    curveArrArr.Append(curveArr);

                    // Extrusion height: 25mm above floor
                    double extHeight = 25.0 / 304.8;
                    var extrusion = famDoc.FamilyCreate.NewExtrusion(true, curveArrArr, sketchPlane, extHeight);

                    // Also add 2D symbolic lines for the inner bowl and treads on plan
                    var subCat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_PlumbingFixtures);
                    GraphicsStyle gStyle = null;
                    if (subCat != null)
                    {
                        gStyle = subCat.GetGraphicsStyle(GraphicsStyleType.Projection);
                    }

                    // Inner bowl profile
                    var innerPts = new XYZ[]
                    {
                        new XYZ(200 * scale, 20 * scale, 0),
                        new XYZ(255 * scale, 75 * scale, 0),
                        new XYZ(255 * scale, 525 * scale, 0),
                        new XYZ(200 * scale, 580 * scale, 0),
                        new XYZ(-200 * scale, 580 * scale, 0),
                        new XYZ(-255 * scale, 525 * scale, 0),
                        new XYZ(-255 * scale, 75 * scale, 0),
                        new XYZ(-200 * scale, 20 * scale, 0)
                    };
                    for (int i = 0; i < innerPts.Length; i++)
                    {
                        var p1 = innerPts[i];
                        var p2 = innerPts[(i + 1) % innerPts.Length];
                        var sl = famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(p1, p2), sketchPlane);
                        if (gStyle != null) sl.Subcategory = gStyle;
                    }

                    // Circle for drain
                    XYZ center = new XYZ(0, 450 * scale, 0);
                    double radius = 55.90 * scale;
                    XYZ norm = XYZ.BasisZ;
                    XYZ xvec = XYZ.BasisX;
                    XYZ yvec = XYZ.BasisY;
                    var arc1 = Arc.Create(center, radius, 0, Math.PI, xvec, yvec);
                    var arc2 = Arc.Create(center, radius, Math.PI, 2 * Math.PI, xvec, yvec);
                    famDoc.FamilyCreate.NewSymbolicCurve(arc1, sketchPlane);
                    famDoc.FamilyCreate.NewSymbolicCurve(arc2, sketchPlane);

                    // Foot treads
                    var treadLeft = new XYZ[]
                    {
                        new XYZ(-200 * scale, 100 * scale, 0),
                        new XYZ(-75 * scale, 100 * scale, 0),
                        new XYZ(-75 * scale, 225 * scale, 0),
                        new XYZ(-106.54 * scale, 300.52 * scale, 0),
                        new XYZ(-131.13 * scale, 318.54 * scale, 0),
                        new XYZ(-175.39 * scale, 325.09 * scale, 0),
                        new XYZ(-200 * scale, 325 * scale, 0)
                    };
                    for (int i = 0; i < treadLeft.Length - 1; i++)
                    {
                        famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(treadLeft[i], treadLeft[i + 1]), sketchPlane);
                        famDoc.FamilyCreate.NewSymbolicCurve(Line.CreateBound(new XYZ(-treadLeft[i].X, treadLeft[i].Y, 0), new XYZ(-treadLeft[i + 1].X, treadLeft[i + 1].Y, 0)), sketchPlane);
                    }

                    t.Commit();
                }

                string savePath = @"D:\Dropbox\_Documents\RevitAI\Xi_Xom.rfa";
                var saveOpt = new SaveAsOptions { OverwriteExistingFile = true };
                famDoc.SaveAs(savePath, saveOpt);

                famDoc.Close(false);

                Family loadedFam = null;
                doc.LoadFamily(savePath, new TestFamilyOption(), out loadedFam);

                return new
                {
                    success = true,
                    familyId = loadedFam?.Id.Value,
                    familyName = loadedFam?.Name,
                    path = savePath
                };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.Message, stack = ex.StackTrace };
            }
        }
    }
}
