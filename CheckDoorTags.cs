using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDoorTags
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            var tags = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .Where(t => t.Category?.Id?.IntegerValue == (int)BuiltInCategory.OST_DoorTags)
                .Select(t => new
                {
                    id = t.Id.Value,
                    tagText = t.TagText,
                    taggedLocalElem = t.GetTaggedLocalElement()?.Id?.Value
                })
                .ToList();

            return new { count = tags.Count, tags = tags };
        }
    }
}
