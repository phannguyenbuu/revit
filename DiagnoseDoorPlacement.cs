using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DiagnoseDoorPlacement
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var lvl = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 1"));
            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;

            var fam = sym.Family;

            var results = new List<object>();

            using (var tx = new Transaction(doc, "Diagnose Placement"))
            {
                tx.Start();
                if (!sym.IsActive) sym.Activate();

                // Delete 2363712
                try { doc.Delete(new ElementId(2363712L)); } catch { }

                var targetPt = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvl.Elevation);

                // Method 1: NewFamilyInstance(XYZ, FamilySymbol, Level, StructuralType)
                try
                {
                    var inst1 = doc.Create.NewFamilyInstance(targetPt, sym, lvl, StructuralType.NonStructural);
                    var bb1 = inst1.get_BoundingBox(null);
                    results.Add(new
                    {
                        method = "NewFamilyInstance(XYZ, sym, lvl, NonStructural)",
                        id = inst1.Id.Value,
                        hasLoc = inst1.Location != null,
                        locType = inst1.Location?.GetType().FullName,
                        bbMin = bb1 != null ? new { x = bb1.Min.X * 0.3048, y = bb1.Min.Y * 0.3048 } : null,
                        bbMax = bb1 != null ? new { x = bb1.Max.X * 0.3048, y = bb1.Max.Y * 0.3048 } : null
                    });
                    doc.Delete(inst1.Id);
                }
                catch (Exception ex) { results.Add(new { method = "1", error = ex.Message }); }

                // Method 2: NewFamilyInstance(XYZ, FamilySymbol, StructuralType)
                try
                {
                    var inst2 = doc.Create.NewFamilyInstance(targetPt, sym, StructuralType.NonStructural);
                    var bb2 = inst2.get_BoundingBox(null);
                    results.Add(new
                    {
                        method = "NewFamilyInstance(XYZ, sym, NonStructural)",
                        id = inst2.Id.Value,
                        hasLoc = inst2.Location != null,
                        bbMin = bb2 != null ? new { x = bb2.Min.X * 0.3048, y = bb2.Min.Y * 0.3048 } : null
                    });
                    doc.Delete(inst2.Id);
                }
                catch (Exception ex) { results.Add(new { method = "2", error = ex.Message }); }

                // Method 3: Hosted on Wall 2362083
                var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
                if (wall != null)
                {
                    try
                    {
                        var inst3 = doc.Create.NewFamilyInstance(targetPt, sym, wall, lvl, StructuralType.NonStructural);
                        var bb3 = inst3.get_BoundingBox(null);
                        results.Add(new
                        {
                            method = "NewFamilyInstance(XYZ, sym, wall, lvl, NonStructural)",
                            id = inst3.Id.Value,
                            hasLoc = inst3.Location != null,
                            locType = inst3.Location?.GetType().FullName,
                            bbMin = bb3 != null ? new { x = bb3.Min.X * 0.3048, y = bb3.Min.Y * 0.3048 } : null
                        });
                        doc.Delete(inst3.Id);
                    }
                    catch (Exception ex) { results.Add(new { method = "3", error = ex.Message }); }
                }

                tx.RollBack();
            }

            return new
            {
                famName = fam.Name,
                placementType = fam.FamilyPlacementType.ToString(),
                hostType = fam.get_Parameter(BuiltInParameter.FAMILY_HOSTING_BEHAVIOR)?.AsValueString(),
                results
            };
        }
    }
}
