using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ZoomActiveView
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (view == null) return new { error = "No view" };

            var openViews = uidoc.GetOpenUIViews();
            foreach (var uiv in openViews)
            {
                if (uiv.ViewId == view.Id)
                {
                    uiv.ZoomToFit();
                }
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                viewName = view.Name
            };
        }
    }
}
