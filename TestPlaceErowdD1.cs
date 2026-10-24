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
    public static class TestPlaceErowdD1
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var levels = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            if (wall == null) return new { error = "Wall 2362083 not found" };

            // Find source symbol 1654212: CỬA 2 CÁNH EROWD KO 1600x2200mm
            var srcSym = doc.GetElement(new ElementId(1654212L)) as FamilySymbol;
            if (srcSym == null) return new { error = "Source symbol 1654212 not found" };

            ElementId newDoorId = ElementId.InvalidElementId;
            ElementId newSymId = ElementId.InvalidElementId;

            using (var tx = new Transaction(doc, "Place Erowd D1 Door"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // Delete any misplaced doors
                try { doc.Delete(new ElementId(2363710L)); } catch { }
                try { doc.Delete(new ElementId(2363711L)); } catch { }
                try { doc.Delete(new ElementId(2363712L)); } catch { }
                try { doc.Delete(new ElementId(2362084L)); } catch { }

                // Delete existing opening 2362102 so the door cuts cleanly
                try { doc.Delete(new ElementId(2362102L)); } catch { }

                // Duplicate symbol to create type D1
                string typeName = "D1 - Kính Cường Lực 10mm 2 Cánh";
                var fam = srcSym.Family;
                FamilySymbol d1Sym = null;
                foreach (var sid in fam.GetFamilySymbolIds())
                {
                    var s = doc.GetElement(sid) as FamilySymbol;
                    if (s != null && s.Name.Equals(typeName, StringComparison.OrdinalIgnoreCase))
                    {
                        d1Sym = s;
                        break;
                    }
                }

                if (d1Sym == null)
                {
                    d1Sym = srcSym.Duplicate(typeName) as FamilySymbol;
                }

                if (d1Sym != null)
                {
                    newSymId = d1Sym.Id;
                    if (!d1Sym.IsActive) d1Sym.Activate();

                    // Set Width = 1900 mm = 1.9m
                    var pW = d1Sym.get_Parameter(BuiltInParameter.DOOR_WIDTH)
                          ?? d1Sym.LookupParameter("Width")
                          ?? d1Sym.LookupParameter("Rộng");
                    if (pW != null && !pW.IsReadOnly) pW.Set(1.900 * M2FT);

                    // Set Height = 2700 mm = 2.7m
                    var pH = d1Sym.get_Parameter(BuiltInParameter.DOOR_HEIGHT)
                          ?? d1Sym.LookupParameter("Height")
                          ?? d1Sym.LookupParameter("Cao");
                    if (pH != null && !pH.IsReadOnly) pH.Set(2.700 * M2FT);

                    // Set Description
                    var pDesc = d1Sym.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION);
                    if (pDesc != null && !pDesc.IsReadOnly) pDesc.Set("Cửa kính cường lực 10mm 2 cánh bản lề sàn bật 2 chiều (D1)");

                    doc.Regenerate();

                    // Place door on wall at (0.550, 6.600)
                    var doorLoc = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                    var door = doc.Create.NewFamilyInstance(doorLoc, d1Sym, wall, lvlTang1, StructuralType.NonStructural);
                    newDoorId = door.Id;

                    // Set Mark parameter to "D1"
                    var pMark = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                    if (pMark != null && !pMark.IsReadOnly) pMark.Set("D1");

                    doc.Regenerate();
                }

                tx.Commit();
            }

            var placedDoor = doc.GetElement(newDoorId) as FamilyInstance;
            var lp = placedDoor?.Location as LocationPoint;
            var bb = placedDoor?.get_BoundingBox(null);

            // Switch to MẶT BẰNG TẦNG 1 floor plan
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

            // Zoom to target area
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == plan.Id);
            var minPt = new XYZ(-1.5 * M2FT, 3.5 * M2FT, 0.0);
            var maxPt = new XYZ(4.0 * M2FT, 9.5 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPt, maxPt);

            string planImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_erowd_crop.png";
            try
            {
                if (File.Exists(planImgPath)) File.Delete(planImgPath);

                var expOpt = new ImageExportOptions
                {
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }

            return new
            {
                success = true,
                doorId = newDoorId.Value,
                symId = newSymId.Value,
                loc = lp != null ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048, z = lp.Point.Z * 0.3048 } : null,
                facing = placedDoor != null ? new { x = placedDoor.FacingOrientation.X, y = placedDoor.FacingOrientation.Y } : null,
                hand = placedDoor != null ? new { x = placedDoor.HandOrientation.X, y = placedDoor.HandOrientation.Y } : null,
                bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048, z = bb.Min.Z * 0.3048 } : null,
                bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048, z = bb.Max.Z * 0.3048 } : null,
                image = planImgPath
            };
        }
    }
}
