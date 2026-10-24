using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTextNoteCreateApi
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var tnType = typeof(TextNote);
            var methods = tnType.GetMethods(BindingFlags.Public | BindingFlags.Static)
                .Where(m => m.Name == "Create")
                .Select(m => m.ToString())
                .ToList();

            return new { methods };
        }
    }
}
