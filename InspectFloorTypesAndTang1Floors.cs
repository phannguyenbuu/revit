using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorTypesAndTang1Floors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;

            var floorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => new
                {
                    id = ft.Id.Value,
                    name = ft.Name,
                    thicknessMm = Math.Round(ft.get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM)?.AsDouble() * 304.8 ?? 0, 1)
                })
                .ToList();

            var lvlTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            var existingFloors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Where(f => f.LevelId == lvlTang1?.Id)
                .Select(f => new
                {
                    id = f.Id.Value,
                    name = f.Name,
                    type = f.FloorType.Name
                })
                .ToList();

            return new
            {
                lvlTang1 = new { id = lvlTang1?.Id.Value, name = lvlTang1?.Name, elev = lvlTang1?.Elevation * 0.3048 },
                floorTypes,
                existingFloors
            };
        }
    }
}
