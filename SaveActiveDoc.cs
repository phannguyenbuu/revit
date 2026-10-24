using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SaveActiveDoc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            try
            {
                var saveOptions = new SaveOptions();
                doc.Save(saveOptions);
                return new { success = true, path = doc.PathName };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message, stackTrace = ex.StackTrace };
            }
        }
    }
}
