using System;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDimBgInt
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            long id = 2413998L;
            if (args.TryGetProperty("typeId", out var pId)) id = pId.GetInt64();
            var dt = doc.GetElement(new ElementId(id)) as DimensionType;
            if (dt == null) return new { error = "Not found" };
            var p = dt.get_Parameter(BuiltInParameter.DIM_TEXT_BACKGROUND);
            return new {
                id = dt.Id.Value,
                name = dt.Name,
                intVal = p != null ? p.AsInteger() : -99,
                strVal = p != null ? p.AsValueString() : "null"
            };
        }
    }
}
