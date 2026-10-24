using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFacadeRefs
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var facade = doc.GetElement(new ElementId(2408695 > 0 ? 2391783 : 2391783)) as FamilyInstance;
            if (facade == null) return new { error = "Facade not found" };

            var refTypes = new List<string>();
            foreach (FamilyInstanceReferenceType rt in Enum.GetValues(typeof(FamilyInstanceReferenceType)))
            {
                var refs = facade.GetReferences(rt);
                if (refs != null && refs.Count > 0)
                {
                    refTypes.Add($"{rt}: {refs.Count}");
                }
            }

            var opt = new Options { ComputeReferences = true, View = view };
            var geom = facade.get_Geometry(opt);
            int solids = 0;
            int planarFaces = 0;
            if (geom != null)
            {
                foreach (var obj in geom)
                {
                    if (obj is Solid s && s.Faces != null)
                    {
                        solids++;
                        foreach (Face f in s.Faces)
                        {
                            if (f is PlanarFace pf && pf.Reference != null) planarFaces++;
                        }
                    }
                    else if (obj is GeometryInstance gi)
                    {
                        var instGeom = gi.GetInstanceGeometry();
                        if (instGeom != null)
                        {
                            foreach (var io in instGeom)
                            {
                                if (io is Solid s2 && s2.Faces != null)
                                {
                                    solids++;
                                    foreach (Face f in s2.Faces)
                                    {
                                        if (f is PlanarFace pf && pf.Reference != null) planarFaces++;
                                    }
                                }
                            }
                        }
                    }
                }
            }

            return new {
                id = facade.Id.Value,
                name = facade.Name,
                refTypes,
                solids,
                planarFaces
            };
        }
    }
}
