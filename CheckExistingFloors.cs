using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckExistingFloors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var floors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Where(f => f.LevelId.Value == 311)
                .Select(f => {
                    var bbox = f.get_BoundingBox(null);
                    var offsetParam = f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    return new {
                        id = f.Id.Value,
                        name = f.FloorType.Name,
                        typeId = f.FloorType.Id.Value,
                        offset = offsetParam != null ? offsetParam.AsDouble() * 304.8 : 0,
                        minX = bbox != null ? bbox.Min.X * 304.8 : 0,
                        maxX = bbox != null ? bbox.Max.X * 304.8 : 0,
                        minY = bbox != null ? bbox.Min.Y * 304.8 : 0,
                        maxY = bbox != null ? bbox.Max.Y * 304.8 : 0,
                    };
                })
                .Where(f => f.minX >= 19000 && f.maxX <= 38000)
                .ToList();

            return floors;
        }
    }
}
