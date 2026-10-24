using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCopyStairZ
    {
        private static double M(double meters) => meters / 0.3048;
        private static double ToM(double feet) => feet * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var stair = doc.GetElement(new ElementId(2368346)) as Stairs;
            if (stair == null) return new { error = "Source stair 2368346 not found" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            var level1 = levels.FirstOrDefault(l => l.Id.Value == 311);
            var level2 = levels.FirstOrDefault(l => l.Id.Value == 694);
            var level3 = levels.FirstOrDefault(l => l.Id.Value == 1727584);

            XYZ translation = new XYZ(0, 0, M(3.6));

            ElementId copiedId = ElementId.InvalidElementId;
            object initialInfo = null;
            object afterParamInfo = null;

            using (Transaction t = new Transaction(doc, "Test Copy Stair Z"))
            {
                var prep = new StairFailurePreprocessor();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                var copiedIds = ElementTransformUtils.CopyElement(doc, stair.Id, translation);
                if (copiedIds != null && copiedIds.Count > 0)
                {
                    copiedId = copiedIds.First();
                    var newStair = doc.GetElement(copiedId) as Stairs;

                    var bb = newStair.get_BoundingBox(null);
                    initialInfo = new
                    {
                        id = copiedId.Value,
                        baseLevel = newStair.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)?.AsElementId()?.Value,
                        topLevel = newStair.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)?.AsElementId()?.Value,
                        baseOffsetM = ToM(newStair.get_Parameter(BuiltInParameter.STAIRS_BASE_OFFSET)?.AsDouble() ?? 0),
                        topOffsetM = ToM(newStair.get_Parameter(BuiltInParameter.STAIRS_TOP_OFFSET)?.AsDouble() ?? 0),
                        minZ = bb != null ? ToM(bb.Min.Z) : 0,
                        maxZ = bb != null ? ToM(bb.Max.Z) : 0
                    };

                    // Try updating level parameters
                    if (level2 != null && level3 != null)
                    {
                        newStair.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)?.Set(level2.Id);
                        newStair.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)?.Set(level3.Id);
                        newStair.get_Parameter(BuiltInParameter.STAIRS_BASE_OFFSET)?.Set(0.0);
                        newStair.get_Parameter(BuiltInParameter.STAIRS_TOP_OFFSET)?.Set(0.0);
                    }

                    doc.Regenerate();
                    var bb2 = newStair.get_BoundingBox(null);
                    afterParamInfo = new
                    {
                        baseLevel = newStair.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)?.AsElementId()?.Value,
                        topLevel = newStair.get_Parameter(BuiltInParameter.STAIRS_TOP_LEVEL_PARAM)?.AsElementId()?.Value,
                        baseOffsetM = ToM(newStair.get_Parameter(BuiltInParameter.STAIRS_BASE_OFFSET)?.AsDouble() ?? 0),
                        topOffsetM = ToM(newStair.get_Parameter(BuiltInParameter.STAIRS_TOP_OFFSET)?.AsDouble() ?? 0),
                        minZ = bb2 != null ? ToM(bb2.Min.Z) : 0,
                        maxZ = bb2 != null ? ToM(bb2.Max.Z) : 0
                    };
                }

                t.Commit();
            }

            return new { copiedId = copiedId.Value, initialInfo, afterParamInfo };
        }
    }
}
