using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectStairsParams
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var stair = doc.GetElement(new ElementId(2368346)) as Stairs;
            if (stair == null)
            {
                stair = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Stairs)
                    .WhereElementIsNotElementType()
                    .Cast<Stairs>()
                    .FirstOrDefault();
            }

            if (stair == null) return new { error = "No stair found" };

            var paramList = new List<object>();
            foreach (Parameter p in stair.Parameters)
            {
                if (p.Definition == null) continue;
                string val = "";
                switch (p.StorageType)
                {
                    case StorageType.Double:
                        val = p.AsDouble().ToString();
                        break;
                    case StorageType.Integer:
                        val = p.AsInteger().ToString();
                        break;
                    case StorageType.String:
                        val = p.AsString();
                        break;
                    case StorageType.ElementId:
                        var eid = p.AsElementId();
                        var elem = eid != null && eid != ElementId.InvalidElementId ? doc.GetElement(eid) : null;
                        val = $"Id={eid?.Value}, Name={elem?.Name}";
                        break;
                }
                paramList.Add(new
                {
                    name = p.Definition.Name,
                    builtIn = p.Definition is InternalDefinition id ? id.BuiltInParameter.ToString() : "N/A",
                    val
                });
            }

            return new { id = stair.Id.Value, name = stair.Name, paramList };
        }
    }
}
