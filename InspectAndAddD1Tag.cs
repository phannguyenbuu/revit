using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAndAddD1Tag
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            var d1 = doc.GetElement(new ElementId(2364731L)) as FamilyInstance;
            if (d1 == null) return new { error = "D1 not found" };

            // Find door tag symbol from any existing door tag
            var anyDoorTag = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .FirstOrDefault(t => t.Category?.Id?.IntegerValue == (int)BuiltInCategory.OST_DoorTags);

            ElementId tagTypeId = anyDoorTag?.GetTypeId();
            if (tagTypeId == null || tagTypeId == ElementId.InvalidElementId)
            {
                var tagSymbol = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilySymbol))
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(s => s.Category?.Id?.IntegerValue == (int)BuiltInCategory.OST_DoorTags);
                tagTypeId = tagSymbol?.Id;
            }

            if (tagTypeId == null) return new { error = "No door tag family found" };

            using (var tx = new Transaction(doc, "Tag Door D1"))
            {
                tx.Start();
                // Place tag at CAD D1 circle location: X = -0.400m, Y = 6.600m
                var tagPos = new XYZ(-0.400 * 3.28084, 6.600 * 3.28084, 0);
                var tag = IndependentTag.Create(
                    doc,
                    view.Id,
                    new Reference(d1),
                    false,
                    TagMode.TM_ADDBY_CATEGORY,
                    TagOrientation.Horizontal,
                    tagPos
                );
                if (tagTypeId != null && tagTypeId != ElementId.InvalidElementId)
                {
                    tag.ChangeTypeId(tagTypeId);
                }
                tag.TagHeadPosition = tagPos;
                tx.Commit();

                return new { status = "created", tagId = tag.Id.Value, text = tag.TagText };
            }
        }
    }
}
