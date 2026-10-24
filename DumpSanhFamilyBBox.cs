using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpSanhFamilyBBox
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            string famPath = @"D:\Dropbox\_Documents\RevitAI\Sanh_Chinh_3dsMax.rfa";
            var famDoc = uiapp.Application.OpenDocumentFile(famPath);
            if (famDoc == null) return new { error = "Cannot open family doc" };
            
            var imp = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .FirstOrDefault();

            var bb = imp?.get_BoundingBox(null);
            double ft2mm = 304.8;
            var res = new {
                min = bb != null ? new { x = bb.Min.X * ft2mm, y = bb.Min.Y * ft2mm, z = bb.Min.Z * ft2mm } : null,
                max = bb != null ? new { x = bb.Max.X * ft2mm, y = bb.Max.Y * ft2mm, z = bb.Max.Z * ft2mm } : null
            };
            famDoc.Close(false);
            return res;
        }
    }
}
