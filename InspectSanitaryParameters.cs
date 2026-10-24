using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSanitaryParameters
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var level = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("1"));

            long[] ids = new long[] { 820673, 818435, 814154, 149387 };
            var results = new List<object>();

            using (var trans = new Transaction(doc, "Inspect Test Params"))
            {
                trans.Start();

                foreach (var id in ids)
                {
                    var symbol = doc.GetElement(new ElementId(id)) as FamilySymbol;
                    if (symbol == null) continue;
                    if (!symbol.IsActive) symbol.Activate();

                    var inst = doc.Create.NewFamilyInstance(XYZ.Zero, symbol, level, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    doc.Regenerate();

                    var paramList = new List<object>();
                    foreach (Parameter p in inst.Parameters)
                    {
                        if (p.Definition == null) continue;
                        string val = p.StorageType switch
                        {
                            StorageType.Double => (p.AsDouble() * 304.8).ToString("F1"),
                            StorageType.Integer => p.AsInteger().ToString(),
                            StorageType.String => p.AsString() ?? "",
                            StorageType.ElementId => p.AsElementId()?.Value.ToString() ?? "",
                            _ => ""
                        };
                        paramList.Add(new { name = p.Definition.Name, isReadOnly = p.IsReadOnly, value = val });
                    }

                    results.Add(new
                    {
                        symbolId = id,
                        symbolName = symbol.Name,
                        familyName = symbol.FamilyName,
                        parameters = paramList.Where(p => {
                            var n = ((dynamic)p).name.ToLower();
                            return n.Contains("offset") || n.Contains("cao") || n.Contains("elevation") || n.Contains("level") || n.Contains("độ cao");
                        }).ToList()
                    });

                    doc.Delete(inst.Id);
                }

                trans.Commit();
            }

            return results;
        }
    }
}
