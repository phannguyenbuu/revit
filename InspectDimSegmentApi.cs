using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDimSegmentApi
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var props = typeof(DimensionSegment).GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .Select(p => $"{p.PropertyType.Name} {p.Name}")
                .ToList();

            var methods = typeof(DimensionSegment).GetMethods(BindingFlags.Public | BindingFlags.Instance)
                .Where(m => !m.IsSpecialName)
                .Select(m => $"{m.ReturnType.Name} {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name))})")
                .ToList();

            return new { props, methods };
        }
    }
}
