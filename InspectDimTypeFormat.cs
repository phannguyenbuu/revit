using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDimTypeFormat
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var dim = doc.GetElement(new ElementId(2408820)) as Dimension;
            var dt = dim?.DimensionType;
            if (dt == null) return new { error = "No dim or dim type" };

            var fo = dt.GetUnitsFormatOptions();
            var unitTypeId = fo.GetUnitTypeId().TypeId;
            double acc = fo.Accuracy;
            bool useDefault = fo.UseDefault;

            return new {
                dtName = dt.Name,
                useDefault,
                unitTypeId,
                acc,
                accInMm = acc * 304.8
            };
        }
    }
}
