using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckExistingColumnLevels
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var col = doc?.GetElement(new ElementId(2360652L)) as FamilyInstance;
            if (col == null) return new { error = "Col 2360652 not found" };

            var pBase = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
            var pTop = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
            var pBaseOff = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
            var pTopOff = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

            return new
            {
                baseLevel = doc.GetElement(pBase?.AsElementId())?.Name,
                topLevel = doc.GetElement(pTop?.AsElementId())?.Name,
                baseOffset = pBaseOff?.AsDouble() * 304.8,
                topOffset = pTopOff?.AsDouble() * 304.8
            };
        }
    }
}
