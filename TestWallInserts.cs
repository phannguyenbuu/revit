
using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestWallInserts
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No doc or view" };

            // Find wall 2368943
            var wall = doc.GetElement(new ElementId(2368943L)) as Wall;
            if (wall == null) return new { error = "Wall not found" };

            var inserts = wall.FindInserts(true, true, true, false);
            var insertDetails = new List<object>();

            var opt = new Options { ComputeReferences = true, View = view };

            foreach (var insId in inserts)
            {
                var elem = doc.GetElement(insId);
                var fi = elem as FamilyInstance;
                var bb = elem.get_BoundingBox(view);
                var lp = elem.Location as LocationPoint;

                // Let's check geometry references of family instance
                int refCount = 0;
                var geom = elem.get_Geometry(opt);
                if (geom != null)
                {
                    foreach (var gObj in geom)
                    {
                        if (gObj is GeometryInstance gi)
                        {
                            var instGeom = gi.GetInstanceGeometry();
                            if (instGeom != null)
                            {
                                foreach (var subObj in instGeom)
                                {
                                    if (subObj is Solid s)
                                    {
                                        foreach (Face f in s.Faces)
                                        {
                                            if (f.Reference != null) refCount++;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                insertDetails.Add(new {
                    id = insId.Value,
                    name = elem.Name,
                    cat = elem.Category?.Name,
                    bbX = bb != null ? new { min = Math.Round(bb.Min.X * 304.8, 1), max = Math.Round(bb.Max.X * 304.8, 1) } : null,
                    refCount
                });
            }

            // Also check wall's own cut faces
            var wallGeom = wall.get_Geometry(opt);
            var xFaces = new List<double>();
            if (wallGeom != null)
            {
                foreach (var gObj in wallGeom)
                {
                    if (gObj is Solid s)
                    {
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null)
                            {
                                if (Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                {
                                    xFaces.Add(Math.Round(pf.Origin.X * 304.8, 1));
                                }
                            }
                        }
                    }
                }
            }
            xFaces.Sort();

            return new {
                wallId = wall.Id.Value,
                insertCount = inserts.Count,
                inserts = insertDetails,
                wallXFacesCount = xFaces.Count,
                wallXFaces = xFaces
            };
        }
    }
}
