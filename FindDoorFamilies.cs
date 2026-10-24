using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindDoorFamilies
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var families = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => f.FamilyCategory?.Id?.IntegerValue == (int)BuiltInCategory.OST_Doors)
                .Select(f => new {
                    f.Name,
                    Symbols = f.GetFamilySymbolIds().Select(id => doc.GetElement(id).Name).ToList()
                })
                .ToList();
            return families;
        }
    }
}
