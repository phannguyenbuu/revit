using System;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class OpenLongTienModel
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string path = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX\Mau_40_CBS_Long_Tien.rvt";
            try
            {
                var uidoc = app.OpenAndActivateDocument(path);
                return new { success = true, title = uidoc?.Document?.Title };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.ToString() };
            }
        }
    }
}
