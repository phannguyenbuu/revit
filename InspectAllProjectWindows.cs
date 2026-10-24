using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllProjectWindows
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var allWindows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Select(w => new
                    {
                        id = w.Id.Value,
                        familyName = w.Symbol.FamilyName,
                        typeName = w.Symbol.Name,
                        level = doc.GetElement(w.LevelId)?.Name,
                        bb = w.get_BoundingBox(null) != null ? new
                        {
                            min = new { x = Math.Round(ToMm(w.get_BoundingBox(null).Min.X), 0), y = Math.Round(ToMm(w.get_BoundingBox(null).Min.Y), 0), z = Math.Round(ToMm(w.get_BoundingBox(null).Min.Z), 0) },
                            max = new { x = Math.Round(ToMm(w.get_BoundingBox(null).Max.X), 0), y = Math.Round(ToMm(w.get_BoundingBox(null).Max.Y), 0), z = Math.Round(ToMm(w.get_BoundingBox(null).Max.Z), 0) }
                        } : null
                    })
                    .ToList();

                // Now inspect family "CUA SO2 CANH NHOM KINH CO O THOANG"
                var fam2 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.Equals("CUA SO2 CANH NHOM KINH CO O THOANG", StringComparison.OrdinalIgnoreCase));

                object fam2Info = null;
                if (fam2 != null && fam2.IsEditable)
                {
                    var famDoc = doc.EditFamily(fam2);
                    if (famDoc != null)
                    {
                        var extrusions = new FilteredElementCollector(famDoc)
                            .OfClass(typeof(Extrusion))
                            .Cast<Extrusion>()
                            .Select(e =>
                            {
                                int loopCount = e.Sketch != null ? e.Sketch.Profile.Size : 0;
                                return new
                                {
                                    id = e.Id.Value,
                                    subCat = e.Subcategory?.Name,
                                    loopCount,
                                    start = Math.Round(ToMm(e.StartOffset), 1),
                                    end = Math.Round(ToMm(e.EndOffset), 1)
                                };
                            })
                            .ToList();

                        famDoc.Close(false);
                        fam2Info = new { name = fam2.Name, extrusions };
                    }
                }

                return new
                {
                    totalWindows = allWindows.Count,
                    allWindows,
                    fam2Info
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
