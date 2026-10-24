using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CloneSelectedWallsUp
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Get selection of walls from args or current Revit selection
            var wallIds = new List<ElementId>();
            if (args.TryGetProperty("elementIds", out var idsProp) && idsProp.ValueKind == System.Text.Json.JsonValueKind.Array)
            {
                foreach (var item in idsProp.EnumerateArray())
                {
                    wallIds.Add(new ElementId(item.GetInt64()));
                }
            }
            else
            {
                var selIds = uidoc.Selection.GetElementIds();
                foreach (var id in selIds)
                {
                    var el = doc.GetElement(id);
                    if (el is Wall) wallIds.Add(id);
                }
            }

            if (wallIds.Count == 0)
            {
                return new { error = "Không có tường nào đang được chọn trong Revit! Vui lòng chọn ít nhất 1 tường." };
            }

            // 2. Get sorted levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            string? targetLevelName = null;
            if (args.TryGetProperty("targetLevelName", out var tProp))
            {
                targetLevelName = tProp.GetString();
            }

            double targetHeightMm = 250.0;
            if (args.TryGetProperty("heightMm", out var hProp))
            {
                targetHeightMm = hProp.GetDouble();
            }

            var createdIds = new List<ElementId>();
            var results = new List<object>();

            using (var trans = new Transaction(doc, "Clone Selected Walls Up 1 Floor (H=250)"))
            {
                var fOpts = trans.GetFailureHandlingOptions();
                fOpts.SetFailuresPreprocessor(new SyncWarningSwallower());
                trans.SetFailureHandlingOptions(fOpts);
                trans.Start();

                foreach (var wallId in wallIds)
                {
                    var wall = doc.GetElement(wallId) as Wall;
                    if (wall == null) continue;

                    // Get current base level
                    var baseParam = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
                    var currentLevelId = baseParam?.AsElementId();
                    var currentLevel = doc.GetElement(currentLevelId) as Level;

                    Level nextLevel = null;
                    if (!string.IsNullOrEmpty(targetLevelName))
                    {
                        nextLevel = levels.FirstOrDefault(l => l.Name.Equals(targetLevelName, StringComparison.OrdinalIgnoreCase) || l.Name.Contains(targetLevelName, StringComparison.OrdinalIgnoreCase));
                    }

                    if (nextLevel == null)
                    {
                        if (currentLevel != null)
                        {
                            nextLevel = levels.FirstOrDefault(l => l.Elevation > currentLevel.Elevation + 0.001);
                        }
                        else
                        {
                            // Fallback: pick level above wall's lowest Z
                            var bb = wall.get_BoundingBox(null);
                            double zMin = bb != null ? bb.Min.Z : 0;
                            nextLevel = levels.FirstOrDefault(l => l.Elevation > zMin + 0.001);
                        }
                    }

                    if (nextLevel == null)
                    {
                        results.Add(new { id = wall.Id.Value, status = "Failed: No level above" });
                        continue;
                    }

                    double currentElev = currentLevel != null ? currentLevel.Elevation : 0;
                    double dz = nextLevel.Elevation - currentElev;

                    // Copy wall by dz vector
                    var copiedIds = ElementTransformUtils.CopyElements(doc, new List<ElementId> { wall.Id }, new XYZ(0, 0, dz));
                    if (copiedIds != null && copiedIds.Count > 0)
                    {
                        var newWallId = copiedIds.First();
                        var newWall = doc.GetElement(newWallId) as Wall;
                        if (newWall != null)
                        {
                            // Set Base Level to nextLevel
                            var pBase = newWall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
                            if (pBase != null && !pBase.IsReadOnly)
                            {
                                pBase.Set(nextLevel.Id);
                            }

                            // Set Base Offset to 0
                            var pBaseOff = newWall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                            if (pBaseOff != null && !pBaseOff.IsReadOnly)
                            {
                                pBaseOff.Set(0.0);
                            }

                            // Set Top Constraint to Unconnected
                            var pTop = newWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                            if (pTop != null && !pTop.IsReadOnly)
                            {
                                pTop.Set(ElementId.InvalidElementId);
                            }

                            // Set Unconnected Height to targetHeightMm
                            var pHeight = newWall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                            if (pHeight != null && !pHeight.IsReadOnly)
                            {
                                pHeight.Set(targetHeightMm / 304.8);
                            }

                            // Set Top Offset to 0
                            var pTopOff = newWall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                            if (pTopOff != null && !pTopOff.IsReadOnly)
                            {
                                pTopOff.Set(0.0);
                            }

                            createdIds.Add(newWallId);
                            results.Add(new
                            {
                                originalId = wall.Id.Value,
                                newId = newWallId.Value,
                                originalLevel = currentLevel?.Name ?? "Unknown",
                                newLevel = nextLevel.Name,
                                newElevationMm = nextLevel.Elevation * 304.8,
                                heightMm = targetHeightMm,
                                wallType = newWall.Name
                            });
                        }
                    }
                }

                trans.Commit();
            }

            // Select newly created walls in Revit UI
            if (createdIds.Count > 0)
            {
                uidoc.Selection.SetElementIds(createdIds);
            }

            return new
            {
                success = true,
                clonedCount = createdIds.Count,
                clonedElements = results
            };
        }
    }
}
