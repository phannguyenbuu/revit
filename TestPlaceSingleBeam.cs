using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestPlaceSingleBeam
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var lvl2 = doc.GetElement(new ElementId(694L)) as Level; // TẦNG 2 (3.6m)
            if (lvl2 == null) return new { error = "Level 2 not found" };

            var sym500 = doc.GetElement(new ElementId(185153L)) as FamilySymbol; // 220X500
            if (sym500 == null) return new { error = "Symbol 220X500 not found" };

            FamilyInstance beam = null;
            using (var tx = new Transaction(doc, "Test Place Beam"))
            {
                tx.Start();
                if (!sym500.IsActive) sym500.Activate();

                // Test beam from (37.15, 0.1) to (37.15, 5.3) at Level 2 (3.6m)
                XYZ p0 = new XYZ(37.15 * M2FT, 0.1 * M2FT, lvl2.Elevation);
                XYZ p1 = new XYZ(37.15 * M2FT, 5.3 * M2FT, lvl2.Elevation);
                Line line = Line.CreateBound(p0, p1);

                beam = doc.Create.NewFamilyInstance(line, sym500, lvl2, StructuralType.Beam);

                tx.Commit();
            }

            var bb = beam?.get_BoundingBox(null);

            return new
            {
                success = beam != null,
                beamId = beam?.Id.Value,
                name = beam?.Name,
                level = lvl2.Name,
                elevM = lvl2.Elevation * FT2M,
                zMinM = bb?.Min.Z * FT2M,
                zMaxM = bb?.Max.Z * FT2M
            };
        }
    }
}
