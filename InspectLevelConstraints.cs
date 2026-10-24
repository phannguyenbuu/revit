using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectLevelConstraints
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var dims = new FilteredElementCollector(doc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .ToList();

            var relevantDims = new List<object>();

            foreach (var d in dims)
            {
                bool isLocked = false;
                try { isLocked = d.IsLocked; } catch { }

                var refIds = new List<long>();
                try
                {
                    if (d.References != null)
                    {
                        foreach (Reference r in d.References)
                        {
                            if (r != null && r.ElementId != ElementId.InvalidElementId)
                                refIds.Add(r.ElementId.Value);
                        }
                    }
                }
                catch { }

                if (isLocked || refIds.Contains(311L) || refIds.Contains(694L))
                {
                    relevantDims.Add(new
                    {
                        id = d.Id.Value,
                        viewId = d.OwnerViewId.Value,
                        isLocked = isLocked,
                        refIds = refIds,
                        val = d.Value * 0.3048 * 1000
                    });
                }
            }

            // Also check all level parameters on Level 1 and Level 2
            var lvl1 = doc.GetElement(new ElementId(311L)) as Level;
            var lvl2 = doc.GetElement(new ElementId(694L)) as Level;

            var getPars = new Func<Level, object>(l => {
                if (l == null) return null;
                return l.Parameters.Cast<Parameter>().Select(p => new {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? p.AsDouble().ToString(),
                    isReadOnly = p.IsReadOnly
                }).ToList();
            });

            return new {
                totalDims = dims.Count,
                relevantDims,
                lvl1Params = getPars(lvl1),
                lvl2Params = getPars(lvl2)
            };
        }
    }
}
