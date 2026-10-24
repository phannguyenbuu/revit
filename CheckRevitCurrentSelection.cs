using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckRevitCurrentSelection
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var selIds = uidoc.Selection.GetElementIds().ToList();
                var items = new List<object>();

                foreach (var id in selIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem == null) continue;

                    var fi = elem as FamilyInstance;
                    var elemType = doc.GetElement(elem.GetTypeId()) as ElementType;

                    // Location
                    object locInfo = null;
                    if (elem.Location is LocationPoint lp)
                    {
                        locInfo = new
                        {
                            x = Math.Round(ToMm(lp.Point.X), 1),
                            y = Math.Round(ToMm(lp.Point.Y), 1),
                            z = Math.Round(ToMm(lp.Point.Z), 1)
                        };
                    }

                    // Bounding Box
                    var bb = elem.get_BoundingBox(null);
                    object bbInfo = null;
                    if (bb != null)
                    {
                        bbInfo = new
                        {
                            min = new { x = Math.Round(ToMm(bb.Min.X), 0), y = Math.Round(ToMm(bb.Min.Y), 0), z = Math.Round(ToMm(bb.Min.Z), 0) },
                            max = new { x = Math.Round(ToMm(bb.Max.X), 0), y = Math.Round(ToMm(bb.Max.Y), 0), z = Math.Round(ToMm(bb.Max.Z), 0) },
                            dx = Math.Round(ToMm(bb.Max.X - bb.Min.X), 0),
                            dy = Math.Round(ToMm(bb.Max.Y - bb.Min.Y), 0),
                            dz = Math.Round(ToMm(bb.Max.Z - bb.Min.Z), 0)
                        };
                    }

                    // Instance Parameters
                    var instParams = new Dictionary<string, string>();
                    foreach (Parameter p in elem.Parameters)
                    {
                        if (p.HasValue && !string.IsNullOrWhiteSpace(p.Definition.Name))
                        {
                            string val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString("F2");
                            if (!string.IsNullOrWhiteSpace(val))
                            {
                                instParams[p.Definition.Name] = val;
                            }
                        }
                    }

                    // Type Parameters
                    var typeParams = new Dictionary<string, string>();
                    if (elemType != null)
                    {
                        foreach (Parameter p in elemType.Parameters)
                        {
                            if (p.HasValue && !string.IsNullOrWhiteSpace(p.Definition.Name))
                            {
                                string val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString("F2");
                                if (!string.IsNullOrWhiteSpace(val))
                                {
                                    typeParams[p.Definition.Name] = val;
                                }
                            }
                        }
                    }

                    items.Add(new
                    {
                        id = id.Value,
                        category = elem.Category?.Name,
                        name = elem.Name,
                        familyName = fi?.Symbol?.FamilyName ?? elemType?.FamilyName,
                        symbolName = fi?.Symbol?.Name ?? elemType?.Name,
                        level = doc.GetElement(elem.LevelId)?.Name,
                        host = fi?.Host != null ? $"{fi.Host.Category?.Name} ID {fi.Host.Id.Value} ({fi.Host.Name})" : null,
                        location = locInfo,
                        boundingBox = bbInfo,
                        instanceParams = instParams,
                        typeParams = typeParams
                    });
                }

                return new
                {
                    count = selIds.Count,
                    items
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
