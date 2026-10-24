using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectEntranceAndSanhTarget
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Find Level 1
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = l.Id.Value, name = l.Name, elevationMm = Math.Round(l.Elevation * FT2MM, 1) })
                .ToList();

            var level1 = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => Math.Abs(l.Elevation) < 0.01 || l.Name.Contains("1") || l.Name.Contains("Tret"));

            // 2. Find Door D1 (or entrance doors)
            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(d => {
                    var lp = d.Location as LocationPoint;
                    var host = d.Host as Wall;
                    var hostCurve = (host?.Location as LocationCurve)?.Curve;
                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        symbolName = d.Symbol.Name,
                        familyName = d.Symbol.FamilyName,
                        level = doc.GetElement(d.LevelId)?.Name,
                        pt = lp != null ? new { x = Math.Round(lp.Point.X * FT2MM, 1), y = Math.Round(lp.Point.Y * FT2MM, 1), z = Math.Round(lp.Point.Z * FT2MM, 1) } : null,
                        facingOrientation = new { x = Math.Round(d.FacingOrientation.X, 4), y = Math.Round(d.FacingOrientation.Y, 4), z = Math.Round(d.FacingOrientation.Z, 4) },
                        handOrientation = new { x = Math.Round(d.HandOrientation.X, 4), y = Math.Round(d.HandOrientation.Y, 4), z = Math.Round(d.HandOrientation.Z, 4) },
                        hostId = host?.Id.Value,
                        hostCurve = hostCurve != null ? new {
                            p0 = new { x = Math.Round(hostCurve.GetEndPoint(0).X * FT2MM, 1), y = Math.Round(hostCurve.GetEndPoint(0).Y * FT2MM, 1) },
                            p1 = new { x = Math.Round(hostCurve.GetEndPoint(1).X * FT2MM, 1), y = Math.Round(hostCurve.GetEndPoint(1).Y * FT2MM, 1) }
                        } : null
                    };
                })
                .ToList();

            // 3. Find Symbol Sanh_Chinh_3dsMax
            var sanhFam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "Sanh_Chinh_3dsMax");

            FamilySymbol sanhSymbol = null;
            if (sanhFam != null)
            {
                var sId = sanhFam.GetFamilySymbolIds().FirstOrDefault();
                if (sId != null && sId != ElementId.InvalidElementId)
                {
                    sanhSymbol = doc.GetElement(sId) as FamilySymbol;
                }
            }

            // Also inspect the Family file bounding box directly if needed
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa";
            object famFileInfo = null;
            if (File.Exists(famPath))
            {
                var fi = new FileInfo(famPath);
                famFileInfo = new { fi.FullName, fi.Length, fi.LastWriteTime };
            }

            return new
            {
                levels,
                level1Found = level1 != null ? new { id = level1.Id.Value, name = level1.Name, elev = Math.Round(level1.Elevation * FT2MM, 1) } : null,
                doors,
                sanhFamId = sanhFam?.Id.Value,
                sanhSymbolId = sanhSymbol?.Id.Value,
                sanhSymbolActive = sanhSymbol?.IsActive,
                famFileInfo
            };
        }
    }
}
