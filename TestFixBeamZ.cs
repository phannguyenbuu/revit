using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestFixBeamZ
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Delete test beam 2381869 if exists
            using (var txDel = new Transaction(doc, "Delete Test Beam"))
            {
                txDel.Start();
                var oldBeam = doc.GetElement(new ElementId(2381869L));
                if (oldBeam != null) doc.Delete(oldBeam.Id);
                txDel.Commit();
            }

            var lvl2 = doc.GetElement(new ElementId(694L)) as Level;
            var sym500 = doc.GetElement(new ElementId(185153L)) as FamilySymbol;

            FamilyInstance beam = null;
            using (var tx = new Transaction(doc, "Place Beam Exact Z"))
            {
                tx.Start();
                if (!sym500.IsActive) sym500.Activate();

                // Line at level elevation
                XYZ p0 = new XYZ(37.15 * M2FT, 0.1 * M2FT, lvl2.Elevation);
                XYZ p1 = new XYZ(37.15 * M2FT, 5.3 * M2FT, lvl2.Elevation);
                Line line = Line.CreateBound(p0, p1);

                beam = doc.Create.NewFamilyInstance(line, sym500, lvl2, StructuralType.Beam);

                // Set z offset to 0
                var pZOff = beam.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                if (pZOff != null && !pZOff.IsReadOnly) pZOff.Set(0.0);

                var pStartOff = beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION);
                if (pStartOff != null && !pStartOff.IsReadOnly) pStartOff.Set(0.0);

                var pEndOff = beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION);
                if (pEndOff != null && !pEndOff.IsReadOnly) pEndOff.Set(0.0);

                tx.Commit();
            }

            var bb = beam?.get_BoundingBox(null);
            double topElev = beam?.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP)?.AsDouble() * FT2M ?? 0;
            double botElev = beam?.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM)?.AsDouble() * FT2M ?? 0;

            return new
            {
                success = beam != null,
                beamId = beam?.Id.Value,
                name = beam?.Name,
                level = lvl2.Name,
                levelElevM = lvl2.Elevation * FT2M,
                topElevM = topElev,
                botElevM = botElev,
                bbMinZM = bb?.Min.Z * FT2M,
                bbMaxZM = bb?.Max.Z * FT2M
            };
        }
    }
}
