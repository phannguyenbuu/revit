using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowFamiliesDetail
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                string[] famNames = new[]
                {
                    "CUA SO 2 CANH NHOM KINH O O THOANG",
                    "CUA SO2 CANH NHOM KINH CO O THOANG"
                };

                var results = new List<object>();

                foreach (var name in famNames)
                {
                    var fam = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name.Equals(name, StringComparison.OrdinalIgnoreCase));

                    if (fam == null)
                    {
                        results.Add(new { name, error = "Family not found" });
                        continue;
                    }

                    var famDoc = doc.EditFamily(fam);
                    if (famDoc == null)
                    {
                        results.Add(new { name, error = "Cannot edit" });
                        continue;
                    }

                    // Family Types
                    var famMgr = famDoc.FamilyManager;
                    var types = new List<object>();
                    foreach (FamilyType ft in famMgr.Types)
                    {
                        var paramDict = new Dictionary<string, string>();
                        foreach (FamilyParameter fp in famMgr.Parameters)
                        {
                            if (ft.HasValue(fp))
                            {
                                paramDict[fp.Definition.Name] = ft.AsString(fp) ?? ft.AsDouble(fp)?.ToString("F1") ?? ft.AsInteger(fp)?.ToString() ?? ft.AsValueString(fp);
                            }
                        }
                        types.Add(new { typeName = ft.Name, paramDict });
                    }

                    // Extrusions
                    var extrusions = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(Extrusion))
                        .Cast<Extrusion>()
                        .Select(e =>
                        {
                            int loopCount = 0;
                            var loopBBoxes = new List<object>();
                            if (e.Sketch != null)
                            {
                                loopCount = e.Sketch.Profile.Size;
                                foreach (CurveArray ca in e.Sketch.Profile)
                                {
                                    double minX = double.MaxValue, maxX = double.MinValue;
                                    double minZ = double.MaxValue, maxZ = double.MinValue;
                                    foreach (Curve c in ca)
                                    {
                                        var p0 = c.GetEndPoint(0);
                                        var p1 = c.GetEndPoint(1);
                                        minX = Math.Min(minX, Math.Min(ToMm(p0.X), ToMm(p1.X)));
                                        maxX = Math.Max(maxX, Math.Max(ToMm(p0.X), ToMm(p1.X)));
                                        minZ = Math.Min(minZ, Math.Min(ToMm(p0.Z), ToMm(p1.Z)));
                                        maxZ = Math.Max(maxZ, Math.Max(ToMm(p0.Z), ToMm(p1.Z)));
                                    }
                                    loopBBoxes.Add(new { minX = Math.Round(minX, 1), maxX = Math.Round(maxX, 1), minZ = Math.Round(minZ, 1), maxZ = Math.Round(maxZ, 1) });
                                }
                            }
                            return new
                            {
                                id = e.Id.Value,
                                name = e.Name,
                                subCategory = e.Subcategory?.Name,
                                loopCount,
                                loopBBoxes,
                                startOffset = Math.Round(ToMm(e.StartOffset), 1),
                                endOffset = Math.Round(ToMm(e.EndOffset), 1)
                            };
                        })
                        .ToList();

                    // Reference Planes
                    var refPlanes = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(ReferencePlane))
                        .Cast<ReferencePlane>()
                        .Select(rp => new { rp.Name, bubble = new { x = Math.Round(ToMm(rp.BubbleEnd.X), 1), y = Math.Round(ToMm(rp.BubbleEnd.Y), 1), z = Math.Round(ToMm(rp.BubbleEnd.Z), 1) } })
                        .ToList();

                    famDoc.Close(false);

                    results.Add(new
                    {
                        name,
                        types,
                        extrusions,
                        refPlanesCount = refPlanes.Count
                    });
                }

                return new { results };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
