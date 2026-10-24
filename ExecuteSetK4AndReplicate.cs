using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExecuteSetK4AndReplicate
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Identify selected window
            var selIds = uidoc.Selection.GetElementIds();
            FamilyInstance win = null;
            if (selIds.Count > 0)
            {
                foreach (var id in selIds)
                {
                    var fi = doc.GetElement(id) as FamilyInstance;
                    if (fi != null && fi.Category?.BuiltInCategory == BuiltInCategory.OST_Windows)
                    {
                        win = fi;
                        break;
                    }
                }
            }

            // Fallback to 2413190
            if (win == null)
            {
                win = doc.GetElement(new ElementId(2413190L)) as FamilyInstance;
            }
            if (win == null) return new { error = "No window found" };

            var report = new Dictionary<string, object>();

            using (var tx = new Transaction(doc, "Set Window K4 and Replicate to Floors 3 and 4"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(opts);
                tx.Start();

                // Step A: Ensure Symbol has Type Mark = "K4"
                var curSym = win.Symbol;
                FamilySymbol k4Sym = null;
                string targetSymName = "K4";

                // Check if symbol "K4" already exists in family
                foreach (ElementId symId in curSym.Family.GetFamilySymbolIds())
                {
                    var s = doc.GetElement(symId) as FamilySymbol;
                    if (s != null && (s.Name == "K4" || s.Name == "K4_1500x1400"))
                    {
                        k4Sym = s;
                        break;
                    }
                }

                if (k4Sym == null)
                {
                    try
                    {
                        k4Sym = curSym.Duplicate(targetSymName) as FamilySymbol;
                    }
                    catch
                    {
                        k4Sym = curSym.Duplicate("K4_1500x1400") as FamilySymbol;
                    }
                }

                if (k4Sym != null)
                {
                    k4Sym.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.Set("K4");
                    win.Symbol = k4Sym;
                }
                else
                {
                    curSym.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.Set("K4");
                    k4Sym = curSym;
                }

                // Also set instance Mark to K4
                win.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("K4");

                report["stepA_windowT2"] = new
                {
                    id = win.Id.Value,
                    typeName = win.Symbol.Name,
                    typeMark = win.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                    mark = win.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString()
                };

                // Step B: Tag Window on Tang 2 (View 695)
                var tagSym = doc.GetElement(new ElementId(146125L)) as FamilySymbol;
                if (tagSym != null && !tagSym.IsActive) tagSym.Activate();

                var view2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
                XYZ winPt = (win.Location as LocationPoint)?.Point ?? new XYZ(37150 * MM_TO_FT, 6602 * MM_TO_FT, 4700 * MM_TO_FT);
                XYZ tagPt2 = new XYZ((37150.0 + 900.0) * MM_TO_FT, 6602.0 * MM_TO_FT, 0);

                IndependentTag tag2 = null;
                try
                {
                    tag2 = IndependentTag.Create(doc, view2.Id, new Reference(win), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, tagPt2);
                    if (tagSym != null) tag2.ChangeTypeId(tagSym.Id);
                    report["stepB_tagT2"] = new { tagId = tag2.Id.Value, text = tag2.TagText };
                }
                catch (Exception ex)
                {
                    report["stepB_tagT2_error"] = ex.Message;
                }

                // Step C: Replicate Window to Tang 3 (View 1727632)
                var wall3 = doc.GetElement(new ElementId(2369705L)) as Wall;
                var lvl3 = doc.GetElement(new ElementId(1727584L)) as Level;
                var view3 = doc.GetElement(new ElementId(1727632L)) as ViewPlan;

                XYZ pt3 = new XYZ(37150.0 * MM_TO_FT, 6602.0 * MM_TO_FT, (7500.0 + 800.0) * MM_TO_FT);
                FamilyInstance win3 = null;
                try
                {
                    win3 = doc.Create.NewFamilyInstance(pt3, k4Sym, wall3, lvl3, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    win3.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(800.0 * MM_TO_FT);
                    win3.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("K4");

                    XYZ tagPt3 = new XYZ((37150.0 + 900.0) * MM_TO_FT, 6602.0 * MM_TO_FT, 0);
                    var tag3 = IndependentTag.Create(doc, view3.Id, new Reference(win3), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, tagPt3);
                    if (tagSym != null) tag3.ChangeTypeId(tagSym.Id);

                    report["stepC_windowT3"] = new
                    {
                        winId = win3.Id.Value,
                        typeName = win3.Symbol.Name,
                        typeMark = win3.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                        tagId = tag3.Id.Value,
                        tagText = tag3.TagText
                    };
                }
                catch (Exception ex)
                {
                    report["stepC_windowT3_error"] = ex.Message;
                }

                // Step D: Replicate Window to Tang 4 (View 2409349)
                var wall4 = doc.GetElement(new ElementId(2369929L)) as Wall;
                var lvl4 = doc.GetElement(new ElementId(2360634L)) as Level;
                var view4 = doc.GetElement(new ElementId(2409349L)) as ViewPlan;

                XYZ pt4 = new XYZ(37150.0 * MM_TO_FT, 6602.0 * MM_TO_FT, (11100.0 + 800.0) * MM_TO_FT);
                FamilyInstance win4 = null;
                try
                {
                    win4 = doc.Create.NewFamilyInstance(pt4, k4Sym, wall4, lvl4, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
                    win4.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(800.0 * MM_TO_FT);
                    win4.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("K4");

                    XYZ tagPt4 = new XYZ((37150.0 + 900.0) * MM_TO_FT, 6602.0 * MM_TO_FT, 0);
                    var tag4 = IndependentTag.Create(doc, view4.Id, new Reference(win4), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, tagPt4);
                    if (tagSym != null) tag4.ChangeTypeId(tagSym.Id);

                    report["stepD_windowT4"] = new
                    {
                        winId = win4.Id.Value,
                        typeName = win4.Symbol.Name,
                        typeMark = win4.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                        tagId = tag4.Id.Value,
                        tagText = tag4.TagText
                    };
                }
                catch (Exception ex)
                {
                    report["stepD_windowT4_error"] = ex.Message;
                }

                tx.Commit();
            }

            return new { success = true, report };
        }
    }
}
