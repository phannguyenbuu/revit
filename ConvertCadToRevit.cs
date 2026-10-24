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
    public static class ConvertCadToRevit
    {
        private const double M2FT = 3.2808398950131235; // 1 meter to feet

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            var results = new Dictionary<string, object>();

            // 1. SAVE AS NEW PROJECT
            string newPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\Mau_40_CBS_Long_Tien.rvt";
            try
            {
                var saveOpts = new SaveAsOptions { OverwriteExistingFile = true };
                doc.SaveAs(newPath, saveOpts);
                results["savedNewProject"] = newPath;
            }
            catch (Exception ex)
            {
                results["saveError"] = ex.Message;
            }

            // 2. CLEAR OLD BUILDING INSTANCES
            int deletedCount = 0;
            using (var tx = new Transaction(doc, "Clear Old Building Instances"))
            {
                tx.Start();
                var catsToDelete = new List<BuiltInCategory>
                {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_Columns,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Floors,
                    BuiltInCategory.OST_Grids
                };

                foreach (var cat in catsToDelete)
                {
                    var ids = new FilteredElementCollector(doc)
                        .OfCategory(cat)
                        .WhereElementIsNotElementType()
                        .ToElementIds();
                    
                    if (ids.Count > 0)
                    {
                        var del = doc.Delete(ids);
                        deletedCount += del.Count;
                    }
                }
                tx.Commit();
            }
            results["clearedOldElementsCount"] = deletedCount;

            // 3. SETUP / SYNCHRONIZE LEVELS
            Level? lvlTang1 = null;
            Level? lvlTang2 = null;
            Level? lvlTang3 = null;
            Level? lvlTang4 = null;
            Level? lvlTum = null;
            Level? lvlMai = null;

            using (var tx = new Transaction(doc, "Setup Levels"))
            {
                tx.Start();
                var existingLevels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                Level GetOrCreateLevel(string name, double elevM)
                {
                    var found = existingLevels.FirstOrDefault(l => l.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
                    if (found == null)
                    {
                        found = Level.Create(doc, elevM * M2FT);
                        found.Name = name;
                        existingLevels.Add(found);
                    }
                    else
                    {
                        found.Elevation = elevM * M2FT;
                    }
                    return found;
                }

                GetOrCreateLevel("MẶT BẰNG SÂN VƯỜN", -0.75);
                lvlTang1 = GetOrCreateLevel("MẶT BẰNG TẦNG 1", 0.0);
                lvlTang2 = GetOrCreateLevel("MẶT BẰNG TẦNG 2", 3.6);
                lvlTang3 = GetOrCreateLevel("MẶT BẰNG TẦNG 3", 7.2);
                lvlTang4 = GetOrCreateLevel("MẶT BẰNG TẦNG 4", 10.8);
                lvlTum   = GetOrCreateLevel("MẶT BẰNG TẦNG TUM", 14.4);
                lvlMai   = GetOrCreateLevel("MẶT BẰNG MÁI", 17.2);

                tx.Commit();
            }
            results["levelsConfigured"] = new[] { "SÂN VƯỜN", "TẦNG 1", "TẦNG 2", "TẦNG 3", "TẦNG 4", "TẦNG TUM", "MÁI" };

            // 4. CREATE NEW GRIDS (1 to 11 and A to E)
            int createdGridsCount = 0;
            using (var tx = new Transaction(doc, "Create Building Grids"))
            {
                tx.Start();

                // Vertical Grids (1 to 11)
                var vGrids = new (string name, double xM)[]
                {
                    ("1", 0.0),
                    ("2", 3.8),
                    ("3", 7.5),
                    ("4", 11.1),
                    ("5", 14.7),
                    ("6", 18.3),
                    ("7", 21.9),
                    ("8", 26.6),
                    ("9", 29.1),
                    ("10", 32.8),
                    ("11", 36.6)
                };

                double yStartFt = -3.0 * M2FT;
                double yEndFt = 18.0 * M2FT;

                foreach (var g in vGrids)
                {
                    double xFt = g.xM * M2FT;
                    var p1 = new XYZ(xFt, yStartFt, 0);
                    var p2 = new XYZ(xFt, yEndFt, 0);
                    var line = Line.CreateBound(p1, p2);
                    var grid = Grid.Create(doc, line);
                    grid.Name = g.name;
                    createdGridsCount++;
                }

                // Horizontal Grids (A to E)
                var hGrids = new (string name, double yM)[]
                {
                    ("A", 0.0),
                    ("B", 5.4),
                    ("C", 7.8),
                    ("D", 13.2),
                    ("E", 14.9)
                };

                double xStartFt = -3.0 * M2FT;
                double xEndFt = 39.5 * M2FT;

                foreach (var g in hGrids)
                {
                    double yFt = g.yM * M2FT;
                    var p1 = new XYZ(xStartFt, yFt, 0);
                    var p2 = new XYZ(xEndFt, yFt, 0);
                    var line = Line.CreateBound(p1, p2);
                    var grid = Grid.Create(doc, line);
                    grid.Name = g.name;
                    createdGridsCount++;
                }

                tx.Commit();
            }
            results["createdGridsCount"] = createdGridsCount;

            // 5. PLACE THE 32 STRUCTURAL COLUMNS (COT220X220)
            int placedColumns = 0;
            string colJsonPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\columns_tang1.json";
            if (File.Exists(colJsonPath) && lvlTang1 != null && lvlTang2 != null)
            {
                using (var tx = new Transaction(doc, "Place Structural Columns Tầng 1"))
                {
                    tx.Start();

                    // Find COT220X220 family symbol
                    var colSymbol = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralColumns)
                        .OfClass(typeof(FamilySymbol))
                        .Cast<FamilySymbol>()
                        .FirstOrDefault(s => s.Name.Contains("COT220X220", StringComparison.OrdinalIgnoreCase))
                        ?? new FilteredElementCollector(doc)
                            .OfCategory(BuiltInCategory.OST_StructuralColumns)
                            .OfClass(typeof(FamilySymbol))
                            .Cast<FamilySymbol>()
                            .FirstOrDefault(s => s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase));

                    if (colSymbol != null)
                    {
                        if (!colSymbol.IsActive) colSymbol.Activate();

                        var jsonText = File.ReadAllText(colJsonPath);
                        using var jdoc = JsonDocument.Parse(jsonText);
                        foreach (var el in jdoc.RootElement.EnumerateArray())
                        {
                            double xM = el.GetProperty("x").GetDouble();
                            double yM = el.GetProperty("y").GetDouble();
                            double rotRad = el.GetProperty("rotationRad").GetDouble();

                            XYZ pt = new XYZ(xM * M2FT, yM * M2FT, 0.0);
                            var inst = doc.Create.NewFamilyInstance(pt, colSymbol, lvlTang1, StructuralType.Column);
                            
                            // Set base and top levels
                            var pBase = inst.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                            if (pBase != null && !pBase.IsReadOnly) pBase.Set(lvlTang1.Id);

                            var pTop = inst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                            if (pTop != null && !pTop.IsReadOnly) pTop.Set(lvlTang2.Id);

                            var pBaseOff = inst.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                            if (pBaseOff != null && !pBaseOff.IsReadOnly) pBaseOff.Set(0.0);

                            var pTopOff = inst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                            if (pTopOff != null && !pTopOff.IsReadOnly) pTopOff.Set(0.0);

                            if (Math.Abs(rotRad) > 1e-4)
                            {
                                var axis = Line.CreateBound(pt, pt + XYZ.BasisZ);
                                ElementTransformUtils.RotateElement(doc, inst.Id, axis, rotRad);
                            }

                            placedColumns++;
                        }
                    }
                    else
                    {
                        results["columnError"] = "No structural column symbol found";
                    }

                    tx.Commit();
                }
            }
            results["placedColumnsCount"] = placedColumns;

            // 6. LINK PLAN_TANG_1.dwg INTO TẦNG 1 VIEW
            string dwgPath = @"D:\Dropbox\_Documents\RevitAI\PLAN_TANG_1.dwg";
            if (File.Exists(dwgPath))
            {
                using (var tx = new Transaction(doc, "Link Floor Plan DWG"))
                {
                    tx.Start();
                    // Find Floor Plan view for Tầng 1
                    var viewTang1 = new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewPlan))
                        .Cast<ViewPlan>()
                        .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase))
                        ?? doc.ActiveView;

                    if (viewTang1 != null)
                    {
                        var opt = new DWGImportOptions
                        {
                            Placement = ImportPlacement.Origin,
                            Unit = ImportUnit.Millimeter,
                            ThisViewOnly = true
                        };

                        ElementId linkId;
                        var linkType = doc.Link(dwgPath, opt, viewTang1, out linkId);
                        results["cadLinkedView"] = viewTang1.Name;
                        results["cadLinkId"] = linkId.Value;
                    }
                    tx.Commit();
                }
            }

            // Save final state
            try
            {
                doc.Save();
                results["finalSaved"] = true;
            }
            catch (Exception ex)
            {
                results["finalSaveError"] = ex.Message;
            }

            return results;
        }
    }
}
