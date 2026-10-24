using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBat2ChieuFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("Cua_Kinh_Cuong_Luc_2Canh_Bat2Chieu", StringComparison.OrdinalIgnoreCase));

            if (fam == null) return new { error = "Family not found" };

            var symbols = fam.GetFamilySymbolIds().Select(sid =>
            {
                var s = doc.GetElement(sid) as FamilySymbol;
                return new { id = sid.Value, name = s?.Name };
            }).ToList();

            var fdoc = doc.EditFamily(fam);
            if (fdoc == null) return new { error = "Cannot edit family" };

            var curves = new FilteredElementCollector(fdoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => new
                {
                    type = c.GetType().Name,
                    subCat = c.LineStyle?.Name
                })
                .ToList();

            var forms = new FilteredElementCollector(fdoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f => new
                {
                    name = f.Name,
                    type = f.GetType().Name,
                    isSolid = f.IsSolid
                })
                .ToList();

            fdoc.Close(false);

            return new
            {
                familyName = fam.Name,
                placementType = fam.FamilyPlacementType.ToString(),
                symbols = symbols,
                curveCount = curves.Count,
                curves = curves,
                forms = forms
            };
        }
    }
}
