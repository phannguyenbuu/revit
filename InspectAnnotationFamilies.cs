using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAnnotationFamilies
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => f.FamilyCategory?.BuiltInCategory == BuiltInCategory.OST_GenericAnnotation 
                         || f.FamilyCategory?.BuiltInCategory == BuiltInCategory.OST_SpotElevations
                         || f.FamilyCategory?.BuiltInCategory == BuiltInCategory.OST_FloorTags)
                .Select(f => new {
                    id = f.Id.Value,
                    name = f.Name,
                    cat = f.FamilyCategory?.Name
                })
                .ToList();

            return fams;
        }
    }
}
