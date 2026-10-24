using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ChangeAxisCDoorsToD7
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, message = "No active document." };

            // 1. Locate target Symbol D7_1200x2200
            FamilySymbol targetSymbol = null;
            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .ToList();

            foreach (var s in doorSymbols)
            {
                if (s.FamilyName.Equals("Cua_Chong_Chay_D7_1Canh", StringComparison.OrdinalIgnoreCase) &&
                    s.Name.Contains("1200x2200"))
                {
                    targetSymbol = s;
                    break;
                }
            }

            if (targetSymbol == null)
            {
                targetSymbol = doorSymbols.FirstOrDefault(s => s.FamilyName.Contains("D7") || s.Name.Contains("D7"));
            }

            if (targetSymbol == null)
            {
                return new { success = false, message = "Không tìm thấy FamilySymbol D7_1200x2200 trong dự án." };
            }

            // 2. Activate symbol if needed
            using (var txAct = new Transaction(doc, "Activate D7 Symbol"))
            {
                txAct.Start();
                if (!targetSymbol.IsActive) targetSymbol.Activate();
                txAct.Commit();
            }

            // 3. Find candidate doors on Axis C (Y=7800 +/- 1500) between Grid 9 (29650) and Grid 10 (33350)
            var allDoors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .ToList();

            var matchedDoors = new List<FamilyInstance>();
            foreach (var d in allDoors)
            {
                var lp = d.Location as LocationPoint;
                if (lp == null) continue;

                double x = lp.Point.X * FT_TO_MM;
                double y = lp.Point.Y * FT_TO_MM;

                double distToC = Math.Abs(y - 7800.0);
                bool between9and10 = (x >= 29500.0 && x <= 33500.0);

                if (distToC <= 1500.0 && between9and10)
                {
                    matchedDoors.Add(d);
                }
            }

            // Order by Level Z elevation
            matchedDoors = matchedDoors.OrderBy(d => (d.Location as LocationPoint).Point.Z).ToList();

            // 4. Update doors in a transaction
            var updatedInfo = new List<object>();

            using (var tx = new Transaction(doc, "Change Axis C Doors between Grids 9 and 10 to D7"))
            {
                tx.Start();

                foreach (var door in matchedDoors)
                {
                    string oldFam = door.Symbol.FamilyName;
                    string oldType = door.Symbol.Name;
                    var lp = door.Location as LocationPoint;

                    // Change type
                    if (door.GetTypeId() != targetSymbol.Id)
                    {
                        door.ChangeTypeId(targetSymbol.Id);
                    }

                    // Set Mark parameter
                    var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                    if (pMark != null && !pMark.IsReadOnly)
                    {
                        string currentMark = pMark.AsString() ?? "";
                        if (!currentMark.StartsWith("D7"))
                        {
                            pMark.Set("D7");
                        }
                    }

                    var level = doc.GetElement(door.LevelId) as Level;

                    updatedInfo.Add(new
                    {
                        id = door.Id.Value,
                        level = level?.Name ?? "N/A",
                        oldFamily = oldFam,
                        oldType = oldType,
                        newFamily = door.Symbol.FamilyName,
                        newType = door.Symbol.Name,
                        mark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                        x = lp != null ? Math.Round(lp.Point.X * FT_TO_MM, 1) : 0,
                        y = lp != null ? Math.Round(lp.Point.Y * FT_TO_MM, 1) : 0,
                        z = lp != null ? Math.Round(lp.Point.Z * FT_TO_MM, 1) : 0,
                        facingFlipped = door.FacingFlipped,
                        handFlipped = door.HandFlipped
                    });
                }

                tx.Commit();
            }

            return new
            {
                success = true,
                message = $"Đã đổi thành công {updatedInfo.Count} cửa đi trên trục C (giữa trục 9 và 10) sang cửa D7 (mở 30 độ).",
                count = updatedInfo.Count,
                doors = updatedInfo
            };
        }
    }
}
