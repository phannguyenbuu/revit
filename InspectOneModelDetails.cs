using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectOneModelDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string filePath = null;
            if (args.TryGetProperty("filePath", out var fp)) filePath = fp.GetString();
            else if (args.TryGetProperty("arguments", out var a) && a.TryGetProperty("filePath", out var fp2)) filePath = fp2.GetString();

            if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
            {
                return new { error = "File not found: " + filePath };
            }

            var fi = new FileInfo(filePath);
            var openOpt = new OpenOptions
            {
                DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
            };

            EventHandler<Autodesk.Revit.UI.Events.DialogBoxShowingEventArgs> dialogHandler = (s, e) =>
            {
                e.OverrideResult(1); // 1 = OK/Yes
            };
            uiapp.DialogBoxShowing += dialogHandler;

            Document doc = null;
            try
            {
                var modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filePath);
                doc = app.OpenDocumentFile(modelPath, openOpt);

                // Collect categories and counts
                var categoriesToCheck = new Dictionary<string, BuiltInCategory>
                {
                    { "Pipes", BuiltInCategory.OST_PipeCurves },
                    { "PipeFittings", BuiltInCategory.OST_PipeFitting },
                    { "PipeAccessories", BuiltInCategory.OST_PipeAccessory },
                    { "Sprinklers", BuiltInCategory.OST_Sprinklers },
                    { "FireAlarmDevices", BuiltInCategory.OST_FireAlarmDevices },
                    { "PlumbingFixtures", BuiltInCategory.OST_PlumbingFixtures },
                    { "MechanicalEquipment", BuiltInCategory.OST_MechanicalEquipment },
                    { "Ducts", BuiltInCategory.OST_DuctCurves },
                    { "DuctFittings", BuiltInCategory.OST_DuctFitting },
                    { "DuctAccessories", BuiltInCategory.OST_DuctAccessory },
                    { "CableTrays", BuiltInCategory.OST_CableTray },
                    { "Conduits", BuiltInCategory.OST_Conduit },
                    { "Walls", BuiltInCategory.OST_Walls },
                    { "StructuralColumns", BuiltInCategory.OST_StructuralColumns },
                    { "Doors", BuiltInCategory.OST_Doors },
                    { "Windows", BuiltInCategory.OST_Windows },
                    { "Floors", BuiltInCategory.OST_Floors },
                    { "Roofs", BuiltInCategory.OST_Roofs }
                };

                var catCounts = new Dictionary<string, int>();
                foreach (var kvp in categoriesToCheck)
                {
                    int count = new FilteredElementCollector(doc)
                        .OfCategory(kvp.Value)
                        .WhereElementIsNotElementType()
                        .GetElementCount();
                    if (count > 0)
                    {
                        catCounts[kvp.Key] = count;
                    }
                }

                // Piping system classifications / types
                var pipingSystems = new FilteredElementCollector(doc)
                    .OfClass(typeof(MEPSystem))
                    .Cast<MEPSystem>()
                    .Select(s => new { s.Name, SystemType = s.GetType().Name })
                    .Take(20)
                    .ToList();

                var pipingSystemTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(PipingSystemType))
                    .Cast<PipingSystemType>()
                    .Select(st => new { st.Name, Classification = st.SystemClassification.ToString() })
                    .ToList();

                // Check views with Fire / PCCC / FFS
                var pcccViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(View))
                    .Cast<View>()
                    .Where(v => !v.IsTemplate && (
                        v.Name.IndexOf("PCCC", StringComparison.OrdinalIgnoreCase) >= 0 ||
                        v.Name.IndexOf("CHỮA CHÁY", StringComparison.OrdinalIgnoreCase) >= 0 ||
                        v.Name.IndexOf("BÁO CHÁY", StringComparison.OrdinalIgnoreCase) >= 0 ||
                        v.Name.IndexOf("FFS", StringComparison.OrdinalIgnoreCase) >= 0 ||
                        v.Name.IndexOf("FIRE", StringComparison.OrdinalIgnoreCase) >= 0 ||
                        v.Name.IndexOf("FP", StringComparison.OrdinalIgnoreCase) >= 0
                    ))
                    .Select(v => new { v.Name, ViewType = v.ViewType.ToString() })
                    .Take(30)
                    .ToList();

                // Sheets
                var sheets = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSheet))
                    .Cast<ViewSheet>()
                    .Select(s => new { s.SheetNumber, s.Name })
                    .Take(30)
                    .ToList();

                // Linked CAD files inside document
                var cadImports = new FilteredElementCollector(doc)
                    .OfClass(typeof(ImportInstance))
                    .Cast<ImportInstance>()
                    .Select(ii =>
                    {
                        var type = doc.GetElement(ii.GetTypeId());
                        return type?.Name ?? "Unknown";
                    })
                    .Distinct()
                    .ToList();

                // Linked RVT files
                var rvtLinks = new FilteredElementCollector(doc)
                    .OfClass(typeof(RevitLinkInstance))
                    .Cast<RevitLinkInstance>()
                    .Select(r => r.Name)
                    .Distinct()
                    .ToList();

                // Worksets
                var userWorksets = new List<string>();
                if (doc.IsWorkshared)
                {
                    userWorksets = new FilteredWorksetCollector(doc)
                        .OfKind(WorksetKind.UserWorkset)
                        .Select(w => w.Name)
                        .ToList();
                }

                // Pipe system breakdown
                var pipeSystemCounts = new Dictionary<string, int>();
                if (catCounts.ContainsKey("Pipes"))
                {
                    var pipes = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_PipeCurves)
                        .WhereElementIsNotElementType()
                        .Cast<Pipe>();
                    foreach (var p in pipes)
                    {
                        string sysName = "Unassigned";
                        try
                        {
                            var pSys = p.MEPSystem;
                            if (pSys != null) sysName = pSys.Name;
                        }
                        catch { }
                        pipeSystemCounts[sysName] = pipeSystemCounts.GetValueOrDefault(sysName, 0) + 1;
                    }
                }

                // Duct system breakdown
                var ductSystemCounts = new Dictionary<string, int>();
                if (catCounts.ContainsKey("Ducts"))
                {
                    var ducts = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_DuctCurves)
                        .WhereElementIsNotElementType()
                        .Cast<Duct>();
                    foreach (var d in ducts)
                    {
                        string sysName = "Unassigned";
                        try
                        {
                            var dSys = d.MEPSystem;
                            if (dSys != null) sysName = dSys.Name;
                        }
                        catch { }
                        ductSystemCounts[sysName] = ductSystemCounts.GetValueOrDefault(sysName, 0) + 1;
                    }
                }

                return new
                {
                    fileName = fi.Name,
                    sizeMB = Math.Round((double)fi.Length / (1024 * 1024), 2),
                    categoryCounts = catCounts,
                    worksets = userWorksets,
                    pipeSystemCounts,
                    ductSystemCounts,
                    pipingSystemTypes,
                    samplePipingSystems = pipingSystems,
                    pcccViews,
                    sampleSheets = sheets,
                    cadImports,
                    rvtLinks
                };
            }
            catch (Exception ex)
            {
                return new { fileName = fi.Name, error = ex.ToString() };
            }
            finally
            {
                uiapp.DialogBoxShowing -= dialogHandler;
                if (doc != null)
                {
                    try { doc.Close(false); } catch { }
                }
            }
        }
    }
}
