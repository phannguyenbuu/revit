using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class PlaceSanhChinhInstance
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Locate Family and Symbol
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "Sanh_Chinh_3dsMax");

            if (fam == null) return new { error = "Family Sanh_Chinh_3dsMax not found in project" };

            FamilySymbol symbol = null;
            foreach (var sid in fam.GetFamilySymbolIds())
            {
                symbol = doc.GetElement(sid) as FamilySymbol;
                if (symbol != null) break;
            }

            if (symbol == null) return new { error = "Symbol for Sanh_Chinh_3dsMax not found" };

            // 2. Locate Level 1
            var level1 = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => Math.Abs(l.Elevation) < 0.01)
                ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name.Contains("1") || l.Name.Contains("Tret"));

            // 3. Check if already placed
            var existingInstances = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => fi.Symbol?.Family?.Name == "Sanh_Chinh_3dsMax" || fi.Symbol?.Id == symbol.Id)
                .ToList();

            FamilyInstance placedInstance = null;
            string actionTaken = "";

            using (var tx = new Transaction(doc, "Place Sanh_Chinh_3dsMax Instance"))
            {
                tx.Start();

                if (!symbol.IsActive)
                {
                    symbol.Activate();
                    doc.Regenerate();
                }

                XYZ targetPt = new XYZ(550.0 * MM2FT, 6600.0 * MM2FT, 0.0);

                if (existingInstances.Count > 0)
                {
                    placedInstance = existingInstances[0];
                    var loc = placedInstance.Location as LocationPoint;
                    if (loc != null)
                    {
                        XYZ currentPt = loc.Point;
                        XYZ delta = targetPt - currentPt;
                        if (delta.GetLength() > 0.001)
                        {
                            ElementTransformUtils.MoveElement(doc, placedInstance.Id, delta);
                            actionTaken = "Moved existing instance to exact coordinates (550, 6600, 0)";
                        }
                        else
                        {
                            actionTaken = "Existing instance already at exact coordinates (550, 6600, 0)";
                        }
                    }
                }
                else
                {
                    try
                    {
                        if (level1 != null)
                        {
                            placedInstance = doc.Create.NewFamilyInstance(targetPt, symbol, level1, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                        }
                        else
                        {
                            placedInstance = doc.Create.NewFamilyInstance(targetPt, symbol, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                        }
                    }
                    catch
                    {
                        placedInstance = doc.Create.NewFamilyInstance(targetPt, symbol, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    }
                    actionTaken = "Created new instance at exact coordinates (550, 6600, 0)";
                }

                if (placedInstance != null)
                {
                    // Ensure Level parameter is assigned
                    if (level1 != null)
                    {
                        var lvlParam = placedInstance.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
                                    ?? placedInstance.get_Parameter(BuiltInParameter.SCHEDULE_LEVEL_PARAM)
                                    ?? placedInstance.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM);
                        if (lvlParam != null && !lvlParam.IsReadOnly)
                        {
                            lvlParam.Set(level1.Id);
                        }
                    }
                }

                tx.Commit();
            }

            // 4. Retrieve Bounding Box & placement summary
            var bb = placedInstance?.get_BoundingBox(null);
            var locPt = (placedInstance?.Location as LocationPoint)?.Point;

            return new
            {
                success = placedInstance != null,
                action = actionTaken,
                instanceId = placedInstance?.Id.Value,
                level = level1 != null ? new { id = level1.Id.Value, name = level1.Name, elev = Math.Round(level1.Elevation * FT2MM, 1) } : null,
                placedLocation = locPt != null ? new { x = Math.Round(locPt.X * FT2MM, 1), y = Math.Round(locPt.Y * FT2MM, 1), z = Math.Round(locPt.Z * FT2MM, 1) } : null,
                boundingBox = bb != null ? new {
                    min = new { x = Math.Round(bb.Min.X * FT2MM, 1), y = Math.Round(bb.Min.Y * FT2MM, 1), z = Math.Round(bb.Min.Z * FT2MM, 1) },
                    max = new { x = Math.Round(bb.Max.X * FT2MM, 1), y = Math.Round(bb.Max.Y * FT2MM, 1), z = Math.Round(bb.Max.Z * FT2MM, 1) }
                } : null
            };
        }
    }
}
