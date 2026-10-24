using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class UpdateWindowsAandD
    {
        private const double M2FT = 3.2808398950131235;
        private static double Mm2Ft(double mm) => mm / 304.8;
        private static double ToMm(double ft) => ft * 304.8;
        private static double ToM(double ft) => ft * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // 1. Collect all candidate S1 windows on Axis A and D between Grids 2 and 10
                var allWindows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .ToList();

                var targetWindows = new List<FamilyInstance>();

                foreach (var w in allWindows)
                {
                    var lp = (w.Location as LocationPoint)?.Point;
                    if (lp == null) continue;

                    double x = ToM(lp.X);
                    double y = ToM(lp.Y);

                    // Check range X: between Grid 2 (4.35m) and Grid 10 (33.35m)
                    if (x < 4.0 || x > 33.6) continue;

                    // Check Axis A (Y ~ 0) or Axis D (Y ~ 13.2)
                    bool isAxisA = Math.Abs(y - 0.0) < 0.6;
                    bool isAxisD = Math.Abs(y - 13.2) < 0.6;

                    if (!isAxisA && !isAxisD) continue;

                    // Filter out S5 toilet windows
                    if (w.Symbol.Name.IndexOf("S5", StringComparison.OrdinalIgnoreCase) >= 0) continue;

                    targetWindows.Add(w);
                }

                if (targetWindows.Count == 0)
                {
                    return new { error = "No target windows found on Axis A and D" };
                }

                FamilySymbol sym1800 = null;
                var updatedList = new List<object>();

                using (Transaction t = new Transaction(doc, "Chinh cua so truc A va D thanh 1500x1800 sill 750"))
                {
                    t.Start();

                    // Find or create FamilySymbol S1_1500x1800
                    var baseSym = targetWindows[0].Symbol;
                    var fam = baseSym.Family;

                    foreach (ElementId symId in fam.GetFamilySymbolIds())
                    {
                        var s = doc.GetElement(symId) as FamilySymbol;
                        if (s != null && s.Name.Equals("S1_1500x1800", StringComparison.OrdinalIgnoreCase))
                        {
                            sym1800 = s;
                            break;
                        }
                    }

                    if (sym1800 == null)
                    {
                        sym1800 = baseSym.Duplicate("S1_1500x1800") as FamilySymbol;
                    }

                    if (!sym1800.IsActive) sym1800.Activate();

                    // Set Type Parameters: Width = 1500, Height = 1800, CAO CANH = 1800, Default Sill Height = 750
                    var widthParam = sym1800.get_Parameter(BuiltInParameter.WINDOW_WIDTH) ?? sym1800.LookupParameter("Width");
                    widthParam?.Set(Mm2Ft(1500.0));

                    var heightParam = sym1800.get_Parameter(BuiltInParameter.WINDOW_HEIGHT) ?? sym1800.LookupParameter("Height");
                    heightParam?.Set(Mm2Ft(1800.0));

                    var caoCanhParam = sym1800.LookupParameter("CAO CÁNH") ?? sym1800.LookupParameter("Cao Cánh");
                    caoCanhParam?.Set(Mm2Ft(1800.0));

                    var defSillParam = sym1800.LookupParameter("Default Sill Height") ?? sym1800.LookupParameter("Cao độ bậu cửa mặc định");
                    defSillParam?.Set(Mm2Ft(750.0));

                    doc.Regenerate();

                    // Update all target instances
                    foreach (var w in targetWindows)
                    {
                        // 1. Change symbol to S1_1500x1800
                        if (w.Symbol.Id != sym1800.Id)
                        {
                            w.ChangeTypeId(sym1800.Id);
                        }

                        // 2. Set Sill Height = 750mm
                        var sillParam = w.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                        if (sillParam != null && !sillParam.IsReadOnly)
                        {
                            sillParam.Set(Mm2Ft(750.0));
                        }

                        doc.Regenerate();

                        var lp = (w.Location as LocationPoint)?.Point;
                        var level = doc.GetElement(w.LevelId) as Level;
                        var headParam = w.get_Parameter(BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM);

                        double currentSill = sillParam != null ? ToMm(sillParam.AsDouble()) : 0;
                        double currentHead = headParam != null ? ToMm(headParam.AsDouble()) : 0;

                        updatedList.Add(new
                        {
                            id = w.Id.Value,
                            x = lp != null ? Math.Round(ToM(lp.X), 2) : 0,
                            y = lp != null ? Math.Round(ToM(lp.Y), 2) : 0,
                            level = level?.Name,
                            symbol = sym1800.Name,
                            sill_mm = Math.Round(currentSill, 1),
                            head_mm = Math.Round(currentHead, 1)
                        });
                    }

                    t.Commit();
                }

                // Export 3D view
                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string img3dPath = Path.Combine(folder, "revit_3d_windows_1800.jpg");

                var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    uidoc.Selection.SetElementIds(new List<ElementId>());

                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview3d?.ZoomToFit();

                    if (File.Exists(img3dPath)) File.Delete(img3dPath);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = img3dPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt3d);
                }

                // Save Document
                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                }
                catch { }

                return new
                {
                    success = true,
                    newTypeName = sym1800.Name,
                    newHeight_mm = 1800,
                    newSill_mm = 750,
                    count = updatedList.Count,
                    updatedWindows = updatedList,
                    img3dPath,
                    docSaved
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
