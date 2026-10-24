using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class WarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failureMessages = failuresAccessor.GetFailureMessages();
            foreach (var failureMessage in failureMessages)
            {
                if (failureMessage.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(failureMessage);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class DiagnoseAndFixFloor600
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No active ViewPlan" };

                var fpe600 = doc.GetElement(new ElementId(8574L)) as FillPatternElement
                    ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "600 x 600mm");

                var e2381562 = doc.GetElement(new ElementId(2381562L));

                // Check View Template overrides on Structural Foundations
                var vt = view.ViewTemplateId != ElementId.InvalidElementId ? doc.GetElement(view.ViewTemplateId) as ViewPlan : null;
                var sfCat = Category.GetCategory(doc, BuiltInCategory.OST_StructuralFoundation);

                bool sfVisibleInTemplate = false;
                bool sfPatternVisibleInTemplate = false;

                if (vt != null && sfCat != null)
                {
                    sfVisibleInTemplate = !vt.GetCategoryHidden(sfCat.Id);
                    var ov = vt.GetCategoryOverrides(sfCat.Id);
                    sfPatternVisibleInTemplate = ov.IsSurfaceForegroundPatternVisible;
                }

                // Check geometry of 2381562
                var optGeom = new Options { View = view, ComputeReferences = true };
                var geom = e2381562?.get_Geometry(optGeom);
                int solidCountWithView = 0;
                if (geom != null)
                {
                    foreach (var obj in geom)
                    {
                        if (obj is Solid s && s.Volume > 0) solidCountWithView++;
                    }
                }

                var optGeomModel = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
                var geomModel = e2381562?.get_Geometry(optGeomModel);
                int solidCountModel = 0;
                List<PlanarFace> topFaces = new List<PlanarFace>();
                if (geomModel != null)
                {
                    foreach (var obj in geomModel)
                    {
                        if (obj is Solid s && s.Volume > 0)
                        {
                            solidCountModel++;
                            foreach (Face f in s.Faces)
                            {
                                if (f is PlanarFace pf && pf.FaceNormal.IsAlmostEqualTo(XYZ.BasisZ))
                                {
                                    topFaces.Add(pf);
                                }
                            }
                        }
                    }
                }

                var elemType = doc.GetElement(e2381562.GetTypeId());
                var matIds = e2381562?.GetMaterialIds(false) ?? new List<ElementId>();
                var elemMatNames = matIds.Select(id => {
                    var m = doc.GetElement(id) as Material;
                    var pat = m?.SurfaceForegroundPatternId != ElementId.InvalidElementId 
                        ? (doc.GetElement(m.SurfaceForegroundPatternId) as FillPatternElement)?.Name : null;
                    return new { id = id.Value, name = m?.Name, pattern = pat };
                }).ToList();

                // Check type compound structure
                var ft = elemType as FloorType;
                var ftMatNames = new List<object>();
                if (ft != null && ft.GetCompoundStructure() != null)
                {
                    foreach (var l in ft.GetCompoundStructure().GetLayers())
                    {
                        var m = doc.GetElement(l.MaterialId) as Material;
                        var pat = m?.SurfaceForegroundPatternId != ElementId.InvalidElementId 
                            ? (doc.GetElement(m.SurfaceForegroundPatternId) as FillPatternElement)?.Name : null;
                        ftMatNames.Add(new { matId = l.MaterialId.Value, name = m?.Name, pattern = pat });
                    }
                }

                return new
                {
                    csharpType = e2381562?.GetType().FullName,
                    isFloor = (e2381562 is Floor),
                    typeCsharpType = elemType?.GetType().FullName,
                    isFloorType = (elemType is FloorType),
                    fpe600Found = fpe600?.Name,
                    fpe600Id = fpe600?.Id.Value,
                    e2381562Category = e2381562?.Category?.Name,
                    elemMaterials = elemMatNames,
                    typeMaterials = ftMatNames,
                    sfVisibleInTemplate = sfVisibleInTemplate,
                    sfPatternVisibleInTemplate = sfPatternVisibleInTemplate,
                    solidCountWithView = solidCountWithView,
                    solidCountModel = solidCountModel,
                    topFacesCount = topFaces.Count,
                    topFaceZ = topFaces.Count > 0 ? topFaces[0].Origin.Z * 304.8 : 0
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
