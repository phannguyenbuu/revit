using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGainAndLines
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var view = uidoc.ActiveView;

            // 1. Current selection
            var selIds = uidoc.Selection.GetElementIds();
            var selectedElements = new List<object>();
            foreach (var id in selIds)
            {
                var el = doc.GetElement(id);
                if (el != null)
                {
                    selectedElements.Add(new
                    {
                        id = id.Value,
                        category = el.Category?.Name,
                        type = el.GetType().Name,
                        name = el.Name
                    });
                }
            }

            // 2. Text notes in active view
            var textNotes = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(TextNote))
                .Cast<TextNote>()
                .Select(t => new
                {
                    id = t.Id.Value,
                    text = t.Text,
                    coordM = new { x = t.Coord.X * FT2M, y = t.Coord.Y * FT2M, z = t.Coord.Z * FT2M }
                })
                .ToList();

            // 3. CurveElements (Detail lines / Model lines) in active view
            var curveElements = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c =>
                {
                    var curve = c.GeometryCurve;
                    var p0 = curve.GetEndPoint(0);
                    var p1 = curve.GetEndPoint(1);
                    var lineStyle = c.LineStyle;
                    string styleName = lineStyle?.Name ?? "Unknown";

                    // Check color if available
                    string colorStr = "";
                    if (lineStyle is GraphicsStyle gs && gs.GraphicsStyleCategory != null)
                    {
                        var col = gs.GraphicsStyleCategory.LineColor;
                        colorStr = $"RGB({col.Red},{col.Green},{col.Blue})";
                    }

                    return new
                    {
                        id = c.Id.Value,
                        type = c.GetType().Name,
                        style = styleName,
                        color = colorStr,
                        p0M = new { x = p0.X * FT2M, y = p0.Y * FT2M },
                        p1M = new { x = p1.X * FT2M, y = p1.Y * FT2M },
                        lengthM = curve.Length * FT2M
                    };
                })
                .ToList();

            // 4. Wall types in document
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .Select(w => new
                {
                    id = w.Id.Value,
                    name = w.Name,
                    widthM = w.Width * FT2M
                })
                .ToList();

            // 5. Cad Imports
            var cadImports = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .Select(i => new
                {
                    id = i.Id.Value,
                    isLinked = i.IsLinked,
                    category = i.Category?.Name
                })
                .ToList();

            return new
            {
                viewName = view.Name,
                selected = selectedElements,
                textNotes = textNotes,
                curveCount = curveElements.Count,
                curves = curveElements,
                wallTypes = wallTypes,
                cadImports = cadImports
            };
        }
    }
}
