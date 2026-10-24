using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestOpenIfc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string ifcPath = args.GetProperty("ifcPath").GetString()!;
            var app = uiapp.Application;
            try
            {
                var doc = app.OpenIFCDocument(ifcPath);
                var els = new FilteredElementCollector(doc)
                    .WhereElementIsNotElementType()
                    .Select(e => new
                    {
                        id = e.Id.Value,
                        name = e.Name,
                        cat = e.Category?.Name,
                        type = e.GetType().Name
                    })
                    .ToList();
                int count = els.Count;
                doc.Close(false);
                return new { success = true, elementCount = count, sample = els.Take(10).ToList() };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.ToString() };
            }
        }
    }
}
