using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDeepElements
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No document" };

                // 1. All Sections in doc
                var allSections = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .Select(s => new {
                        id = s.Id.Value,
                        name = s.Name,
                        viewType = s.ViewType.ToString(),
                        isCallout = s.IsCallout
                    }).ToList();

                // 2. All Callouts in doc (ViewSection or ViewPlan with IsCallout)
                var allCallouts = new FilteredElementCollector(doc)
                    .OfClass(typeof(View))
                    .Cast<View>()
                    .Where(v => v.IsCallout)
                    .Select(v => new {
                        id = v.Id.Value,
                        name = v.Name,
                        viewType = v.ViewType.ToString(),
                        genLevel = v.GenLevel?.Name ?? ""
                    }).ToList();

                // 3. All Floor Plan views
                var viewPlans = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .Where(v => !v.IsTemplate)
                    .Select(v => new {
                        id = v.Id.Value,
                        name = v.Name,
                        levelName = v.GenLevel?.Name ?? "",
                        levelId = v.GenLevel?.Id.Value ?? -1,
                        isCallout = v.IsCallout
                    }).ToList();

                // 4. Dimensions on Tang 1 (ID 312)
                var view1 = doc.GetElement(new ElementId(312)) as View;
                var dimsOnV1 = new List<object>();
                if (view1 != null)
                {
                    var dims = new FilteredElementCollector(doc, view1.Id)
                        .OfClass(typeof(Dimension))
                        .Cast<Dimension>()
                        .ToList();
                    foreach (var d in dims)
                    {
                        dimsOnV1.Add(new {
                            id = d.Id.Value,
                            name = d.Name,
                            dimType = d.DimensionType.Name,
                            numSegs = d.NumberOfSegments
                        });
                    }
                }

                // 5. Inspect Slabs / Floors
                var allFloors = new FilteredElementCollector(doc)
                    .OfClass(typeof(Floor))
                    .Cast<Floor>()
                    .Select(f => {
                        var lvl = doc.GetElement(f.LevelId) as Level;
                        var ft = f.FloorType;
                        return new {
                            id = f.Id.Value,
                            name = f.Name,
                            floorTypeName = ft.Name,
                            levelName = lvl?.Name ?? "",
                            levelId = f.LevelId.Value
                        };
                    }).ToList();

                // 6. Door tags on all views
                var doorTags = new FilteredElementCollector(doc)
                    .OfClass(typeof(IndependentTag))
                    .Cast<IndependentTag>()
                    .Where(t => t.Category != null && t.Category.Id.Value == (long)BuiltInCategory.OST_DoorTags)
                    .Select(t => new {
                        id = t.Id.Value,
                        viewId = t.OwnerViewId.Value,
                        viewName = doc.GetElement(t.OwnerViewId)?.Name ?? "",
                        tagText = t.TagText
                    }).ToList();

                return new {
                    allSections,
                    allCallouts,
                    viewPlans,
                    dimsCount = dimsOnV1.Count,
                    dimsOnV1,
                    allFloors,
                    doorTagsCount = doorTags.Count,
                    doorTags
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
