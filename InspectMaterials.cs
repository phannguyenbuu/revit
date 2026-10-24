using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Visual;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectMaterials
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var mats = new FilteredElementCollector(doc)
                .OfClass(typeof(Material))
                .Cast<Material>()
                .Select(m => new
                {
                    id = m.Id.Value,
                    name = m.Name,
                    color = m.Color != null ? $"RGB({m.Color.Red},{m.Color.Green},{m.Color.Blue})" : null,
                    assetId = m.AppearanceAssetId.Value
                })
                .ToList();

            var assets = new FilteredElementCollector(doc)
                .OfClass(typeof(AppearanceAssetElement))
                .Cast<AppearanceAssetElement>()
                .Select(a => new
                {
                    id = a.Id.Value,
                    name = a.Name
                })
                .ToList();

            return new
            {
                doc = doc.Title,
                materials = mats,
                appearanceAssets = assets
            };
        }
    }
}
