using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ClearRemainingOldBuilding
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            int deletedCount = 0;
            using (var tx = new Transaction(doc, "Clear Remaining Old Building"))
            {
                tx.Start();
                var catsToDelete = new List<BuiltInCategory>
                {
                    BuiltInCategory.OST_Roofs,
                    BuiltInCategory.OST_RoofSoffit,
                    BuiltInCategory.OST_Fascia,
                    BuiltInCategory.OST_StructuralFraming,
                    BuiltInCategory.OST_Stairs,
                    BuiltInCategory.OST_StairsRailing,
                    BuiltInCategory.OST_Ramps,
                    BuiltInCategory.OST_GenericModel,
                    BuiltInCategory.OST_TextNotes
                };

                foreach (var cat in catsToDelete)
                {
                    var ids = new FilteredElementCollector(doc)
                        .OfCategory(cat)
                        .WhereElementIsNotElementType()
                        .ToElementIds();

                    if (ids.Count > 0)
                    {
                        var del = doc.Delete(ids);
                        deletedCount += del.Count;
                    }
                }
                tx.Commit();
            }

            // Save document
            try { doc.Save(); } catch { }

            return new { success = true, deletedCount = deletedCount };
        }
    }
}
