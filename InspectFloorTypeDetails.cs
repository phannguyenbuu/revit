using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorTypeDetails
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            FloorType ft = null;
            if (args.TryGetProperty("typeId", out var tp))
            {
                ft = doc.GetElement(new ElementId(tp.GetInt64())) as FloorType;
            }
            else
            {
                var fl = doc.GetElement(new ElementId(2409419L)) as Floor;
                ft = doc.GetElement(fl.GetTypeId()) as FloorType;
            }
            var cs = ft.GetCompoundStructure();

            var layers = new List<object>();
            if (cs != null)
            {
                foreach (var l in cs.GetLayers())
                {
                    var mat = doc.GetElement(l.MaterialId) as Material;
                    layers.Add(new {
                        func = l.Function.ToString(),
                        widthMm = l.Width * 304.8,
                        material = mat?.Name,
                        matId = l.MaterialId.Value
                    });
                }
            }

            // Also check how many floors use this FloorType in the whole project
            var floorsUsingType = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Where(f => f.GetTypeId() == ft.Id)
                .Select(f => new { id = f.Id.Value, level = doc.GetElement(f.LevelId)?.Name })
                .ToList();

            return new {
                floorTypeName = ft.Name,
                totalThicknessMm = cs != null ? cs.GetWidth() * 304.8 : 0,
                layers,
                floorsUsingType
            };
        }
    }
}