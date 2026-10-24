using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetDimensionFitLength800
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var updatedTypes = new List<object>();
            int deletedDuplicates = 0;

            using (var tx = new Transaction(doc, "Set Dimension Fit Length 800mm and Clean Overlaps"))
            {
                tx.Start();

                // 1. Update all linear dimension types in the project
                var dimTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(DimensionType))
                    .Cast<DimensionType>()
                    .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                    .ToList();

                foreach (var dt in dimTypes)
                {
                    bool modified = false;

                    // Witness Line Control: 1 = Fixed to Dimension Line
                    var pCntrl = dt.get_Parameter(BuiltInParameter.DIM_WITNS_LINE_CNTRL);
                    if (pCntrl != null && !pCntrl.IsReadOnly)
                    {
                        pCntrl.Set(1);
                        modified = true;
                    }

                    // Witness Line Length: 8.0 mm on paper (= 800mm in model at 1:100 scale)
                    var pLen = dt.get_Parameter(BuiltInParameter.DIM_WITNS_LINE_EXTENSION_BELOW);
                    if (pLen != null && !pLen.IsReadOnly)
                    {
                        pLen.Set(8.0 * MM_TO_FT);
                        modified = true;
                    }

                    // Text Background: 1 = Transparent (No Fill)
                    var pBg = dt.get_Parameter(BuiltInParameter.DIM_TEXT_BACKGROUND);
                    if (pBg != null && !pBg.IsReadOnly)
                    {
                        pBg.Set(1);
                        modified = true;
                    }

                    // Witness Line Extension beyond dim line: 2.0 mm
                    var pExt = dt.get_Parameter(BuiltInParameter.WITNS_LINE_EXTENSION);
                    if (pExt != null && !pExt.IsReadOnly && pExt.AsDouble() < 1.0 * MM_TO_FT)
                    {
                        pExt.Set(2.0 * MM_TO_FT);
                        modified = true;
                    }

                    // Dim Line Extension: 1.5 mm
                    var pLineExt = dt.get_Parameter(BuiltInParameter.DIM_LINE_EXTENSION);
                    if (pLineExt != null && !pLineExt.IsReadOnly && pLineExt.AsDouble() < 0.5 * MM_TO_FT)
                    {
                        pLineExt.Set(1.5 * MM_TO_FT);
                        modified = true;
                    }

                    updatedTypes.Add(new
                    {
                        id = dt.Id.Value,
                        name = dt.Name,
                        witnessLineControl = pCntrl != null ? pCntrl.AsValueString() : "null",
                        witnessLineLength = pLen != null ? pLen.AsValueString() : "null",
                        textBackground = pBg != null ? pBg.AsValueString() : "null"
                    });
                }

                // 2. Remove older duplicate/overlapping dimensions on Floor 1 (View 312)
                // Older test dimensions: 2408818, 2408819, 2408821, 2408822, 2408824, 2408825,
                // 2408828, 2408829, 2409102, 2409285, 2409286, 2409287, 2409288
                var oldDuplicateIds = new List<long>
                {
                    2408818L, 2408819L, 2408821L, 2408822L, 2408824L, 2408825L,
                    2408828L, 2408829L, 2409102L, 2409285L, 2409286L, 2409287L, 2409288L,
                    2413358L, 2413359L
                };

                foreach (var oldId in oldDuplicateIds)
                {
                    var el = doc.GetElement(new ElementId(oldId));
                    if (el != null)
                    {
                        try
                        {
                            doc.Delete(el.Id);
                            deletedDuplicates++;
                        }
                        catch { }
                    }
                }

                tx.Commit();
            }

            return new
            {
                success = true,
                message = "Đã set tất cả Linear Dimension Types trong project có độ dài chân dim cố định (fit length) 800mm (8.0mm ở tỉ lệ 1/100) và text trong suốt.",
                updatedTypesCount = updatedTypes.Count,
                deletedDuplicatesCount = deletedDuplicates,
                types = updatedTypes
            };
        }
    }
}
