using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllFloorTypes
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var floorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => {
                    var cs = ft.GetCompoundStructure();
                    return new {
                        id = ft.Id.Value,
                        name = ft.Name,
                        thicknessMm = cs != null ? cs.GetWidth() * 304.8 : 0,
                        layerCount = cs != null ? cs.GetLayers().Count : 0
                    };
                })
                .OrderBy(x => x.name)
                .ToList();

            return new { count = floorTypes.Count, floorTypes };
        }
    }
}
