using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectMatTienGeometry
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var elem = doc.GetElement(new ElementId(2391783L));
            if (elem == null) return new { error = "Element 2391783 not found" };

            var opt = new Options
            {
                ComputeReferences = true,
                DetailLevel = ViewDetailLevel.Fine,
                IncludeNonVisibleObjects = true
            };

            var geomElem = elem.get_Geometry(opt);
            var results = new List<object>();

            void ExtractGeom(GeometryObject g, string path)
            {
                if (g is GeometryInstance gInst)
                {
                    var instGeom = gInst.GetInstanceGeometry();
                    var symGeom = gInst.GetSymbolGeometry();
                    results.Add(new { path, type = "GeometryInstance", instGeomCount = instGeom?.Count() ?? 0, symGeomCount = symGeom?.Count() ?? 0 });
                    if (instGeom != null)
                    {
                        int idx = 0;
                        foreach (var sub in instGeom)
                        {
                            ExtractGeom(sub, $"{path}/inst_{idx++}");
                        }
                    }
                }
                else if (g is Solid solid)
                {
                    results.Add(new
                    {
                        path,
                        type = "Solid",
                        volume = solid.Volume,
                        facesCount = solid.Faces.Size,
                        edgesCount = solid.Edges.Size
                    });
                }
                else if (g is Mesh mesh)
                {
                    results.Add(new
                    {
                        path,
                        type = "Mesh",
                        numTriangles = mesh.NumTriangles,
                        numVertices = mesh.Vertices.Count
                    });
                }
                else
                {
                    results.Add(new { path, type = g.GetType().Name });
                }
            }

            if (geomElem != null)
            {
                int rootIdx = 0;
                foreach (var g in geomElem)
                {
                    ExtractGeom(g, $"root_{rootIdx++}");
                }
            }

            return new { elemId = elem.Id.Value, elemName = elem.Name, geomCount = geomElem?.Count() ?? 0, results };
        }
    }
}
