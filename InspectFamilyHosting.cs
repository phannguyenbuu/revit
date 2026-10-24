using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyHosting
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            long[] ids = new long[] { 820673, 147293, 818435, 817633, 814154, 149387 };
            var list = new List<object>();

            foreach (var id in ids)
            {
                var elem = doc.GetElement(new ElementId(id));
                if (elem is FamilySymbol fs)
                {
                    var fam = fs.Family;
                    list.Add(new
                    {
                        id = fs.Id.Value,
                        symbolName = fs.Name,
                        familyName = fam.Name,
                        placementType = fam.FamilyPlacementType.ToString(),
                        isActive = fs.IsActive,
                        category = fs.Category?.Name
                    });
                }
            }

            return list;
        }
    }
}
