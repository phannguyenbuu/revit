using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetAll3DToBottomGrid
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            var lowestLevel = levels.FirstOrDefault(); // HẦM 3 (-8.8m)
            if (lowestLevel == null) return new { error = "No levels found" };

            var singleSet = new HashSet<ElementId> { lowestLevel.Id };

            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .ToList(); // includes templates and non-templates

            int count = 0;
            using (var tx = new Transaction(doc, "Set Lowest Grid on All 3D Views"))
            {
                tx.Start();

                foreach (var v in view3Ds)
                {
                    try
                    {
                        v.ShowGridsOnLevels(singleSet);
                        count++;
                    }
                    catch { }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                lowestLevel = lowestLevel.Name,
                elevation = lowestLevel.Elevation * 0.3048,
                updatedViewsAndTemplates = count
            };
        }
    }
}
