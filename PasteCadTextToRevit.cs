using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class PasteCadTextToRevit
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, message = "Không tìm thấy Revit Document." };

            var methodArgs = args.TryGetProperty("args", out var n) && n.ValueKind == JsonValueKind.Object ? n : args;

            long targetViewId = 2409349L; // MẶT BẰNG TẦNG 4
            if (methodArgs.TryGetProperty("viewId", out var vProp) && vProp.GetInt64() > 0)
            {
                targetViewId = vProp.GetInt64();
            }

            var view = doc.GetElement(new ElementId(targetViewId)) as View;
            if (view == null)
            {
                view = uidoc.ActiveView;
            }
            if (view == null)
            {
                return new { success = false, message = $"Không tìm thấy view ID {targetViewId}." };
            }

            // Text note type
            long textTypeIdVal = 361L; // 2.5mm Arial default
            if (methodArgs.TryGetProperty("textTypeId", out var ttProp) && ttProp.GetInt64() > 0)
            {
                textTypeIdVal = ttProp.GetInt64();
            }

            var allTextTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .ToList();

            var textType = allTextTypes.FirstOrDefault(t => t.Id.Value == textTypeIdVal) 
                        ?? allTextTypes.FirstOrDefault(t => t.Name == "2.5mm Arial")
                        ?? allTextTypes.FirstOrDefault(t => t.Name.Contains("Arial"))
                        ?? allTextTypes.First();

            if (!methodArgs.TryGetProperty("items", out var itemsElem) || itemsElem.ValueKind != JsonValueKind.Array)
            {
                return new { success = false, message = "Danh sách text items không hợp lệ hoặc rỗng." };
            }

            const double MM_TO_FEET = 1.0 / 304.8;
            var createdIds = new List<long>();
            var createdInfos = new List<object>();

            using (Transaction trans = new Transaction(doc, "Paste CAD Texts to Floor 4"))
            {
                trans.Start();

                foreach (var item in itemsElem.EnumerateArray())
                {
                    try
                    {
                        string text = item.GetProperty("text").GetString() ?? "";
                        if (string.IsNullOrWhiteSpace(text)) continue;

                        double xMm = item.GetProperty("x").GetDouble();
                        double yMm = item.GetProperty("y").GetDouble();

                        XYZ pos = new XYZ(xMm * MM_TO_FEET, yMm * MM_TO_FEET, 0.0);

                        TextNoteOptions options = new TextNoteOptions(textType.Id)
                        {
                            HorizontalAlignment = HorizontalTextAlignment.Center,
                            Rotation = 0.0
                        };

                        TextNote tn = TextNote.Create(doc, view.Id, pos, text, options);
                        if (tn != null)
                        {
                            createdIds.Add(tn.Id.Value);
                            createdInfos.Add(new {
                                id = tn.Id.Value,
                                text = text,
                                x = xMm,
                                y = yMm
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        // Record failure for this note
                    }
                }

                trans.Commit();
            }

            // Set selection in active view
            try
            {
                if (createdIds.Count > 0 && uidoc != null)
                {
                    var elemIds = createdIds.Select(id => new ElementId(id)).ToList();
                    uidoc.Selection.SetElementIds(elemIds);
                }
            }
            catch { }

            return new {
                success = true,
                count = createdIds.Count,
                viewId = view.Id.Value,
                viewName = view.Name,
                textTypeName = textType.Name,
                createdIds = createdIds,
                items = createdInfos
            };
        }
    }
}
