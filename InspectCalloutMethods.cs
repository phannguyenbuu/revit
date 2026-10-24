using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCalloutMethods
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sectionMethods = typeof(ViewSection).GetMethods(BindingFlags.Public | BindingFlags.Static)
                .Where(m => m.Name.Contains("Callout"))
                .Select(m => new {
                    declaringType = "ViewSection",
                    name = m.Name,
                    parameters = m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name).ToList(),
                    returnType = m.ReturnType.Name
                })
                .ToList();

            var viewMethods = typeof(View).GetMethods(BindingFlags.Public | BindingFlags.Static)
                .Where(m => m.Name.Contains("Callout"))
                .Select(m => new {
                    declaringType = "View",
                    name = m.Name,
                    parameters = m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name).ToList(),
                    returnType = m.ReturnType.Name
                })
                .ToList();

            var vftCollector = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .Select(vft => new {
                    id = vft.Id.Value,
                    name = vft.Name,
                    viewFamily = vft.ViewFamily.ToString()
                })
                .ToList();

            return new {
                sectionMethods = sectionMethods,
                viewMethods = viewMethods,
                viewFamilyTypes = vftCollector
            };
        }
    }
}
