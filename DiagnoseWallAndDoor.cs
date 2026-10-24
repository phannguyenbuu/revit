using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DiagnoseWallAndDoor
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            var door = doc.GetElement(new ElementId(2364731L)) as FamilyInstance;

            bool wallCatVis = view.GetCategoryHidden(new ElementId((int)BuiltInCategory.OST_Walls));
            bool doorCatVis = view.GetCategoryHidden(new ElementId((int)BuiltInCategory.OST_Doors));

            // Check if CAD link is visible
            var cadLinks = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .Select(i => new { id = i.Id.Value, isHidden = i.IsHidden(view) })
                .ToList();

            // Export image with CAD link hidden to see PURE Revit elements!
            // First let's check what elements are in view
            return new
            {
                viewName = view.Name,
                viewPhase = view.get_Parameter(BuiltInParameter.VIEW_PHASE)?.AsValueString(),
                viewDiscipline = view.Discipline.ToString(),
                wall = wall == null ? null : new
                {
                    id = wall.Id.Value,
                    name = wall.Name,
                    wallType = wall.WallType.Name,
                    isHidden = wall.IsHidden(view),
                    phaseCreated = wall.get_Parameter(BuiltInParameter.PHASE_CREATED)?.AsValueString(),
                    phaseDemolished = wall.get_Parameter(BuiltInParameter.PHASE_DEMOLISHED)?.AsValueString(),
                    level = wall.LevelId.Value
                },
                door = door == null ? null : new
                {
                    id = door.Id.Value,
                    name = door.Name,
                    symbolName = door.Symbol?.Name,
                    familyName = door.Symbol?.Family?.Name,
                    isHidden = door.IsHidden(view),
                    phaseCreated = door.get_Parameter(BuiltInParameter.PHASE_CREATED)?.AsValueString(),
                    phaseDemolished = door.get_Parameter(BuiltInParameter.PHASE_DEMOLISHED)?.AsValueString(),
                    level = door.LevelId.Value
                },
                wallCatHidden = wallCatVis,
                doorCatHidden = doorCatVis,
                cadLinks = cadLinks
            };
        }
    }
}
