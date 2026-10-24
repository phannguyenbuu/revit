using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStackPosition
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var elem = doc.GetElement(new ElementId(2377860));
                if (elem == null) return new { error = "Element 2377860 not found" };

                // Get bounding box in model coordinates
                var bb = elem.get_BoundingBox(null);
                double minZ = bb != null ? bb.Min.Z * FT2M : double.NaN;
                double maxZ = bb != null ? bb.Max.Z * FT2M : double.NaN;
                double minX = bb != null ? bb.Min.X * FT2M : double.NaN;
                double maxX = bb != null ? bb.Max.X * FT2M : double.NaN;
                double minY = bb != null ? bb.Min.Y * FT2M : double.NaN;
                double maxY = bb != null ? bb.Max.Y * FT2M : double.NaN;

                // Parameters
                var sillParam = elem.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                double sillM = sillParam != null ? sillParam.AsDouble() * FT2M : double.NaN;

                var lvlParam = elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM);
                string lvlName = "";
                double lvlElevM = double.NaN;
                if (lvlParam != null)
                {
                    var lvl = doc.GetElement(lvlParam.AsElementId()) as Level;
                    if (lvl != null)
                    {
                        lvlName = lvl.Name;
                        lvlElevM = lvl.Elevation * FT2M;
                    }
                }

                // Check all levels in doc
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .Select(l => new { id = l.Id.Value, name = l.Name, elevM = l.Elevation * FT2M })
                    .ToList();

                // List all parameters on the instance
                var paramList = new List<object>();
                foreach (Parameter p in elem.Parameters)
                {
                    if (p.HasValue)
                    {
                        string val = p.StorageType switch
                        {
                            StorageType.Double => (p.AsDouble() * FT2M).ToString("F4") + " m (raw: " + p.AsDouble() + ")",
                            StorageType.Integer => p.AsInteger().ToString(),
                            StorageType.String => p.AsString(),
                            StorageType.ElementId => p.AsElementId().Value.ToString(),
                            _ => ""
                        };
                        paramList.Add(new { name = p.Definition.Name, val });
                    }
                }

                return new
                {
                    bbox = new { minX, maxX, minY, maxY, minZ, maxZ },
                    level = new { name = lvlName, elevM = lvlElevM },
                    sillHeightM = sillM,
                    levels,
                    paramList
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
