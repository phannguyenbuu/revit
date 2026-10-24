using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class MoveD1TagExact
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var tag = doc.GetElement(new ElementId(2367834L)) as IndependentTag;
            if (tag == null) return new { error = "Tag not found" };

            using (var tx = new Transaction(doc, "Move D1 Tag Exact"))
            {
                tx.Start();
                tag.TagHeadPosition = new XYZ(-0.6968 * 3.28084, 6.6799 * 3.28084, 0);
                tx.Commit();
            }

            return new { success = true, pos = tag.TagHeadPosition.ToString() };
        }
    }
}
