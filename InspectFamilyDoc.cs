using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyDoc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            var famDoc = doc.EditFamily(sym.Family);
            var mgr = famDoc.FamilyManager;

            var pars = mgr.Parameters.Cast<FamilyParameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    isInstance = p.IsInstance,
                    storage = p.StorageType.ToString()
                })
                .ToList();

            var types = mgr.Types.Cast<FamilyType>()
                .Select(t => t.Name)
                .ToList();

            famDoc.Close(false);

            return new
            {
                familyName = sym.Family.Name,
                types = types,
                parameters = pars
            };
        }
    }
}
