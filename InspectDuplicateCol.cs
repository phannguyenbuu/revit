using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDuplicateCol
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var c1 = doc.GetElement(new ElementId(2361390L));
            var c2 = doc.GetElement(new ElementId(2379835L));

            var bb1 = c1?.get_BoundingBox(null);
            var bb2 = c2?.get_BoundingBox(null);

            return new
            {
                c1Exists = c1 != null,
                c2Exists = c2 != null,
                c1Pinned = c1?.Pinned,
                c2Pinned = c2?.Pinned,
                c1MinZ = bb1?.Min.Z * 0.3048,
                c1MaxZ = bb1?.Max.Z * 0.3048,
                c2MinZ = bb2?.Min.Z * 0.3048,
                c2MaxZ = bb2?.Max.Z * 0.3048
            };
        }
    }
}
