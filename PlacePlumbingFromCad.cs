using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;
using System.Text.Json;

namespace RevitScript
{
    public static class PlacePlumbingFromCad
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // Find Level 1
            var level = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("1"));

            if (level == null) return new { error = "Level 1 not found" };

            string jsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\sanitary_to_place.json";
            if (!File.Exists(jsonPath)) return new { error = "Data file not found" };

            var jsonContent = File.ReadAllText(jsonPath);
            using var jsonDoc = JsonDocument.Parse(jsonContent);
            var root = jsonDoc.RootElement;

            var createdList = new List<object>();
            var createdIds = new List<ElementId>();

            using (var trans = new Transaction(doc, "Place Plumbing Fixtures from CAD"))
            {
                trans.Start();

                foreach (var item in root.EnumerateArray())
                {
                    long symbolId = item.GetProperty("symbolId").GetInt64();
                    string blockName = item.GetProperty("blockName").GetString() ?? "";
                    string category = item.GetProperty("category").GetString() ?? "";
                    var revitPtMm = item.GetProperty("revit_pt_mm");
                    double xMm = revitPtMm[0].GetDouble();
                    double yMm = revitPtMm[1].GetDouble();
                    double rotRad = item.GetProperty("rotRad").GetDouble();
                    double rotDeg = item.GetProperty("rotDeg").GetDouble();
                    double elevMm = item.GetProperty("elevMm").GetDouble();

                    var symbol = doc.GetElement(new ElementId(symbolId)) as FamilySymbol;
                    if (symbol == null)
                    {
                        createdList.Add(new { error = $"Symbol {symbolId} not found", blockName });
                        continue;
                    }

                    if (!symbol.IsActive)
                    {
                        symbol.Activate();
                        doc.Regenerate();
                    }

                    double xFt = xMm / 304.8;
                    double yFt = yMm / 304.8;
                    double zFt = 0.0;

                    XYZ pt = new XYZ(xFt, yFt, zFt);
                    var inst = doc.Create.NewFamilyInstance(pt, symbol, level, StructuralType.NonStructural);
                    doc.Regenerate();

                    // Apply elevation offset if needed (e.g. for sink)
                    if (elevMm > 0)
                    {
                        var elevParam = inst.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM) 
                                     ?? inst.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM);
                        if (elevParam != null && !elevParam.IsReadOnly)
                        {
                            elevParam.Set(elevMm / 304.8);
                        }
                    }

                    // Apply rotation
                    if (Math.Abs(rotRad) > 1e-4)
                    {
                        var axis = Line.CreateBound(pt, pt + XYZ.BasisZ);
                        ElementTransformUtils.RotateElement(doc, inst.Id, axis, rotRad);
                    }

                    createdIds.Add(inst.Id);
                    createdList.Add(new
                    {
                        id = inst.Id.Value,
                        symbolId = symbolId,
                        symbolName = symbol.Name,
                        familyName = symbol.FamilyName,
                        blockName = blockName,
                        xMm = xMm,
                        yMm = yMm,
                        elevMm = elevMm,
                        rotDeg = rotDeg
                    });
                }

                trans.Commit();
            }

            // Select newly created elements in UI
            if (createdIds.Count > 0)
            {
                try
                {
                    uidoc.Selection.SetElementIds(createdIds);
                }
                catch { }
            }

            return new
            {
                success = true,
                count = createdList.Count,
                items = createdList
            };
        }
    }
}
