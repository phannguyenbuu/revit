import math
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Concrete B25 (TCVN 5574:2018)
Rb = 14.5  # MPa
Rs = 350   # MPa (CB400-V)
Es = 200000 # MPa

# Loads
q_floor_dl = 7.5  # kN/m2 (Sàn 100mm + hoàn thiện + dầm quy đổi + tường quy đổi)
q_floor_ll = 2.4  # kN/m2 (Văn phòng CBCS có hệ số gamma_f = 1.2)
q_floor = q_floor_dl + q_floor_ll # 9.9 ~ 10.0 kN/m2
# Tường bao che và tường ngăn tập trung trên dầm được tính cụ thể:
# Hoặc tổng tải quy ước an toàn:
q_story_typical = 12.0 # kN/m2
q_story_roof = 8.5     # kN/m2

columns = {
    'Cột giữa (B, C)': {'Strib': 14.04, 'k_ecc': 1.20, 'desc': 'Trục B2-B10, C2-C10'},
    'Cột biên (A, D)': {'Strib': 9.72,  'k_ecc': 1.35, 'desc': 'Trục A2-A10, D2-D10'},
    'Cột góc (A1, A11, D1, D11)': {'Strib': 5.13, 'k_ecc': 1.55, 'desc': 'Trục 1-A, 1-D, 11-A, 11-D'},
    'Cột thang (E)':   {'Strib': 6.30,  'k_ecc': 1.30, 'desc': 'Trục E2-E3, E9-E10'}
}

levels = [
    ('Tầng 1 (0.000 -> +3.600m)', 4, 3.6),
    ('Tầng 2 (+3.600 -> +7.200m)', 3, 3.6),
    ('Tầng 3 (+7.200 -> +10.800m)', 2, 3.6),
    ('Tầng 4 (+10.800 -> +14.400m)', 1, 3.6),
    ('Tầng Tum (+14.400 -> +17.200m)', 0.6, 2.8)
]

print('| Vị trí cột | Tầng | S_trib (m²) | N tích lũy (kN) | A_c yêu cầu (cm²) | Tiết diện đề xuất (mm) | A_c thực tế (cm²) | Hệ số nén ν = N/(Rb·Ac) | Thép dự kiến |')
print('| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |')

results = []

for c_name, c_data in columns.items():
    strib = c_data['Strib']
    k_ecc = c_data['k_ecc']
    
    for l_name, n_floors, h_story in levels:
        if 'Tum' in l_name and 'góc' in c_name.lower():
            continue
        if 'Tum' in l_name and 'biên' in c_name.lower():
            continue
            
        # Cumulative vertical load
        if n_floors == 4:
            q_sum = 3 * q_story_typical + q_story_roof
        elif n_floors == 3:
            q_sum = 2 * q_story_typical + q_story_roof
        elif n_floors == 2:
            q_sum = 1 * q_story_typical + q_story_roof
        elif n_floors == 1:
            q_sum = q_story_roof
        else:
            q_sum = q_story_roof * 0.6
            
        # Self-weight of column stack
        sw_col = n_floors * 3.6 * (0.25 * 0.35 * 25) * 1.1
        N = round(q_sum * strib + sw_col, 1)
        
        # Required area (cm2) with Rb in kN/cm2 (1.45 kN/cm2)
        A_req = round((k_ecc * N) / (Rb / 10.0), 1)
        
        # Choose standardized section
        # Constraints: b >= 200, matches walls 200/220
        if 'giữa' in c_name.lower():
            if 'Tầng 1' in l_name:
                b, h = 250, 400
                rebar = '8Φ18 (μ=1.8%)'
            elif 'Tầng 2' in l_name:
                b, h = 250, 350
                rebar = '6Φ18 (μ=1.5%)'
            elif 'Tầng 3' in l_name:
                b, h = 220, 300
                rebar = '6Φ16 (μ=1.6%)'
            elif 'Tầng 4' in l_name:
                b, h = 200, 250
                rebar = '4Φ16 (μ=1.4%)'
            else:
                b, h = 200, 200
                rebar = '4Φ14 (μ=1.3%)'
        elif 'biên' in c_name.lower():
            if 'Tầng 1' in l_name:
                b, h = 250, 350
                rebar = '6Φ18 (μ=1.5%)'
            elif 'Tầng 2' in l_name:
                b, h = 220, 300
                rebar = '6Φ16 (μ=1.6%)'
            elif 'Tầng 3' in l_name:
                b, h = 200, 250
                rebar = '4Φ16 (μ=1.4%)'
            else:
                b, h = 200, 200
                rebar = '4Φ14 (μ=1.3%)'
        elif 'góc' in c_name.lower():
            if 'Tầng 1' in l_name:
                b, h = 220, 250
                rebar = '4Φ18 (μ=1.6%)'
            else:
                b, h = 200, 200
                rebar = '4Φ14 (μ=1.3%)'
        else: # Thang E
            b, h = 200, 200
            rebar = '4Φ14 (μ=1.3%)'
            
        A_prov = (b * h) / 100.0
        nu = round(N / (Rb * 1000 * (b * h * 1e-6)), 2)
        
        t_short = l_name.split(' ')[0] + ' ' + l_name.split(' ')[1]
        print(f'| **{c_name}** | {t_short} | {strib} | {N} | {A_req} | **{b} × {h}** | {A_prov:.0f} | {nu} | {rebar} |')
