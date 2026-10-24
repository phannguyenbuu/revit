
using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorTemplate
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Door.rft";
            var famDoc = app.NewFamilyDocument(templatePath);
            if (famDoc == null) return new { error = "Cannot open template" };

            var elements = new FilteredElementCollector(famDoc)
                .WhereElementIsNotElementType()
                .Select(e => new { id = e.Id.Value, type = e.GetType().Name, name = e.Name, cat = e.Category?.Name })
                .ToList();

            var subcats = famDoc.OwnerFamily.FamilyCategory?.SubCategories?.Cast<Category>()
                .Select(c => c.Name)
                .ToList();

            famDoc.Close(false);

            return new { elements, subcats };
        }
    }
}
