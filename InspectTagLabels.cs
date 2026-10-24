using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTagLabels
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var results = new List<object>();

            var doorTagFam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "KÝ HIEU CUA ĐI");

            if (doorTagFam != null)
            {
                var famDoc = doc.EditFamily(doorTagFam);
                if (famDoc != null)
                {
                    var textNotes = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(TextElement))
                        .Select(t => t.Name)
                        .ToList();
                    famDoc.Close(false);
                    results.Add(new { fam = "KÝ HIEU CUA ĐI", textNotes });
                }
            }

            var winTagFam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "KÝ HIỆU CỬA SỔ");

            if (winTagFam != null)
            {
                var famDoc = doc.EditFamily(winTagFam);
                if (famDoc != null)
                {
                    var textNotes = new FilteredElementCollector(famDoc)
                        .OfClass(typeof(TextElement))
                        .Select(t => t.Name)
                        .ToList();
                    famDoc.Close(false);
                    results.Add(new { fam = "KÝ HIỆU CỬA SỔ", textNotes });
                }
            }

            return results;
        }
    }
}
