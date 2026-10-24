using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class GenerateMepBimModel
    {
        private const double MM2FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null)
            {
                return new { success = false, error = "Không tìm thấy tài liệu Revit đang hoạt động!" };
            }

            // Đọc tham số đầu vào (nếu có)
            double widthMm = 12000.0;
            double depthMm = 8000.0;
            double heightMm = 3600.0;
            int numFloors = 2;
            string ifcFilePath = "";

            if (args.ValueKind == JsonValueKind.Object)
            {
                if (args.TryGetProperty("width_mm", out var pW)) widthMm = pW.GetDouble();
                if (args.TryGetProperty("depth_mm", out var pD)) depthMm = pD.GetDouble();
                if (args.TryGetProperty("height_mm", out var pH)) heightMm = pH.GetDouble();
                if (args.TryGetProperty("num_floors", out var pF)) numFloors = pF.GetInt32();
                if (args.TryGetProperty("ifc_file_path", out var pIfc)) ifcFilePath = pIfc.GetString() ?? "";
            }

            var defaultIfc = Path.Combine(@"D:\Dropbox\_Documents\RevitAI\exports\mep_bim", "ToaNha_BIM_MEP_12x8m.ifc");
            if (string.IsNullOrEmpty(ifcFilePath) && File.Exists(defaultIfc))
            {
                ifcFilePath = defaultIfc;
            }

            var createdElements = new List<string>();

            // Lấy Level cơ sở
            var level = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault();

            if (level == null)
            {
                return new { success = false, error = "Dự án Revit chưa có Level nào!" };
            }

            using (var trans = new Transaction(doc, "RevitAI: Dựng Mô Hình MEP 3D Tự Động"))
            {
                trans.Start();

                try
                {
                    // 1. Dựng Tuyến Ống Gió Cấp (Duct - HVAC Supply)
                    var ductType = new FilteredElementCollector(doc)
                        .OfClass(typeof(DuctType))
                        .Cast<DuctType>()
                        .FirstOrDefault();

                    var mepSystemTypeHvac = new FilteredElementCollector(doc)
                        .OfClass(typeof(MEPSystemType))
                        .Cast<MEPSystemType>()
                        .FirstOrDefault(s => s.SystemClassification == MEPSystemClassification.SupplyAir);

                    if (ductType != null && mepSystemTypeHvac != null)
                    {
                        var ptStart = new XYZ(2000.0 * MM2FT, 4000.0 * MM2FT, 2900.0 * MM2FT);
                        var ptEnd = new XYZ(8000.0 * MM2FT, 4000.0 * MM2FT, 2900.0 * MM2FT);
                        var duct = Duct.Create(doc, mepSystemTypeHvac.Id, ductType.Id, level.Id, ptStart, ptEnd);
                        if (duct != null)
                        {
                            duct.get_Parameter(BuiltInParameter.RBS_CURVE_WIDTH_PARAM)?.Set(500.0 * MM2FT);
                            duct.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM)?.Set(250.0 * MM2FT);
                            createdElements.Add($"Duct SA 500x250 (ID: {duct.Id})");
                        }
                    }

                    // 2. Dựng Tuyến Ống Cấp Nước Lạnh (Pipe - DCW PPR)
                    var pipeType = new FilteredElementCollector(doc)
                        .OfClass(typeof(PipeType))
                        .Cast<PipeType>()
                        .FirstOrDefault();

                    var mepSystemTypePlumb = new FilteredElementCollector(doc)
                        .OfClass(typeof(MEPSystemType))
                        .Cast<MEPSystemType>()
                        .FirstOrDefault(s => s.SystemClassification == MEPSystemClassification.DomesticColdWater);

                    if (pipeType != null && mepSystemTypePlumb != null)
                    {
                        var ptP1 = new XYZ(1000.0 * MM2FT, 2000.0 * MM2FT, 3200.0 * MM2FT);
                        var ptP2 = new XYZ(7000.0 * MM2FT, 2000.0 * MM2FT, 3200.0 * MM2FT);
                        var pipe = Pipe.Create(doc, mepSystemTypePlumb.Id, pipeType.Id, level.Id, ptP1, ptP2);
                        if (pipe != null)
                        {
                            pipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM)?.Set(32.0 * MM2FT);
                            createdElements.Add($"Pipe DCW DN25 (ID: {pipe.Id})");
                        }
                    }

                    // 3. Dựng Tuyến Máng Cáp Điện (Cable Tray)
                    var trayType = new FilteredElementCollector(doc)
                        .OfClass(typeof(CableTrayType))
                        .Cast<CableTrayType>()
                        .FirstOrDefault();

                    if (trayType != null)
                    {
                        var ptT1 = new XYZ(1500.0 * MM2FT, 4500.0 * MM2FT, 3150.0 * MM2FT);
                        var ptT2 = new XYZ(8500.0 * MM2FT, 4500.0 * MM2FT, 3150.0 * MM2FT);
                        var tray = CableTray.Create(doc, trayType.Id, ptT1, ptT2, level.Id);
                        if (tray != null)
                        {
                            tray.get_Parameter(BuiltInParameter.RBS_CABLETRAY_WIDTH_PARAM)?.Set(300.0 * MM2FT);
                            tray.get_Parameter(BuiltInParameter.RBS_CABLETRAY_HEIGHT_PARAM)?.Set(100.0 * MM2FT);
                            createdElements.Add($"Cable Tray 300x100 (ID: {tray.Id})");
                        }
                    }

                    trans.Commit();
                }
                catch (Exception ex)
                {
                    trans.RollBack();
                    return new { success = false, error = "Lỗi khi tạo đối tượng MEP trong Revit: " + ex.Message };
                }
            }

            return new
            {
                success = true,
                message = "Đã tạo thành công các đối tượng MEP BIM trực tiếp trong tài liệu Revit!",
                created_elements = createdElements,
                total_created = createdElements.Count,
                ifc_file_ready = ifcFilePath
            };
        }
    }
}
