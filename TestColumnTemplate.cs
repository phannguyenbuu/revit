using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestColumnTemplate
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Structural Column.rft";
            if (!File.Exists(templatePath))
            {
                templatePath = @"C:\ProgramData\Autodesk\RVT 2027\Family Templates\English\Metric Structural Column.rft";
            }

            if (!File.Exists(templatePath))
            {
                return new { error = "Template not found" };
            }

            Document famDoc = app.NewFamilyDocument(templatePath);
            if (famDoc == null) return new { error = "Failed to create family document" };

            var famMgr = famDoc.FamilyManager;
            var types = famMgr.Types.Cast<FamilyType>().Select(t => t.Name).ToList();
            var pars = famMgr.Parameters.Cast<FamilyParameter>().Select(p => p.Definition.Name).ToList();

            famDoc.Close(false);

            return new
            {
                success = true,
                template = templatePath,
                existingTypes = types,
                parameters = pars
            };
        }
    }
}
