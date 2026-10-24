using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Inspect3DCoordination
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .Where(v => !v.IsTemplate)
                .ToList();

            var coordView = view3Ds.FirstOrDefault(v => v.Name.IndexOf("Coordination", StringComparison.OrdinalIgnoreCase) >= 0);

            return new
            {
                total3DViews = view3Ds.Count,
                views = view3Ds.Select(v => new
                {
                    id = v.Id.Value,
                    name = v.Name,
                    hasTemplate = v.ViewTemplateId != ElementId.InvalidElementId,
                    discipline = v.Discipline.ToString(),
                    isSectionBoxActive = v.IsSectionBoxActive,
                    partsVisibility = v.PartsVisibility.ToString(),
                    levelsShowingGrids = v.GetLevelsThatShowGrids().Select(id => id.Value).ToList()
                }).ToList()
            };
        }
    }
}
