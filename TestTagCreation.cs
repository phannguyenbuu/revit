using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestTagCreation
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var door = doc.GetElement(new ElementId(2360900L)) as FamilyInstance;
            if (door == null) return new { error = "Door 2360900 not found" };

            var doorTagSym = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(BuiltInCategory.OST_DoorTags)
                .Cast<FamilySymbol>()
                .FirstOrDefault();

            var winTagSym = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(BuiltInCategory.OST_WindowTags)
                .Cast<FamilySymbol>()
                .FirstOrDefault(s => s.FamilyName == "KÝ HIỆU CỬA SỔ")
                ?? new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(BuiltInCategory.OST_WindowTags)
                .Cast<FamilySymbol>()
                .FirstOrDefault();

            string doorTagText = "";
            string winTagText = "";

            var win = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            using (var tx = new Transaction(doc, "Test Tag Creation"))
            {
                tx.Start();

                if (doorTagSym != null)
                {
                    var pt = (door.Location as LocationPoint).Point;
                    var tag = IndependentTag.Create(doc, view.Id, new Reference(door), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, pt);
                    tag.ChangeTypeId(doorTagSym.Id);
                    doorTagText = tag.TagText;
                }

                if (winTagSym != null && win != null)
                {
                    var pt = (win.Location as LocationPoint).Point;
                    var tag = IndependentTag.Create(doc, view.Id, new Reference(win), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, pt);
                    tag.ChangeTypeId(winTagSym.Id);
                    winTagText = tag.TagText;
                }

                tx.RollBack();
            }

            return new
            {
                doorTagSymName = doorTagSym?.FamilyName + " : " + doorTagSym?.Name,
                doorTagText = doorTagText,
                doorMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                doorTypeMark = door.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                winTagSymName = winTagSym?.FamilyName + " : " + winTagSym?.Name,
                winTagText = winTagText,
                winMark = win?.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                winTypeMark = win?.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                winName = win?.Name
            };
        }
    }
}
