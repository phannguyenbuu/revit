using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class EnsureD1Mark
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var elem = doc.GetElement(new ElementId(2364731L));
            if (elem == null) return new { error = "Door not found" };

            string oldMark = elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString() ?? "";
            using (var tx = new Transaction(doc, "Ensure D1 Mark"))
            {
                tx.Start();
                elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("D1");
                tx.Commit();
            }

            return new
            {
                doorId = elem.Id.Value,
                oldMark = oldMark,
                newMark = elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString()
            };
        }
    }
}
