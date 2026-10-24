using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTextNotesAndColumns
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Text Note Types
            var textTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .Select(t => new
                {
                    id = t.Id.Value,
                    name = t.Name,
                    font = t.get_Parameter(BuiltInParameter.TEXT_FONT)?.AsString(),
                    sizeMm = Math.Round((t.get_Parameter(BuiltInParameter.TEXT_SIZE)?.AsDouble() ?? 0) * 304.8, 2)
                })
                .ToList();

            // 2. Text Note Instances
            var textNotes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNote))
                .Cast<TextNote>()
                .Select(n => new
                {
                    id = n.Id.Value,
                    typeId = n.GetTypeId().Value,
                    typeName = doc.GetElement(n.GetTypeId())?.Name,
                    viewId = n.OwnerViewId.Value,
                    viewName = doc.GetElement(n.OwnerViewId)?.Name,
                    text = n.Text.Length > 40 ? n.Text.Substring(0, 40) + "..." : n.Text
                })
                .ToList();

            // 3. Columns Summary
            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(c =>
                {
                    var pBase = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    var baseElem = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) : null;
                    var topElem = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) : null;
                    var lp = c.Location as LocationPoint;

                    return new
                    {
                        id = c.Id.Value,
                        symbol = c.Symbol.Name,
                        baseLevel = baseElem?.Name,
                        topLevel = topElem?.Name,
                        x = lp != null ? Math.Round(lp.Point.X * 304.8, 1) : 0,
                        y = lp != null ? Math.Round(lp.Point.Y * 304.8, 1) : 0,
                        z = lp != null ? Math.Round(lp.Point.Z * 304.8, 1) : 0
                    };
                })
                .ToList();

            // 4. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevationM = Math.Round(l.Elevation * 0.3048, 3)
                })
                .ToList();

            return new
            {
                textTypes,
                textNoteCount = textNotes.Count,
                textNotesSample = textNotes.Take(10).ToList(),
                columnCount = cols.Count,
                levels
            };
        }
    }
}
