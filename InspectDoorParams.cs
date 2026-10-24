using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorParams
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var ids = new long[] { 112212, 145917, 2070933 };
            var list = new List<object>();

            foreach (var id in ids)
            {
                var fs = doc.GetElement(new ElementId(id)) as FamilySymbol;
                if (fs == null) continue;

                var pars = fs.Parameters.Cast<Parameter>().Select(p => new {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? p.AsString()
                }).Where(p => p.name.ToLower().Contains("width") || p.name.ToLower().Contains("height") || p.name.ToLower().Contains("rộng") || p.name.ToLower().Contains("cao") || p.name.ToLower().Contains("dày")).ToList();

                list.Add(new {
                    id = id,
                    family = fs.FamilyName,
                    name = fs.Name,
                    pars = pars
                });
            }

            return list;
        }
    }
}
