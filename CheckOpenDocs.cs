using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckOpenDocs
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            var docs = app.Documents.Cast<Document>()
                .Select(d => new
                {
                    title = d.Title,
                    path = d.PathName,
                    isFamily = d.IsFamilyDocument,
                    isActive = d.Equals(uiapp.ActiveUIDocument?.Document)
                })
                .ToList();

            return new { docs };
        }
    }
}
