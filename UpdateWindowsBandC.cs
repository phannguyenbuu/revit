using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class UpdateWindowsBandC
    {
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

                // 1. Collect all candidate windows on Axis B (Y ~ 5.4) and Axis C (Y ~ 7.8)
                var allWindows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .ToList();

                var targetWindowsB = new List<FamilyInstance>();
                var targetWindowsC = new List<FamilyInstance>();

                foreach (var w in allWindows)
                {
                    var lp = (w.Location as LocationPoint)?.Point;
                    if (lp == null) continue;

                    double x = ToM(lp.X);
                    double y = ToM(lp.Y);

                    // Check Axis B (Y ~ 5.4) or Axis C (Y ~ 7.8)
                    bool isAxisB = Math.Abs(y - 5.40) < 0.6;
                    bool isAxisC = Math.Abs(y - 7.80) < 0.6;

                    if (isAxisB)
                    {
                        targetWindowsB.Add(w);
                    }
                    else if (isAxisC)
                    {
                        targetWindowsC.Add(w);
                    }
                }

                var allTargetWindows = new List<FamilyInstance>();
                allTargetWindows.AddRange(targetWindowsB);
                allTargetWindows.AddRange(targetWindowsC);

                FamilySymbol sym1800 = null;
                var updatedList = new List<object>();

                if (allTargetWindows.Count > 0)
                {
                    using (Transaction t = new Transaction(doc, "Chinh cua so truc B va C thanh 1500x1800 sill 750"))
                    {
                        t.Start();

                        // Find or create FamilySymbol S1_1500x1800
                        var baseSym = allTargetWindows[0].Symbol;
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
                            if (!sym1800.IsActive) sym1800.Activate();

                            var widthParam = sym1800.get_Parameter(BuiltInParameter.WINDOW_WIDTH) ?? sym1800.LookupParameter("Width");
                            widthParam?.Set(Mm2Ft(1500.0));

                            var heightParam = sym1800.get_Parameter(BuiltInParameter.WINDOW_HEIGHT) ?? sym1800.LookupParameter("Height");
                            heightParam?.Set(Mm2Ft(1800.0));

                            var caoCanhParam = sym1800.LookupParameter("CAO CÁNH") ?? sym1800.LookupParameter("Cao Cánh");
                            caoCanhParam?.Set(Mm2Ft(1800.0));

                            var defSillParam = sym1800.LookupParameter("Default Sill Height") ?? sym1800.LookupParameter("Cao độ bậu cửa mặc định");
                            defSillParam?.Set(Mm2Ft(750.0));
                        }
                        else
                        {
                            if (!sym1800.IsActive) sym1800.Activate();
                        }

                        doc.Regenerate();

                        // Update all target instances
                        foreach (var w in allTargetWindows)
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
                            double curY = lp != null ? ToM(lp.Y) : 0;

                            string axis = Math.Abs(curY - 5.40) < 0.6 ? "Trục B" : (Math.Abs(curY - 7.80) < 0.6 ? "Trục C" : "Khác");

                            updatedList.Add(new
                            {
                                id = w.Id.Value,
                                axis,
                                x = lp != null ? Math.Round(ToM(lp.X), 2) : 0,
                                y = lp != null ? Math.Round(curY, 2) : 0,
                                level = level?.Name,
                                symbol = sym1800.Name,
                                sill_mm = Math.Round(currentSill, 1),
                                head_mm = Math.Round(currentHead, 1)
                            });
                        }

                        t.Commit();
                    }
                }

                // Export 3D view
                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string img3dPath = Path.Combine(folder, "revit_3d_windows_all_1800.jpg");
                string imgTang4Path = Path.Combine(folder, "revit_tang4_windows_b.png");

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

                // Export Tầng 4 floor plan view
                var planViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                    .ToList();

                var tang4View = doc.GetElement(new ElementId(931687L)) as ViewPlan
                    ?? planViews.FirstOrDefault(v => v.Name.IndexOf("TẦNG 4", StringComparison.OrdinalIgnoreCase) >= 0 || v.Name.IndexOf("TANG 4", StringComparison.OrdinalIgnoreCase) >= 0 || v.Name.IndexOf("ÁP MÁI", StringComparison.OrdinalIgnoreCase) >= 0);

                if (tang4View != null)
                {
                    uidoc.ActiveView = tang4View;
                    uidoc.Selection.SetElementIds(new List<ElementId>());

                    var uiTang4 = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == tang4View.Id);
                    uiTang4?.ZoomToFit();

                    if (File.Exists(imgTang4Path)) File.Delete(imgTang4Path);
                    var expOptPlan = new ImageExportOptions
                    {
                        FilePath = imgTang4Path,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOptPlan);
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
                    countB = targetWindowsB.Count,
                    countC = targetWindowsC.Count,
                    totalUpdated = updatedList.Count,
                    updatedWindows = updatedList,
                    img3dPath,
                    imgTang4Path,
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
