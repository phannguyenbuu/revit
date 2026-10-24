using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class InspectMepElements
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var bics = new Dictionary<string, BuiltInCategory>
            {
                { "Pipes", BuiltInCategory.OST_PipeCurves },
                { "PipeFittings", BuiltInCategory.OST_PipeFitting },
                { "Sprinklers", BuiltInCategory.OST_Sprinklers },
                { "Ducts", BuiltInCategory.OST_DuctCurves },
                { "DuctFittings", BuiltInCategory.OST_DuctFitting },
                { "DuctTerminals", BuiltInCategory.OST_DuctTerminal },
                { "CableTrays", BuiltInCategory.OST_CableTray },
                { "CableTrayFittings", BuiltInCategory.OST_CableTrayFitting },
                { "Conduits", BuiltInCategory.OST_Conduit },
                { "ConduitFittings", BuiltInCategory.OST_ConduitFitting },
                { "FireAlarmDevices", BuiltInCategory.OST_FireAlarmDevices },
                { "ElectricalEquipment", BuiltInCategory.OST_ElectricalEquipment },
                { "MechanicalEquipment", BuiltInCategory.OST_MechanicalEquipment },
                { "GenericModels", BuiltInCategory.OST_GenericModel }
            };

            var hostCounts = new Dictionary<string, int>();
            foreach (var kvp in bics)
            {
                int count = new FilteredElementCollector(doc)
                    .OfCategory(kvp.Value)
                    .WhereElementIsNotElementType()
                    .GetElementCount();
                if (count > 0) hostCounts[kvp.Key] = count;
            }

            var links = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkInstance))
                .Cast<RevitLinkInstance>()
                .ToList();

            var linkData = new List<object>();
            foreach (var l in links)
            {
                var lDoc = l.GetLinkDocument();
                var counts = new Dictionary<string, int>();
                if (lDoc != null)
                {
                    foreach (var kvp in bics)
                    {
                        int count = new FilteredElementCollector(lDoc)
                            .OfCategory(kvp.Value)
                            .WhereElementIsNotElementType()
                            .GetElementCount();
                        if (count > 0) counts[kvp.Key] = count;
                    }
                }

                linkData.Add(new
                {
                    name = l.Name,
                    isLoaded = lDoc != null,
                    counts
                });
            }

            return new
            {
                host = new
                {
                    title = doc.Title,
                    counts = hostCounts
                },
                links = linkData
            };
        }
    }
}
