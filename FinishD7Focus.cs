using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FinishD7Focus
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            var d1Id = new ElementId(2360900L);
            var d2Id = new ElementId(2360910L);

            // Select both doors again
            uidoc.Selection.SetElementIds(new List<ElementId> { d1Id, d2Id });

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
            if (uiview != null)
            {
                // Zoom to encompass both doors (X: 3000 to 35000, Y: 4000 to 11000)
                XYZ p1 = new XYZ(2000.0 / 304.8, 2000.0 / 304.8, 0);
                XYZ p2 = new XYZ(36000.0 / 304.8, 12000.0 / 304.8, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }

            return new { success = true };
        }
    }
}
