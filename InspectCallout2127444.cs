using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCallout2127444
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var v = doc.GetElement(new ElementId(2127444L)) as View;
            if (v == null) return new { error = "View not found" };

            var parentParam = v.get_Parameter(BuiltInParameter.SECTION_PARENT_VIEW_NAME)?.AsString();
            
            return new {
                id = v.Id.Value,
                name = v.Name,
                viewType = v.ViewType.ToString(),
                vftId = v.GetTypeId().Value,
                vftName = doc.GetElement(v.GetTypeId())?.Name,
                isCallout = v.IsCallout,
                scale = v.Scale,
                parent = parentParam,
                cropBoxMin = v.CropBox.Min.ToString(),
                cropBoxMax = v.CropBox.Max.ToString()
            };
        }
    }
}
