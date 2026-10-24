using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairsMethods
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var stairsMethods = typeof(Stairs).GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance)
                .Select(m => m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")")
                .Distinct()
                .OrderBy(s => s)
                .ToList();

            var runMethods = typeof(StairsRun).GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance)
                .Select(m => m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")")
                .Distinct()
                .OrderBy(s => s)
                .ToList();

            var landingMethods = typeof(StairsLanding).GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance)
                .Select(m => m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")")
                .Distinct()
                .OrderBy(s => s)
                .ToList();

            var scopeMethods = typeof(StairsEditScope).GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance)
                .Select(m => m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")")
                .Distinct()
                .OrderBy(s => s)
                .ToList();

            return new { stairsMethods, runMethods, landingMethods, scopeMethods };
        }
    }
}
