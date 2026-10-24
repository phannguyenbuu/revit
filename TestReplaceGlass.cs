using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestReplaceGlass
    {
        private const double MM2FT = 1.0 / 304.8;
        private static double Mm(double val) => val * MM2FT;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var fam = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

                if (fam == null) return new { error = "Family not found" };

                var famDoc = doc.EditFamily(fam);
                if (famDoc == null) return new { error = "Cannot edit family" };

                var log = new List<string>();

                using (Transaction t = new Transaction(famDoc, "Replace Glass With Single Panes"))
                {
                    t.Start();

                    // Find existing glass extrusion
                    var oldGlass = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Extrusion))
                        .Cast<Extrusion>()
                        .FirstOrDefault(e => e.Subcategory != null && e.Subcategory.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase))
                        ?? new FilteredElementCollector(famDoc).OfClass(typeof(Extrusion)).Cast<Extrusion>().FirstOrDefault(e => e.Id.Value == 2371620L);

                    if (oldGlass == null)
                    {
                        return new { error = "Old glass extrusion not found" };
                    }

                    var sp = oldGlass.Sketch.SketchPlane;
                    var subCat = oldGlass.Subcategory;
                    var matParam = oldGlass.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM);
                    ElementId matId = matParam != null && matParam.HasValue ? matParam.AsElementId() : ElementId.InvalidElementId;
                    double startOffset = oldGlass.StartOffset;
                    double endOffset = oldGlass.EndOffset;

                    // Delete old glass extrusion
                    famDoc.Delete(oldGlass.Id);
                    log.Add("Deleted old glass extrusion with 6 loops");

                    // Create new profile with 2 loops (1 per sash)
                    // Dimensions for S1 (Width=1500, Height=1800, Sill=750):
                    // X right: [76, 674], Z: [826, 2474]
                    // X left: [-674, -76], Z: [826, 2474]
                    // Note: Y is determined by the sketch plane and start/end offsets.
                    double y = 0.0; // on sketch plane

                    var curveArrArray = new CurveArrArray();

                    // Loop 1: Right sash glass
                    var ca1 = new CurveArray();
                    XYZ p1 = new XYZ(Mm(76.0), y, Mm(826.0));
                    XYZ p2 = new XYZ(Mm(674.0), y, Mm(826.0));
                    XYZ p3 = new XYZ(Mm(674.0), y, Mm(2474.0));
                    XYZ p4 = new XYZ(Mm(76.0), y, Mm(2474.0));

                    ca1.Append(Line.CreateBound(p1, p2));
                    ca1.Append(Line.CreateBound(p2, p3));
                    ca1.Append(Line.CreateBound(p3, p4));
                    ca1.Append(Line.CreateBound(p4, p1));
                    curveArrArray.Append(ca1);

                    // Loop 2: Left sash glass
                    var ca2 = new CurveArray();
                    XYZ q1 = new XYZ(Mm(-674.0), y, Mm(826.0));
                    XYZ q2 = new XYZ(Mm(-76.0), y, Mm(826.0));
                    XYZ q3 = new XYZ(Mm(-76.0), y, Mm(2474.0));
                    XYZ q4 = new XYZ(Mm(-674.0), y, Mm(2474.0));

                    ca2.Append(Line.CreateBound(q1, q2));
                    ca2.Append(Line.CreateBound(q2, q3));
                    ca2.Append(Line.CreateBound(q3, q4));
                    ca2.Append(Line.CreateBound(q4, q1));
                    curveArrArray.Append(ca2);

                    // Create a dedicated SketchPlane on the X-Z plane (Y = 0)
                    Plane plane = Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero);
                    SketchPlane newSp = SketchPlane.Create(famDoc, plane);

                    // Create new Extrusion
                    Extrusion newGlass = famDoc.FamilyCreate.NewExtrusion(true, curveArrArray, newSp, Mm(65.0));
                    newGlass.StartOffset = Mm(60.0);
                    if (subCat != null) newGlass.Subcategory = subCat;
                    if (matId != ElementId.InvalidElementId)
                    {
                        newGlass.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.Set(matId);
                    }

                    log.Add($"Created new glass extrusion ID {newGlass.Id.Value} with 2 continuous panes");

                    t.Commit();
                }

                // Reload into doc
                famDoc.LoadFamily(doc, new FamilyLoadOptionOverride());
                log.Add("Reloaded family into project document");

                famDoc.Close(false);

                // Regenerate doc
                using (Transaction t = new Transaction(doc, "Regen doc after glass replace"))
                {
                    t.Start();
                    doc.Regenerate();
                    t.Commit();
                }

                // Export cropped 3D image
                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string full3dPath = Path.Combine(folder, "revit_3d_new_glass.jpg");

                var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    uidoc.Selection.SetElementIds(new List<ElementId>());

                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview3d?.ZoomToFit();

                    if (File.Exists(full3dPath)) File.Delete(full3dPath);
                    var expOptFull = new ImageExportOptions
                    {
                        FilePath = full3dPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOptFull);
                }

                // Save Document
                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                }
                catch { }

                return new
                {
                    success = true,
                    log,
                    full3dPath,
                    docSaved
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
