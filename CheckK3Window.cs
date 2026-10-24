using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckK3Window
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var win = doc.GetElement(new ElementId(2360996L)) as FamilyInstance;
            var tag = doc.GetElement(new ElementId(2407751L)) as IndependentTag;
            var tagSym = doc.GetElement(tag.GetTypeId()) as FamilySymbol;

            var mark = win.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString();
            var typeMark = win.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString();

            return new {
                winId = win.Id.Value,
                mark,
                typeMark,
                tagType = tagSym?.Name,
                tagFamily = tagSym?.FamilyName,
                tagText = tag.TagText
            };
        }
    }
}