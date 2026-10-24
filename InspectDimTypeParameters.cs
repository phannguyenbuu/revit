using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDimTypeParameters
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                .ToList();

            var list = new List<object>();
            foreach (var dt in dimTypes)
            {
                var pCntrl = dt.get_Parameter(BuiltInParameter.DIM_WITNS_LINE_CNTRL);
                var pLen = dt.get_Parameter(BuiltInParameter.DIM_WITNS_LINE_EXTENSION_BELOW);
                var pExt = dt.get_Parameter(BuiltInParameter.WITNS_LINE_EXTENSION);
                var pLineExt = dt.get_Parameter(BuiltInParameter.DIM_LINE_EXTENSION);
                var pGap = dt.get_Parameter(BuiltInParameter.WITNS_LINE_GAP_TO_ELT);

                list.Add(new {
                    id = dt.Id.Value,
                    name = dt.Name,
                    cntrlInt = pCntrl != null ? pCntrl.AsInteger() : -1,
                    cntrlStr = pCntrl != null ? pCntrl.AsValueString() : "null",
                    lenMm = pLen != null ? Math.Round(pLen.AsDouble() * FT_TO_MM, 2) : -1,
                    lenStr = pLen != null ? pLen.AsValueString() : "null",
                    extMm = pExt != null ? Math.Round(pExt.AsDouble() * FT_TO_MM, 2) : -1,
                    lineExtMm = pLineExt != null ? Math.Round(pLineExt.AsDouble() * FT_TO_MM, 2) : -1,
                    gapMm = pGap != null ? Math.Round(pGap.AsDouble() * FT_TO_MM, 2) : -1
                });
            }

            return new { count = list.Count, types = list };
        }
    }
}
