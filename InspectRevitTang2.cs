
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRevitTang2
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            Level level2 = doc.GetElement(new ElementId(694)) as Level;
            if (level2 == null) return new { error = "Level 2 not found" };

            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => w.LevelId == level2.Id)
                .Select(w => new { id = w.Id.Value, name = w.Name, type = w.WallType.Name })
                .ToList();

            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(d => d.LevelId == level2.Id)
                .Select(d => new { id = d.Id.Value, name = d.Name })
                .ToList();

            var windows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(w => w.LevelId == level2.Id)
                .Select(w => new { id = w.Id.Value, name = w.Name })
                .ToList();

            var columns = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => c.LevelId == level2.Id)
                .Select(c => new { id = c.Id.Value, name = c.Name })
                .ToList();

            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.GenLevel?.Id == level2.Id)
                .Select(v => new { id = v.Id.Value, name = v.Name, viewType = v.ViewType.ToString() })
                .ToList();

            return new {
                level2Name = level2.Name,
                wallsCount = walls.Count,
                doorsCount = doors.Count,
                windowsCount = windows.Count,
                columnsCount = columns.Count,
                walls,
                doors,
                windows,
                columns,
                views
            };
        }
    }
}
