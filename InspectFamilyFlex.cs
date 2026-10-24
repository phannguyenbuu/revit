using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyFlex
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // Let's inspect K3_3100x2100 instance geometry in doc!
                var k3Instance = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .FirstOrDefault(w => w.Symbol.Name.Equals("K3_3100x2100", StringComparison.OrdinalIgnoreCase));

                object k3Geom = null;
                if (k3Instance != null)
                {
                    var opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = false };
                    var geomElem = k3Instance.get_Geometry(opt);
                    var solids = new List<object>();
                    if (geomElem != null)
                    {
                        ExtractSolids(geomElem, solids);
                    }
                    var bb = k3Instance.get_BoundingBox(null);
                    k3Geom = new
                    {
                        bbMin = bb != null ? new { x = Math.Round(ToMm(bb.Min.X), 0), y = Math.Round(ToMm(bb.Min.Y), 0), z = Math.Round(ToMm(bb.Min.Z), 0) } : null,
                        bbMax = bb != null ? new { x = Math.Round(ToMm(bb.Max.X), 0), y = Math.Round(ToMm(bb.Max.Y), 0), z = Math.Round(ToMm(bb.Max.Z), 0) } : null,
                        solids
                    };
                }

                // Also check S1_1500x1800 instance geometry
                var s1Instance = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .FirstOrDefault(w => w.Symbol.Name.Equals("S1_1500x1800", StringComparison.OrdinalIgnoreCase));

                object s1Geom = null;
                if (s1Instance != null)
                {
                    var opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = false };
                    var geomElem = s1Instance.get_Geometry(opt);
                    var solids = new List<object>();
                    if (geomElem != null)
                    {
                        ExtractSolids(geomElem, solids);
                    }
                    var bb = s1Instance.get_BoundingBox(null);
                    s1Geom = new
                    {
                        bbMin = bb != null ? new { x = Math.Round(ToMm(bb.Min.X), 0), y = Math.Round(ToMm(bb.Min.Y), 0), z = Math.Round(ToMm(bb.Min.Z), 0) } : null,
                        bbMax = bb != null ? new { x = Math.Round(ToMm(bb.Max.X), 0), y = Math.Round(ToMm(bb.Max.Y), 0), z = Math.Round(ToMm(bb.Max.Z), 0) } : null,
                        solids
                    };
                }

                return new { k3Geom, s1Geom };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }

        private static void ExtractSolids(GeometryElement geomElem, List<object> solids)
        {
            foreach (var obj in geomElem)
            {
                if (obj is Solid s && s.Volume > 1e-6)
                {
                    var bb = s.GetBoundingBox();
                    double dx = ToMm(bb.Max.X - bb.Min.X);
                    double dy = ToMm(bb.Max.Y - bb.Min.Y);
                    double dz = ToMm(bb.Max.Z - bb.Min.Z);
                    var matId = s.Faces.IsEmpty ? ElementId.InvalidElementId : (s.Faces.get_Item(0) as Face)?.MaterialElementId ?? ElementId.InvalidElementId;
                    solids.Add(new
                    {
                        dx = Math.Round(dx, 0),
                        dy = Math.Round(dy, 0),
                        dz = Math.Round(dz, 0),
                        vol = Math.Round(s.Volume * 0.0283168, 4), // m3
                        matId = matId.Value
                    });
                }
                else if (obj is GeometryInstance gi)
                {
                    ExtractSolids(gi.GetInstanceGeometry(), solids);
                }
            }
        }
    }
}
