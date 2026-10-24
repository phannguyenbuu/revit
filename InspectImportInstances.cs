using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectImportInstances
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;

            var imports = new FilteredElementCollector(doc)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .Select(i => new {
                    id = i.Id.Value,
                    isLinked = i.IsLinked,
                    ownerViewId = i.OwnerViewId.Value,
                    ownerViewName = doc.GetElement(i.OwnerViewId)?.Name,
                    pinned = i.Pinned,
                    category = i.Category?.Name,
                    typeId = i.GetTypeId().Value,
                    typeName = doc.GetElement(i.GetTypeId())?.Name
                })
                .ToList();

            // Also check CAD Link types
            var cadTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(CADLinkType))
                .Cast<CADLinkType>()
                .Select(t => new {
                    id = t.Id.Value,
                    name = t.Name,
                    isExternal = t.IsExternalFileReference()
                })
                .ToList();

            // Check existing TextNote types in project
            var textTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .Select(t => new {
                    id = t.Id.Value,
                    name = t.Name
                })
                .ToList();

            return new { imports, cadTypes, textTypes };
        }
    }
}
