using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectErowdFamilyDoc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(1654212L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 1654212 not found" };

            var fam = sym.Family;
            var famDoc = doc.EditFamily(fam);

            var curves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => new
                {
                    type = c.GetType().Name,
                    subCat = c.LineStyle?.Name,
                    isSymbolic = c is SymbolicCurve
                })
                .ToList();

            var forms = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f => new
                {
                    name = f.Name,
                    type = f.GetType().Name,
                    isSolid = f.IsSolid
                })
                .ToList();

            var fParams = famDoc.FamilyManager.Parameters.Cast<FamilyParameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    isInstance = p.IsInstance
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                familyName = fam.Name,
                placementType = fam.FamilyPlacementType.ToString(),
                curveCount = curves.Count,
                curves,
                formCount = forms.Count,
                forms,
                parameters = fParams
            };
        }
    }
}
