using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTestSanhFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Test_Sanh_Import.rfa";
            var app = uiapp.Application;

            var famDoc = app.OpenDocumentFile(famPath);
            if (famDoc == null) return new { error = "Cannot open family doc" };

            var cats = famDoc.Settings.Categories.Cast<Category>().ToList();
            var importCat = cats.FirstOrDefault(c => c.Name.Equals("Imports in Families", StringComparison.OrdinalIgnoreCase));
            
            var subCats = new List<object>();
            if (importCat != null)
            {
                foreach (Category sub in importCat.SubCategories)
                {
                    subCats.Add(new
                    {
                        name = sub.Name,
                        material = sub.Material?.Name,
                        color = sub.LineColor != null ? $"{sub.LineColor.Red},{sub.LineColor.Green},{sub.LineColor.Blue}" : null
                    });
                }
            }

            var materials = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Material))
                .Cast<Material>()
                .Select(m => m.Name)
                .ToList();

            var impElem = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .FirstOrDefault();

            var geomInfo = new List<string>();
            if (impElem != null)
            {
                var opt = new Options { ComputeReferences = true };
                var geom = impElem.get_Geometry(opt);
                if (geom != null)
                {
                    foreach (var gobj in geom)
                    {
                        if (gobj is GeometryInstance gi)
                        {
                            var instGeom = gi.GetInstanceGeometry();
                            foreach (var o in instGeom)
                            {
                                geomInfo.Add(o.GetType().Name);
                            }
                        }
                        else
                        {
                            geomInfo.Add(gobj.GetType().Name);
                        }
                    }
                }
            }

            famDoc.Close(false);

            return new
            {
                subCats,
                materials,
                geomTypes = geomInfo.GroupBy(x => x).Select(g => new { type = g.Key, count = g.Count() }).ToList()
            };
        }
    }
}
