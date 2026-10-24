using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCreatedTumSlab
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var floor = doc.GetElement(new ElementId(2381771)) as Floor;
            if (floor == null) return new { error = "Floor 2381771 not found" };

            var bb = floor.get_BoundingBox(null);
            var lvl = doc.GetElement(floor.LevelId) as Level;

            var planViews = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate)
                .Select(v => new
                {
                    id = v.Id.Value,
                    name = v.Name,
                    levelName = v.GenLevel?.Name,
                    levelElev = (v.GenLevel?.Elevation ?? 0) * FT2M
                })
                .ToList();

            return new
            {
                floorId = floor.Id.Value,
                levelName = lvl?.Name,
                levelElevM = (lvl?.Elevation ?? 0) * FT2M,
                bbMinM = new { x = bb.Min.X * FT2M, y = bb.Min.Y * FT2M, z = bb.Min.Z * FT2M },
                bbMaxM = new { x = bb.Max.X * FT2M, y = bb.Max.Y * FT2M, z = bb.Max.Z * FT2M },
                planViews
            };
        }
    }
}
