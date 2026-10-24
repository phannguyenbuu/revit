using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWcStallDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var w1 = doc.GetElement(new ElementId(2368971L)) as Wall;
            var w2 = doc.GetElement(new ElementId(2368972L)) as Wall;

            return new
            {
                w1 = w1 != null ? new {
                    id = w1.Id.Value,
                    baseLevel = w1.LevelId.Value,
                    topLevel = w1.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsValueString(),
                    unconnectedHeight = w1.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * 0.3048,
                    baseOffset = w1.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() * 0.3048,
                    topOffset = w1.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * 0.3048
                } : null,
                w2 = w2 != null ? new {
                    id = w2.Id.Value,
                    baseLevel = w2.LevelId.Value,
                    topLevel = w2.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsValueString(),
                    unconnectedHeight = w2.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * 0.3048,
                    baseOffset = w2.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() * 0.3048,
                    topOffset = w2.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * 0.3048
                } : null
            };
        }
    }
}
