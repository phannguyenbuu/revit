using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectOpenViews
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var openViews = uidoc.GetOpenUIViews().Select(uv =>
                {
                    var v = doc.GetElement(uv.ViewId) as View;
                    return new
                    {
                        viewId = uv.ViewId.Value,
                        name = v?.Name,
                        type = v?.ViewType.ToString(),
                        isActive = uv.ViewId == uidoc.ActiveView.Id
                    };
                }).ToList();

                return new
                {
                    activeViewId = uidoc.ActiveView.Id.Value,
                    activeViewName = uidoc.ActiveView.Name,
                    activeViewType = uidoc.ActiveView.ViewType.ToString(),
                    openViews
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
