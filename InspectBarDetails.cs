using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBarDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
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

            var bar1 = famDoc.GetElement(new ElementId(588912L)) as Extrusion;
            var bar2 = famDoc.GetElement(new ElementId(588919L)) as Extrusion;

            var info1 = GetExtrusionInfo(bar1);
            var info2 = GetExtrusionInfo(bar2);

            // Also check dimensions in famDoc that might reference these bars
            var dims = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .Select(d => new
                {
                    id = d.Id.Value,
                    name = d.Name,
                    familyParam = d.FamilyLabel?.Definition.Name,
                    val = d.Value.HasValue ? Math.Round(d.Value.Value * 304.8, 1) : 0
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                bar1 = info1,
                bar2 = info2,
                dims
            };
        }

        private static object GetExtrusionInfo(Extrusion ext)
        {
            if (ext == null) return null;

            var paramList = new List<object>();
            foreach (Parameter p in ext.Parameters)
            {
                if (p.HasValue && !string.IsNullOrEmpty(p.AsValueString()))
                {
                    paramList.Add(new { name = p.Definition.Name, val = p.AsValueString() });
                }
            }

            return new
            {
                id = ext.Id.Value,
                start = ext.StartOffset * 304.8,
                end = ext.EndOffset * 304.8,
                hasSketch = ext.Sketch != null,
                paramsInfo = paramList
            };
        }
    }
}
