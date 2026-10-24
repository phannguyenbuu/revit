using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectChauRuaFamily
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var symbol = doc.GetElement(new ElementId(814154)) as FamilySymbol;
            if (symbol == null) return new { error = "Symbol 814154 not found" };

            var famDoc = doc.EditFamily(symbol.Family);
            if (famDoc == null) return new { error = "Could not edit family" };

            var solids = new List<object>();
            foreach (var elem in new FilteredElementCollector(famDoc).WherePasses(new ElementMulticategoryFilter(new BuiltInCategory[] {
                BuiltInCategory.OST_PlumbingFixtures,
                BuiltInCategory.OST_GenericModel
            })))
            {
                var geo = elem.get_Geometry(new Options());
                if (geo != null)
                {
                    foreach (var obj in geo)
                    {
                        if (obj is Solid s && s.Volume > 0.0001)
                        {
                            var bb = s.GetBoundingBox();
                            solids.Add(new
                            {
                                elemId = elem.Id.Value,
                                elemType = elem.GetType().Name,
                                vol = s.Volume * 0.0283168,
                                zMin = bb.Min.Z * 304.8,
                                zMax = bb.Max.Z * 304.8
                            });
                        }
                    }
                }
            }

            var refPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ReferencePlane))
                .Cast<ReferencePlane>()
                .Select(rp => new { name = rp.Name, bubble = $"[{rp.BubbleEnd.X*304.8:F1}, {rp.BubbleEnd.Y*304.8:F1}, {rp.BubbleEnd.Z*304.8:F1}]" })
                .ToList();

            var famParams = famDoc.FamilyManager.Parameters
                .Cast<FamilyParameter>()
                .Select(p => new { name = p.Definition.Name, isInstance = p.IsInstance })
                .ToList();

            famDoc.Close(false);

            return new
            {
                solids,
                refPlanes,
                famParams
            };
        }
    }
}
