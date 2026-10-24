using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamily145917
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var ids = new long[] { 145917, 112212, 1742758, 810799, 820673 };
            var list = new List<object>();
            foreach (var id in ids)
            {
                var elem = doc.GetElement(new ElementId(id));
                if (elem is FamilySymbol fs)
                {
                    list.Add(new {
                        id = id,
                        type = "FamilySymbol",
                        name = fs.Name,
                        familyName = fs.FamilyName,
                        category = fs.Category?.Name,
                        familyCategory = fs.Family?.FamilyCategory?.Name,
                        hostType = fs.Family?.get_Parameter(BuiltInParameter.FAMILY_HOSTING_BEHAVIOR)?.AsValueString()
                    });
                }
                else
                {
                    list.Add(new { id = id, type = elem?.GetType().Name ?? "null" });
                }
            }
            return list;
        }
    }
}
