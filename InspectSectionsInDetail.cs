using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSectionsInDetail
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var v1 = doc.GetElement(new ElementId(312)) as ViewPlan;
                var v2 = doc.GetElement(new ElementId(695)) as ViewPlan;
                var v3 = doc.GetElement(new ElementId(1727632)) as ViewPlan;

                var sections = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .Where(s => !s.IsCallout && s.ViewType == ViewType.Section)
                    .ToList();

                var list = new List<object>();
                foreach (var s in sections)
                {
                    // Parameter VIEWER_HIDE_FINE_FLAGS / SECTION_COARSER_SCALE_PULLDOWN_METRIC
                    var pCoarser = s.get_Parameter(BuiltInParameter.SECTION_COARSER_SCALE_PULLDOWN_METRIC);
                    int coarserVal = pCoarser != null ? pCoarser.AsInteger() : -1;

                    bool hiddenInV1 = v1 != null && s.IsHidden(v1);
                    bool hiddenInV2 = v2 != null && s.IsHidden(v2);
                    bool hiddenInV3 = v3 != null && s.IsHidden(v3);

                    list.Add(new {
                        id = s.Id.Value,
                        name = s.Name,
                        coarserVal,
                        hiddenInV1,
                        hiddenInV2,
                        hiddenInV3
                    });
                }

                return new {
                    sections = list
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
