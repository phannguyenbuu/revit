using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CompareSanhAndMatTien
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var e1 = doc.GetElement(new ElementId(2385103L));
            var e2 = doc.GetElement(new ElementId(2391783L));

            var opt = new Options { DetailLevel = ViewDetailLevel.Fine };

            var g1 = e1?.get_Geometry(opt);
            var g2 = e2?.get_Geometry(opt);

            return new
            {
                elem1 = new { id = e1?.Id.Value, name = e1?.Name, cat = e1?.Category?.Name, type = e1?.GetType().Name },
                elem2 = new { id = e2?.Id.Value, name = e2?.Name, cat = e2?.Category?.Name, type = e2?.GetType().Name }
            };
        }
    }
}
