using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SwitchTo3D
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var view3D = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            if (view3D != null)
            {
                using (var tx = new Transaction(doc, "Set 3D View Display"))
                {
                    tx.Start();
                    view3D.DisplayStyle = DisplayStyle.FlatColors;
                    try
                    {
                        var vdm = view3D.GetViewDisplayModel();
                        vdm.SmoothEdges = true;
                        view3D.SetViewDisplayModel(vdm);
                    }
                    catch { }
                    tx.Commit();
                }

                try
                {
                    uiapp.ActiveUIDocument!.ActiveView = view3D;
                    uiapp.ActiveUIDocument.RefreshActiveView();
                }
                catch { }

                return new { success = true, view = view3D.Name };
            }

            return new { error = "No 3D view found" };
        }
    }
}
