using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWestAndEastDetails
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. West Face Elements (X <= 1500)
            var westElements = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_GenericModel
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return null;
                    double minX = bb.Min.X * FT_TO_MM;
                    double maxX = bb.Max.X * FT_TO_MM;
                    if (minX > 1500) return null;

                    var fi = e as FamilyInstance;
                    var leftRefs = fi?.GetReferences(FamilyInstanceReferenceType.Left)?.Count ?? 0;
                    var rightRefs = fi?.GetReferences(FamilyInstanceReferenceType.Right)?.Count ?? 0;
                    var frontRefs = fi?.GetReferences(FamilyInstanceReferenceType.Front)?.Count ?? 0;
                    var backRefs = fi?.GetReferences(FamilyInstanceReferenceType.Back)?.Count ?? 0;

                    return new {
                        id = e.Id.Value,
                        cat = e.Category.Name,
                        name = e.Name,
                        family = fi?.Symbol.FamilyName,
                        minX = Math.Round(minX, 1),
                        maxX = Math.Round(maxX, 1),
                        minY = Math.Round(bb.Min.Y * FT_TO_MM, 1),
                        maxY = Math.Round(bb.Max.Y * FT_TO_MM, 1),
                        leftRefs, rightRefs, frontRefs, backRefs
                    };
                })
                .Where(x => x != null)
                .OrderBy(x => x.minY)
                .ToList();

            // 2. East Face Elements (X >= 36500)
            var eastElements = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> {
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Floors
                }))
                .WhereElementIsNotElementType()
                .Select(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return null;
                    double minX = bb.Min.X * FT_TO_MM;
                    double maxX = bb.Max.X * FT_TO_MM;
                    if (maxX < 36500) return null;

                    var fi = e as FamilyInstance;
                    var leftRefs = fi?.GetReferences(FamilyInstanceReferenceType.Left)?.Count ?? 0;
                    var rightRefs = fi?.GetReferences(FamilyInstanceReferenceType.Right)?.Count ?? 0;
                    var frontRefs = fi?.GetReferences(FamilyInstanceReferenceType.Front)?.Count ?? 0;
                    var backRefs = fi?.GetReferences(FamilyInstanceReferenceType.Back)?.Count ?? 0;

                    return new {
                        id = e.Id.Value,
                        cat = e.Category.Name,
                        name = e.Name,
                        family = fi?.Symbol.FamilyName,
                        minX = Math.Round(minX, 1),
                        maxX = Math.Round(maxX, 1),
                        minY = Math.Round(bb.Min.Y * FT_TO_MM, 1),
                        maxY = Math.Round(bb.Max.Y * FT_TO_MM, 1),
                        leftRefs, rightRefs, frontRefs, backRefs
                    };
                })
                .Where(x => x != null)
                .OrderBy(x => x.minY)
                .ToList();

            return new {
                westElements,
                eastElements
            };
        }
    }
}
