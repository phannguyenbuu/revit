using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class InspectCurrentLinks
    {
        public static object Run(UIApplication uiapp, dynamic args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu nào đang mở!" };

            var linkTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkType))
                .Cast<RevitLinkType>()
                .Select(lt => new
                {
                    id = lt.Id.Value,
                    name = lt.Name,
                    isLoaded = RevitLinkType.IsLoaded(doc, lt.Id),
                    path = lt.GetExternalFileReference()?.GetPath() != null 
                        ? ModelPathUtils.ConvertModelPathToUserVisiblePath(lt.GetExternalFileReference().GetPath())
                        : ""
                })
                .ToList();

            var linkInstances = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkInstance))
                .Cast<RevitLinkInstance>()
                .Select(li => new
                {
                    id = li.Id.Value,
                    name = li.Name,
                    typeId = li.GetTypeId().Value,
                    typeName = doc.GetElement(li.GetTypeId())?.Name
                })
                .ToList();

            return new
            {
                success = true,
                docTitle = doc.Title,
                linkTypeCount = linkTypes.Count,
                linkTypes,
                linkInstanceCount = linkInstances.Count,
                linkInstances
            };
        }
    }
}
