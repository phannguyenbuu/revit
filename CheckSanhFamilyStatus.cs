using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckSanhFamilyStatus
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Check all families matching Sanh / Hien / Generic
            var allFamilies = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .ToList();

            var matchingFamilies = allFamilies
                .Where(f => f.Name.IndexOf("sanh", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            f.Name.IndexOf("hien", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            f.Name.IndexOf("porch", StringComparison.OrdinalIgnoreCase) >= 0)
                .Select(f => new
                {
                    id = f.Id.Value,
                    name = f.Name,
                    category = f.FamilyCategory?.Name,
                    symbols = f.GetFamilySymbolIds().Select(sid => {
                        var sym = doc.GetElement(sid) as FamilySymbol;
                        return new { id = sid.Value, name = sym?.Name, isActive = sym?.IsActive };
                    }).ToList()
                })
                .ToList();

            // 2. Check all instances of Generic Models or matching family instances
            var allInstances = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => fi.Symbol?.Family?.Name.IndexOf("sanh", StringComparison.OrdinalIgnoreCase) >= 0 ||
                             fi.Symbol?.Family?.Name.IndexOf("hien", StringComparison.OrdinalIgnoreCase) >= 0 ||
                             fi.Symbol?.Family?.Name.IndexOf("porch", StringComparison.OrdinalIgnoreCase) >= 0 ||
                             fi.Name.IndexOf("sanh", StringComparison.OrdinalIgnoreCase) >= 0)
                .Select(fi => {
                    var loc = fi.Location as LocationPoint;
                    var pt = loc != null ? loc.Point : null;
                    var bb = fi.get_BoundingBox(null);
                    return new
                    {
                        id = fi.Id.Value,
                        name = fi.Name,
                        familyName = fi.Symbol?.Family?.Name,
                        level = doc.GetElement(fi.LevelId)?.Name,
                        point = pt != null ? new { x = pt.X * 304.8, y = pt.Y * 304.8, z = pt.Z * 304.8 } : null,
                        bbox = bb != null ? new {
                            minX = bb.Min.X * 304.8, minY = bb.Min.Y * 304.8, minZ = bb.Min.Z * 304.8,
                            maxX = bb.Max.X * 304.8, maxY = bb.Max.Y * 304.8, maxZ = bb.Max.Z * 304.8
                        } : null,
                        isPinned = fi.Pinned
                    };
                })
                .ToList();

            // 3. Check active view visibility for Generic Models
            var view = doc.ActiveView;
            var genericCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel);
            bool isGenericHiddenInView = false;
            if (view != null && genericCat != null)
            {
                try { isGenericHiddenInView = view.GetCategoryHidden(genericCat.Id); } catch {}
            }

            // Also check all 3D views
            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .Where(v => !v.IsTemplate)
                .Select(v => {
                    bool catHidden = false;
                    try {
                        catHidden = v.GetCategoryHidden(genericCat.Id);
                    } catch {}
                    return new {
                        id = v.Id.Value,
                        name = v.Name,
                        isGenericModelHidden = catHidden
                    };
                })
                .ToList();

            return new
            {
                totalFamiliesInDoc = allFamilies.Count,
                matchingFamilies,
                placedInstances = allInstances,
                activeView = new { id = view?.Id.Value, name = view?.Name, type = view?.ViewType.ToString() },
                views3D = view3Ds
            };
        }
    }
}
