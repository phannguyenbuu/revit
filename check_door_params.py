import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

code = """
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorParams
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var dWood = doc.GetElement(new ElementId(2360902L)) as FamilyInstance;
            var dEuro = doc.GetElement(new ElementId(2361179L)) as FamilyInstance;

            var getInfo = new Func<FamilyInstance, object>(d => {
                if (d == null) return null;
                var pSill = d.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                var pHead = d.get_Parameter(BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM);
                return new {
                    id = d.Id.Value,
                    name = d.Name,
                    family = d.Symbol.FamilyName,
                    handFlipped = d.HandFlipped,
                    facingFlipped = d.FacingFlipped,
                    sillHeightMm = pSill != null ? pSill.AsDouble() * FT2M * 1000 : 0,
                    headHeightMm = pHead != null ? pHead.AsDouble() * FT2M * 1000 : 0
                };
            });

            return new {
                wood = getInfo(dWood),
                euro = getInfo(dEuro)
            };
        }
    }
}
"""
print("Code ready")
