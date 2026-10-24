
using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTwoDoors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var ids = new long[] { 2360900, 2360910 };
            var list = new List<object>();
            foreach (var id in ids)
            {
                var el = doc.GetElement(new ElementId(id)) as FamilyInstance;
                if (el == null) continue;
                var loc = el.Location as LocationPoint;
                var sym = el.Symbol;
                var host = el.Host;
                
                var pList = el.Parameters.Cast<Parameter>()
                    .Where(p => !string.IsNullOrEmpty(p.AsValueString()) || !string.IsNullOrEmpty(p.AsString()))
                    .Select(p => new { name = p.Definition.Name, val = p.AsValueString() ?? p.AsString() })
                    .ToList();

                list.Add(new {
                    id = el.Id.Value,
                    name = el.Name,
                    symbolId = sym.Id.Value,
                    symbolName = sym.Name,
                    familyName = sym.FamilyName,
                    x = loc != null ? loc.Point.X * 304.8 : 0,
                    y = loc != null ? loc.Point.Y * 304.8 : 0,
                    z = loc != null ? loc.Point.Z * 304.8 : 0,
                    rotation = loc != null ? loc.Rotation * 180 / Math.PI : 0,
                    facingFlipped = el.FacingFlipped,
                    handFlipped = el.HandFlipped,
                    facingOrientation = new { x = el.FacingOrientation.X, y = el.FacingOrientation.Y, z = el.FacingOrientation.Z },
                    handOrientation = new { x = el.HandOrientation.X, y = el.HandOrientation.Y, z = el.HandOrientation.Z },
                    hostId = host?.Id.Value,
                    hostName = host?.Name,
                    paramsVal = pList
                });
            }
            return list;
        }
    }
}
