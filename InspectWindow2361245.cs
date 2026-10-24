using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindow2361245
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            if (win == null) return new { error = "Window 2361245 not found" };

            var hostWall = win.Host as Wall;
            var hostType = hostWall != null ? doc.GetElement(hostWall.GetTypeId()) as WallType : null;
            var cs = hostType?.GetCompoundStructure();

            var layers = new List<object>();
            if (cs != null)
            {
                foreach (var l in cs.GetLayers())
                {
                    layers.Add(new
                    {
                        func = l.Function.ToString(),
                        widthMm = l.Width * 304.8,
                        mat = doc.GetElement(l.MaterialId)?.Name ?? "None"
                    });
                }
            }

            var typeParams = new Dictionary<string, string>();
            foreach (Parameter p in win.Symbol.Parameters)
            {
                if (p.HasValue)
                {
                    typeParams[p.Definition.Name] = p.StorageType == StorageType.Double ? $"{p.AsDouble() * 304.8:F1} mm" : p.AsValueString() ?? p.AsString();
                }
            }

            var instParams = new Dictionary<string, string>();
            foreach (Parameter p in win.Parameters)
            {
                if (p.HasValue)
                {
                    instParams[p.Definition.Name] = p.StorageType == StorageType.Double ? $"{p.AsDouble() * 304.8:F1} mm" : p.AsValueString() ?? p.AsString();
                }
            }

            // Get location and orientation
            var lp = win.Location as LocationPoint;
            var facing = win.FacingOrientation;
            var hand = win.HandOrientation;

            return new
            {
                id = win.Id.Value,
                name = win.Name,
                familyName = win.Symbol.FamilyName,
                hostWallId = hostWall?.Id.Value,
                hostWallName = hostWall?.Name,
                hostWallWidthMm = (hostWall?.Width ?? 0) * 304.8,
                layers = layers,
                facingOrientation = $"[{facing.X:F3}, {facing.Y:F3}, {facing.Z:F3}]",
                handOrientation = $"[{hand.X:F3}, {hand.Y:F3}, {hand.Z:F3}]",
                locationPoint = lp != null ? $"[{lp.Point.X * 304.8:F1}, {lp.Point.Y * 304.8:F1}, {lp.Point.Z * 304.8:F1}]" : "null",
                typeParams = typeParams,
                instParams = instParams
            };
        }
    }
}
