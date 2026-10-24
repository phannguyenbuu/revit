using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class LinkFloorPlanReference
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string dxfPath = @"D:\Dropbox\_Documents\RevitAI\FLOORPLAN_1.dxf";
            string dwgPath = @"D:\Dropbox\_Documents\RevitAI\FLOORPLAN_1.dwg";

            string filePath = File.Exists(dxfPath) ? dxfPath : dwgPath;
            if (!File.Exists(filePath))
            {
                return new { error = $"Neither DXF nor DWG found: {dxfPath}" };
            }

            // Find TẦNG TRỆT view
            var targetView = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name == "TẦNG TRỆT") 
                ?? (doc.ActiveView is ViewPlan ? doc.ActiveView : null);

            if (targetView == null)
            {
                return new { error = "Could not find TẦNG TRỆT view" };
            }

            var options = new DWGImportOptions
            {
                ColorMode = ImportColorMode.Preserved,
                Unit = ImportUnit.Millimeter,
                Placement = ImportPlacement.Origin,
                ThisViewOnly = false // Model-wide reference (Xref / Block)
            };

            ElementId linkInstanceId = ElementId.InvalidElementId;
            string usedFile = filePath;

            using (var tx = new Transaction(doc, "Link Reference Floor Plan"))
            {
                var fopts = tx.GetFailureHandlingOptions();
                fopts.SetFailuresPreprocessor(new GridWarningSwallower());
                tx.SetFailureHandlingOptions(fopts);

                tx.Start();
                try
                {
                    bool ok = doc.Link(filePath, options, targetView, out linkInstanceId);
                    if (!ok || linkInstanceId == ElementId.InvalidElementId)
                    {
                        // Fallback to DWG if DXF had an issue
                        if (filePath.EndsWith(".dxf", StringComparison.OrdinalIgnoreCase) && File.Exists(dwgPath))
                        {
                            usedFile = dwgPath;
                            doc.Link(dwgPath, options, targetView, out linkInstanceId);
                        }
                    }
                }
                catch (Exception ex)
                {
                    if (filePath.EndsWith(".dxf", StringComparison.OrdinalIgnoreCase) && File.Exists(dwgPath))
                    {
                        usedFile = dwgPath;
                        try
                        {
                            doc.Link(dwgPath, options, targetView, out linkInstanceId);
                        }
                        catch (Exception ex2)
                        {
                            tx.RollBack();
                            return new { error = $"Link failed for both DXF ({ex.Message}) and DWG ({ex2.Message})" };
                        }
                    }
                    else
                    {
                        tx.RollBack();
                        return new { error = ex.Message };
                    }
                }

                tx.Commit();
            }

            // Get link instance info
            ImportInstance? importInst = null;
            if (linkInstanceId != ElementId.InvalidElementId)
            {
                importInst = doc.GetElement(linkInstanceId) as ImportInstance;
            }

            var bb = importInst?.get_BoundingBox(null);

            return new
            {
                success = linkInstanceId != ElementId.InvalidElementId,
                usedFile = usedFile,
                linkInstanceId = linkInstanceId.Value,
                placedInView = targetView.Name,
                isLinked = importInst?.IsLinked ?? false,
                bbMinMeters = bb != null ? new double[] { bb.Min.X * 0.3048, bb.Min.Y * 0.3048, bb.Min.Z * 0.3048 } : null,
                bbMaxMeters = bb != null ? new double[] { bb.Max.X * 0.3048, bb.Max.Y * 0.3048, bb.Max.Z * 0.3048 } : null
            };
        }
    }
}
