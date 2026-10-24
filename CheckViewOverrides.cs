
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckViewOverrides
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = doc?.ActiveView;
            if (view == null) return new { error = "No view" };

            var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            var doorCat = Category.GetCategory(doc, BuiltInCategory.OST_Doors);
            var winCat = Category.GetCategory(doc, BuiltInCategory.OST_Windows);
            var doorTagCat = Category.GetCategory(doc, BuiltInCategory.OST_DoorTags);
            var winTagCat = Category.GetCategory(doc, BuiltInCategory.OST_WindowTags);

            var ovFloor = view.GetCategoryOverrides(floorCat.Id);
            var ovDoorTag = view.GetCategoryOverrides(doorTagCat.Id);
            var ovWinTag = view.GetCategoryOverrides(winTagCat.Id);

            return new {
                floorHidden = view.GetCategoryHidden(floorCat.Id),
                doorTagHidden = view.GetCategoryHidden(doorTagCat.Id),
                winTagHidden = view.GetCategoryHidden(winTagCat.Id),
                floorHalftone = ovFloor.Halftone,
                floorTransparency = ovFloor.Transparency,
                floorSurfacePatVisible = ovFloor.IsSurfaceForegroundPatternVisible,
                floorSurfacePatId = ovFloor.SurfaceForegroundPatternId.Value
            };
        }
    }
}
