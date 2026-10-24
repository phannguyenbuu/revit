using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRConcreteCat
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string rfaPath = @"C:\ProgramData\Autodesk\Revit Steel Connections 2025\en-UK\Family Templates\AS_EXT_COLUMN_RConcrete.rfa";
            var famDoc = app.OpenDocumentFile(rfaPath);
            if (famDoc == null) return new { error = "Cannot open RFA" };

            var cat = famDoc.OwnerFamily?.FamilyCategory?.Name;
            var bic = famDoc.OwnerFamily?.FamilyCategory?.BuiltInCategory.ToString();

            famDoc.Close(false);

            return new
            {
                categoryName = cat,
                builtInCategory = bic
            };
        }
    }
}
