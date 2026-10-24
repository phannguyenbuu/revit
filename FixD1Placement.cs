using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixD1Placement
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // Find Symbol cua thuy luc 2 canh - Đ1
            var doorSym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (doorSym == null)
            {
                var fCollector = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsElementType()
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(s => s.FamilyName.Contains("thuy luc", StringComparison.OrdinalIgnoreCase));
                doorSym = fCollector;
            }
            if (doorSym == null) return new { error = "Symbol cua thuy luc not found" };

            ElementId newDoorId = ElementId.InvalidElementId;

            using (var tx = new Transaction(doc, "Correct D1 Placement"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                if (!doorSym.IsActive) doorSym.Activate();

                // Delete misplaced doors
                try { doc.Delete(new ElementId(2363710L)); } catch { }
                try { doc.Delete(new ElementId(2363711L)); } catch { }
                try { doc.Delete(new ElementId(2363712L)); } catch { }

                // Place directly at targetPt (0.550, 6.600)
                var targetPt = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                var door = doc.Create.NewFamilyInstance(targetPt, doorSym, lvlTang1, StructuralType.NonStructural);
                newDoorId = door.Id;

                // Rotate 90 degrees around Z axis at targetPt
                var axis = Line.CreateBound(targetPt, targetPt + XYZ.BasisZ);
                ElementTransformUtils.RotateElement(doc, door.Id, axis, Math.PI / 2.0);

                var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                if (pMark != null && !pMark.IsReadOnly) pMark.Set("D1");

                doc.Regenerate();
                tx.Commit();
            }

            var placedDoor = doc.GetElement(newDoorId) as FamilyInstance;
            var lp = placedDoor?.Location as LocationPoint;
            var bb = placedDoor?.get_BoundingBox(null);

            // Export verification image
            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase));
            if (plan != null && uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

            if (newDoorId != ElementId.InvalidElementId)
            {
                uidoc.Selection.SetElementIds(new List<ElementId> { newDoorId });
            }

            string cleanImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_glass_hinge_clean.png";
            try
            {
                if (File.Exists(cleanImgPath)) File.Delete(cleanImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = cleanImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                doorId = newDoorId.Value,
                loc = lp != null ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null,
                rotation = lp?.Rotation,
                bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048, z = bb.Min.Z * 0.3048 } : null,
                bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048, z = bb.Max.Z * 0.3048 } : null,
                image = cleanImgPath
            };
        }
    }
}
