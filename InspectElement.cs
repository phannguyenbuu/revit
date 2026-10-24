using System;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectElement
    {
        public static object Run(UIApplication uiapp, dynamic args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var el = doc?.GetElement(new ElementId(4795191));
            return new
            {
                id = el?.Id.Value,
                type = el?.GetType().Name,
                category = el?.Category?.Name,
                name = el?.Name,
                isGroup = el is Group,
                groupId = (el is Group g) ? g.GroupType?.Name : null
            };
        }
    }
}
