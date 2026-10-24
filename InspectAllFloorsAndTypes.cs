
using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllFloorsAndTypes
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var floorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => {
                    var matIds = ft.GetCompoundStructure()?.GetLayers()
                        .Select(l => l.MaterialId)
                        .Where(id => id != ElementId.InvalidElementId)
                        .ToList() ?? new List<ElementId>();
                    var mats = matIds.Select(mid => {
                        var m = doc.GetElement(mid) as Material;
                        var patEl = m?.SurfaceForegroundPatternId != ElementId.InvalidElementId 
                            ? doc.GetElement(m.SurfaceForegroundPatternId) as FillPatternElement : null;
                        return new {
                            id = mid.Value,
                            name = m?.Name,
                            surfacePattern = patEl?.Name
                        };
                    }).ToList();

                    return new {
                        id = ft.Id.Value,
                        name = ft.Name,
                        category = ft.Category?.Name,
                        materials = mats
                    };
                }).ToList();

            var allFloors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Select(f => {
                    var bbox = f.get_BoundingBox(null);
                    return new {
                        id = f.Id.Value,
                        name = f.Name,
                        typeName = f.FloorType?.Name,
                        levelId = f.LevelId.Value,
                        levelName = doc.GetElement(f.LevelId)?.Name,
                        minX = bbox != null ? bbox.Min.X * 304.8 : 0,
                        maxX = bbox != null ? bbox.Max.X * 304.8 : 0,
                        minY = bbox != null ? bbox.Min.Y * 304.8 : 0,
                        maxY = bbox != null ? bbox.Max.Y * 304.8 : 0
                    };
                }).ToList();

            return new { floorTypes, allFloors };
        }
    }
}
