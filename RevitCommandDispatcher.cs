using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpBridge
{
    public static class RevitCommandDispatcher
    {
        private const double FeetToMm = 304.8;
        private const double MmToFeet = 1.0 / 304.8;
        private const double MetersToFeet = 1.0 / 0.3048;
        private const double FeetToMeters = 0.3048;

        public static object GetDocumentInfo(UIApplication app)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null)
            {
                return new { status = "no_document_open" };
            }

            var activeView = app.ActiveUIDocument?.ActiveView;
            var selection = app.ActiveUIDocument?.Selection.GetElementIds()
                .Select(id => id.Value)
                .ToList() ?? new List<long>();

            return new
            {
                title = doc.Title,
                path = doc.PathName,
                isModified = doc.IsModified,
                isFamilyDocument = doc.IsFamilyDocument,
                activeView = activeView != null ? new
                {
                    id = activeView.Id.Value,
                    name = activeView.Name,
                    viewType = activeView.ViewType.ToString(),
                    scale = activeView.Scale
                } : null,
                selectedElementCount = selection.Count,
                selectedElementIds = selection
            };
        }

        public static object GetModelSummary(UIApplication app)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null)
            {
                return new { error = "No active document" };
            }

            // Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevationM = Math.Round(l.Elevation * FeetToMeters, 3),
                    elevationMm = Math.Round(l.Elevation * FeetToMm, 1)
                })
                .ToList();

            // Grids
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .OrderBy(g => g.Name)
                .Select(g => new
                {
                    id = g.Id.Value,
                    name = g.Name
                })
                .ToList();

            // Count primary categories
            int wallCount = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().GetElementCount();
            int doorCount = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().GetElementCount();
            int windowCount = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType().GetElementCount();
            int roomCount = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().GetElementCount();
            int columnCount = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Columns).WhereElementIsNotElementType().GetElementCount()
                           + new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType().GetElementCount();
            int sheetCount = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().GetElementCount();

            // Sheets list
            var sheets = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>()
                .OrderBy(s => s.SheetNumber)
                .Select(s => new
                {
                    id = s.Id.Value,
                    sheetNumber = s.SheetNumber,
                    sheetName = s.Name
                })
                .Take(50)
                .ToList();

            return new
            {
                projectTitle = doc.Title,
                levels,
                grids,
                counts = new
                {
                    walls = wallCount,
                    doors = doorCount,
                    windows = windowCount,
                    rooms = roomCount,
                    columns = columnCount,
                    sheets = sheetCount
                },
                sheets
            };
        }

        public static object QueryElements(UIApplication app, string categoryName, int limit = 50)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            BuiltInCategory? bic = categoryName.ToLowerInvariant() switch
            {
                "wall" or "walls" or "tuong" => BuiltInCategory.OST_Walls,
                "door" or "doors" or "cua" => BuiltInCategory.OST_Doors,
                "window" or "windows" or "cuaso" => BuiltInCategory.OST_Windows,
                "room" or "rooms" or "phong" => BuiltInCategory.OST_Rooms,
                "column" or "columns" or "cot" => BuiltInCategory.OST_Columns,
                "level" or "levels" or "tang" => BuiltInCategory.OST_Levels,
                "grid" or "grids" or "truc" => BuiltInCategory.OST_Grids,
                "sheet" or "sheets" or "banve" => BuiltInCategory.OST_Sheets,
                "floor" or "floors" or "san" => BuiltInCategory.OST_Floors,
                _ => null
            };

            FilteredElementCollector collector = new FilteredElementCollector(doc);
            if (bic.HasValue)
            {
                collector = collector.OfCategory(bic.Value).WhereElementIsNotElementType();
            }
            else
            {
                collector = collector.WhereElementIsNotElementType();
            }

            var elements = collector
                .Take(limit)
                .Select(e => new
                {
                    id = e.Id.Value,
                    name = e.Name,
                    category = e.Category?.Name ?? "Unknown",
                    level = e.LevelId != null && e.LevelId != ElementId.InvalidElementId 
                        ? doc.GetElement(e.LevelId)?.Name : null
                })
                .ToList();

            return new
            {
                category = categoryName,
                totalFound = elements.Count,
                elements
            };
        }

        public static object CreateLevel(UIApplication app, string name, double elevationMeters)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            double elevationFeet = elevationMeters * MetersToFeet;

            using var t = new Transaction(doc, "AI Copilot: Create Level");
            t.Start();
            try
            {
                var level = Level.Create(doc, elevationFeet);
                if (!string.IsNullOrWhiteSpace(name))
                {
                    level.Name = name;
                }
                t.Commit();

                return new
                {
                    success = true,
                    levelId = level.Id.Value,
                    name = level.Name,
                    elevationM = elevationMeters
                };
            }
            catch (Exception ex)
            {
                t.RollBack();
                return new { success = false, error = ex.Message };
            }
        }

        public static object CreateGrid(UIApplication app, string name, double startXm, double startYm, double endXm, double endYm)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var p1 = new XYZ(startXm * MetersToFeet, startYm * MetersToFeet, 0);
            var p2 = new XYZ(endXm * MetersToFeet, endYm * MetersToFeet, 0);
            var line = Line.CreateBound(p1, p2);

            using var t = new Transaction(doc, "AI Copilot: Create Grid");
            t.Start();
            try
            {
                var grid = Grid.Create(doc, line);
                if (!string.IsNullOrWhiteSpace(name))
                {
                    grid.Name = name;
                }
                t.Commit();

                return new
                {
                    success = true,
                    gridId = grid.Id.Value,
                    name = grid.Name
                };
            }
            catch (Exception ex)
            {
                t.RollBack();
                return new { success = false, error = ex.Message };
            }
        }

        public static object LinkCadDwg(UIApplication app, string dwgPath, bool currentViewOnly = true)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };
            if (!File.Exists(dwgPath)) return new { error = $"File DWG not found: {dwgPath}" };

            var view = currentViewOnly ? app.ActiveUIDocument?.ActiveView : null;

            var options = new DWGImportOptions
            {
                ColorMode = ImportColorMode.Preserved,
                Unit = ImportUnit.Millimeter,
                Placement = ImportPlacement.Centered,
                ThisViewOnly = currentViewOnly
            };

            using var t = new Transaction(doc, "AI Copilot: Link CAD DWG");
            t.Start();
            try
            {
                ElementId linkId;
                if (currentViewOnly && view != null)
                {
                    doc.Link(dwgPath, options, view, out linkId);
                }
                else
                {
                    doc.Link(dwgPath, options, doc.ActiveView, out linkId);
                }
                t.Commit();

                return new
                {
                    success = true,
                    dwgPath,
                    linkElementId = linkId.Value
                };
            }
            catch (Exception ex)
            {
                t.RollBack();
                return new { success = false, error = ex.Message };
            }
        }

        public static object IsolateFloors3D(UIApplication app, JsonElement args)
        {
            var uidoc = app.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "No active document open" };

            string defaultFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads", "PCCC_3DViews_TungTang");
            string outputFolder = args.TryGetProperty("outputFolder", out var f) && !string.IsNullOrWhiteSpace(f.GetString())
                ? f.GetString()! 
                : defaultFolder;

            bool exportImages = !args.TryGetProperty("exportImages", out var ei) || ei.GetBoolean();
            bool exportDwg = args.TryGetProperty("exportDwg", out var ed) && ed.GetBoolean();
            string archMode = args.TryGetProperty("archMode", out var am) ? am.GetString()?.ToLowerInvariant() ?? "transparent" : "transparent";
            string viewPrefix = args.TryGetProperty("viewPrefix", out var vp) ? vp.GetString() ?? "3D PCCC - " : "3D PCCC - ";
            int pixelSize = args.TryGetProperty("pixelSize", out var ps) ? ps.GetInt32() : 3840;

            // Source view to clone settings from
            View3D? sourceView = null;
            if (args.TryGetProperty("sourceViewId", out var svId) && svId.GetInt64() > 0)
            {
                sourceView = doc.GetElement(new ElementId(svId.GetInt64())) as View3D;
            }
            if (sourceView == null)
            {
                sourceView = uidoc.ActiveView as View3D;
            }
            if (sourceView == null)
            {
                sourceView = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("3D"));
            }

            var vft = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewFamilyType))
                .Cast<ViewFamilyType>()
                .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

            if (sourceView == null && vft == null)
            {
                return new { success = false, error = "No 3D view or 3D ViewFamilyType found" };
            }

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            if (levels.Count == 0)
            {
                return new { success = false, error = "No levels found in document" };
            }

            // Compute bounding box from pipes or model
            double minX = double.MaxValue, minY = double.MaxValue;
            double maxX = double.MinValue, maxY = double.MinValue;
            var pipes = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_PipeCurves)
                .WhereElementIsNotElementType();

            foreach (Element p in pipes)
            {
                var b = p.get_BoundingBox(null);
                if (b != null)
                {
                    minX = Math.Min(minX, b.Min.X);
                    minY = Math.Min(minY, b.Min.Y);
                    maxX = Math.Max(maxX, b.Max.X);
                    maxY = Math.Max(maxY, b.Max.Y);
                }
            }

            double pad = 2.0 * MetersToFeet;
            if (minX < maxX && minY < maxY)
            {
                minX -= pad; maxX += pad;
                minY -= pad; maxY += pad;
            }
            else
            {
                minX = -150; maxX = 150;
                minY = -150; maxY = 150;
            }

            var createdViews = new List<View3D>();
            var createdViewInfos = new List<object>();

            using (var t = new Transaction(doc, "AI Copilot: Isolate PCCC Floors 3D"))
            {
                t.Start();

                // 1. Ensure solid floor slabs exist on every level
                int createdFloors = EnsureFloorSlabsExist(doc, levels);

                // 2. Setup 3D Section-Boxed views for each level
                for (int i = 0; i < levels.Count; i++)
                {
                    var lvl = levels[i];
                    // zBottom extends below level elevation to fully enclose the floor slab
                    double zBottom = lvl.Elevation - (1.0 * MetersToFeet);
                    // zTop stops just before the next floor slab so we look down directly onto the floor and pipes
                    double zTop;
                    if (i < levels.Count - 1)
                    {
                        zTop = levels[i + 1].Elevation - (0.4 * MetersToFeet);
                    }
                    else
                    {
                        zTop = lvl.Elevation + (4.5 * MetersToFeet);
                    }

                    string cleanLvlName = CleanLevelName(lvl.Name);
                    string viewName = $"{viewPrefix}{cleanLvlName}";

                    var existingView = new FilteredElementCollector(doc)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate && v.Name == viewName);

                    View3D view3d;
                    if (existingView != null)
                    {
                        view3d = existingView;
                    }
                    else if (sourceView != null)
                    {
                        var dupId = sourceView.Duplicate(ViewDuplicateOption.Duplicate);
                        view3d = (View3D)doc.GetElement(dupId);
                        try { view3d.Name = viewName; } catch { }
                    }
                    else
                    {
                        view3d = View3D.CreateIsometric(doc, vft!.Id);
                        try { view3d.Name = viewName; } catch { }
                    }

                    var box = new BoundingBoxXYZ
                    {
                        Min = new XYZ(minX, minY, zBottom),
                        Max = new XYZ(maxX, maxY, zTop)
                    };
                    view3d.SetSectionBox(box);
                    view3d.IsSectionBoxActive = true;
                    view3d.DetailLevel = ViewDetailLevel.Fine;
                    view3d.DisplayStyle = DisplayStyle.Shading;

                    ApplyPcccVisibilityOverrides(doc, view3d, archMode);

                    createdViews.Add(view3d);
                    createdViewInfos.Add(new
                    {
                        viewId = view3d.Id.Value,
                        viewName = view3d.Name,
                        levelName = lvl.Name,
                        elevationM = Math.Round(lvl.Elevation * FeetToMeters, 2)
                    });
                }

                // 3. Setup Building Overview 3D View (All 24 floors with vertical risers)
                string overviewName = $"{viewPrefix}TOÀN CÔNG TRÌNH";
                var existingOverview = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name == overviewName);

                View3D overviewView;
                if (existingOverview != null)
                {
                    overviewView = existingOverview;
                }
                else if (sourceView != null)
                {
                    var dupId = sourceView.Duplicate(ViewDuplicateOption.Duplicate);
                    overviewView = (View3D)doc.GetElement(dupId);
                    try { overviewView.Name = overviewName; } catch { }
                }
                else
                {
                    overviewView = View3D.CreateIsometric(doc, vft!.Id);
                    try { overviewView.Name = overviewName; } catch { }
                }

                double zAllBottom = levels[0].Elevation - (2.0 * MetersToFeet);
                double zAllTop = levels[levels.Count - 1].Elevation + (8.0 * MetersToFeet);
                var overviewBox = new BoundingBoxXYZ
                {
                    Min = new XYZ(minX, minY, zAllBottom),
                    Max = new XYZ(maxX, maxY, zAllTop)
                };
                overviewView.SetSectionBox(overviewBox);
                overviewView.IsSectionBoxActive = true;
                overviewView.DetailLevel = ViewDetailLevel.Fine;
                overviewView.DisplayStyle = DisplayStyle.Shading;
                ApplyPcccVisibilityOverrides(doc, overviewView, archMode);

                createdViews.Add(overviewView);
                createdViewInfos.Add(new
                {
                    viewId = overviewView.Id.Value,
                    viewName = overviewView.Name,
                    levelName = "TOÀN CÔNG TRÌNH",
                    elevationM = 0.0
                });

                t.Commit();
            }

            var exportedFiles = new List<string>();
            if (exportImages && createdViews.Count > 0)
            {
                Directory.CreateDirectory(outputFolder);

                foreach (var view in createdViews)
                {
                    try
                    {
                        string safeName = SanitizeFileName(view.Name);
                        string outPath = Path.Combine(outputFolder, safeName);
                        var imgOpt = new ImageExportOptions
                        {
                            ExportRange = ExportRange.SetOfViews,
                            FilePath = outPath,
                            FitDirection = FitDirectionType.Horizontal,
                            HLRandWFViewsFileType = ImageFileType.PNG,
                            ImageResolution = ImageResolution.DPI_300,
                            PixelSize = pixelSize,
                            ShadowViewsFileType = ImageFileType.PNG,
                            ZoomType = ZoomFitType.FitToPage
                        };
                        imgOpt.SetViewsAndSheets(new List<ElementId> { view.Id });
                        doc.ExportImage(imgOpt);
                        exportedFiles.Add(outPath + ".png");
                    }
                    catch
                    {
                    }
                }
            }

            if (exportDwg && createdViews.Count > 0)
            {
                Directory.CreateDirectory(outputFolder);
                var dwgOpt = new DWGExportOptions
                {
                    ExportingAreas = false,
                    MergedViews = true,
                    TargetUnit = ExportUnit.Millimeter
                };
                foreach (var view in createdViews)
                {
                    try
                    {
                        string safeName = SanitizeFileName(view.Name);
                        doc.Export(outputFolder, $"{safeName}.dwg", new List<ElementId> { view.Id }, dwgOpt);
                    }
                    catch
                    {
                    }
                }
            }

            try
            {
                if (createdViews.Count > 0 && uidoc != null)
                {
                    uidoc.ActiveView = createdViews[0];
                }
            }
            catch { }

            return new
            {
                success = true,
                outputFolder,
                totalViews = createdViews.Count,
                views = createdViewInfos,
                exportedFiles
            };
        }

        private static int EnsureFloorSlabsExist(Document doc, IList<Level> levels)
        {
            var existingFloors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .Cast<Floor>()
                .ToList();

            ElementId? floorTypeId = null;
            IList<CurveLoop>? profileLoops = null;

            if (existingFloors.Count > 0)
            {
                foreach (var fl in existingFloors)
                {
                    if (floorTypeId == null) floorTypeId = fl.GetTypeId();
                    try
                    {
                        var topFaces = HostObjectUtils.GetTopFaces(fl);
                        if (topFaces != null && topFaces.Count > 0)
                        {
                            if (fl.GetGeometryObjectFromReference(topFaces[0]) is PlanarFace face)
                            {
                                var loops = face.GetEdgesAsCurveLoops();
                                if (loops != null && loops.Count > 0)
                                {
                                    var flattened = new List<CurveLoop>();
                                    foreach (var loop in loops)
                                    {
                                        var flatLoop = new CurveLoop();
                                        foreach (Curve c in loop)
                                        {
                                            var p0 = c.GetEndPoint(0);
                                            var p1 = c.GetEndPoint(1);
                                            flatLoop.Append(Line.CreateBound(new XYZ(p0.X, p0.Y, 0), new XYZ(p1.X, p1.Y, 0)));
                                        }
                                        flattened.Add(flatLoop);
                                    }
                                    profileLoops = flattened;
                                    break;
                                }
                            }
                        }
                    }
                    catch { }
                }
            }

            if (floorTypeId == null || floorTypeId == ElementId.InvalidElementId)
            {
                var ft = new FilteredElementCollector(doc)
                    .OfClass(typeof(FloorType))
                    .Cast<FloorType>()
                    .FirstOrDefault();
                floorTypeId = ft?.Id;
            }

            if (floorTypeId == null) return 0;

            if (profileLoops == null || profileLoops.Count == 0)
            {
                // Fallback boundary from pipes or grids
                double minX = double.MaxValue, minY = double.MaxValue;
                double maxX = double.MinValue, maxY = double.MinValue;
                var pipes = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_PipeCurves)
                    .WhereElementIsNotElementType();

                foreach (Element p in pipes)
                {
                    var b = p.get_BoundingBox(null);
                    if (b != null)
                    {
                        minX = Math.Min(minX, b.Min.X);
                        minY = Math.Min(minY, b.Min.Y);
                        maxX = Math.Max(maxX, b.Max.X);
                        maxY = Math.Max(maxY, b.Max.Y);
                    }
                }

                if (minX >= maxX || minY >= maxY)
                {
                    minX = -120; maxX = 120;
                    minY = -120; maxY = 120;
                }

                double pad = 2.0 * MetersToFeet;
                minX -= pad; maxX += pad;
                minY -= pad; maxY += pad;

                var loop = new CurveLoop();
                loop.Append(Line.CreateBound(new XYZ(minX, minY, 0), new XYZ(maxX, minY, 0)));
                loop.Append(Line.CreateBound(new XYZ(maxX, minY, 0), new XYZ(maxX, maxY, 0)));
                loop.Append(Line.CreateBound(new XYZ(maxX, maxY, 0), new XYZ(minX, maxY, 0)));
                loop.Append(Line.CreateBound(new XYZ(minX, maxY, 0), new XYZ(minX, minY, 0)));
                profileLoops = new List<CurveLoop> { loop };
            }

            int createdCount = 0;
            foreach (var lvl in levels)
            {
                bool hasFloor = existingFloors.Any(f => f.LevelId == lvl.Id);
                if (!hasFloor)
                {
                    try
                    {
                        var nf = Floor.Create(doc, profileLoops, floorTypeId, lvl.Id);
                        if (nf != null) createdCount++;
                    }
                    catch { }
                }
            }
            return createdCount;
        }

        public static object SaveDocument(UIApplication app)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };
            try
            {
                if (doc.IsWorkshared)
                {
                    var opt = new SynchronizeWithCentralOptions();
                    var relinq = new RelinquishOptions(true);
                    opt.SetRelinquishOptions(relinq);
                    doc.SynchronizeWithCentral(new TransactWithCentralOptions(), opt);
                }
                else
                {
                    doc.Save();
                }
                return new { success = true, path = doc.PathName };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message };
            }
        }

        public static object ExecuteDynamic(UIApplication app, JsonElement args)
        {
            string dllPath = args.GetProperty("dllPath").GetString()!;
            string typeName = args.TryGetProperty("typeName", out var tn) ? tn.GetString()! : "RevitScript.Script";
            string methodName = args.TryGetProperty("methodName", out var mn) ? mn.GetString()! : "Run";
            byte[] bytes = File.ReadAllBytes(dllPath);
            var asm = System.Reflection.Assembly.Load(bytes);
            var type = asm.GetType(typeName);
            var method = type?.GetMethod(methodName);
            if (method == null) return new { error = $"Method {methodName} in {typeName} not found" };
            return method.Invoke(null, new object[] { app, args })!;
        }

        private static string CleanLevelName(string name)
        {
            string s = name.Trim();
            foreach (char c in Path.GetInvalidFileNameChars())
            {
                s = s.Replace(c, '_');
            }
            return s;
        }

        private static string SanitizeFileName(string name)
        {
            string s = name.Trim();
            foreach (char c in Path.GetInvalidFileNameChars())
            {
                s = s.Replace(c, '_');
            }
            return s;
        }

        private static void ApplyPcccVisibilityOverrides(Document doc, View3D view, string archMode)
        {
            BuiltInCategory[] mepCats = new[]
            {
                BuiltInCategory.OST_PipeCurves,
                BuiltInCategory.OST_PipeFitting,
                BuiltInCategory.OST_PipeAccessory,
                BuiltInCategory.OST_Sprinklers,
                BuiltInCategory.OST_MechanicalEquipment,
                BuiltInCategory.OST_PlumbingFixtures,
                BuiltInCategory.OST_PlumbingEquipment,
                BuiltInCategory.OST_DuctCurves,
                BuiltInCategory.OST_DuctFitting,
                BuiltInCategory.OST_DuctAccessory,
                BuiltInCategory.OST_DuctTerminal,
                BuiltInCategory.OST_FlexPipeCurves,
                BuiltInCategory.OST_FlexDuctCurves
            };

            foreach (var bic in mepCats)
            {
                try
                {
                    var cat = Category.GetCategory(doc, bic);
                    if (cat != null && view.CanCategoryBeHidden(cat.Id))
                    {
                        view.SetCategoryHidden(cat.Id, false);
                        var s = new OverrideGraphicSettings();
                        s.SetSurfaceTransparency(0);
                        s.SetHalftone(false);
                        view.SetCategoryOverrides(cat.Id, s);
                    }
                }
                catch { }
            }

            // Explicitly configure solid floor slabs so they are clearly visible
            try
            {
                var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                if (floorCat != null && view.CanCategoryBeHidden(floorCat.Id))
                {
                    view.SetCategoryHidden(floorCat.Id, false);
                    var s = new OverrideGraphicSettings();
                    s.SetSurfaceTransparency(0);
                    s.SetHalftone(false);

                    var solidPattern = new FilteredElementCollector(doc)
                        .OfClass(typeof(FillPatternElement))
                        .Cast<FillPatternElement>()
                        .FirstOrDefault(fp => fp.GetFillPattern().IsSolidFill);

                    if (solidPattern != null)
                    {
                        s.SetSurfaceForegroundPatternId(solidPattern.Id);
                        s.SetSurfaceForegroundPatternColor(new Color(235, 235, 235));
                        s.SetCutForegroundPatternId(solidPattern.Id);
                        s.SetCutForegroundPatternColor(new Color(215, 215, 215));
                    }
                    s.SetProjectionLineColor(new Color(110, 110, 110));
                    s.SetProjectionLineWeight(1);
                    view.SetCategoryOverrides(floorCat.Id, s);
                }
            }
            catch { }

            BuiltInCategory[] archCats = new[]
            {
                BuiltInCategory.OST_Walls,
                BuiltInCategory.OST_Columns,
                BuiltInCategory.OST_StructuralColumns,
                BuiltInCategory.OST_StructuralFraming,
                BuiltInCategory.OST_Ceilings,
                BuiltInCategory.OST_Doors,
                BuiltInCategory.OST_Windows,
                BuiltInCategory.OST_Stairs,
                BuiltInCategory.OST_Railings,
                BuiltInCategory.OST_Roofs
            };

            foreach (var bic in archCats)
            {
                try
                {
                    var cat = Category.GetCategory(doc, bic);
                    if (cat != null && view.CanCategoryBeHidden(cat.Id))
                    {
                        if (archMode == "hidden")
                        {
                            view.SetCategoryHidden(cat.Id, true);
                        }
                        else
                        {
                            view.SetCategoryHidden(cat.Id, false);
                            var s = new OverrideGraphicSettings();
                            s.SetSurfaceTransparency(80);
                            s.SetHalftone(true);
                            view.SetCategoryOverrides(cat.Id, s);
                        }
                    }
                }
                catch { }
            }
        }
    }
}


