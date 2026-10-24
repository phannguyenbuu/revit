using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixGridB
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var oldB = doc.GetElement(new ElementId(714613L)) as Grid;
            var cmB = doc.GetElement(new ElementId(2564458L)) as Grid;

            bool renamedOld = false;
            bool renamedNew = false;
            bool deletedOld = false;
            string msg = "";

            using (var tx = new Transaction(doc, "Rename B_OLD and CM-B to B"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                if (oldB != null)
                {
                    try
                    {
                        oldB.Name = "B_OLD";
                        renamedOld = true;
                    }
                    catch (Exception ex)
                    {
                        msg += "Rename oldB failed: " + ex.Message + "; ";
                    }
                }

                if (cmB != null)
                {
                    try
                    {
                        cmB.Name = "B";
                        renamedNew = true;
                    }
                    catch (Exception ex)
                    {
                        msg += "Rename cmB failed: " + ex.Message + "; ";
                    }
                }

                if (oldB != null)
                {
                    try
                    {
                        if (oldB.Pinned) oldB.Pinned = false;
                        doc.Delete(oldB.Id);
                        deletedOld = true;
                    }
                    catch (Exception ex)
                    {
                        msg += "Delete oldB failed: " + ex.Message + "; ";
                    }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                renamedOld,
                renamedNew,
                deletedOld,
                msg
            };
        }
    }
}
