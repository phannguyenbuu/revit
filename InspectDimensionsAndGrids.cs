using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDimensionsAndGrids
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var doc = uiapp.ActiveUIDocument?.Document;
                var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No view" };

                // 1. Check DimensionTypes
                var dimTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(DimensionType))
                    .Cast<DimensionType>()
                    .Select(dt => new {
                        id = dt.Id.Value,
                        name = dt.Name,
                        dimStyle = dt.StyleType.ToString()
                    })
                    .ToList();

                // 2. Check existing Dimensions in view
                var existingDims = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .Select(d => new {
                        id = d.Id.Value,
                        type = d.DimensionType?.Name,
                        val = d.Value * 304.8
                    })
                    .ToList();

                // 3. Check Grids in document
                var grids = new FilteredElementCollector(doc)
                    .OfClass(typeof(Grid))
                    .Cast<Grid>()
                    .Select(g => {
                        var curve = g.Curve;
                        var p1 = curve.GetEndPoint(0) * 304.8;
                        var p2 = curve.GetEndPoint(1) * 304.8;
                        return new {
                            id = g.Id.Value,
                            name = g.Name,
                            p1 = new { x = p1.X, y = p1.Y },
                            p2 = new { x = p2.X, y = p2.Y }
                        };
                    })
                    .ToList();

                // 4. Check category OST_Dimensions visibility in View/Template
                var vt = view.ViewTemplateId != ElementId.InvalidElementId 
                    ? doc.GetElement(view.ViewTemplateId) as ViewPlan 
                    : null;
                var targetView = vt ?? view;

                var dimCat = Category.GetCategory(doc, BuiltInCategory.OST_Dimensions);
                bool dimHidden = dimCat != null && targetView.CanCategoryBeHidden(dimCat.Id)
                    ? targetView.GetCategoryHidden(dimCat.Id) : false;

                return new
                {
                    dimTypes = dimTypes,
                    existingDimsCount = existingDims.Count,
                    existingDims = existingDims.Take(10).ToList(),
                    grids = grids,
                    dimCategoryHidden = dimHidden
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
