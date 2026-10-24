using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectPlanElementsAtBay
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // Bay bounding box: X[0.0, 1.5], Y[11.5, 13.5], Z[0.0, 4.0]
                Outline outline = new Outline(
                    new XYZ(0.0 * M2FT, 11.5 * M2FT, -1.0 * M2FT),
                    new XYZ(1.5 * M2FT, 13.5 * M2FT, 4.0 * M2FT)
                );
                var filter = new BoundingBoxIntersectsFilter(outline);

                var elements = new FilteredElementCollector(doc)
                    .WherePasses(filter)
                    .WhereElementIsNotElementType()
                    .Select(e => new
                    {
                        id = e.Id.Value,
                        name = e.Name,
                        category = e.Category?.Name ?? "None",
                        type = e.GetType().Name
                    })
                    .ToList();

                // Check active view settings (Detail Level, Model Display, Graphic Display Options)
                var activeView = uidoc.ActiveView;
                string detailLevel = activeView.DetailLevel.ToString();
                string displayStyle = activeView.DisplayStyle.ToString();

                // Also check if Window_K2_Stack has visibility settings or subcategories
                var stackInst = doc.GetElement(new ElementId(2377860)) as FamilyInstance;
                string stackFamName = stackInst?.Symbol.FamilyName ?? "null";

                return new
                {
                    viewName = activeView.Name,
                    detailLevel,
                    displayStyle,
                    elements,
                    stackInstId = stackInst?.Id.Value
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
