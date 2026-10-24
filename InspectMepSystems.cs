using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class InspectMepSystems
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var links = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkInstance))
                .Cast<RevitLinkInstance>()
                .ToList();

            var result = new Dictionary<string, object>();

            // Inspect host doc pipes
            var hostPipes = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_PipeCurves)
                .WhereElementIsNotElementType()
                .Take(200)
                .ToList();
            var hostPipeSystems = hostPipes
                .Select(p => p.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM)?.AsString() ?? "")
                .Distinct()
                .ToList();
            result["hostPipeSystems"] = hostPipeSystems;

            foreach (var link in links)
            {
                var lDoc = link.GetLinkDocument();
                if (lDoc == null) continue;

                var lName = link.Name;
                var info = new Dictionary<string, object>();

                // Ducts
                var ducts = new FilteredElementCollector(lDoc)
                    .OfCategory(BuiltInCategory.OST_DuctCurves)
                    .WhereElementIsNotElementType()
                    .Take(500)
                    .ToList();
                var ductSystems = ducts
                    .Select(d => $"{d.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM)?.AsString()} [{d.get_Parameter(BuiltInParameter.RBS_SYSTEM_CLASSIFICATION_PARAM)?.AsString()}]")
                    .Distinct()
                    .ToList();
                info["ductSystems"] = ductSystems;

                // Cable trays
                var trays = new FilteredElementCollector(lDoc)
                    .OfCategory(BuiltInCategory.OST_CableTray)
                    .WhereElementIsNotElementType()
                    .Take(200)
                    .ToList();
                var trayNames = trays
                    .Select(t => t.Name)
                    .Distinct()
                    .ToList();
                info["cableTrayTypes"] = trayNames;

                // Equipment
                var equip = new FilteredElementCollector(lDoc)
                    .OfCategory(BuiltInCategory.OST_ElectricalEquipment)
                    .WhereElementIsNotElementType()
                    .Take(100)
                    .ToList();
                var equipNames = equip
                    .Select(e => e.Name)
                    .Distinct()
                    .ToList();
                info["elecEquipment"] = equipNames;

                result[lName] = info;
            }

            return result;
        }
    }
}
