using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpFamDimensions
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var fam = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

                if (fam == null) return new { error = "Family not found" };

                var famDoc = doc.EditFamily(fam);
                if (famDoc == null) return new { error = "Cannot edit family" };

                var dims = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                var dimList = new List<object>();
                foreach (var d in dims)
                {
                    string label = null;
                    try { label = d.FamilyLabel?.Definition.Name; } catch { }

                    bool isLocked = false;
                    try { isLocked = d.IsLocked; } catch { }

                    double val = 0;
                    try { if (d.Value.HasValue) val = d.Value.Value * 304.8; } catch { }

                    int segCount = 0;
                    try { segCount = d.Segments.Size; } catch { }

                    dimList.Add(new
                    {
                        id = d.Id.Value,
                        name = d.Name,
                        label,
                        isLocked,
                        val = Math.Round(val, 1),
                        segCount
                    });
                }

                famDoc.Close(false);

                return new
                {
                    totalDims = dims.Count,
                    dims = dimList
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
