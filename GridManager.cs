using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class GridWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            failuresAccessor.DeleteAllWarnings();
            return FailureProcessingResult.Continue;
        }
    }

    public static class GridManager
    {
        private const double MetersToFeet = 1.0 / 0.3048;
        private const double FeetToMeters = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string mode = "inspect";
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("mode", out var m))
            {
                mode = m.GetString()?.ToLowerInvariant() ?? "inspect";
            }

            if (mode == "create" || mode == "create_batch")
            {
                return CreateGrids(uiapp, args);
            }

            if (mode == "replace_old" || mode == "delete_old")
            {
                return ReplaceOldGrids(uiapp, args);
            }

            return InspectGrids(uiapp, args);
        }

        public static object InspectGrids(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g =>
                {
                    var curve = g.Curve;
                    var p0 = curve.GetEndPoint(0);
                    var p1 = curve.GetEndPoint(1);
                    return new
                    {
                        id = g.Id.Value,
                        name = g.Name,
                        p0Meters = new double[] { Math.Round(p0.X * FeetToMeters, 3), Math.Round(p0.Y * FeetToMeters, 3), Math.Round(p0.Z * FeetToMeters, 3) },
                        p1Meters = new double[] { Math.Round(p1.X * FeetToMeters, 3), Math.Round(p1.Y * FeetToMeters, 3), Math.Round(p1.Z * FeetToMeters, 3) },
                        dxMeters = Math.Round((p1.X - p0.X) * FeetToMeters, 3),
                        dyMeters = Math.Round((p1.Y - p0.Y) * FeetToMeters, 3)
                    };
                })
                .OrderBy(g => g.name)
                .ToList();

            // Model bounding box from pipes & MEP elements
            double minX = double.MaxValue, minY = double.MaxValue, minZ = double.MaxValue;
            double maxX = double.MinValue, maxY = double.MinValue, maxZ = double.MinValue;
            int mepCount = 0;

            var collector = new FilteredElementCollector(doc)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory>
                {
                    BuiltInCategory.OST_PipeCurves,
                    BuiltInCategory.OST_DuctCurves,
                    BuiltInCategory.OST_Sprinklers,
                    BuiltInCategory.OST_MechanicalEquipment
                }))
                .WhereElementIsNotElementType();

            foreach (var el in collector)
            {
                var bb = el.get_BoundingBox(null);
                if (bb != null)
                {
                    minX = Math.Min(minX, bb.Min.X);
                    minY = Math.Min(minY, bb.Min.Y);
                    minZ = Math.Min(minZ, bb.Min.Z);
                    maxX = Math.Max(maxX, bb.Max.X);
                    maxY = Math.Max(maxY, bb.Max.Y);
                    maxZ = Math.Max(maxZ, bb.Max.Z);
                    mepCount++;
                }
            }

            return new
            {
                success = true,
                gridCount = grids.Count,
                grids = grids,
                mepElementCount = mepCount,
                modelBoundsMeters = mepCount > 0 ? new
                {
                    minX = Math.Round(minX * FeetToMeters, 3),
                    minY = Math.Round(minY * FeetToMeters, 3),
                    minZ = Math.Round(minZ * FeetToMeters, 3),
                    maxX = Math.Round(maxX * FeetToMeters, 3),
                    maxY = Math.Round(maxY * FeetToMeters, 3),
                    maxZ = Math.Round(maxZ * FeetToMeters, 3),
                    sizeX = Math.Round((maxX - minX) * FeetToMeters, 3),
                    sizeY = Math.Round((maxY - minY) * FeetToMeters, 3),
                    sizeZ = Math.Round((maxZ - minZ) * FeetToMeters, 3)
                } : null
            };
        }

        public static object CreateGrids(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            if (!args.TryGetProperty("grids", out var gridsArr) || gridsArr.ValueKind != JsonValueKind.Array)
            {
                return new { error = "Missing 'grids' array in arguments" };
            }

            var existingGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToDictionary(g => g.Name, g => g);

            var created = new List<object>();
            var updated = new List<object>();
            var errors = new List<string>();

            using (var tx = new Transaction(doc, "Create Column Grids from AutoCAD"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                opts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                foreach (var gElem in gridsArr.EnumerateArray())
                {
                    string name = gElem.GetProperty("name").GetString() ?? "";
                    double x1 = gElem.GetProperty("x1").GetDouble() * MetersToFeet;
                    double y1 = gElem.GetProperty("y1").GetDouble() * MetersToFeet;
                    double x2 = gElem.GetProperty("x2").GetDouble() * MetersToFeet;
                    double y2 = gElem.GetProperty("y2").GetDouble() * MetersToFeet;

                    XYZ p0 = new XYZ(x1, y1, 0);
                    XYZ p1 = new XYZ(x2, y2, 0);

                    if (p0.DistanceTo(p1) < 0.1)
                    {
                        errors.Add($"Grid {name} line length is too small.");
                        continue;
                    }

                    try
                    {
                        Line line = Line.CreateBound(p0, p1);
                        if (existingGrids.TryGetValue(name, out var existingGrid))
                        {
                            // Update curve or note existing
                            updated.Add(new { name = name, id = existingGrid.Id.Value });
                        }
                        else
                        {
                            Grid newGrid = Grid.Create(doc, line);
                            if (newGrid != null)
                            {
                                try
                                {
                                    newGrid.Name = name;
                                }
                                catch (Exception nEx)
                                {
                                    // Name might collide with an internal name, append if needed
                                    errors.Add($"Name collision for {name}: {nEx.Message}");
                                }
                                created.Add(new { name = newGrid.Name, id = newGrid.Id.Value });
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        errors.Add($"Failed to create grid {name}: {ex.Message}");
                    }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                createdCount = created.Count,
                updatedCount = updated.Count,
                created = created,
                updated = updated,
                errors = errors
            };
        }

        public static object ReplaceOldGrids(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            var allGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var oldGrids = allGrids.Where(g => !g.Name.StartsWith("CM-")).ToList();
            var newGrids = allGrids.Where(g => g.Name.StartsWith("CM-")).ToList();

            var deletedNames = new List<string>();
            var renamedNames = new List<object>();
            var errors = new List<string>();

            using (var tx = new Transaction(doc, "Delete Old Grids and Use AutoCAD Grids"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                opts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // 1. Delete old grids
                foreach (var og in oldGrids)
                {
                    try
                    {
                        deletedNames.Add(og.Name);
                        doc.Delete(og.Id);
                    }
                    catch (Exception ex)
                    {
                        errors.Add($"Failed to delete old grid {og.Name}: {ex.Message}");
                    }
                }

                doc.Regenerate();

                // 2. Rename new grids: strip "CM-" prefix
                foreach (var ng in newGrids)
                {
                    string oldName = ng.Name;
                    string targetName = oldName.Substring(3); // remove "CM-"
                    try
                    {
                        ng.Name = targetName;
                        renamedNames.Add(new { previousName = oldName, currentName = targetName, id = ng.Id.Value });
                    }
                    catch (Exception ex)
                    {
                        errors.Add($"Failed to rename {oldName} to {targetName}: {ex.Message}");
                    }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                deletedOldCount = deletedNames.Count,
                deletedOldGrids = deletedNames,
                renamedCount = renamedNames.Count,
                renamedGrids = renamedNames,
                errors = errors
            };
        }
    }
}
