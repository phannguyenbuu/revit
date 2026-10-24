using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListDoorTypes
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var doors = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(BuiltInCategory.OST_Doors)
                .Cast<FamilySymbol>()
                .Select(fs => new {
                    id = fs.Id.Value,
                    familyName = fs.FamilyName,
                    name = fs.Name,
                    width = fs.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble() * 304.8,
                    height = fs.get_Parameter(BuiltInParameter.DOOR_HEIGHT)?.AsDouble() * 304.8
                })
                .ToList();

            return doors;
        }
    }
}
