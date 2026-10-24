using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyGeometry
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Concrete-Rectangular-Column.rfa";
            var famDoc = app.OpenDocumentFile(rfaPath);
            if (famDoc == null) return new { error = "Cannot open RFA" };

            var extrusions = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Extrusion))
                .Cast<Extrusion>()
                .ToList();

            var forms = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .ToList();

            var refPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ReferencePlane))
                .Cast<ReferencePlane>()
                .Select(rp => rp.Name)
                .ToList();

            famDoc.Close(false);

            return new
            {
                extrusionsCount = extrusions.Count,
                formsCount = forms.Count,
                refPlanes = refPlanes
            };
        }
    }
}
