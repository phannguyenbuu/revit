using System;
using System.Reflection;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestHideEdges
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as View3D;
            if (doc == null || view == null) return new { error = "No active 3D view" };

            var enumNames = Enum.GetNames(typeof(DisplayStyle));

            using (var tx = new Transaction(doc, "Set Display Style FlatColors"))
            {
                tx.Start();
                view.DisplayStyle = DisplayStyle.FlatColors;
                var vdm = view.GetViewDisplayModel();
                vdm.SmoothEdges = true;
                view.SetViewDisplayModel(vdm);
                tx.Commit();
            }

            try { uiapp.ActiveUIDocument?.RefreshActiveView(); } catch { }

            return new
            {
                currentStyle = view.DisplayStyle.ToString(),
                availableStyles = enumNames
            };
        }
    }
}
