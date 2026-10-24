using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFillPatternApi
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var fpType = typeof(FillPattern);
            var fpeType = typeof(FillPatternElement);

            var fpConstructors = fpType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
                .Select(c => c.ToString())
                .ToList();

            var fpeMethods = fpeType.GetMethods(BindingFlags.Public | BindingFlags.Static)
                .Select(m => m.ToString())
                .ToList();

            var fpMethods = fpType.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static)
                .Select(m => m.ToString())
                .ToList();

            return new
            {
                fpConstructors,
                fpeMethods,
                fpMethods
            };
        }
    }
}
