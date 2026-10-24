using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestAssignMaterialPattern
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var mat = doc.GetElement(new ElementId(107066)) as Material;
            if (mat == null) return new { error = "Material not found" };

            var fpe = doc.GetElement(new ElementId(2406226)) as FillPatternElement;
            if (fpe == null) return new { error = "Pattern not found" };

            using (var t = new Transaction(doc, "Assign pattern to WC material"))
            {
                t.Start();
                try
                {
                    mat.SurfaceForegroundPatternId = fpe.Id;
                    t.Commit();
                    return new {
                        status = "success",
                        matName = mat.Name,
                        patternId = mat.SurfaceForegroundPatternId.Value
                    };
                }
                catch (Exception ex)
                {
                    t.RollBack();
                    return new { status = "error", message = ex.ToString() };
                }
            }
        }
    }
}
