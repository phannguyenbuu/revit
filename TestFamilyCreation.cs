using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestFamilyCreation
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var app = uiapp.Application;
                string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
                if (!File.Exists(templatePath))
                {
                    return new { error = "Template not found: " + templatePath };
                }

                Document famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Failed to create family doc" };

                string famPath = Path.Combine(Path.GetTempPath(), "TestWindowFamily.rfa");
                if (File.Exists(famPath)) File.Delete(famPath);

                List<string> logs = new List<string>();

                using (Transaction tx = new Transaction(famDoc, "Set Category and Geometry"))
                {
                    tx.Start();

                    // 1. Set Category to OST_Windows
                    var winCat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows);
                    famDoc.OwnerFamily.FamilyCategory = winCat;
                    logs.Add($"Category set to: {famDoc.OwnerFamily.FamilyCategory.Name}");

                    // List subcategories
                    foreach (Category sub in winCat.SubCategories)
                    {
                        logs.Add($"SubCat: {sub.Name} (Id={sub.Id.Value})");
                    }

                    // 2. Test GeometryCreationUtilities CreateExtrusionGeometry
                    double wFt = 657.5 / 304.8;
                    double hFt = 1575.5 / 304.8;
                    double tFt = 10.0 / 304.8;

                    XYZ p0 = new XYZ(-wFt / 2, 0, 112.5 / 304.8);
                    XYZ p1 = new XYZ(wFt / 2, 0, 112.5 / 304.8);
                    XYZ p2 = new XYZ(wFt / 2, 0, 112.5 / 304.8 + hFt);
                    XYZ p3 = new XYZ(-wFt / 2, 0, 112.5 / 304.8 + hFt);

                    CurveLoop loop = new CurveLoop();
                    loop.Append(Line.CreateBound(p0, p1));
                    loop.Append(Line.CreateBound(p1, p2));
                    loop.Append(Line.CreateBound(p2, p3));
                    loop.Append(Line.CreateBound(p3, p0));

                    Solid solid = GeometryCreationUtilities.CreateExtrusionGeometry(new List<CurveLoop> { loop }, XYZ.BasisY, tFt);
                    logs.Add($"Solid created: Volume={solid.Volume}");

                    // Test FreeFormElement
                    FreeFormElement ffe = FreeFormElement.Create(famDoc, solid);
                    logs.Add($"FreeFormElement created: Id={ffe.Id.Value}");

                    // Test Subcategory
                    var glassSubCat = winCat.SubCategories.Cast<Category>().FirstOrDefault(c => c.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase));
                    if (glassSubCat != null)
                    {
                        ffe.Subcategory = glassSubCat;
                        logs.Add($"FreeFormElement subcategory set to: {glassSubCat.Name}");
                    }

                    tx.Commit();
                }

                famDoc.SaveAs(famPath);
                famDoc.Close(false);

                return new { success = true, logs, famPath };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
