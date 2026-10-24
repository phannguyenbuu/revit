using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSanitaryGeometry
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var level = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("1"));

            if (level == null) return new { error = "No Level 1 found" };

            long[] ids = new long[] { 820673, 818435, 814154 };
            var results = new List<object>();

            using (var trans = new Transaction(doc, "Inspect Test Sanitary"))
            {
                trans.Start();

                foreach (var id in ids)
                {
                    var symbol = doc.GetElement(new ElementId(id)) as FamilySymbol;
                    if (symbol == null) continue;
                    if (!symbol.IsActive) symbol.Activate();

                    var inst = doc.Create.NewFamilyInstance(XYZ.Zero, symbol, level, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    doc.Regenerate();

                    var bb = inst.get_BoundingBox(null);
                    var facing = inst.FacingOrientation;
                    var hand = inst.HandOrientation;

                    results.Add(new
                    {
                        symbolId = id,
                        symbolName = symbol.Name,
                        familyName = symbol.FamilyName,
                        bbMin = bb != null ? new { x = bb.Min.X * 304.8, y = bb.Min.Y * 304.8, z = bb.Min.Z * 304.8 } : null,
                        bbMax = bb != null ? new { x = bb.Max.X * 304.8, y = bb.Max.Y * 304.8, z = bb.Max.Z * 304.8 } : null,
                        bbWidthX = bb != null ? (bb.Max.X - bb.Min.X) * 304.8 : 0,
                        bbDepthY = bb != null ? (bb.Max.Y - bb.Min.Y) * 304.8 : 0,
                        bbHeightZ = bb != null ? (bb.Max.Z - bb.Min.Z) * 304.8 : 0,
                        facing = new { x = facing.X, y = facing.Y, z = facing.Z },
                        hand = new { x = hand.X, y = hand.Y, z = hand.Z }
                    });

                    doc.Delete(inst.Id);
                }

                trans.Commit();
            }

            return results;
        }
    }
}
