using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyInternals
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var famNames = new string[] {
                "CUA SO 2 CANH NHOM KINH O O THOANG",
                "CỬA 1 CÁNH EROWINDOW(có ô chết)",
                "CỬA 2 CÁNH EROWINDOW(có ô chết)",
                "CUA ĐI 2 CANH NHOM KINH O O THOANG",
                "ATT_Window 2"
            };

            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => famNames.Contains(f.Name))
                .ToList();

            var res = new List<object>();

            foreach (var fam in fams)
            {
                Document famDoc = null;
                try
                {
                    famDoc = doc.EditFamily(fam);
                }
                catch (Exception ex)
                {
                    res.Add(new { name = fam.Name, error = ex.Message });
                    continue;
                }

                if (famDoc == null) continue;

                // Inspect parameters in FamilyManager
                var fm = famDoc.FamilyManager;
                var paramList = new List<object>();
                foreach (FamilyParameter fp in fm.Parameters)
                {
                    string defName = fp.Definition.Name;
                    paramList.Add(new
                    {
                        name = defName,
                        isInstance = fp.IsInstance,
                        storageType = fp.StorageType.ToString()
                    });
                }

                // Inspect types and values
                var typesList = new List<object>();
                foreach (FamilyType ft in fm.Types)
                {
                    var vals = new Dictionary<string, string>();
                    foreach (FamilyParameter fp in fm.Parameters)
                    {
                        string n = fp.Definition.Name;
                        if (n.Contains("Width") || n.Contains("Height") || n.Contains("Frame") || n.Contains("Offset") || n.Contains("Projection") || n.Contains("Inset") || n.Contains("Depth") || n.Contains("Lọt") || n.Contains("Bì") || n.Contains("Outside") || n.Contains("Inside") || n.Contains("Rough"))
                        {
                            if (ft.HasValue(fp))
                            {
                                if (fp.StorageType == StorageType.Double)
                                {
                                    double? d = ft.AsDouble(fp);
                                    vals[n] = d.HasValue ? $"{d.Value * 304.8:F1} mm" : "null";
                                }
                                else if (fp.StorageType == StorageType.String)
                                {
                                    vals[n] = ft.AsString(fp) ?? "";
                                }
                            }
                        }
                    }
                    typesList.Add(new { typeName = ft.Name, values = vals });
                }

                // Check solids/extrusions and reference planes
                var extrusions = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Extrusion))
                    .Cast<Extrusion>()
                    .Count();

                var sweeps = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Sweep))
                    .Cast<Sweep>()
                    .Count();

                var refPlanes = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(ReferencePlane))
                    .Cast<ReferencePlane>()
                    .Select(rp => rp.Name)
                    .Where(n => !string.IsNullOrEmpty(n))
                    .ToList();

                famDoc.Close(false);

                res.Add(new
                {
                    familyName = fam.Name,
                    types = typesList,
                    refPlanes = refPlanes,
                    extrusions = extrusions,
                    sweeps = sweeps
                });
            }

            return res;
        }
    }
}
