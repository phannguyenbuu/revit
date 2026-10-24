using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorParams
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var fl = doc.GetElement(new ElementId(2409419L)) as Floor;
            var offset = fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)?.AsDouble() * 304.8;
            var bb = fl.get_BoundingBox(null);

            return new {
                floorId = fl.Id.Value,
                offsetMm = offset,
                bbZMin = bb?.Min.Z * 304.8,
                bbZMax = bb?.Max.Z * 304.8
            };
        }
    }
}