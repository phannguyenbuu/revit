using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ViewDisplayOptimizer
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as View3D;
            if (doc == null || view == null) return new { error = "Not a 3D view" };

            using (var tx = new Transaction(doc, "Optimize View Display"))
            {
                tx.Start();
                
                var pShowEdges = view.get_Parameter(BuiltInParameter.VIEW_GRAPHIC_DISPLAY_SHOW_EDGES);
                if (pShowEdges != null && !pShowEdges.IsReadOnly)
                {
                    pShowEdges.Set(0); // Turn off mesh edges for ultra clean signage display
                }

                var pSmooth = view.get_Parameter(BuiltInParameter.VIEW_GRAPHIC_DISPLAY_SHOW_ANTI_ALIASING);
                if (pSmooth != null && !pSmooth.IsReadOnly)
                {
                    pSmooth.Set(1); // Enable anti-aliasing
                }

                view.DisplayStyle = DisplayStyle.Shading;

                tx.Commit();
            }

            try { uiapp.ActiveUIDocument?.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                displayStyle = view.DisplayStyle.ToString(),
                edges = view.get_Parameter(BuiltInParameter.VIEW_GRAPHIC_DISPLAY_SHOW_EDGES)?.AsInteger()
            };
        }
    }
}
