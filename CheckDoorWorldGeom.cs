using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDoorWorldGeom
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var door = doc.GetElement(new ElementId(2363712L)) as FamilyInstance;
            if (door == null) return new { error = "Door 2363712 not found" };

            var opt = new Options { DetailLevel = ViewDetailLevel.Fine, IncludeNonVisibleObjects = true };
            var geom = door.get_Geometry(opt);

            var solids = new List<object>();
            var instGeomList = new List<object>();

            if (geom != null)
            {
                foreach (var g in geom)
                {
                    if (g is Solid s && s.Volume > 0)
                    {
                        var bb = s.GetBoundingBox();
                        solids.Add(new
                        {
                            vol = s.Volume,
                            min = new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048, z = bb.Min.Z * 0.3048 },
                            max = new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048, z = bb.Max.Z * 0.3048 }
                        });
                    }
                    else if (g is GeometryInstance gi)
                    {
                        var tr = gi.Transform;
                        var ig = gi.GetInstanceGeometry();
                        instGeomList.Add(new
                        {
                            origin = new { x = tr.Origin.X * 0.3048, y = tr.Origin.Y * 0.3048, z = tr.Origin.Z * 0.3048 },
                            basisX = new { x = tr.BasisX.X, y = tr.BasisX.Y, z = tr.BasisX.Z },
                            basisY = new { x = tr.BasisY.X, y = tr.BasisY.Y, z = tr.BasisY.Z },
                            basisZ = new { x = tr.BasisZ.X, y = tr.BasisZ.Y, z = tr.BasisZ.Z }
                        });
                    }
                }
            }

            return new { solids, instGeomList };
        }
    }
}
