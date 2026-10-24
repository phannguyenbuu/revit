using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorAndTagsStatus
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = doc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. All floors on Tang 1
            var floors = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Select(f => {
                    var ft = doc.GetElement(f.GetTypeId()) as FloorType;
                    var matIds = f.GetMaterialIds(false);
                    var matNames = matIds.Select(mid => doc.GetElement(mid)?.Name).ToList();
                    return new {
                        id = f.Id.Value,
                        name = f.Name,
                        typeName = ft?.Name,
                        materials = matNames
                    };
                })
                .ToList();

            // 2. All fill patterns (Model)
            var patterns = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .Select(fp => {
                    var pat = fp.GetFillPattern();
                    return new {
                        id = fp.Id.Value,
                        name = fp.Name,
                        target = pat?.Target.ToString(),
                        gridCount = pat?.GetFillGrids().Count
                    };
                })
                .Where(p => p.target == "Model")
                .ToList();

            // 3. Tag symbols available for Doors and Windows
            var doorTagSymbols = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(BuiltInCategory.OST_DoorTags)
                .Cast<FamilySymbol>()
                .Select(s => new { id = s.Id.Value, fam = s.FamilyName, name = s.Name })
                .ToList();

            var windowTagSymbols = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(BuiltInCategory.OST_WindowTags)
                .Cast<FamilySymbol>()
                .Select(s => new { id = s.Id.Value, fam = s.FamilyName, name = s.Name })
                .ToList();

            // 4. Doors in Tang 1 view
            var doorsInView = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(d => {
                    var pt = (d.Location as LocationPoint)?.Point;
                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        mark = d.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                        typeMark = d.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                        x = pt != null ? pt.X * 304.8 : 0,
                        y = pt != null ? pt.Y * 304.8 : 0
                    };
                })
                .ToList();

            // 5. Windows in Tang 1 view
            var windowsInView = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(w => {
                    var pt = (w.Location as LocationPoint)?.Point;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        mark = w.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                        typeMark = w.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString(),
                        x = pt != null ? pt.X * 304.8 : 0,
                        y = pt != null ? pt.Y * 304.8 : 0
                    };
                })
                .ToList();

            // 6. Existing Door Tags and Window Tags in view
            var existingDoorTags = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_DoorTags)
                .WhereElementIsNotElementType()
                .Cast<IndependentTag>()
                .Select(t => {
                    var taggedIds = t.GetTaggedLocalElementIds().Select(id => id.Value).ToList();
                    return new { id = t.Id.Value, taggedIds = taggedIds };
                })
                .ToList();

            var existingWindowTags = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_WindowTags)
                .WhereElementIsNotElementType()
                .Cast<IndependentTag>()
                .Select(t => {
                    var taggedIds = t.GetTaggedLocalElementIds().Select(id => id.Value).ToList();
                    return new { id = t.Id.Value, taggedIds = taggedIds };
                })
                .ToList();

            return new
            {
                floors,
                patterns,
                doorTagSymbols,
                windowTagSymbols,
                doorsCount = doorsInView.Count,
                windowsCount = windowsInView.Count,
                doorsInView,
                windowsInView,
                existingDoorTagsCount = existingDoorTags.Count,
                existingWindowTagsCount = existingWindowTags.Count,
                existingDoorTags,
                existingWindowTags
            };
        }
    }
}
