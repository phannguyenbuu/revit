using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRConcrete
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string rfaPath = @"C:\ProgramData\Autodesk\Revit Steel Connections 2025\en-UK\Family Templates\AS_EXT_COLUMN_RConcrete.rfa";
            var famDoc = app.OpenDocumentFile(rfaPath);
            if (famDoc == null) return new { error = "Cannot open RFA" };

            var extrusions = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Extrusion))
                .Cast<Extrusion>()
                .ToList();

            var famMgr = famDoc.FamilyManager;
            var pars = famMgr.Parameters.Cast<FamilyParameter>().Select(p => p.Definition.Name).ToList();
            var types = famMgr.Types.Cast<FamilyType>().Select(t => t.Name).ToList();

            famDoc.Close(false);

            return new
            {
                extrusionsCount = extrusions.Count,
                parameters = pars,
                types = types
            };
        }
    }
}
