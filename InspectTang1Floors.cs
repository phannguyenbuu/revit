using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTang1Floors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var e2381562 = doc.GetElement(new ElementId(2381562L));

            var cats = new List<BuiltInCategory> {
                BuiltInCategory.OST_Floors,
                BuiltInCategory.OST_StructuralFoundation
            };

            var elemsInView = new FilteredElementCollector(doc, view.Id)
                .WherePasses(new ElementMulticategoryFilter(cats))
                .WhereElementIsNotElementType()
                .Select(e => new {
                    id = e.Id.Value,
                    name = e.Name,
                    cat = e.Category?.Name,
                    typeId = e.GetTypeId().Value,
                    typeName = doc.GetElement(e.GetTypeId())?.Name
                })
                .ToList();

            var vt = view.ViewTemplateId != ElementId.InvalidElementId ? doc.GetElement(view.ViewTemplateId) as View : null;
            var targetView = vt ?? view;

            var sfCat = Category.GetCategory(doc, BuiltInCategory.OST_StructuralFoundation);
            var fCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);

            var sfHidden = sfCat != null && targetView.CanCategoryBeHidden(sfCat.Id) ? targetView.GetCategoryHidden(sfCat.Id) : false;
            var fHidden = fCat != null && targetView.CanCategoryBeHidden(fCat.Id) ? targetView.GetCategoryHidden(fCat.Id) : false;

            var sfOverrides = sfCat != null ? targetView.GetCategoryOverrides(sfCat.Id) : null;
            var fOverrides = fCat != null ? targetView.GetCategoryOverrides(fCat.Id) : null;

            // Also check all floors in model with LevelId == view.GenLevel.Id
            var levelFloors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Where(f => f.LevelId == view.GenLevel?.Id)
                .Select(f => new {
                    id = f.Id.Value,
                    name = f.Name,
                    typeName = f.FloorType?.Name,
                    cat = f.Category?.Name
                })
                .ToList();

            var vr = view.GetViewRange();
            double cutOffset = vr.GetOffset(PlanViewPlane.CutPlane) * 304.8;
            double bottomOffset = vr.GetOffset(PlanViewPlane.BottomClipPlane) * 304.8;
            double depthOffset = vr.GetOffset(PlanViewPlane.ViewDepthPlane) * 304.8;

            var bbox2381562 = e2381562?.get_BoundingBox(null);
            var bboxInView = e2381562?.get_BoundingBox(view);

            var pOffset = e2381562?.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)?.AsDouble() * 304.8;
            
            // Check all parameters of e2381562
            var paramDict = new Dictionary<string, string>();
            if (e2381562 != null)
            {
                foreach (Parameter p in e2381562.Parameters)
                {
                    if (p.HasValue)
                    {
                        paramDict[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString();
                    }
                }
            }

            return new {
                e2381562 = new {
                    id = e2381562?.Id.Value,
                    name = e2381562?.Name,
                    cat = e2381562?.Category?.Name,
                    typeName = doc.GetElement(e2381562?.GetTypeId() ?? ElementId.InvalidElementId)?.Name,
                    bbox = bbox2381562 != null ? new { minZ = bbox2381562.Min.Z * 304.8, maxZ = bbox2381562.Max.Z * 304.8 } : null,
                    bboxInView = bboxInView != null ? new { minZ = bboxInView.Min.Z * 304.8, maxZ = bboxInView.Max.Z * 304.8 } : null,
                    pOffset = pOffset,
                    paramsVal = paramDict
                },
                viewRange = new {
                    cutOffset = cutOffset,
                    bottomOffset = bottomOffset,
                    depthOffset = depthOffset
                },
                elemsInView = elemsInView,
                structuralFoundation = new {
                    hidden = sfHidden,
                    surfaceForegroundPatternVisible = sfOverrides?.IsSurfaceForegroundPatternVisible
                },
                floors = new {
                    hidden = fHidden,
                    surfaceForegroundPatternVisible = fOverrides?.IsSurfaceForegroundPatternVisible
                }
            };
        }
    }
}
