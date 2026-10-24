using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectParam25
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            var fam = win.Symbol.Family;

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            var fm = famDoc.FamilyManager;
            var dims = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .ToList();

            var dimInfo = new List<object>();
            foreach (var d in dims)
            {
                string label = d.FamilyLabel?.Definition?.Name ?? "NoLabel";
                double val = (d.Value ?? 0) * 304.8;
                dimInfo.Add(new
                {
                    id = d.Id.Value,
                    label = label,
                    valMm = val,
                    view = doc.GetElement(d.OwnerViewId)?.Name ?? "NoView"
                });
            }

            // Also check all family parameters and their formulas
            var pList = new List<object>();
            foreach (FamilyParameter fp in fm.Parameters)
            {
                pList.Add(new
                {
                    name = fp.Definition.Name,
                    formula = fp.Formula,
                    isInstance = fp.IsInstance
                });
            }

            famDoc.Close(false);

            return new { dims = dimInfo, parameters = pList };
        }
    }
}
