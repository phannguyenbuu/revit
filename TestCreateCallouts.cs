using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCreateCallouts
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var vftList = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .Select(vft => new {
                    id = vft.Id.Value,
                    name = vft.Name,
                    viewFamily = vft.ViewFamily.ToString(),
                    isValid = ViewSection.IsViewFamilyTypeValidForCallout(doc, vft.Id, view.Id)
                })
                .ToList();

            return new {
                viewId = view.Id.Value,
                viewName = view.Name,
                validVfts = vftList.Where(x => x.isValid).ToList(),
                allVfts = vftList
            };
        }
    }
}
