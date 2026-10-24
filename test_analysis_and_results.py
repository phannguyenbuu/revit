import sys
import comtypes.client
from comtypes.gen import ETABSv1

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def test_analysis_and_results():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO .EDB"
    print("Khởi động ETABS OAPI...")
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    print("Mở file mô hình:", edb_path)
    sap.File.OpenFile(edb_path)
    
    print("Chạy phân tích kết cấu (RunAnalysis)...")
    ret = sap.Analyze.RunAnalysis()
    print("Kết quả RunAnalysis code:", ret)
    print("Trạng thái khóa mô hình (Locked):", sap.GetModelIsLocked())
    
    # Thiết lập kết quả xuất cho tất cả tổ hợp Combos
    sap.Results.Setup.DeselectAllCasesAndCombosForOutput()
    sap.Results.Setup.SetComboSelectedForOutput("BAO", True)
    sap.Results.Setup.SetComboSelectedForOutput("Comb1", True)
    
    # 1. Trích xuất Chuyển vị tầng / Độ lệch tầng (Story Drift)
    print("\n=== 1. KIỂM TRA ĐỘ LỆCH TẦNG (STORY DRIFT) ===")
    drift_data = sap.Results.StoryDrifts()
    # drift_data returns: [NumberResults, Story, LoadCase, StepType, StepNum, Direction, Drift, Label, Ret]
    num_results = drift_data[0]
    print(f"Số lượng kết quả Drift: {num_results}")
    if num_results > 0:
        stories = drift_data[1]
        load_cases = drift_data[2]
        directions = drift_data[5]
        drifts = drift_data[6]
        
        max_drift = 0.0
        max_info = ""
        for i in range(num_results):
            d = abs(drifts[i])
            if d > max_drift:
                max_drift = d
                max_info = f"Tầng {stories[i]}, TH: {load_cases[i]}, Phương: {directions[i]}, Drift = {d:.6f}"
                
        print(f"Độ lệch tầng lớn nhất: {max_info}")
        # Giới hạn TCVN: 1/500 = 0.002
        tcvn_limit = 1.0 / 500.0
        if max_drift <= tcvn_limit:
            print(f"-> ĐÁNH GIÁ: THỎA MÃN ĐỘ CỨNG & AN TOÀN (Max Drift = {max_drift:.5f} <= [Drift] = {tcvn_limit:.5f} [1/500])")
        else:
            print(f"-> ĐÁNH GIÁ: VƯỢT GIỚI HẠN (Max Drift = {max_drift:.5f} > [Drift] = {tcvn_limit:.5f})")

    # 2. Trích xuất Moment dầm & cột (Frame Forces)
    print("\n=== 2. TRÍCH XUẤT MOMENT (M3) VÀ LỰC CẮT (V2) ===")
    # Lấy 1 dầm và 1 cột để kiểm tra
    frame_names = sap.FrameObj.GetNameList()[1]
    
    # Dầm ID 2, Dầm ID 3
    sample_beams = ['2', '3', '4']
    for beam_id in sample_beams:
        sec = sap.FrameObj.GetSection(beam_id)[0]
        # FrameForce: (NumberResults, Obj, ObjSta, Elm, ElmSta, LoadCase, StepType, StepNum, P, V2, V3, T, M2, M3, ret)
        forces = sap.Results.FrameForce(beam_id, 0)
        n_res = forces[0]
        if n_res > 0:
            stations = forces[2]
            combos_list = forces[5]
            p_list = forces[8]
            v2_list = forces[9]
            m3_list = forces[13]
            
            # Đơn vị trong ETABS: kN-mm hoặc N-mm -> chuyển sang kN.m
            # Ta kiểm tra đơn vị hiện tại
            # PresentUnits: 9 = N_mm_C -> Moment là N.mm = 1e-6 kN.m
            scale_m = 1e-6 if sap.GetPresentUnits() == 9 else 1.0
            scale_v = 1e-3 if sap.GetPresentUnits() == 9 else 1.0
            
            max_m3 = max(m3_list) * scale_m
            min_m3 = min(m3_list) * scale_m
            max_v2 = max([abs(v) for v in v2_list]) * scale_v
            
            print(f"\n * DẦM {beam_id} (Tiết diện {sec}):")
            print(f"   - Moment uốn max (+): M3_max = {max_m3:8.2f} kN.m (Moment bụng nhịp)")
            print(f"   - Moment uốn min (-): M3_min = {min_m3:8.2f} kN.m (Moment gối tựa)")
            print(f"   - Lực cắt lớn nhất  : V2_max = {max_v2:8.2f} kN")
            print(f"   - Số vị trí mặt cắt (Stations): {len(set(stations))}")

    # Cột ID 1
    sample_col = '1'
    sec_col = sap.FrameObj.GetSection(sample_col)[0]
    forces_col = sap.Results.FrameForce(sample_col, 0)
    if forces_col[0] > 0:
        scale_p = 1e-3 if sap.GetPresentUnits() == 9 else 1.0
        scale_m = 1e-6 if sap.GetPresentUnits() == 9 else 1.0
        p_col = forces_col[8]
        m3_col = forces_col[13]
        max_p = max([abs(p) for p in p_col]) * scale_p
        max_m = max([abs(m) for m in m3_col]) * scale_m
        print(f"\n * CỘT {sample_col} (Tiết diện {sec_col}):")
        print(f"   - Lực dọc lớn nhất  : P_max  = {max_p:8.2f} kN")
        print(f"   - Moment uốn lớn nhất: M3_max = {max_m:8.2f} kN.m")

    app.ApplicationExit(False)
    print("\nHoàn thành kiểm tra ETABS OAPI!")

if __name__ == "__main__":
    test_analysis_and_results()
