using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class LowerAllBeams100mm
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            double targetOffsetFt = -100.0 / FT2MM;
            int updatedCount = 0;
            int failedCount = 0;

            using (var tx = new Transaction(doc, "Lower All Beams 100mm"))
            {
                tx.Start();
                foreach (var b in beams)
                {
                    try
                    {
                        var pZOff = b.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                        if (pZOff != null && !pZOff.IsReadOnly)
                        {
                            pZOff.Set(targetOffsetFt);
                            updatedCount++;
                        }
                        else
                        {
                            failedCount++;
                        }
                    }
                    catch
                    {
                        failedCount++;
                    }
                }
                tx.Commit();
            }

            return new {
                totalBeams = beams.Count,
                updatedCount,
                failedCount,
                targetOffsetMm = -100.0
            };
        }
    }
}
