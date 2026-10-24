using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCopyTasks
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No document" };

            // 1. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new {
                    id = l.Id.Value,
                    name = l.Name,
                    elevation_m = l.Elevation * 0.3048
                }).ToList();

            // 2. Floor plan views
            var floorPlans = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(vp => !vp.IsTemplate && vp.ViewType == ViewType.FloorPlan)
                .Select(vp => new {
                    id = vp.Id.Value,
                    name = vp.Name,
                    levelId = vp.GenLevel?.Id.Value ?? -1,
                    levelName = vp.GenLevel?.Name ?? ""
                }).ToList();

            // Find Tang 1 view
            var tang1View = floorPlans.FirstOrDefault(vp => vp.name.ToUpper().Contains("TẦNG 1") || vp.name.ToUpper().Contains("TANG 1"));

            // 3. Floors / Slabs
            var floors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .Cast<Floor>()
                .Select(f => {
                    var lvl = doc.GetElement(f.LevelId) as Level;
                    var paramOffset = f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    return new {
                        id = f.Id.Value,
                        name = f.Name,
                        floorType = f.FloorType.Name,
                        levelId = f.LevelId.Value,
                        levelName = lvl?.Name ?? "",
                        offset_mm = paramOffset != null ? paramOffset.AsDouble() * 304.8 : 0.0
                    };
                }).ToList();

            // 4. Plumbing Fixtures
            var plumbing = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_PlumbingFixtures)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(fi => {
                    var lvl = doc.GetElement(fi.LevelId) as Level;
                    var locPt = fi.Location as LocationPoint;
                    return new {
                        id = fi.Id.Value,
                        name = fi.Name,
                        symbol = fi.Symbol.Name,
                        levelId = fi.LevelId.Value,
                        levelName = lvl?.Name ?? "",
                        point_mm = locPt != null ? new {
                            x = locPt.Point.X * 304.8,
                            y = locPt.Point.Y * 304.8,
                            z = locPt.Point.Z * 304.8
                        } : null
                    };
                }).ToList();

            // 5. Annotations on Tang 1
            int dimCount = 0;
            var dimSample = new List<object>();
            int sectionCount = 0;
            int calloutCount = 0;

            if (tang1View != null)
            {
                var view1 = doc.GetElement(new ElementId(tang1View.id)) as View;
                if (view1 != null)
                {
                    var dims = new FilteredElementCollector(doc, view1.Id)
                        .OfCategory(BuiltInCategory.OST_Dimensions)
                        .WhereElementIsNotElementType()
                        .Cast<Dimension>()
                        .ToList();
                    dimCount = dims.Count;
                    dimSample = dims.Take(5).Select(d => (object)new {
                        id = d.Id.Value,
                        dimType = d.DimensionType.Name,
                        numSegments = d.NumberOfSegments
                    }).ToList();

                    var sections = new FilteredElementCollector(doc, view1.Id)
                        .OfCategory(BuiltInCategory.OST_Sections)
                        .WhereElementIsNotElementType()
                        .ToList();
                    sectionCount = sections.Count;

                    var callouts = new FilteredElementCollector(doc, view1.Id)
                        .OfCategory(BuiltInCategory.OST_Callouts)
                        .WhereElementIsNotElementType()
                        .ToList();
                    calloutCount = callouts.Count;
                }
            }

            // 6. Doors & Door Tags
            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(d => {
                    var lvl = doc.GetElement(d.LevelId) as Level;
                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        symbol = d.Symbol.Name,
                        levelName = lvl?.Name ?? "",
                        levelId = d.LevelId.Value
                    };
                }).ToList();

            var doorTags = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_DoorTags)
                .WhereElementIsNotElementType()
                .Cast<IndependentTag>()
                .Select(dt => new {
                    id = dt.Id.Value,
                    viewId = dt.OwnerViewId.Value
                }).ToList();

            // Door tag family symbols
            var doorTagSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_DoorTags)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => new {
                    id = s.Id.Value,
                    name = s.Name,
                    familyName = s.FamilyName
                }).ToList();

            return new {
                levels,
                floorPlans,
                floors,
                plumbingCount = plumbing.Count,
                plumbingSample = plumbing.Take(10).ToList(),
                tang1Annotations = new {
                    tang1View,
                    dimCount,
                    dimSample,
                    sectionCount,
                    calloutCount
                },
                doorsCount = doors.Count,
                doorsByLevel = doors.GroupBy(d => d.levelName).ToDictionary(g => g.Key, g => g.Count()),
                doorTagsCount = doorTags.Count,
                doorTagSymbols
            };
        }
    }
}
