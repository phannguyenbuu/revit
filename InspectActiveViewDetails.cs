using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveViewDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (view == null) return new { error = "No view" };

            var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);

            bool floorCatHidden = floorCat != null && view.CanCategoryBeHidden(floorCat.Id) && view.GetCategoryHidden(floorCat.Id);
            bool gridCatHidden = gridCat != null && view.CanCategoryBeHidden(gridCat.Id) && view.GetCategoryHidden(gridCat.Id);

            var v3d = view as View3D;
            var levelsShowingGrids = v3d != null ? v3d.GetLevelsThatShowGrids().Select(id => id.Value).ToList() : null;

            var floors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .ToElementIds()
                .Select(id => id.Value)
                .ToList();

            var gridsInView = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Grids)
                .WhereElementIsNotElementType()
                .ToElementIds()
                .Select(id => id.Value)
                .ToList();

            return new
            {
                viewId = view.Id.Value,
                viewName = view.Name,
                viewType = view.ViewType.ToString(),
                floorCategoryHidden = floorCatHidden,
                gridCategoryHidden = gridCatHidden,
                floorsVisibleInViewCount = floors.Count,
                gridsVisibleInViewCount = gridsInView.Count,
                levelsShowingGrids = levelsShowingGrids
            };
        }
    }
}
