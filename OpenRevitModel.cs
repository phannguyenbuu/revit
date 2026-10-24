using System;
using System.IO;
using System.Text.Json;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class OpenRevitModel
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                string path = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\Mau_40_CBS_Long_Tien.rvt";
                if (!File.Exists(path))
                {
                    return new { error = "File not found: " + path };
                }

                var uidoc = uiapp.OpenAndActivateDocument(path);
                return new {
                    success = true,
                    docTitle = uidoc.Document?.Title,
                    pathName = uidoc.Document?.PathName
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
