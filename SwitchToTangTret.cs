using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SwitchToTangTret
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var view = doc.GetElement(new ElementId(715156)) as View;
            if (view == null)
            {
                view = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name == "TẦNG TRỆT");
            }

            if (view == null) return new { error = "TẦNG TRỆT view not found" };

            try
            {
                uidoc.ActiveView = view;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == view.Id);
                uiview?.ZoomToFit();

                return new
                {
                    success = true,
                    switchedTo = view.Name,
                    id = view.Id.Value
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.Message };
            }
        }
    }
}
