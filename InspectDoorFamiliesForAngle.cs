using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorFamiliesForAngle
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => f.FamilyCategory?.Id?.Value == (long)BuiltInCategory.OST_Doors)
                .ToList();

            var list = new List<object>();

            foreach (var fam in fams)
            {
                Document famDoc = null;
                try
                {
                    famDoc = doc.EditFamily(fam);
                }
                catch
                {
                    continue;
                }

                if (famDoc == null) continue;

                var pars = famDoc.FamilyManager.Parameters.Cast<FamilyParameter>()
                    .Select(p => new {
                        name = p.Definition.Name,
                        type = p.GetDataType().TypeId,
                        isInstance = p.IsInstance
                    })
                    .Where(p => p.name.ToLower().Contains("angle") || p.name.ToLower().Contains("goc") || p.name.ToLower().Contains("góc") || p.name.ToLower().Contains("mo") || p.name.ToLower().Contains("mở") || p.type.ToLower().Contains("angle"))
                    .ToList();

                if (pars.Count > 0)
                {
                    list.Add(new {
                        family = fam.Name,
                        parameters = pars
                    });
                }

                famDoc.Close(false);
            }

            return list;
        }
    }
}
