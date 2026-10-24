using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectActiveViewAndRange
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                var activeView = uidoc.ActiveView;
                string viewType = activeView.ViewType.ToString();
                string viewName = activeView.Name;

                if (activeView is ViewPlan planView)
                {
                    var vr = planView.GetViewRange();
                    double cutOffsetM = vr.GetOffset(PlanViewPlane.CutPlane) * FT2M;
                    double topOffsetM = vr.GetOffset(PlanViewPlane.TopClipPlane) * FT2M;
                    double bottomOffsetM = vr.GetOffset(PlanViewPlane.BottomClipPlane) * FT2M;
                    double depthOffsetM = vr.GetOffset(PlanViewPlane.ViewDepthPlane) * FT2M;

                    return new
                    {
                        isPlan = true,
                        viewName,
                        viewType,
                        cutOffsetM,
                        topOffsetM,
                        bottomOffsetM,
                        depthOffsetM
                    };
                }
                else if (activeView is View3D view3D)
                {
                    bool isSectionBoxActive = view3D.IsSectionBoxActive;
                    BoundingBoxXYZ sb = isSectionBoxActive ? view3D.GetSectionBox() : null;
                    return new
                    {
                        is3D = true,
                        viewName,
                        viewType,
                        isSectionBoxActive,
                        minZ = sb != null ? sb.Min.Z * FT2M : double.NaN,
                        maxZ = sb != null ? sb.Max.Z * FT2M : double.NaN
                    };
                }
                else
                {
                    return new
                    {
                        isOther = true,
                        viewName,
                        viewType
                    };
                }
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
