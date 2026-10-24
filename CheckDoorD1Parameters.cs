using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDoorD1Parameters
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var d1 = doc.GetElement(new ElementId(2364731L)) as FamilyInstance;
            if (d1 == null) return new { error = "D1 not found" };

            using (var tx = new Transaction(doc, "Set D1 Marks"))
            {
                tx.Start();
                d1.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("D1");
                d1.Symbol?.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.Set("D1");
                tx.Commit();
            }

            var tag = doc.GetElement(new ElementId(2367834L)) as IndependentTag;

            return new
            {
                mark = d1.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                typeMark = d1.Symbol?.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                tagText = tag?.TagText
            };
        }
    }
}
