using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorReferences
    {
        private const double FT_TO_MM = 304.8;
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc.GetElement(new ElementId(312L)) as View;
            var opt = new Options { ComputeReferences = true, View = view };

            var doorIds = new List<long> { 2361175L, 2360902L };
            var results = new List<object>();

            foreach (var dId in doorIds)
            {
                var door = doc.GetElement(new ElementId(dId)) as FamilyInstance;
                if (door == null) continue;

                var geom = door.get_Geometry(opt);
                var facesList = new List<object>();

                if (geom != null)
                {
                    foreach (var gObj in geom)
                    {
                        if (gObj is GeometryInstance gInst)
                        {
                            var instGeom = gInst.GetInstanceGeometry();
                            foreach (var g2 in instGeom)
                            {
                                if (g2 is Solid s && s.Faces != null)
                                {
                                    foreach (Face f in s.Faces)
                                    {
                                        if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                        {
                                            facesList.Add(new {
                                                x = Math.Round(pf.Origin.X * FT_TO_MM, 1),
                                                refStr = pf.Reference.ConvertToStableRepresentation(doc)
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Also check host wall faces
                var host = door.Host as Wall;
                var wallFaces = new List<object>();
                if (host != null)
                {
                    var hostGeom = host.get_Geometry(opt);
                    if (hostGeom != null)
                    {
                        foreach (var gObj in hostGeom)
                        {
                            if (gObj is Solid s && s.Faces != null)
                            {
                                foreach (Face f in s.Faces)
                                {
                                    if (f is PlanarFace pf && pf.Reference != null && Math.Abs(Math.Abs(pf.FaceNormal.X) - 1.0) < 0.01)
                                    {
                                        double fx = Math.Round(pf.Origin.X * FT_TO_MM, 1);
                                        wallFaces.Add(new {
                                            x = fx,
                                            refStr = pf.Reference.ConvertToStableRepresentation(doc)
                                        });
                                    }
                                }
                            }
                        }
                    }
                }

                results.Add(new {
                    doorId = dId,
                    doorName = door.Name,
                    doorFaces = facesList,
                    hostWallId = host?.Id.Value,
                    hostWallFaces = wallFaces
                });
            }

            return new { results };
        }
    }
}
