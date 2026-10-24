using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorDetails
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var floor = doc.GetElement(new ElementId(2381562)) as Floor;
            if (floor == null) return new { error = "Floor 2381562 not found" };

            var floorType = doc.GetElement(floor.GetTypeId()) as FloorType;
            var cs = floorType?.GetCompoundStructure();

            var layers = new List<object>();
            if (cs != null)
            {
                foreach (var layer in cs.GetLayers())
                {
                    layers.Add(new
                    {
                        layerId = layer.LayerId,
                        function = layer.Function.ToString(),
                        widthMm = layer.Width * 304.8,
                        materialId = layer.MaterialId.Value,
                        materialName = doc.GetElement(layer.MaterialId)?.Name ?? "None"
                    });
                }
            }

            // Check how many floors use this FloorType
            var sameTypeFloors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Where(f => f.GetTypeId() == floorType.Id)
                .Select(f => f.Id.Value)
                .ToList();

            // Also list all FloorTypes in the project
            var allFloorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => new { id = ft.Id.Value, name = ft.Name })
                .ToList();

            // Floor instance parameters (Height Offset from Level, etc.)
            double heightOffset = (floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)?.AsDouble() ?? 0) * 304.8;
            string levelName = floor.get_Parameter(BuiltInParameter.LEVEL_PARAM)?.AsValueString() ?? "None";

            return new
            {
                floorId = floor.Id.Value,
                floorTypeName = floorType?.Name,
                floorTypeId = floorType?.Id.Value,
                sameTypeFloorIds = sameTypeFloors,
                layers = layers,
                allFloorTypes = allFloorTypes,
                heightOffset = heightOffset,
                levelName = levelName
            };
        }
    }
}
