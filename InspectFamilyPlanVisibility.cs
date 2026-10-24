using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyPlanVisibility
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var famDoc = uiapp.Application.OpenDocumentFile(@"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa");
            if (famDoc == null) return new { error = "Cannot open family doc" };

            var importInst = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .FirstOrDefault();

            var lines = new FilteredElementCollector(famDoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => new {
                    id = c.Id.Value,
                    type = c.GetType().Name,
                    subcat = c.LineStyle?.Name
                })
                .ToList();

            var lineCat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines);
            var lineStyles = lineCat?.SubCategories
                .Cast<Category>()
                .Select(c => c.Name)
                .ToList();

            famDoc.Close(false);

            return new {
                importInstId = importInst?.Id.Value,
                lineCount = lines.Count,
                lineStyles
            };
        }
    }
}
