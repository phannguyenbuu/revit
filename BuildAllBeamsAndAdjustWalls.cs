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
    public class BeamsWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            failuresAccessor.DeleteAllWarnings();
            return FailureProcessingResult.Continue;
        }
    }

    public static class BuildAllBeamsAndAdjustWalls
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public class BeamSpec
        {
            public long lvlId { get; set; }
            public string lvlName { get; set; } = "";
            public string type { get; set; } = "";
            public double[] p0 { get; set; } = new double[2];
            public double[] p1 { get; set; } = new double[2];
            public string tag { get; set; } = "";
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            string specPath = @"D:\Dropbox\_Documents\RevitAI\beam_specs.json";
            if (!File.Exists(specPath)) return new { error = $"Specs file not found: {specPath}" };

            var jsonText = File.ReadAllText(specPath);
            var beamSpecs = JsonSerializer.Deserialize<List<BeamSpec>>(jsonText);
            if (beamSpecs == null || beamSpecs.Count == 0) return new { error = "No beam specs loaded" };

            // 1. CLEANUP: Delete duplicate column 2379808 and old test beams
            int deletedOldBeams = 0;
            bool deletedDupCol = false;
            using (var txClean = new Transaction(doc, "Cleanup Duplicate Elements"))
            {
                txClean.Start();
                var dupCol = doc.GetElement(new ElementId(2379808L));
                if (dupCol != null)
                {
                    doc.Delete(dupCol.Id);
                    deletedDupCol = true;
                }

                var existingBeams = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralFraming)
                    .WhereElementIsNotElementType()
                    .ToElementIds();
                
                foreach (var bid in existingBeams)
                {
                    doc.Delete(bid);
                    deletedOldBeams++;
                }
                txClean.Commit();
            }

            // 2. LOAD SYMBOLS
            var sym500 = doc.GetElement(new ElementId(185153L)) as FamilySymbol;
            var sym350 = doc.GetElement(new ElementId(456521L)) as FamilySymbol;
            if (sym500 == null || sym350 == null)
            {
                return new { error = "Beam symbols 185153 (220X500) or 456521 (220X350) not found" };
            }

            // 3. CREATE BEAMS
            int createdBeams = 0;
            var createdIds = new List<long>();
            var beamsByLevel = new Dictionary<string, int>();

            using (var txBeams = new Transaction(doc, "Create All Structural Beams"))
            {
                var failOpts = txBeams.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new BeamsWarningSwallower());
                failOpts.SetClearAfterRollback(true);
                txBeams.SetFailureHandlingOptions(failOpts);

                txBeams.Start();

                if (!sym500.IsActive) sym500.Activate();
                if (!sym350.IsActive) sym350.Activate();

                foreach (var spec in beamSpecs)
                {
                    var lvl = doc.GetElement(new ElementId(spec.lvlId)) as Level;
                    if (lvl == null) continue;

                    var sym = spec.type.Contains("500") ? sym500 : sym350;

                    // Convert mm to feet
                    double x0 = (spec.p0[0] / 1000.0) * M2FT;
                    double y0 = (spec.p0[1] / 1000.0) * M2FT;
                    double x1 = (spec.p1[0] / 1000.0) * M2FT;
                    double y1 = (spec.p1[1] / 1000.0) * M2FT;

                    var p0 = new XYZ(x0, y0, lvl.Elevation);
                    var p1 = new XYZ(x1, y1, lvl.Elevation);

                    if (p0.DistanceTo(p1) < 0.1) continue;

                    var line = Line.CreateBound(p0, p1);
                    var beam = doc.Create.NewFamilyInstance(line, sym, lvl, StructuralType.Beam);

                    var pZOff = beam.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                    if (pZOff != null && !pZOff.IsReadOnly) pZOff.Set(0.0);

                    var p0Off = beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION);
                    if (p0Off != null && !p0Off.IsReadOnly) p0Off.Set(0.0);

                    var p1Off = beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION);
                    if (p1Off != null && !p1Off.IsReadOnly) p1Off.Set(0.0);

                    createdBeams++;
                    createdIds.Add(beam.Id.Value);

                    if (!beamsByLevel.ContainsKey(spec.lvlName)) beamsByLevel[spec.lvlName] = 0;
                    beamsByLevel[spec.lvlName]++;
                }

                txBeams.Commit();
            }

            // 4. ADJUST WALL TOP OFFSETS
            int adjustedWalls = 0;
            var wallsSummary = new Dictionary<string, int>();

            double[] X_AXES = new double[] { 550, 4350, 8050, 11650, 15250, 18850, 22450, 26050, 29650, 33350, 37150 };

            using (var txWalls = new Transaction(doc, "Adjust Wall Heights to Beam Bottom"))
            {
                var failOpts = txWalls.GetFailureHandlingOptions();
                failOpts.SetFailuresPreprocessor(new BeamsWarningSwallower());
                failOpts.SetClearAfterRollback(true);
                txWalls.SetFailureHandlingOptions(failOpts);

                txWalls.Start();

                var allWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .ToList();

                foreach (var w in allWalls)
                {
                    var tLvlId = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId();
                    if (tLvlId == null || tLvlId == ElementId.InvalidElementId) continue;

                    var pTopOff = w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                    if (pTopOff == null || pTopOff.IsReadOnly) continue;

                    double currentOffMm = pTopOff.AsDouble() * FT2M * 1000.0;
                    // Skip facade decorative pilasters (top offset = 1500mm)
                    if (currentOffMm > 500.0) continue;

                    var lc = w.Location as LocationCurve;
                    if (lc == null) continue;

                    double x0 = lc.Curve.GetEndPoint(0).X * FT2M * 1000.0;
                    double y0 = lc.Curve.GetEndPoint(0).Y * FT2M * 1000.0;
                    double x1 = lc.Curve.GetEndPoint(1).X * FT2M * 1000.0;
                    double y1 = lc.Curve.GetEndPoint(1).Y * FT2M * 1000.0;

                    double dx = Math.Abs(x1 - x0);
                    double dy = Math.Abs(y1 - y0);
                    double midX = (x0 + x1) / 2.0;
                    double midY = (y0 + y1) / 2.0;

                    double targetOffMm = -100.0; // default for partition wall under 100mm slab
                    string cat = "Slab-100";

                    if (dx > dy)
                    {
                        // Wall parallel to X (along Y = const)
                        if (Math.Abs(midY - 0) < 250 || Math.Abs(midY - 100) < 250) { targetOffMm = -350.0; cat = "Beam-350-TrucA"; }
                        else if (Math.Abs(midY - 5300) < 250 || Math.Abs(midY - 5400) < 250) { targetOffMm = -350.0; cat = "Beam-350-TrucB"; }
                        else if (Math.Abs(midY - 7800) < 250 || Math.Abs(midY - 7900) < 250) { targetOffMm = -350.0; cat = "Beam-350-TrucC"; }
                        else if (Math.Abs(midY - 13100) < 250 || Math.Abs(midY - 13200) < 250) { targetOffMm = -350.0; cat = "Beam-350-TrucD"; }
                        else if (Math.Abs(midY - 14900) < 250) { targetOffMm = -350.0; cat = "Beam-350-TrucE"; }
                    }
                    else
                    {
                        // Wall parallel to Y (along X = const)
                        bool nearAxis = X_AXES.Any(ax => Math.Abs(midX - ax) < 250);
                        if (nearAxis)
                        {
                            if (midY < 5350) { targetOffMm = -500.0; cat = "Beam-500-SpanAB"; }
                            else if (midY <= 7950) { targetOffMm = -350.0; cat = "Beam-350-SpanBC"; }
                            else if (midY <= 13150) { targetOffMm = -500.0; cat = "Beam-500-SpanCD"; }
                            else { targetOffMm = -350.0; cat = "Beam-350-SpanDE"; }
                        }
                    }

                    // Apply offset
                    pTopOff.Set((targetOffMm / 1000.0) * M2FT);
                    adjustedWalls++;

                    if (!wallsSummary.ContainsKey(cat)) wallsSummary[cat] = 0;
                    wallsSummary[cat]++;
                }

                txWalls.Commit();
            }

            return new
            {
                success = true,
                deletedDupCol,
                deletedOldBeams,
                createdBeams,
                beamsByLevel,
                adjustedWalls,
                wallsSummary
            };
        }
    }
}
