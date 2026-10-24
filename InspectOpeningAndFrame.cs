using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectOpeningAndFrame
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            var fam = win.Symbol.Family;

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            // Find OpeningCut
            var openings = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Opening))
                .Cast<Opening>()
                .ToList();

            var openingInfo = new List<object>();
            foreach (var op in openings)
            {
                var bb = op.get_BoundingBox(null);
                string bbStr = bb != null ? $"Min: [{bb.Min.X*304.8:F1}, {bb.Min.Y*304.8:F1}, {bb.Min.Z*304.8:F1}], Max: [{bb.Max.X*304.8:F1}, {bb.Max.Y*304.8:F1}, {bb.Max.Z*304.8:F1}] Width: {(bb.Max.X - bb.Min.X)*304.8:F1}mm" : "No BB";
                openingInfo.Add(new { id = op.Id.Value, bb = bbStr });
            }

            // Find Extrusions and Sweeps (Frames)
            var extrusions = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Extrusion))
                .Cast<Extrusion>()
                .Select(e =>
                {
                    var bb = e.get_BoundingBox(null);
                    return new
                    {
                        id = e.Id.Value,
                        isSolid = e.IsSolid,
                        bb = bb != null ? $"Min: [{bb.Min.X*304.8:F1}, {bb.Min.Y*304.8:F1}, {bb.Min.Z*304.8:F1}], Max: [{bb.Max.X*304.8:F1}, {bb.Max.Y*304.8:F1}, {bb.Max.Z*304.8:F1}] Width: {(bb.Max.X - bb.Min.X)*304.8:F1}mm, ThickY: {(bb.Max.Y - bb.Min.Y)*304.8:F1}mm" : "No BB"
                    };
                })
                .ToList();

            // Find all reference planes and dimensions
            var refPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ReferencePlane))
                .Cast<ReferencePlane>()
                .Select(rp => new { name = rp.Name, bubble = rp.BubbleEnd != null ? $"[{rp.BubbleEnd.X*304.8:F1}, {rp.BubbleEnd.Y*304.8:F1}, {rp.BubbleEnd.Z*304.8:F1}]" : "" })
                .ToList();

            var currentType = famDoc.FamilyManager.CurrentType;
            var typeValues = new Dictionary<string, string>();
            foreach (FamilyParameter fp in famDoc.FamilyManager.Parameters)
            {
                if (currentType != null && currentType.HasValue(fp))
                {
                    if (fp.StorageType == StorageType.Double)
                        typeValues[fp.Definition.Name] = $"{(currentType.AsDouble(fp) ?? 0) * 304.8:F1} mm";
                    else
                        typeValues[fp.Definition.Name] = currentType.AsString(fp) ?? "";
                }
            }

            famDoc.Close(false);

            return new
            {
                currentTypeName = currentType?.Name,
                typeValues = typeValues,
                openings = openingInfo,
                extrusions = extrusions,
                refPlanes = refPlanes
            };
        }
    }
}
