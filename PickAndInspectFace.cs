using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Selection;

namespace RevitScript
{
    public static class PickAndInspectFace
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document in Revit" };

            try
            {
                // Prompt user to pick a face in Revit viewport
                Reference pickedRef = uidoc.Selection.PickObject(
                    ObjectType.Face, 
                    "Vui lòng CLICK CHỌN 1 MẶT trên Family trong khung nhìn Revit (hoặc nhấn Esc để hủy)..."
                );

                if (pickedRef == null)
                {
                    return new { success = false, message = "No face was picked" };
                }

                var elem = doc.GetElement(pickedRef.ElementId);
                var geomObj = elem?.GetGeometryObjectFromReference(pickedRef);
                var face = geomObj as Face;

                if (face == null)
                {
                    return new 
                    { 
                        success = false, 
                        message = "Could not resolve Face from reference", 
                        elemId = pickedRef.ElementId.Value,
                        geomType = geomObj?.GetType().Name 
                    };
                }

                // Analyze face
                string faceType = face.GetType().Name;
                double areaMm2 = face.Area * FT2MM * FT2MM;

                XYZ normal = XYZ.Zero;
                XYZ origin = XYZ.Zero;
                if (face is PlanarFace pf)
                {
                    normal = pf.FaceNormal;
                    origin = pf.Origin;
                }
                else
                {
                    var bboxUV = face.GetBoundingBox();
                    var midUV = (bboxUV.Min + bboxUV.Max) * 0.5;
                    normal = face.ComputeNormal(midUV);
                    origin = face.Evaluate(midUV);
                }

                // Calculate centroid and bounds from triangulation
                var mesh = face.Triangulate();
                var pts = new List<XYZ>();
                XYZ sumPt = XYZ.Zero;
                double minX = double.MaxValue, maxX = double.MinValue;
                double minY = double.MaxValue, maxY = double.MinValue;
                double minZ = double.MaxValue, maxZ = double.MinValue;

                if (mesh != null && mesh.Vertices.Count > 0)
                {
                    for (int i = 0; i < mesh.Vertices.Count; i++)
                    {
                        var pt = mesh.Vertices[i];
                        pts.Add(pt);
                        sumPt += pt;
                        if (pt.X < minX) minX = pt.X;
                        if (pt.X > maxX) maxX = pt.X;
                        if (pt.Y < minY) minY = pt.Y;
                        if (pt.Y > maxY) maxY = pt.Y;
                        if (pt.Z < minZ) minZ = pt.Z;
                        if (pt.Z > maxZ) maxZ = pt.Z;
                    }
                    sumPt = sumPt / mesh.Vertices.Count;
                }
                else
                {
                    sumPt = origin;
                    minX = maxX = origin.X;
                    minY = maxY = origin.Y;
                    minZ = maxZ = origin.Z;
                }

                // Highlight the face in Revit if possible using Paint or Material
                string paintStatus = "Not painted";
                try
                {
                    using (var tx = new Transaction(doc, "Highlight Selected Face"))
                    {
                        tx.Start();
                        // Find or create highlight material (Orange/Cyan)
                        var mat = new FilteredElementCollector(doc)
                            .OfClass(typeof(Material))
                            .Cast<Material>()
                            .FirstOrDefault(m => m.Name.Equals("AI_Selected_Face_Highlight", StringComparison.OrdinalIgnoreCase));

                        if (mat == null)
                        {
                            var matId = Material.Create(doc, "AI_Selected_Face_Highlight");
                            mat = doc.GetElement(matId) as Material;
                            if (mat != null)
                            {
                                mat.Color = new Color(255, 128, 0); // Orange
                                mat.Transparency = 0;
                            }
                        }

                        if (mat != null)
                        {
                            doc.Paint(elem.Id, face, mat.Id);
                            paintStatus = "Painted orange (AI_Selected_Face_Highlight)";
                        }
                        tx.Commit();
                    }
                }
                catch (Exception exPaint)
                {
                    paintStatus = "Paint failed: " + exPaint.Message;
                }

                // Export confirmation screenshot
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string outImg = Path.Combine(outDir, "revit_face_picked.png");
                try
                {
                    var opt3D = new ImageExportOptions
                    {
                        FilePath = outImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(opt3D);
                }
                catch { }

                return new
                {
                    success = true,
                    elementId = elem.Id.Value,
                    elementName = elem.Name,
                    category = elem.Category?.Name,
                    faceType,
                    paintStatus,
                    normal = $"({normal.X:F3}, {normal.Y:F3}, {normal.Z:F3})",
                    centroidMm = $"({sumPt.X * FT2MM:F1}, {sumPt.Y * FT2MM:F1}, {sumPt.Z * FT2MM:F1})",
                    bboxMinMm = $"({minX * FT2MM:F1}, {minY * FT2MM:F1}, {minZ * FT2MM:F1})",
                    bboxMaxMm = $"({maxX * FT2MM:F1}, {maxY * FT2MM:F1}, {maxZ * FT2MM:F1})",
                    areaMm2 = Math.Round(areaMm2, 1),
                    vertexCount = pts.Count,
                    image = outImg
                };
            }
            catch (Autodesk.Revit.Exceptions.OperationCanceledException)
            {
                return new { success = false, canceled = true, message = "Người dùng đã nhấn Esc (Hủy chọn mặt)" };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message, stackTrace = ex.StackTrace };
            }
        }
    }
}
