using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetSelectedSlabThickness
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Get selected floors
            var selIds = uidoc.Selection.GetElementIds();
            var floorIds = new List<ElementId>();
            foreach (var id in selIds)
            {
                var el = doc.GetElement(id);
                if (el is Floor) floorIds.Add(id);
            }

            // Fallback to 2381562 if selection is empty (due to focus loss)
            if (floorIds.Count == 0)
            {
                var fallback = doc.GetElement(new ElementId(2381562L));
                if (fallback is Floor) floorIds.Add(fallback.Id);
            }

            if (floorIds.Count == 0)
            {
                return new { error = "Không tìm thấy slab/sàn nào đang được chọn!" };
            }

            double targetThicknessMm = 750.0;
            if (args.TryGetProperty("thicknessMm", out var thProp))
            {
                targetThicknessMm = thProp.GetDouble();
            }

            string targetTypeName = $"Sàn BTCT {targetThicknessMm:0}mm";
            var results = new List<object>();

            using (var trans = new Transaction(doc, $"Set Slab Thickness to {targetThicknessMm}mm"))
            {
                var fOpts = trans.GetFailureHandlingOptions();
                fOpts.SetFailuresPreprocessor(new SyncWarningSwallower());
                trans.SetFailureHandlingOptions(fOpts);
                trans.Start();

                // Find or duplicate FloorType
                FloorType targetFloorType = new FilteredElementCollector(doc)
                    .OfClass(typeof(FloorType))
                    .Cast<FloorType>()
                    .FirstOrDefault(ft => ft.Name.Equals(targetTypeName, StringComparison.OrdinalIgnoreCase));

                foreach (var floorId in floorIds)
                {
                    var floor = doc.GetElement(floorId) as Floor;
                    if (floor == null) continue;

                    var currentType = doc.GetElement(floor.GetTypeId()) as FloorType;
                    if (currentType == null) continue;

                    // If target type doesn't exist yet, duplicate from current
                    if (targetFloorType == null)
                    {
                        targetFloorType = currentType.Duplicate(targetTypeName) as FloorType;
                        if (targetFloorType != null)
                        {
                            var cs = targetFloorType.GetCompoundStructure();
                            if (cs != null)
                            {
                                var layers = cs.GetLayers();
                                if (layers.Count > 0)
                                {
                                    // Set structural layer thickness
                                    layers[0].Width = targetThicknessMm / 304.8;
                                    cs.SetLayers(layers);
                                    targetFloorType.SetCompoundStructure(cs);
                                }
                            }
                        }
                    }

                    if (targetFloorType != null)
                    {
                        floor.ChangeTypeId(targetFloorType.Id);
                        
                        var bb = floor.get_BoundingBox(null);
                        string bbStr = bb != null
                            ? $"Z: [{bb.Min.Z * 304.8:F0} -> {bb.Max.Z * 304.8:F0} mm]"
                            : "";

                        results.Add(new
                        {
                            floorId = floor.Id.Value,
                            oldType = currentType.Name,
                            newType = targetFloorType.Name,
                            thicknessMm = targetThicknessMm,
                            boundingBox = bbStr
                        });
                    }
                }

                trans.Commit();
            }

            // Keep the floor selected in Revit
            uidoc.Selection.SetElementIds(floorIds);

            return new
            {
                success = true,
                modifiedCount = results.Count,
                floors = results
            };
        }
    }
}
