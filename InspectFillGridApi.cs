using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFillGridApi
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var fgType = typeof(FillGrid);
            var ctors = fgType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
                .Select(c => c.ToString())
                .ToList();
            var props = fgType.GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .Select(p => p.Name + " (" + p.PropertyType.Name + ")")
                .ToList();
            var methods = fgType.GetMethods(BindingFlags.Public | BindingFlags.Instance)
                .Select(m => m.ToString())
                .ToList();

            return new { ctors, props, methods };
        }
    }
}
