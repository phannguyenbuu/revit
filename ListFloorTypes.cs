using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListFloorTypes
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var fts = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => new {
                    id = ft.Id.Value,
                    name = ft.Name,
                    thickness = ft.get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM)?.AsDouble() * 304.8
                })
                .ToList();

            return fts;
        }
    }
}
