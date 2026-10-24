using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CreateUnifiedK2StackFamily
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        private static Solid CreateBoxSolid(double minXMm, double maxXMm, double minYMm, double maxYMm, double minZMm, double maxZMm)
        {
            double minX = minXMm * MM2FT;
            double maxX = maxXMm * MM2FT;
            double minY = minYMm * MM2FT;
            double maxY = maxYMm * MM2FT;
            double minZ = minZMm * MM2FT;
            double maxZ = maxZMm * MM2FT;

            XYZ p0 = new XYZ(minX, minY, minZ);
            XYZ p1 = new XYZ(maxX, minY, minZ);
            XYZ p2 = new XYZ(maxX, minY, maxZ);
            XYZ p3 = new XYZ(minX, minY, maxZ);

            CurveLoop loop = new CurveLoop();
            loop.Append(Line.CreateBound(p0, p1));
            loop.Append(Line.CreateBound(p1, p2));
            loop.Append(Line.CreateBound(p2, p3));
            loop.Append(Line.CreateBound(p3, p0));

            double depth = maxY - minY;
            return GeometryCreationUtilities.CreateExtrusionGeometry(new List<CurveLoop> { loop }, XYZ.BasisY, depth);
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var app = uiapp.Application;
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active Revit doc" };

                List<string> logs = new List<string>();

                // -------------------------------------------------------------------------
                // 1. Create Window_K2_Stack.rfa
                // -------------------------------------------------------------------------
                string templatePath = @"C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\Metric Generic Model.rft";
                if (!File.Exists(templatePath))
                {
                    return new { error = "Template not found: " + templatePath };
                }

                string famPath = @"D:\Dropbox\_Documents\RevitAI\Window_K2_Stack.rfa";
                if (File.Exists(famPath))
                {
                    try { File.Delete(famPath); } catch { }
                }

                Document famDoc = app.NewFamilyDocument(templatePath);
                if (famDoc == null) return new { error = "Failed to create family document" };

                using (Transaction tx = new Transaction(famDoc, "Create Unified K2 Stack Geometry"))
                {
                    tx.Start();

                    // Set Category to OST_Windows
                    var winCat = famDoc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows);
                    famDoc.OwnerFamily.FamilyCategory = winCat;
                    logs.Add("Family category set to Windows");

                    var glassSubCat = winCat.SubCategories.Cast<Category>().FirstOrDefault(c => c.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase));
                    var frameSubCat = winCat.SubCategories.Cast<Category>().FirstOrDefault(c => c.Name.Equals("Frame/Mullion", StringComparison.OrdinalIgnoreCase));

                    // A. 4 Wall Blocks (width 900mm: X[-450, 450], thickness 200mm: Y[-100, 100])
                    var wallBlocks = new List<(double minZ, double maxZ, string name)>
                    {
                        (0.0, 1500.0, "Wall 1 (Z: 0 to 1500)"),
                        (3300.0, 5100.0, "Wall 2 (Z: 3300 to 5100)"),
                        (6900.0, 8700.0, "Wall 3 (Z: 6900 to 8700)"),
                        (10500.0, 11350.0, "Wall 4 (Z: 10500 to 11350)")
                    };

                    foreach (var wb in wallBlocks)
                    {
                        Solid wSolid = CreateBoxSolid(-450.0, 450.0, -100.0, 100.0, wb.minZ, wb.maxZ);
                        FreeFormElement wFfe = FreeFormElement.Create(famDoc, wSolid);
                        logs.Add($"Created {wb.name}");
                    }

                    // B. 3 Windows (Z_bases: 1500, 5100, 8700)
                    double[] winBases = new double[] { 1500.0, 5100.0, 8700.0 };

                    // Frame templates relative to window base
                    var frameRelBoxes = new List<(double minX, double maxX, double minY, double maxY, double minZ, double maxZ)>
                    {
                        (-396.0, 396.0, -50.0, 50.0, 1746.0, 1800.0), // Outer Top
                        (-396.0, 396.0, -50.0, 50.0, 0.0, 54.5),       // Outer Bottom
                        (-450.0, -396.0, -50.0, 50.0, 0.0, 1800.0),   // Outer Left
                        (396.0, 450.0, -50.0, 50.0, 0.0, 1800.0),    // Outer Right
                        (-328.75, 328.75, 0.0, 50.0, 1688.0, 1746.0), // Sash Top
                        (-328.75, 328.75, 0.0, 50.0, 54.5, 112.5),    // Sash Bottom
                        (-396.0, -328.75, 0.0, 50.0, 54.5, 1746.0),   // Sash Left
                        (328.75, 396.0, 0.0, 50.0, 54.5, 1746.0)     // Sash Right
                    };

                    int winIdx = 1;
                    foreach (double zBase in winBases)
                    {
                        // 1. Glass Solid: X[-328.75, 328.75], Y[20, 30], Z[zBase + 112.5, zBase + 1688]
                        Solid gSolid = CreateBoxSolid(-328.75, 328.75, 20.0, 30.0, zBase + 112.5, zBase + 1688.0);
                        FreeFormElement gFfe = FreeFormElement.Create(famDoc, gSolid);
                        if (glassSubCat != null) gFfe.Subcategory = glassSubCat;

                        // 2. Frame Solids (8 boxes)
                        foreach (var fb in frameRelBoxes)
                        {
                            Solid fSolid = CreateBoxSolid(fb.minX, fb.maxX, fb.minY, fb.maxY, zBase + fb.minZ, zBase + fb.maxZ);
                            FreeFormElement fFfe = FreeFormElement.Create(famDoc, fSolid);
                            if (frameSubCat != null) fFfe.Subcategory = frameSubCat;
                        }
                        logs.Add($"Created Window {winIdx} (Z: {zBase} to {zBase + 1800})");
                        winIdx++;
                    }

                    tx.Commit();
                }

                famDoc.SaveAs(famPath);
                famDoc.Close(false);
                logs.Add($"Saved unified family to {famPath}");

                // -------------------------------------------------------------------------
                // 2. Load Window_K2_Stack.rfa into Project Doc
                // -------------------------------------------------------------------------
                Family famStack = null;
                using (Transaction tx = new Transaction(doc, "Load Window_K2_Stack"))
                {
                    tx.Start();
                    doc.LoadFamily(famPath, new SimpleFamilyLoadOptions(), out famStack);
                    tx.Commit();
                }

                if (famStack == null)
                {
                    famStack = new FilteredElementCollector(doc)
                        .OfClass(typeof(Family))
                        .Cast<Family>()
                        .FirstOrDefault(f => f.Name == "Window_K2_Stack");
                }
                if (famStack == null) return new { error = "Could not find loaded Window_K2_Stack" };

                FamilySymbol symStack = null;
                foreach (ElementId sid in famStack.GetFamilySymbolIds())
                {
                    symStack = doc.GetElement(sid) as FamilySymbol;
                    if (symStack != null) break;
                }
                if (symStack == null) return new { error = "No symbol found for Window_K2_Stack" };

                using (Transaction tx = new Transaction(doc, "Activate Window_K2_Stack Symbol"))
                {
                    tx.Start();
                    if (!symStack.IsActive) symStack.Activate();
                    tx.Commit();
                }
                logs.Add($"Activated symbol: {symStack.Name}");

                // -------------------------------------------------------------------------
                // 3. Replace Selected Elements with 1 Instance of Window_K2_Stack
                // -------------------------------------------------------------------------
                var selIds = uidoc.Selection.GetElementIds();
                var toDelete = new List<ElementId>();

                // Check the currently selected elements or target IDs
                foreach (ElementId id in selIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem is Wall || (elem is FamilyInstance fi && fi.Symbol.FamilyName.Contains("K2")))
                    {
                        toDelete.Add(id);
                    }
                }

                // If selection was cleared, find them by location
                if (toDelete.Count == 0)
                {
                    var oldWins = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_Windows)
                        .WhereElementIsNotElementType()
                        .Cast<FamilyInstance>()
                        .Where(w => w.Symbol.FamilyName == "Window_K2")
                        .Select(w => w.Id);

                    var oldWalls = new FilteredElementCollector(doc)
                        .OfClass(typeof(Wall))
                        .Cast<Wall>()
                        .Where(w =>
                        {
                            var lc = (w.Location as LocationCurve)?.Curve;
                            if (lc == null) return false;
                            double x = lc.GetEndPoint(0).X / M2FT;
                            double y0 = lc.GetEndPoint(0).Y / M2FT;
                            return Math.Abs(x - 0.55) < 0.05 && Math.Abs(y0 - 12.09375) < 0.05;
                        })
                        .Select(w => w.Id);

                    toDelete.AddRange(oldWins);
                    toDelete.AddRange(oldWalls);
                }

                var lvlTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .First();

                double truc1XM = 0.55;
                double bayCenterYM = 12.54375;

                FamilyInstance stackInst = null;

                using (Transaction tx = new Transaction(doc, "Replace with Unified Window_K2_Stack"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new K2WarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    // Delete the separate wall and window instances
                    if (toDelete.Count > 0)
                    {
                        doc.Delete(toDelete);
                        logs.Add($"Deleted {toDelete.Count} separate elements");
                    }

                    // Place 1 single instance of Window_K2_Stack
                    XYZ loc = new XYZ(truc1XM * M2FT, bayCenterYM * M2FT, lvlTang1.Elevation);
                    stackInst = doc.Create.NewFamilyInstance(loc, symStack, lvlTang1, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);

                    // Rotate 90 degrees around Z axis through loc to align with Truc 1
                    Line rotAxis = Line.CreateBound(loc, new XYZ(loc.X, loc.Y, loc.Z + 10.0));
                    ElementTransformUtils.RotateElement(doc, stackInst.Id, rotAxis, Math.PI / 2.0);

                    // Set Mark
                    stackInst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("K2_STACK");

                    tx.Commit();
                }

                logs.Add($"Placed 1 unified instance: Id={stackInst.Id.Value}");

                // -------------------------------------------------------------------------
                // 4. Select the new unified instance in UI and Refresh
                // -------------------------------------------------------------------------
                uidoc.Selection.SetElementIds(new List<ElementId> { stackInst.Id });

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == uidoc.ActiveView.Id);
                uiview?.ZoomToFit();
                uidoc.RefreshActiveView();

                // Save doc
                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    familyPath = famPath,
                    familyName = famStack.Name,
                    instanceId = stackInst.Id.Value,
                    deletedElementCount = toDelete.Count,
                    logs
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
