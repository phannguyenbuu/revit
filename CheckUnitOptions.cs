using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckUnitOptions
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var dt = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .FirstOrDefault(d => d.Name == "Linear Dimension Style");

            var fo = dt?.GetUnitsFormatOptions();
            return new {
                useDefault = fo?.UseDefault,
                unitType = fo?.GetUnitTypeId().TypeId,
                accuracy = fo?.Accuracy
            };
        }
    }
}
