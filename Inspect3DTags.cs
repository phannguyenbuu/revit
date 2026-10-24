using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Inspect3DTags
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var view = uidoc.ActiveView;
            var view3D = view as View3D ?? new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

            // 1. Tags in view
            var tagsInView = new FilteredElementCollector(doc, view3D.Id)
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .Select(t => new {
                    id = t.Id.Value,
                    name = t.Name,
                    tagText = t.TagText,
                    category = t.Category?.Name
                })
                .ToList();

            // 2. TextNotes in view
            var textNotesInView = new FilteredElementCollector(doc, view3D.Id)
                .OfClass(typeof(TextNote))
                .Cast<TextNote>()
                .Select(tn => new {
                    id = tn.Id.Value,
                    text = tn.Text
                })
                .ToList();

            // 3. All tags in doc
            var allTags = new FilteredElementCollector(doc)
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .Select(t => new {
                    id = t.Id.Value,
                    ownerView = doc.GetElement(t.OwnerViewId)?.Name,
                    tagText = t.TagText,
                    cat = t.Category?.Name
                })
                .ToList();

            // 4. Check annotation visibility on view3D
            bool areAnnotationsHidden = false;
            try { areAnnotationsHidden = view3D.AreAnnotationCategoriesHidden; } catch {}

            return new {
                activeView = new { id = view?.Id.Value, name = view?.Name, type = view?.ViewType.ToString() },
                view3DName = view3D.Name,
                areAnnotationsHidden,
                tagsInView,
                textNotesInView,
                allTagsInDocCount = allTags.Count,
                allTagsSample = allTags.Take(15).ToList()
            };
        }
    }
}
