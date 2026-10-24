using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindDoorCuaThuyLuc
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // Find all doors with family name containing "thuy luc" or "thủy lực"
                var doors = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(d => d.Symbol.FamilyName.IndexOf("thuy luc", StringComparison.OrdinalIgnoreCase) >= 0
                             || d.Symbol.FamilyName.IndexOf("thủy lực", StringComparison.OrdinalIgnoreCase) >= 0)
                    .ToList();

                var doorDetails = new List<object>();

                foreach (var d in doors)
                {
                    var lp = d.Location as LocationPoint;
                    var bb = d.get_BoundingBox(null);
                    var level = doc.GetElement(d.LevelId);
                    var host = d.Host;

                    // Parameters
                    var pDict = new Dictionary<string, string>();
                    foreach (Parameter p in d.Parameters)
                    {
                        if (p.HasValue && !string.IsNullOrWhiteSpace(p.Definition.Name))
                        {
                            string val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString("F2");
                            if (!string.IsNullOrWhiteSpace(val))
                            {
                                pDict[p.Definition.Name] = val;
                            }
                        }
                    }

                    // Type parameters
                    var tDict = new Dictionary<string, string>();
                    foreach (Parameter p in d.Symbol.Parameters)
                    {
                        if (p.HasValue && !string.IsNullOrWhiteSpace(p.Definition.Name))
                        {
                            string val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString("F2");
                            if (!string.IsNullOrWhiteSpace(val))
                            {
                                tDict[p.Definition.Name] = val;
                            }
                        }
                    }

                    doorDetails.Add(new
                    {
                        id = d.Id.Value,
                        category = d.Category?.Name,
                        familyName = d.Symbol.FamilyName,
                        typeName = d.Symbol.Name,
                        level = level?.Name,
                        host = host != null ? $"{host.Category?.Name} ID {host.Id.Value} ({host.Name})" : "none",
                        location = lp != null ? new { x = Math.Round(ToMm(lp.Point.X), 1), y = Math.Round(ToMm(lp.Point.Y), 1), z = Math.Round(ToMm(lp.Point.Z), 1) } : null,
                        bb = bb != null ? new
                        {
                            dx = Math.Round(ToMm(bb.Max.X - bb.Min.X), 0),
                            dy = Math.Round(ToMm(bb.Max.Y - bb.Min.Y), 0),
                            dz = Math.Round(ToMm(bb.Max.Z - bb.Min.Z), 0)
                        } : null,
                        instanceParams = pDict,
                        typeParams = tDict
                    });
                }

                // If doors found, select it back in the UI!
                if (doors.Count > 0)
                {
                    uidoc.Selection.SetElementIds(doors.Select(d => d.Id).ToList());
                }

                return new
                {
                    totalFound = doors.Count,
                    doors = doorDetails
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
