using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectK2Geometry
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // List all open documents
                var openDocs = uiapp.Application.Documents.Cast<Document>().Select(d => new
                {
                    title = d.Title,
                    path = d.PathName,
                    isActive = d == doc
                }).ToList();

                // Check the 3 K2 instances
                var k2Instances = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(w => w.Symbol.FamilyName == "Window_K2")
                    .ToList();

                var k2GeomInfo = new List<object>();
                Options opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };

                foreach (var inst in k2Instances)
                {
                    var geom = inst.get_Geometry(opt);
                    int solidCount = 0;
                    double totalVolume = 0;

                    if (geom != null)
                    {
                        foreach (GeometryObject go in geom)
                        {
                            if (go is Solid s && s.Volume > 1e-6)
                            {
                                solidCount++;
                                totalVolume += s.Volume;
                            }
                            else if (go is GeometryInstance gi)
                            {
                                var instGeom = gi.GetInstanceGeometry();
                                if (instGeom != null)
                                {
                                    foreach (GeometryObject igo in instGeom)
                                    {
                                        if (igo is Solid isSolid && isSolid.Volume > 1e-6)
                                        {
                                            solidCount++;
                                            totalVolume += isSolid.Volume;
                                        }
                                    }
                                }
                            }
                        }
                    }

                    var bb = inst.get_BoundingBox(null);
                    k2GeomInfo.Add(new
                    {
                        id = inst.Id.Value,
                        name = inst.Name,
                        solidCount,
                        totalVolumeFt3 = Math.Round(totalVolume, 4),
                        bbMin = bb != null ? new { x = Math.Round(bb.Min.X * FT2M, 3), y = Math.Round(bb.Min.Y * FT2M, 3), z = Math.Round(bb.Min.Z * FT2M, 3) } : null,
                        bbMax = bb != null ? new { x = Math.Round(bb.Max.X * FT2M, 3), y = Math.Round(bb.Max.Y * FT2M, 3), z = Math.Round(bb.Max.Z * FT2M, 3) } : null
                    });
                }

                // Check the 4 stacked walls
                var stackWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var lc = (w.Location as LocationCurve)?.Curve;
                        if (lc == null) return false;
                        double x = lc.GetEndPoint(0).X * FT2M;
                        double y0 = lc.GetEndPoint(0).Y * FT2M;
                        return Math.Abs(x - 0.55) < 0.05 && Math.Abs(y0 - 12.09375) < 0.05;
                    })
                    .Select(w =>
                    {
                        var bb = w.get_BoundingBox(null);
                        return new
                        {
                            id = w.Id.Value,
                            bbMin = bb != null ? new { x = Math.Round(bb.Min.X * FT2M, 3), y = Math.Round(bb.Min.Y * FT2M, 3), z = Math.Round(bb.Min.Z * FT2M, 3) } : null,
                            bbMax = bb != null ? new { x = Math.Round(bb.Max.X * FT2M, 3), y = Math.Round(bb.Max.Y * FT2M, 3), z = Math.Round(bb.Max.Z * FT2M, 3) } : null
                        };
                    })
                    .ToList();

                return new
                {
                    success = true,
                    activeDoc = doc.Title,
                    activeDocPath = doc.PathName,
                    openDocs,
                    k2GeomInfo,
                    stackWalls
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
