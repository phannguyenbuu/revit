using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCreateAnglePattern
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Check if already exists
            var existingDraft = FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Drafting, "ANGLE");
            var existingModel = FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "ANGLE");

            if (existingDraft != null || existingModel != null)
            {
                return new {
                    status = "already_exists",
                    draftId = existingDraft?.Id.Value,
                    modelId = existingModel?.Id.Value
                };
            }

            using (var t = new Transaction(doc, "Create ANGLE pattern"))
            {
                t.Start();
                try
                {
                    double spacing = 250.0 / 304.8;
                    // Angle 45 deg = PI / 4
                    var fp = new FillPattern("ANGLE", FillPatternTarget.Model, FillPatternHostOrientation.ToHost, Math.PI / 4.0, spacing, spacing);
                    var fpe = FillPatternElement.Create(doc, fp);
                    t.Commit();
                    return new { status = "created_model", id = fpe.Id.Value };
                }
                catch (Exception ex)
                {
                    t.RollBack();
                    return new { status = "error", message = ex.ToString() };
                }
            }
        }
    }
}
