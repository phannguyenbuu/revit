using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class GeometryInspector
    {
        public static object InspectDetails(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var elements = new FilteredElementCollector(doc)
                .WhereElementIsNotElementType()
                .ToList();

            var summary = new List<object>();

            var opt = new Options { ComputeReferences = true };

            foreach (var elem in elements)
            {
                if (elem is GenericForm form)
                {
                    var geom = form.get_Geometry(opt);
                    int solidCount = 0;
                    int faceCount = 0;
                    var paintedFaces = new List<string>();

                    if (geom != null)
                    {
                        foreach (var gObj in geom)
                        {
                            if (gObj is Solid solid && solid.Faces.Size > 0)
                            {
                                solidCount++;
                                faceCount += solid.Faces.Size;
                                foreach (Face face in solid.Faces)
                                {
                                    if (doc.IsPainted(elem.Id, face))
                                    {
                                        var paintMatId = doc.GetPaintedMaterial(elem.Id, face);
                                        var paintMat = doc.GetElement(paintMatId) as Material;
                                        paintedFaces.Add($"{paintMat?.Name} ({paintMatId.Value})");
                                    }
                                }
                            }
                        }
                    }

                    var matParam = form.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM);
                    var matId = matParam?.AsElementId();
                    var mat = matId != null && matId != ElementId.InvalidElementId ? doc.GetElement(matId) as Material : null;

                    summary.Add(new
                    {
                        id = elem.Id.Value,
                        name = elem.Name,
                        type = elem.GetType().Name,
                        material = mat?.Name,
                        materialColor = mat?.Color != null ? $"{mat.Color.Red},{mat.Color.Green},{mat.Color.Blue}" : null,
                        solidCount,
                        faceCount,
                        paintedFaces
                    });
                }
            }

            return new
            {
                doc = doc.Title,
                count = summary.Count,
                forms = summary
            };
        }
    }
}
