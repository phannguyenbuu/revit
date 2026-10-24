using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ApplyFloorsHatchAndTagAllOpenings
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No active ViewPlan" };

                // 1. UPDATE PATTERNS & MATERIALS & VIEW TEMPLATE
                FillPatternElement? fpeAngle = null;
                FillPatternElement? fpe600 = null;

                using (var txPat = new Transaction(doc, "Setup Floor Hatch Patterns"))
                {
                    txPat.Start();

                    // 1A. Sàn vệ sinh: 200 * 200 (mẫu angle)
                    fpeAngle = doc.GetElement(new ElementId(2406226L)) as FillPatternElement
                        ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "ANGLE");

                    double spacing200 = 200.0 * MM_TO_FT;
                    var fpAngle = new FillPattern("ANGLE", FillPatternTarget.Model, FillPatternHostOrientation.ToHost, Math.PI / 4.0, spacing200, spacing200);

                    if (fpeAngle != null)
                    {
                        fpeAngle.SetFillPattern(fpAngle);
                    }
                    else
                    {
                        fpeAngle = FillPatternElement.Create(doc, fpAngle);
                    }

                    // Assign to Material WC
                    var matWc = doc.GetElement(new ElementId(107066L)) as Material
                        ?? new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>().FirstOrDefault(m => m.Name.Equals("WC", StringComparison.OrdinalIgnoreCase));
                    if (matWc != null && fpeAngle != null)
                    {
                        matWc.SurfaceForegroundPatternId = fpeAngle.Id;
                        matWc.SurfaceForegroundPatternColor = new Color(120, 120, 120);
                    }

                    // 1B. Sàn gạch 600 * 600
                    fpe600 = doc.GetElement(new ElementId(8574L)) as FillPatternElement
                        ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "600 x 600mm");

                    if (fpe600 == null)
                    {
                        double spacing600 = 600.0 * MM_TO_FT;
                        var fp600 = new FillPattern("600 x 600mm", FillPatternTarget.Model, FillPatternHostOrientation.ToHost, 0.0, spacing600, spacing600);
                        fpe600 = FillPatternElement.Create(doc, fp600);
                    }

                    // Assign 600x600 pattern to floor materials
                    string[] mainMatNames = new string[] { "Concrete - Cast In Situ", "9-8 LAT NỀN CAMERIC", "6-LAT GACH NHA 06", "6-LAT GACH SAN" };
                    foreach (var mName in mainMatNames)
                    {
                        var m = new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>()
                            .FirstOrDefault(mat => mat.Name.Equals(mName, StringComparison.OrdinalIgnoreCase));
                        if (m != null && fpe600 != null)
                        {
                            m.SurfaceForegroundPatternId = fpe600.Id;
                            m.SurfaceForegroundPatternColor = new Color(175, 175, 175);
                        }
                    }

                    // Also create/assign dedicated material "GẠCH LÁT NỀN 600x600"
                    var mat600 = new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>()
                        .FirstOrDefault(m => m.Name.Equals("GẠCH LÁT NỀN 600x600", StringComparison.OrdinalIgnoreCase));
                    if (mat600 == null)
                    {
                        var matId = Material.Create(doc, "GẠCH LÁT NỀN 600x600");
                        mat600 = doc.GetElement(matId) as Material;
                    }
                    if (mat600 != null && fpe600 != null)
                    {
                        mat600.Color = new Color(245, 245, 245);
                        mat600.SurfaceForegroundPatternId = fpe600.Id;
                        mat600.SurfaceForegroundPatternColor = new Color(175, 175, 175);
                    }

                    // Assign to main Floor 2381562
                    var mainFloor = doc.GetElement(new ElementId(2381562L)) as Floor;
                    if (mainFloor != null)
                    {
                        var ft = mainFloor.FloorType;
                        var cs = ft.GetCompoundStructure();
                        if (cs != null && mat600 != null)
                        {
                            var layers = cs.GetLayers();
                            if (layers.Count > 0)
                            {
                                cs.SetMaterialId(0, mat600.Id);
                                ft.SetCompoundStructure(cs);
                            }
                        }
                    }

                    // 1C. Enable Floor Surface Foreground Patterns in View Template / View
                    var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                    var doorTagCat = Category.GetCategory(doc, BuiltInCategory.OST_DoorTags);
                    var winTagCat = Category.GetCategory(doc, BuiltInCategory.OST_WindowTags);

                    var vt = view.ViewTemplateId != ElementId.InvalidElementId 
                        ? doc.GetElement(view.ViewTemplateId) as View 
                        : null;

                    if (vt != null)
                    {
                        var ovFloor = vt.GetCategoryOverrides(floorCat.Id);
                        ovFloor.SetSurfaceForegroundPatternVisible(true);
                        vt.SetCategoryOverrides(floorCat.Id, ovFloor);

                        if (doorTagCat != null && vt.CanCategoryBeHidden(doorTagCat.Id))
                            vt.SetCategoryHidden(doorTagCat.Id, false);

                        if (winTagCat != null && vt.CanCategoryBeHidden(winTagCat.Id))
                            vt.SetCategoryHidden(winTagCat.Id, false);
                    }
                    else
                    {
                        if (view.IsCategoryOverridable(floorCat.Id))
                        {
                            var ovFloor = view.GetCategoryOverrides(floorCat.Id);
                            ovFloor.SetSurfaceForegroundPatternVisible(true);
                            view.SetCategoryOverrides(floorCat.Id, ovFloor);
                        }

                        if (doorTagCat != null && view.CanCategoryBeHidden(doorTagCat.Id))
                            view.SetCategoryHidden(doorTagCat.Id, false);

                        if (winTagCat != null && view.CanCategoryBeHidden(winTagCat.Id))
                            view.SetCategoryHidden(winTagCat.Id, false);
                    }

                    txPat.Commit();
                }

                // 2. SET TYPE MARKS FOR DOOR & WINDOW SYMBOLS
                using (var txTm = new Transaction(doc, "Set Type Marks For Openings"))
                {
                    txTm.Start();

                    // Door symbols
                    var doorSymbols = new FilteredElementCollector(doc)
                        .OfClass(typeof(FamilySymbol))
                        .OfCategory(BuiltInCategory.OST_Doors)
                        .Cast<FamilySymbol>()
                        .ToList();

                    foreach (var sym in doorSymbols)
                    {
                        var pTm = sym.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
                        if (pTm == null || pTm.IsReadOnly) continue;

                        string n = (sym.FamilyName + " " + sym.Name).ToUpper();
                        if (n.Contains("D7") || n.Contains("Đ7")) pTm.Set("D7");
                        else if (n.Contains("D4") || n.Contains("Đ4")) pTm.Set("D4");
                        else if (n.Contains("D2") || n.Contains("Đ2")) pTm.Set("D2");
                        else if (n.Contains("D5") || n.Contains("Đ5")) pTm.Set("D5");
                        else if (n.Contains("D1") || n.Contains("Đ1")) pTm.Set("D1");
                    }

                    // Window symbols
                    var winSymbols = new FilteredElementCollector(doc)
                        .OfClass(typeof(FamilySymbol))
                        .OfCategory(BuiltInCategory.OST_Windows)
                        .Cast<FamilySymbol>()
                        .ToList();

                    foreach (var sym in winSymbols)
                    {
                        var pTm = sym.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
                        if (pTm == null || pTm.IsReadOnly) continue;

                        string n = (sym.FamilyName + " " + sym.Name).ToUpper();
                        if (n.Contains("S1_") || n.StartsWith("S1")) pTm.Set("S1");
                        else if (n.Contains("S4_") || n.StartsWith("S4")) pTm.Set("S4");
                        else if (n.Contains("S5_") || n.StartsWith("S5")) pTm.Set("S5");
                        else if (n.Contains("K3_") || n.StartsWith("K3")) pTm.Set("K3");
                        else if (n.Contains("K2") || n.Contains("WINDOW_K2")) pTm.Set("K2");
                    }

                    txTm.Commit();
                }

                // 3. TAG ALL DOORS AND WINDOWS IN VIEW 312
                int doorsTagged = 0;
                int windowsTagged = 0;

                var doorTagSym = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilySymbol))
                    .OfCategory(BuiltInCategory.OST_DoorTags)
                    .Cast<FamilySymbol>()
                    .FirstOrDefault();

                var winTagSym = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilySymbol))
                    .OfCategory(BuiltInCategory.OST_WindowTags)
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(s => s.FamilyName.Contains("KÝ HIỆU CỬA SỔ"))
                    ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilySymbol))
                    .OfCategory(BuiltInCategory.OST_WindowTags)
                    .Cast<FamilySymbol>()
                    .FirstOrDefault();

                using (var txTag = new Transaction(doc, "Tag All Doors and Windows"))
                {
                    txTag.Start();

                    // Existing tags in view
                    var existingTaggedDoorIds = new HashSet<long>(
                        new FilteredElementCollector(doc, view.Id)
                            .OfCategory(BuiltInCategory.OST_DoorTags)
                            .WhereElementIsNotElementType()
                            .Cast<IndependentTag>()
                            .SelectMany(t => t.GetTaggedLocalElementIds().Select(id => id.Value))
                    );

                    var existingTaggedWinIds = new HashSet<long>(
                        new FilteredElementCollector(doc, view.Id)
                            .OfCategory(BuiltInCategory.OST_WindowTags)
                            .WhereElementIsNotElementType()
                            .Cast<IndependentTag>()
                            .SelectMany(t => t.GetTaggedLocalElementIds().Select(id => id.Value))
                    );

                    // Doors in view
                    var doors = new FilteredElementCollector(doc, view.Id)
                        .OfCategory(BuiltInCategory.OST_Doors)
                        .WhereElementIsNotElementType()
                        .Cast<FamilyInstance>()
                        .ToList();

                    foreach (var d in doors)
                    {
                        if (existingTaggedDoorIds.Contains(d.Id.Value)) continue;

                        var loc = d.Location as LocationPoint;
                        if (loc == null) continue;

                        var pt = loc.Point;
                        // Offset 400mm along facing orientation (towards swing side)
                        var face = d.FacingOrientation;
                        var headPt = pt + face * (400.0 * MM_TO_FT);

                        var tag = IndependentTag.Create(doc, view.Id, new Reference(d), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, headPt);
                        if (doorTagSym != null) tag.ChangeTypeId(doorTagSym.Id);
                        doorsTagged++;
                    }

                    // Windows in view
                    var windows = new FilteredElementCollector(doc, view.Id)
                        .OfCategory(BuiltInCategory.OST_Windows)
                        .WhereElementIsNotElementType()
                        .Cast<FamilyInstance>()
                        .ToList();

                    foreach (var w in windows)
                    {
                        if (existingTaggedWinIds.Contains(w.Id.Value)) continue;

                        var loc = w.Location as LocationPoint;
                        if (loc == null) continue;

                        var pt = loc.Point;
                        // Offset 600mm along facing orientation
                        var face = w.FacingOrientation;
                        var headPt = pt + face * (600.0 * MM_TO_FT);

                        var tag = IndependentTag.Create(doc, view.Id, new Reference(w), false, TagMode.TM_ADDBY_CATEGORY, TagOrientation.Horizontal, headPt);
                        if (winTagSym != null) tag.ChangeTypeId(winTagSym.Id);
                        windowsTagged++;
                    }

                    txTag.Commit();
                }

                // 4. EXPORT HIGH RES VERIFICATION IMAGE
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ p1 = new XYZ(-2000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                    XYZ p2 = new XYZ(39000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p1, p2);
                }

                string planImgPath = Path.Combine(outDir, "revit_tang1_floor_hatch_and_tags.png");
                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 3000,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt);

                return new
                {
                    success = true,
                    toiletPattern = "ANGLE (200x200 at 45 deg)",
                    mainFloorPattern = "600 x 600mm",
                    doorsTagged = doorsTagged,
                    windowsTagged = windowsTagged,
                    image = "revit_tang1_floor_hatch_and_tags.png"
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
