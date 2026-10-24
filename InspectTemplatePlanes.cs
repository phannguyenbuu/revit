using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTemplatePlanes
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Structural Column.rft";
            var famDoc = app.OpenDocumentFile(templatePath);
            if (famDoc == null) return new { error = "Cannot open template" };

            var levels = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .Select(l => new { id = l.Id.Value, name = l.Name, elevation = l.Elevation })
                .ToList();

            var refPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ReferencePlane))
                .Cast<ReferencePlane>()
                .Select(rp => new { id = rp.Id.Value, name = rp.Name })
                .ToList();

            var sketchPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(SketchPlane))
                .Cast<SketchPlane>()
                .Select(sp => new { id = sp.Id.Value, name = sp.Name })
                .ToList();

            famDoc.Close(false);

            return new
            {
                levels = levels,
                refPlanes = refPlanes,
                sketchPlanes = sketchPlanes
            };
        }
    }
}
