using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveViewState
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var selIds = uidoc.Selection.GetElementIds().Select(id => id.Value).ToList();

                var openViews = uidoc.GetOpenUIViews().Select(uv =>
                {
                    var v = doc.GetElement(uv.ViewId) as View;
                    return new
                    {
                        viewId = uv.ViewId.Value,
                        viewName = v?.Name,
                        viewType = v?.ViewType.ToString()
                    };
                }).ToList();

                var activeView = uidoc.ActiveView;

                return new
                {
                    docTitle = doc.Title,
                    activeViewId = activeView?.Id.Value,
                    activeViewName = activeView?.Name,
                    activeViewType = activeView?.ViewType.ToString(),
                    selectionCount = selIds.Count,
                    selectionIds = selIds,
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
