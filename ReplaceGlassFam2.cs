using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ReplaceGlassFam2
    {
        private const double MM2FT = 1.0 / 304.8;
        private static double Mm(double val) => val * MM2FT;
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var log = new List<string>();

                // 1. Check ATT_Window 2 just in case
                var famAtt = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.IndexOf("ATT", StringComparison.OrdinalIgnoreCase) >= 0);

                if (famAtt != null && famAtt.IsEditable)
                {
                    var fDoc = doc.EditFamily(famAtt);
                    if (fDoc != null)
                    {
                        var forms = new FilteredElementCollector(fDoc).OfClass(typeof(GenericForm)).Cast<GenericForm>().ToList();
                        log.Add($"ATT_Window forms count: {forms.Count}");
                        foreach (var form in forms)
                        {
                            var bb = form.get_BoundingBox(null);
                            if (bb != null)
                            {
                                double dz = ToMm(bb.Max.Z - bb.Min.Z);
                                double dy = ToMm(bb.Max.Y - bb.Min.Y);
                                log.Add($"ATT form ID {form.Id.Value}: dz={dz:F1}mm, dy={dy:F1}mm, name={form.Name}, subCat={form.Subcategory?.Name}");
                            }
                        }
                        fDoc.Close(false);
                    }
                }

                // 2. Modify "CUA SO2 CANH NHOM KINH CO O THOANG"
                var fam2 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.Equals("CUA SO2 CANH NHOM KINH CO O THOANG", StringComparison.OrdinalIgnoreCase));

                if (fam2 == null) return new { error = "Family 2 not found", log };

                var famDoc = doc.EditFamily(fam2);
                if (famDoc == null) return new { error = "Cannot edit Family 2", log };

                using (Transaction t = new Transaction(famDoc, "Replace Glass with 4 Continuous Panes"))
                {
                    t.Start();

                    // Find existing glass extrusion
                    var oldGlass = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Extrusion))
                        .Cast<Extrusion>()
                        .FirstOrDefault(e => e.Subcategory != null && e.Subcategory.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase))
                        ?? new FilteredElementCollector(famDoc).OfClass(typeof(Extrusion)).Cast<Extrusion>().FirstOrDefault(e => e.Id.Value == 2372698L);

                    if (oldGlass == null)
                    {
                        t.RollBack();
                        famDoc.Close(false);
                        return new { error = "Old glass extrusion in fam2 not found", log };
                    }

                    var subCat = oldGlass.Subcategory;
                    var matParam = oldGlass.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM);
                    ElementId matId = matParam != null && matParam.HasValue ? matParam.AsElementId() : ElementId.InvalidElementId;
                    double startOffset = oldGlass.StartOffset;
                    double endOffset = oldGlass.EndOffset;

                    log.Add($"Old glass: startOffset={ToMm(startOffset):F1}mm, endOffset={ToMm(endOffset):F1}mm, matId={matId.Value}");

                    // Delete old glass extrusion
                    famDoc.Delete(oldGlass.Id);
                    log.Add("Deleted old glass extrusion in fam2");

                    // Create 4 continuous rectangular loops:
                    // 1) Top right (ô thoáng): [76, 374] x [2401, 2624]
                    // 2) Top left (ô thoáng): [-374, -76] x [2401, 2624]
                    // 3) Bottom right (cánh chính): [76, 374] x [876, 2224]
                    // 4) Bottom left (cánh chính): [-374, -76] x [876, 2224]
                    var curveArrArray = new CurveArrArray();
                    double y = 0.0;

                    // Loop 1: Top right
                    var ca1 = new CurveArray();
                    ca1.Append(Line.CreateBound(new XYZ(Mm(76.0), y, Mm(2401.0)), new XYZ(Mm(374.0), y, Mm(2401.0))));
                    ca1.Append(Line.CreateBound(new XYZ(Mm(374.0), y, Mm(2401.0)), new XYZ(Mm(374.0), y, Mm(2624.0))));
                    ca1.Append(Line.CreateBound(new XYZ(Mm(374.0), y, Mm(2624.0)), new XYZ(Mm(76.0), y, Mm(2624.0))));
                    ca1.Append(Line.CreateBound(new XYZ(Mm(76.0), y, Mm(2624.0)), new XYZ(Mm(76.0), y, Mm(2401.0))));
                    curveArrArray.Append(ca1);

                    // Loop 2: Top left
                    var ca2 = new CurveArray();
                    ca2.Append(Line.CreateBound(new XYZ(Mm(-374.0), y, Mm(2401.0)), new XYZ(Mm(-76.0), y, Mm(2401.0))));
                    ca2.Append(Line.CreateBound(new XYZ(Mm(-76.0), y, Mm(2401.0)), new XYZ(Mm(-76.0), y, Mm(2624.0))));
                    ca2.Append(Line.CreateBound(new XYZ(Mm(-76.0), y, Mm(2624.0)), new XYZ(Mm(-374.0), y, Mm(2624.0))));
                    ca2.Append(Line.CreateBound(new XYZ(Mm(-374.0), y, Mm(2624.0)), new XYZ(Mm(-374.0), y, Mm(2401.0))));
                    curveArrArray.Append(ca2);

                    // Loop 3: Bottom right
                    var ca3 = new CurveArray();
                    ca3.Append(Line.CreateBound(new XYZ(Mm(76.0), y, Mm(876.0)), new XYZ(Mm(374.0), y, Mm(876.0))));
                    ca3.Append(Line.CreateBound(new XYZ(Mm(374.0), y, Mm(876.0)), new XYZ(Mm(374.0), y, Mm(2224.0))));
                    ca3.Append(Line.CreateBound(new XYZ(Mm(374.0), y, Mm(2224.0)), new XYZ(Mm(76.0), y, Mm(2224.0))));
                    ca3.Append(Line.CreateBound(new XYZ(Mm(76.0), y, Mm(2224.0)), new XYZ(Mm(76.0), y, Mm(876.0))));
                    curveArrArray.Append(ca3);

                    // Loop 4: Bottom left
                    var ca4 = new CurveArray();
                    ca4.Append(Line.CreateBound(new XYZ(Mm(-374.0), y, Mm(876.0)), new XYZ(Mm(-76.0), y, Mm(876.0))));
                    ca4.Append(Line.CreateBound(new XYZ(Mm(-76.0), y, Mm(876.0)), new XYZ(Mm(-76.0), y, Mm(2224.0))));
                    ca4.Append(Line.CreateBound(new XYZ(Mm(-76.0), y, Mm(2224.0)), new XYZ(Mm(-374.0), y, Mm(2224.0))));
                    ca4.Append(Line.CreateBound(new XYZ(Mm(-374.0), y, Mm(2224.0)), new XYZ(Mm(-374.0), y, Mm(876.0))));
                    curveArrArray.Append(ca4);

                    // Sketch plane on X-Z (Y=0)
                    Plane plane = Plane.CreateByNormalAndOrigin(XYZ.BasisY, XYZ.Zero);
                    SketchPlane newSp = SketchPlane.Create(famDoc, plane);

                    double extEnd = endOffset != 0 ? endOffset : Mm(5.0);
                    Extrusion newGlass = famDoc.FamilyCreate.NewExtrusion(true, curveArrArray, newSp, extEnd);
                    newGlass.StartOffset = startOffset;
                    if (subCat != null) newGlass.Subcategory = subCat;
                    if (matId != ElementId.InvalidElementId)
                    {
                        newGlass.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.Set(matId);
                    }

                    log.Add($"Created new glass extrusion ID {newGlass.Id.Value} in fam2 with 4 continuous loops");
                    t.Commit();
                }

                // Reload fam2 into doc
                famDoc.LoadFamily(doc, new FamilyLoadOptionOverride());
                log.Add("Reloaded fam2 into project document");
                famDoc.Close(false);

                // Regenerate doc
                using (Transaction t = new Transaction(doc, "Regen doc after glass fam2 replace"))
                {
                    t.Start();
                    doc.Regenerate();
                    t.Commit();
                }

                // Save Document
                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                    log.Add("Saved document successfully");
                }
                catch (Exception ex)
                {
                    log.Add("doc.Save error: " + ex.Message);
                }

                return new { success = true, log, docSaved };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
