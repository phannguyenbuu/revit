using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckWallVisibility
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;
            var wall = doc.GetElement(new ElementId(2362083L));
            if (wall == null) return new { error = "Wall not found" };
            return new
            {
                wallId = wall.Id.Value,
                viewName = view.Name,
                isHidden = wall.IsHidden(view),
                canBeHidden = wall.CanBeHidden(view)
            };
        }
    }
}
