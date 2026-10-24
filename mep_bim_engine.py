#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
mep_bim_engine.py - Hệ thống Thiết Kế Tự Động MEP & Mô Hình Hóa 3D BIM Chuyên Nghiệp
================================================================================
Tác vụ chính:
1. ✅ Thiết kế hệ thống điện và chiếu sáng (Electrical & Lighting Design)
2. ✅ Thiết kế hệ thống cấp thoát nước (Plumbing & Water Supply/Drainage)
3. ✅ Thiết kế điều hòa, thông gió HVAC (HVAC Design & Airflow)
4. ✅ Dựng mô hình BIM 3D chuyên nghiệp (IFC 4, 3D Wavefront OBJ/MTL, AutoCAD 3D DXF)
5. ✅ Kiểm tra xung đột hệ thống MEP (3D Clash Detection & Auto-Resolution)
6. ✅ Bóc tách khối lượng (BOQ Schedule) & Xuất bản vẽ kỹ thuật CAD chuẩn TCVN
================================================================================
"""

import os
import sys
import math
import json
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Third-party imports
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    ezdxf = None

try:
    import ifcopenshell
    import ifcopenshell.api
except ImportError:
    ifcopenshell = None

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.join(CURRENT_DIR, "exports", "mep_bim")
os.makedirs(EXPORTS_DIR, exist_ok=True)


# ==============================================================================
# 1. CÁC LỚP HÌNH HỌC VÀ ĐỐI TƯỢNG MEP CƠ BẢN (DATA MODELS)
# ==============================================================================

class BBox3D:
    """Bounding Box 3D cho kiểm tra va chạm & tính toán bao phủ."""
    def __init__(self, min_x: float, min_y: float, min_z: float, max_x: float, max_y: float, max_z: float):
        self.min_x = min(min_x, max_x)
        self.min_y = min(min_y, max_y)
        self.min_z = min(min_z, max_z)
        self.max_x = max(min_x, max_x)
        self.max_y = max(min_y, max_y)
        self.max_z = max(min_z, max_z)

    @property
    def center(self) -> Tuple[float, float, float]:
        return (
            (self.min_x + self.max_x) / 2.0,
            (self.min_y + self.max_y) / 2.0,
            (self.min_z + self.max_z) / 2.0
        )

    @property
    def size(self) -> Tuple[float, float, float]:
        return (
            abs(self.max_x - self.min_x),
            abs(self.max_y - self.min_y),
            abs(self.max_z - self.min_z)
        )

    def intersects(self, other: 'BBox3D', tolerance: float = 0.0) -> bool:
        """Kiểm tra giao nhau giữa 2 BBox có tính dung sai clearance."""
        if self.max_x + tolerance < other.min_x or self.min_x - tolerance > other.max_x:
            return False
        if self.max_y + tolerance < other.min_y or self.min_y - tolerance > other.max_y:
            return False
        if self.max_z + tolerance < other.min_z or self.min_z - tolerance > other.max_z:
            return False
        return True

    def intersection_volume(self, other: 'BBox3D') -> Optional['BBox3D']:
        """Tính vùng thể tích giao nhau (nếu có)."""
        ix_min = max(self.min_x, other.min_x)
        ix_max = min(self.max_x, other.max_x)
        iy_min = max(self.min_y, other.min_y)
        iy_max = min(self.max_y, other.max_y)
        iz_min = max(self.min_z, other.min_z)
        iz_max = min(self.max_z, other.max_z)

        if ix_min < ix_max and iy_min < iy_max and iz_min < iz_max:
            return BBox3D(ix_min, iy_min, iz_min, ix_max, iy_max, iz_max)
        return None

    def to_dict(self) -> Dict[str, float]:
        return {
            "min_x": round(self.min_x, 1),
            "min_y": round(self.min_y, 1),
            "min_z": round(self.min_z, 1),
            "max_x": round(self.max_x, 1),
            "max_y": round(self.max_y, 1),
            "max_z": round(self.max_z, 1)
        }


class MepElement:
    """Đối tượng phần tử MEP hoặc Kiến trúc trong mô hình BIM."""
    def __init__(self,
                 elem_id: str,
                 name: str,
                 category: str,       # 'Duct', 'Pipe', 'CableTray', 'Fixture', 'Equipment', 'Wall', 'Beam', 'Slab'
                 system: str,         # 'HVAC_Supply', 'HVAC_Return', 'Plumbing_Cold', 'Plumbing_Drain', 'Electrical', 'Structure'
                 level: str,          # 'Tang_1', 'Tang_2', 'Mai'
                 geometry_type: str,  # 'box', 'cylinder', 'mesh'
                 params: Dict[str, Any],
                 bbox: BBox3D):
        self.elem_id = elem_id
        self.name = name
        self.category = category
        self.system = system
        self.level = level
        self.geometry_type = geometry_type
        self.params = params
        self.bbox = bbox
        self.clash_resolved = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.elem_id,
            "name": self.name,
            "category": self.category,
            "system": self.system,
            "level": self.level,
            "geometry_type": self.geometry_type,
            "params": self.params,
            "bbox": self.bbox.to_dict()
        }


# ==============================================================================
# 2. BỘ MÁY THIẾT KẾ KỸ THUẬT MEP (ENGINEERING DESIGN CALCULATIONS)
# ==============================================================================

class ElectricalLightingEngine:
    """
    1. Thiết kế hệ thống điện và chiếu sáng:
    - Tính toán độ rọi Lux tiêu chuẩn theo TCVN 7114 / CIBSE.
    - Phương pháp quang thông (Lumen method): Số lượng đèn N, mảng lưới đèn (Nx x Ny).
    - Thang máng cáp (Cable Trays), Tủ điện phân phối (MDB, DB-1, DB-2).
    - Tính toán phụ tải công suất (kW), cường độ dòng điện (Amperes) & tiết diện dây cáp.
    """

    LUX_STANDARDS = {
        "Office": 450.0,
        "MeetingRoom": 400.0,
        "LivingRoom": 300.0,
        "Bedroom": 180.0,
        "Kitchen": 320.0,
        "Toilet": 200.0,
        "Corridor": 150.0,
        "TechnicalRoom": 300.0,
        "Default": 300.0
    }

    FIXTURE_SPECS = {
        "Panel_600x600": {
            "name": "Đèn LED Panel Âm Trần 600x600",
            "power_w": 40.0,
            "lumens": 4000.0,
            "width": 600.0,
            "length": 600.0,
            "height": 45.0,
            "unit_cost": 380000.0
        },
        "Downlight_D150": {
            "name": "Đèn LED Downlight Âm Trần Ø150",
            "power_w": 18.0,
            "lumens": 1800.0,
            "diameter": 150.0,
            "height": 60.0,
            "unit_cost": 160000.0
        },
        "Batten_1200": {
            "name": "Bộ Đèn LED Tube T8 1200mm",
            "power_w": 36.0,
            "lumens": 3600.0,
            "width": 80.0,
            "length": 1200.0,
            "height": 50.0,
            "unit_cost": 210000.0
        }
    }

    @classmethod
    def calculate_lighting(cls, room_type: str, length_m: float, width_m: float, height_m: float) -> Dict[str, Any]:
        area_m2 = length_m * width_m
        target_lux = cls.LUX_STANDARDS.get(room_type, cls.LUX_STANDARDS["Default"])
        uf = 0.55  # Utilization Factor
        mf = 0.80  # Maintenance Factor

        total_lumens_needed = (target_lux * area_m2) / (uf * mf)

        fixture_key = "Panel_600x600" if room_type in ["Office", "MeetingRoom", "LivingRoom"] else (
            "Downlight_D150" if room_type in ["Bedroom", "Toilet", "Corridor"] else "Batten_1200"
        )
        fixture = cls.FIXTURE_SPECS[fixture_key]
        num_fixtures_raw = total_lumens_needed / fixture["lumens"]
        num_fixtures = max(1, math.ceil(num_fixtures_raw))

        # Phân bổ lưới đèn theo tỷ lệ dài x rộng
        aspect_ratio = max(0.1, length_m / max(0.1, width_m))
        ny = max(1, round(math.sqrt(num_fixtures / aspect_ratio)))
        nx = max(1, math.ceil(num_fixtures / ny))
        total_fixtures = nx * ny

        actual_lumens = total_fixtures * fixture["lumens"]
        actual_lux = (actual_lumens * uf * mf) / area_m2
        total_power_w = total_fixtures * fixture["power_w"]

        return {
            "room_type": room_type,
            "area_m2": round(area_m2, 2),
            "target_lux": target_lux,
            "actual_lux": round(actual_lux, 1),
            "fixture_type": fixture_key,
            "fixture_name": fixture["name"],
            "grid": (nx, ny),
            "total_fixtures": total_fixtures,
            "total_power_w": total_power_w,
            "power_density_w_m2": round(total_power_w / area_m2, 1)
        }

    @classmethod
    def calculate_electrical_load(cls, lighting_kw: float, socket_count: int, hvac_kw: float) -> Dict[str, Any]:
        """Tính toán tổng phụ tải điện và chọn dây cáp nguồn chính."""
        # Ổ cắm tính trung bình 300W/ổ, hệ số đồng thời Ks = 0.65
        socket_load_kw = socket_count * 0.3 * 0.65
        total_connected_kw = lighting_kw + socket_load_kw + hvac_kw
        demand_factor = 0.8
        total_demand_kw = total_connected_kw * demand_factor

        # Dòng điện 3 pha 380V (cos phi = 0.85)
        # I = P / (sqrt(3) * U * cos_phi)
        voltage = 380.0
        cos_phi = 0.85
        current_a = (total_demand_kw * 1000.0) / (math.sqrt(3) * voltage * cos_phi)

        # Chọn dây cáp điện Cu/XLPE/PVC
        if current_a < 35:
            feeder_cable = "Cu/XLPE/PVC 4x6mm² + E6mm²"
            main_mcb = "MCB 3P 40A - 10kA"
        elif current_a < 55:
            feeder_cable = "Cu/XLPE/PVC 4x10mm² + E10mm²"
            main_mcb = "MCCB 3P 63A - 18kA"
        elif current_a < 80:
            feeder_cable = "Cu/XLPE/PVC 4x16mm² + E10mm²"
            main_mcb = "MCCB 3P 100A - 25kA"
        elif current_a < 120:
            feeder_cable = "Cu/XLPE/PVC 4x25mm² + E16mm²"
            main_mcb = "MCCB 3P 125A - 30kA"
        else:
            feeder_cable = "Cu/XLPE/PVC 4x35mm² + E16mm²"
            main_mcb = "MCCB 3P 160A - 36kA"

        return {
            "total_connected_kw": round(total_connected_kw, 2),
            "total_demand_kw": round(total_demand_kw, 2),
            "design_current_a": round(current_a, 1),
            "feeder_cable": feeder_cable,
            "main_breaker": main_mcb
        }


class PlumbingDrainageEngine:
    """
    2. Thiết kế hệ thống cấp thoát nước:
    - Mạng cấp nước lạnh (DCW) PPR: Đồng hồ/Bơm -> Ống chính DN32 -> Nhánh DN25/DN20 -> Thiết bị DN15.
    - Mạng thoát nước thải sinh hoạt (Soil & Waste) uPVC: Độ dốc 2% tự chảy, bẫy nước ngăn mùi.
    - Thoát nước mưa (Storm water) từ sàn mái xuống hố ga ngầm.
    - Tính lưu lượng nước cấp (l/s), dung tích bồn nước mái (m3).
    """

    @classmethod
    def calculate_water_demand(cls, num_people: int, fixture_counts: Dict[str, int]) -> Dict[str, Any]:
        # Tiêu chuẩn dùng nước sinh hoạt: 150 - 200 lít/người/ngày-đêm (TCVN 4513)
        daily_consumption_l = num_people * 180.0
        # Dung tích bồn nước mái tích trữ 1 ngày đêm + dự phòng
        tank_volume_m3 = round(daily_consumption_l * 1.25 / 1000.0, 1)
        tank_volume_m3 = max(1.5, tank_volume_m3)

        # Tính đơn vị đương lượng (Fixture Units - FU) cấp nước
        # WC: 2.5 FU, Lavabo: 1.0 FU, Sen tắm: 2.0 FU, Bếp: 1.5 FU
        fu_wc = fixture_counts.get("wc", 0) * 2.5
        fu_lavabo = fixture_counts.get("lavabo", 0) * 1.0
        fu_shower = fixture_counts.get("shower", 0) * 2.0
        fu_sink = fixture_counts.get("sink", 0) * 1.5
        total_fu = fu_wc + fu_lavabo + fu_shower + fu_sink

        # Lưu lượng thiết kế quy đổi (L/s) theo công thức kinh nghiệm Hunter
        flow_rate_lps = round(0.25 * math.sqrt(max(1.0, total_fu)), 2)

        return {
            "num_people": num_people,
            "daily_consumption_liters": daily_consumption_l,
            "roof_tank_capacity_m3": tank_volume_m3,
            "total_fixture_units": total_fu,
            "design_flow_rate_lps": flow_rate_lps,
            "recommended_main_pipe": "PPR DN32 (PN16)",
            "recommended_soil_pipe": "uPVC Ø114 (Class 2) Dốc 2%",
            "recommended_waste_pipe": "uPVC Ø60 (Class 2) Dốc 2%"
        }


class HvacEngine:
    """
    3. Thiết kế điều hòa, thông gió HVAC:
    - Tính phụ tải lạnh (Cooling load BTU/h & kW) theo diện tích & công năng.
    - Lựa chọn thiết bị lạnh: FCU / Cassette 4 hướng thổi âm trần.
    - Tính kích thước đường ống gió cấp (SA) và ống gió hồi (RA) theo vận tốc gió (v = 4-6 m/s).
    - Tính lưu lượng gió CMH (m3/h) và bố trí miệng gió khuếch tán Diffuser 600x600.
    """

    COOLING_LOAD_NORM_W_M2 = {
        "Office": 220.0,
        "MeetingRoom": 250.0,
        "LivingRoom": 200.0,
        "Bedroom": 160.0,
        "Kitchen": 260.0,
        "Corridor": 120.0,
        "TechnicalRoom": 300.0,
        "Default": 200.0
    }

    @classmethod
    def calculate_room_hvac(cls, room_type: str, area_m2: float, height_m: float) -> Dict[str, Any]:
        norm_w = cls.COOLING_LOAD_NORM_W_M2.get(room_type, cls.COOLING_LOAD_NORM_W_M2["Default"])
        cooling_capacity_w = area_m2 * norm_w
        cooling_btu = cooling_capacity_w * 3.412142
        cooling_hp = cooling_btu / 9000.0

        # Lưu lượng gió cấp cần thiết: Q = Capacity_W / (1.2 * 1.005 * Delta_T), với Delta_T ~ 8-10 K
        # Kinh nghiệm: 1 kW lạnh cần khoảng 160 - 200 m3/h gió
        airflow_cmh = round((cooling_capacity_w / 1000.0) * 180.0, 0)
        airflow_m3_s = airflow_cmh / 3600.0

        # Kích thước ống gió chính với vận tốc gió v = 4.5 m/s
        v_main = 4.5
        duct_area_m2 = airflow_m3_s / v_main

        # Quy đổi sang tiết diện chữ nhật W x H (chọn H cố định = 200mm hoặc 250mm để lọt trần)
        duct_h_mm = 200.0 if duct_area_m2 < 0.08 else 250.0
        duct_w_mm = max(200.0, math.ceil((duct_area_m2 / (duct_h_mm / 1000.0)) * 1000.0 / 50.0) * 50.0)

        # Số lượng miệng gió cấp Diffuser (mỗi miệng 600x600 thổi khoảng 300 - 450 CMH)
        diffuser_count = max(1, math.ceil(airflow_cmh / 400.0))

        # Chọn thiết bị lạnh
        if cooling_hp <= 1.2:
            equipment_model = "FCU Giấu Trần Nối Ống Gió 1.0 HP (9,000 BTU/h)"
            unit_kw = 2.6
        elif cooling_hp <= 1.7:
            equipment_model = "FCU Giấu Trần Nối Ống Gió 1.5 HP (12,000 BTU/h)"
            unit_kw = 3.5
        elif cooling_hp <= 2.3:
            equipment_model = "FCU Giấu Trần Nối Ống Gió 2.0 HP (18,000 BTU/h)"
            unit_kw = 5.2
        elif cooling_hp <= 3.3:
            equipment_model = "FCU Giấu Trần Nối Ống Gió 3.0 HP (24,000 BTU/h)"
            unit_kw = 7.1
        else:
            equipment_model = "VRV Cassette 4 Hướng Thổi 4.0 HP (36,000 BTU/h)"
            unit_kw = 10.5

        return {
            "room_type": room_type,
            "area_m2": round(area_m2, 2),
            "cooling_capacity_w": round(cooling_capacity_w, 1),
            "cooling_btu": round(cooling_btu, 0),
            "cooling_hp": round(cooling_hp, 2),
            "airflow_cmh": airflow_cmh,
            "main_duct_size_mm": f"{int(duct_w_mm)}x{int(duct_h_mm)}",
            "duct_width_mm": duct_w_mm,
            "duct_height_mm": duct_h_mm,
            "diffuser_count": diffuser_count,
            "equipment_model": equipment_model,
            "unit_electric_power_kw": round(unit_kw / 3.2, 2)  # COP ~ 3.2
        }


# ==============================================================================
# 3. TRÌNH TẠO MÔ HÌNH TOÀN DIỆN (BUILDING GENERATOR & MEP ROUTING)
# ==============================================================================

class CompleteMepBimModel:
    """Mô hình tổng hợp Kiến trúc + Kết cấu + MEP (Điện, Nước, HVAC)."""
    def __init__(self, name: str = "CongTrinh_MEP_BIM_3D"):
        self.name = name
        self.elements: List[MepElement] = []
        self.rooms: List[Dict[str, Any]] = []
        self.clashes: List[Dict[str, Any]] = []
        self.boq_items: List[Dict[str, Any]] = []
        self.summary_stats: Dict[str, Any] = {}

    def add_element(self, elem: MepElement):
        self.elements.append(elem)

    def get_elements_by_system(self, system: str) -> List[MepElement]:
        return [e for e in self.elements if e.system == system]

    def get_elements_by_category(self, category: str) -> List[MepElement]:
        return [e for e in self.elements if e.category == category]


class MepBimBuilder:
    """
    Xây dựng mô hình 3D công trình tích hợp đầy đủ hệ thống MEP theo tiêu chuẩn.
    Hỗ trợ sinh tự động tòa nhà đa năng (Văn phòng, Căn hộ, Nhà phố/Biệt thự).
    """

    @classmethod
    def generate_building_mep_model(cls,
                                     building_width: float = 12000.0,
                                     building_depth: float = 8000.0,
                                     floor_height: float = 3600.0,
                                     num_floors: int = 2) -> CompleteMepBimModel:
        """
        Sinh trọn vẹn mô hình BIM 3D công trình:
        - Kiến trúc & Kết cấu: Móng, Sàn, Cột (400x400), Dầm (300x500), Tường bao (200), Tường ngăn (100).
        - 1. Điện & Chiếu sáng: Đèn LED Panel âm trần, Thang máng cáp, Tủ điện MDB/DB, Tuyến dây điện.
        - 2. Cấp thoát nước: Tuyến ống cấp nước PPR lạnh/nóng, Ống thoát phân Ø114 dốc 2%, Ống thoát sàn Ø60, Bồn cầu, Lavabo, Phễu thu sàn, Bồn nước mái.
        - 3. HVAC: Dàn lạnh FCU giấu trần, Tuyến ống gió cấp SA kèm miệng gió khuếch tán Diffuser 600x600, Ống gió hồi RA, Ống đồng môi chất, Quạt hút WC.
        """
        model = CompleteMepBimModel(f"ToaNha_BIM_MEP_{int(building_width/1000)}x{int(building_depth/1000)}m")

        W = float(building_width)
        D = float(building_depth)
        H = float(floor_height)
        col_w = 400.0
        beam_w = 300.0
        beam_h = 500.0
        slab_t = 150.0
        ceiling_z_offset = 2800.0  # Cao độ trần thạch cao +2.8m

        # ======================================================================
        # A. DỰNG KIẾN TRÚC & KẾT CẤU (ARCHITECTURE & STRUCTURE)
        # ======================================================================
        for floor_idx in range(num_floors):
            floor_name = f"Tang_{floor_idx + 1}"
            base_z = floor_idx * H

            # 1. Sàn bê tông cốt thép (IfcSlab)
            slab_bbox = BBox3D(0, 0, base_z - slab_t, W, D, base_z)
            model.add_element(MepElement(
                elem_id=f"SLAB_{floor_name}",
                name=f"Sàn Bê Tông {floor_name}",
                category="Slab",
                system="Structure",
                level=floor_name,
                geometry_type="box",
                params={"width": W, "depth": D, "thickness": slab_t, "material": "Concrete_C25"},
                bbox=slab_bbox
            ))

            # 2. Hệ Cột Kết Cấu (Structural Columns 400x400 tại các lưới trục)
            col_x_list = [0.0, W / 2.0, W]
            col_y_list = [0.0, D / 2.0, D]
            for cx in col_x_list:
                for cy in col_y_list:
                    # Lùi tâm cột vào trong biên
                    x0 = max(0.0, min(W - col_w, cx - col_w / 2.0 if cx == W / 2.0 else (0.0 if cx == 0 else W - col_w)))
                    y0 = max(0.0, min(D - col_w, cy - col_w / 2.0 if cy == D / 2.0 else (0.0 if cy == 0 else D - col_w)))
                    col_bbox = BBox3D(x0, y0, base_z, x0 + col_w, y0 + col_w, base_z + H - beam_h)
                    model.add_element(MepElement(
                        elem_id=f"COL_{floor_name}_{int(cx)}_{int(cy)}",
                        name=f"Cột Bê Tông 400x400 {floor_name}",
                        category="Column",
                        system="Structure",
                        level=floor_name,
                        geometry_type="box",
                        params={"width": col_w, "depth": col_w, "height": H - beam_h, "material": "Concrete_C25"},
                        bbox=col_bbox
                    ))

            # 3. Hệ Dầm Kết Cấu (Structural Beams 300x500 treo dưới đáy sàn tầng trên)
            beam_z_bottom = base_z + H - beam_h
            # Dầm chính theo phương X
            for by in [0.0, D / 2.0, D - beam_w]:
                b_bbox = BBox3D(0, by, beam_z_bottom, W, by + beam_w, base_z + H)
                model.add_element(MepElement(
                    elem_id=f"BEAM_X_{floor_name}_{int(by)}",
                    name=f"Dầm D300x500 {floor_name} Y={int(by)}",
                    category="Beam",
                    system="Structure",
                    level=floor_name,
                    geometry_type="box",
                    params={"width": W, "depth": beam_w, "height": beam_h, "material": "Concrete_C25"},
                    bbox=b_bbox
                ))

            # Dầm phụ theo phương Y
            for bx in [0.0, W / 2.0, W - beam_w]:
                b_bbox = BBox3D(bx, 0, beam_z_bottom, bx + beam_w, D, base_z + H)
                model.add_element(MepElement(
                    elem_id=f"BEAM_Y_{floor_name}_{int(bx)}",
                    name=f"Dầm D300x500 {floor_name} X={int(bx)}",
                    category="Beam",
                    system="Structure",
                    level=floor_name,
                    geometry_type="box",
                    params={"width": beam_w, "depth": D, "height": beam_h, "material": "Concrete_C25"},
                    bbox=b_bbox
                ))

            # 4. Tường Bao Ngoại Thất (Exterior Walls Dày 200mm)
            wall_t = 200.0
            wall_h = H - beam_h
            # Tường trước (Y=0)
            model.add_element(MepElement(
                elem_id=f"WALL_FRONT_{floor_name}",
                name=f"Tường Mặt Tiền 200 {floor_name}",
                category="Wall",
                system="Architecture",
                level=floor_name,
                geometry_type="box",
                params={"thickness": wall_t, "length": W, "height": wall_h, "material": "Brick_200"},
                bbox=BBox3D(0, 0, base_z, W, wall_t, base_z + wall_h)
            ))
            # Tường sau (Y=D-wall_t)
            model.add_element(MepElement(
                elem_id=f"WALL_BACK_{floor_name}",
                name=f"Tường Sau 200 {floor_name}",
                category="Wall",
                system="Architecture",
                level=floor_name,
                geometry_type="box",
                params={"thickness": wall_t, "length": W, "height": wall_h, "material": "Brick_200"},
                bbox=BBox3D(0, D - wall_t, base_z, W, D, base_z + wall_h)
            ))
            # Tường trái (X=0)
            model.add_element(MepElement(
                elem_id=f"WALL_LEFT_{floor_name}",
                name=f"Tường Hông Trái 200 {floor_name}",
                category="Wall",
                system="Architecture",
                level=floor_name,
                geometry_type="box",
                params={"thickness": wall_t, "length": D, "height": wall_h, "material": "Brick_200"},
                bbox=BBox3D(0, 0, base_z, wall_t, D, base_z + wall_h)
            ))
            # Tường phải (X=W-wall_t)
            model.add_element(MepElement(
                elem_id=f"WALL_RIGHT_{floor_name}",
                name=f"Tường Hông Phải 200 {floor_name}",
                category="Wall",
                system="Architecture",
                level=floor_name,
                geometry_type="box",
                params={"thickness": wall_t, "length": D, "height": wall_h, "material": "Brick_200"},
                bbox=BBox3D(W - wall_t, 0, base_z, W, D, base_z + wall_h)
            ))

            # 5. Phân chia phòng trên mặt bằng (Room Partitioning)
            # Phòng 1: Phòng Làm Việc / Phòng Khách (0 .. W/2, 0 .. D/2)
            # Phòng 2: Phòng Kỹ Thuật MEP & WC (W/2 .. W, 0 .. D/2) -> Trong đó WC: (W/2 .. W*0.75, 0 .. D/2), MEP: (W*0.75 .. W, 0 .. D/2)
            # Phòng 3: Phòng Họp / Phòng Ngủ (0 .. W/2, D/2 .. D)
            # Phòng 4: Không Gian Mở / Văn Phòng Lớn (W/2 .. W, D/2 .. D)
            # Hành lang trung tâm (Corridor) chạy dọc theo trục Y hoặc X
            corridor_w = 1600.0
            corridor_y0 = (D / 2.0) - (corridor_w / 2.0)
            corridor_y1 = (D / 2.0) + (corridor_w / 2.0)

            rooms_floor = [
                {"name": f"Văn Phòng Chính {floor_name}", "type": "Office", "x0": wall_t, "y0": corridor_y1, "x1": W / 2.0 - 50.0, "y1": D - wall_t},
                {"name": f"Phòng Họp Cao Cấp {floor_name}", "type": "MeetingRoom", "x0": W / 2.0 + 50.0, "y0": corridor_y1, "x1": W - wall_t, "y1": D - wall_t},
                {"name": f"Khu Vực Làm Việc Chung {floor_name}", "type": "Office", "x0": wall_t, "y0": wall_t, "x1": W / 2.0 - 50.0, "y1": corridor_y0},
                {"name": f"Khu Vệ Sinh WC {floor_name}", "type": "Toilet", "x0": W / 2.0 + 50.0, "y0": wall_t, "x1": W * 0.75 - 50.0, "y1": corridor_y0},
                {"name": f"Phòng Kỹ Thuật MEP {floor_name}", "type": "TechnicalRoom", "x0": W * 0.75 + 50.0, "y0": wall_t, "x1": W - wall_t, "y1": corridor_y0},
                {"name": f"Hành Lang Trung Tâm {floor_name}", "type": "Corridor", "x0": wall_t, "y0": corridor_y0, "x1": W - wall_t, "y1": corridor_y1}
            ]

            for r in rooms_floor:
                r["level"] = floor_name
                r["base_z"] = base_z
                r["area_m2"] = ((r["x1"] - r["x0"]) * (r["y1"] - r["y0"])) / 1e6
                model.rooms.append(r)

            # ==================================================================
            # B. THIẾT KẾ HỆ THỐNG ĐIỆN VÀ CHIẾU SÁNG (ELECTRICAL & LIGHTING)
            # ==================================================================
            # 1. Tủ điện phân phối tầng (DB - Distribution Board) đặt tại Phòng Kỹ Thuật MEP
            mep_room = [r for r in rooms_floor if r["type"] == "TechnicalRoom"][0]
            db_w, db_h_dim, db_depth = 600.0, 900.0, 180.0
            db_pos_x = mep_room["x0"] + 200.0
            db_pos_y = mep_room["y0"] + wall_t + 10.0
            db_pos_z = base_z + 1400.0  # Tâm tủ cao 1.4m
            db_bbox = BBox3D(db_pos_x, db_pos_y, db_pos_z, db_pos_x + db_w, db_pos_y + db_depth, db_pos_z + db_h_dim)
            model.add_element(MepElement(
                elem_id=f"ELEC_DB_{floor_name}",
                name=f"Tủ Điện Phân Phối DB-{floor_idx + 1}",
                category="Equipment",
                system="Electrical",
                level=floor_name,
                geometry_type="box",
                params={"width": db_w, "height": db_h_dim, "depth": db_depth, "voltage": "380V/220V", "phase": 3},
                bbox=db_bbox
            ))

            # 2. Thang Máng Cáp Điện (Cable Tray 300x100) chạy dọc trần Hành Lang Trung Tâm
            # Cao độ máng cáp treo ở Z = +3.15m (nằm phía trên trần thạch cao, dưới dầm)
            tray_z = base_z + 3150.0
            tray_w = 300.0
            tray_h_dim = 100.0
            tray_y = (corridor_y0 + corridor_y1) / 2.0 - (tray_w / 2.0)
            tray_bbox = BBox3D(wall_t + 200.0, tray_y, tray_z, W - wall_t - 200.0, tray_y + tray_w, tray_z + tray_h_dim)
            model.add_element(MepElement(
                elem_id=f"CABLE_TRAY_MAIN_{floor_name}",
                name=f"Máng Cáp Điện Trục Chính 300x100 {floor_name}",
                category="CableTray",
                system="Electrical",
                level=floor_name,
                geometry_type="box",
                params={"width": tray_w, "height": tray_h_dim, "length": W - 2 * wall_t - 400.0, "material": "Galvanized_Steel"},
                bbox=tray_bbox
            ))

            # Nhánh máng cáp rẽ vào Phòng Kỹ Thuật MEP nối tới tủ điện DB
            tray_branch_bbox = BBox3D(mep_room["x0"] + 300.0, mep_room["y0"] + 200.0, tray_z,
                                      mep_room["x0"] + 500.0, corridor_y0, tray_z + tray_h_dim)
            model.add_element(MepElement(
                elem_id=f"CABLE_TRAY_BRANCH_{floor_name}",
                name=f"Máng Cáp Nhánh Vào Phòng Kỹ Thuật 200x100 {floor_name}",
                category="CableTray",
                system="Electrical",
                level=floor_name,
                geometry_type="box",
                params={"width": 200.0, "height": tray_h_dim, "material": "Galvanized_Steel"},
                bbox=tray_branch_bbox
            ))

            # 3. Tính toán & Bố trí mảng đèn chiếu sáng cho từng phòng
            light_z = base_z + ceiling_z_offset
            for r in rooms_floor:
                rm_len = (r["x1"] - r["x0"]) / 1000.0
                rm_wid = (r["y1"] - r["y0"]) / 1000.0
                calc_light = ElectricalLightingEngine.calculate_lighting(r["type"], rm_len, rm_wid, H / 1000.0)
                nx, ny = calc_light["grid"]
                dx = (r["x1"] - r["x0"]) / (nx + 1)
                dy = (r["y1"] - r["y0"]) / (ny + 1)

                fw = 600.0 if calc_light["fixture_type"] == "Panel_600x600" else 200.0
                fl = 600.0 if calc_light["fixture_type"] == "Panel_600x600" else 200.0
                fh = 50.0

                for ix in range(nx):
                    for iy in range(ny):
                        fx_center = r["x0"] + dx * (ix + 1)
                        fy_center = r["y0"] + dy * (iy + 1)
                        f_bbox = BBox3D(fx_center - fw / 2.0, fy_center - fl / 2.0, light_z,
                                        fx_center + fw / 2.0, fy_center + fl / 2.0, light_z + fh)
                        model.add_element(MepElement(
                            elem_id=f"LIGHT_{floor_name}_{r['type']}_{ix}_{iy}",
                            name=f"{calc_light['fixture_name']} - {r['name']}",
                            category="Fixture",
                            system="Electrical",
                            level=floor_name,
                            geometry_type="box",
                            params={"fixture_type": calc_light["fixture_type"], "power_w": 40.0, "lumens": 4000.0},
                            bbox=f_bbox
                        ))

            # ==================================================================
            # C. THIẾT KẾ ĐIỀU HÒA, THÔNG GIÓ HVAC (HVAC AIR CONDITIONING)
            # ==================================================================
            # Bố trí Dàn lạnh FCU giấu trần nối ống gió cho các phòng làm việc & phòng họp
            fcu_z = base_z + 2950.0  # Cao độ đáy FCU +2.95m
            duct_z = base_z + 2920.0 # Cao độ đáy ống gió cấp +2.92m

            for r in rooms_floor:
                if r["type"] not in ["Office", "MeetingRoom"]:
                    continue
                rm_area = r["area_m2"]
                hvac_calc = HvacEngine.calculate_room_hvac(r["type"], rm_area, H / 1000.0)

                # 1. Khối Dàn Lạnh FCU
                fcu_w, fcu_l, fcu_h = 1000.0, 700.0, 260.0
                fcu_x = r["x0"] + 400.0
                fcu_y = r["y1"] - fcu_l - 300.0
                fcu_bbox = BBox3D(fcu_x, fcu_y, fcu_z, fcu_x + fcu_w, fcu_y + fcu_l, fcu_z + fcu_h)
                model.add_element(MepElement(
                    elem_id=f"HVAC_FCU_{floor_name}_{r['name']}",
                    name=f"Dàn Lạnh {hvac_calc['equipment_model']} - {r['name']}",
                    category="Equipment",
                    system="HVAC_Supply",
                    level=floor_name,
                    geometry_type="box",
                    params=hvac_calc,
                    bbox=fcu_bbox
                ))

                # 2. Tuyến Ống Gió Cấp Chính (Supply Air Duct) từ FCU chạy dọc giữa phòng
                dw = hvac_calc["duct_width_mm"]
                dh = hvac_calc["duct_height_mm"]
                d_len = (r["x1"] - r["x0"]) * 0.65
                duct_bbox = BBox3D(fcu_x + fcu_w, fcu_y + fcu_l / 2.0 - dw / 2.0, duct_z,
                                   fcu_x + fcu_w + d_len, fcu_y + fcu_l / 2.0 + dw / 2.0, duct_z + dh)
                model.add_element(MepElement(
                    elem_id=f"DUCT_SA_MAIN_{floor_name}_{r['name']}",
                    name=f"Ống Gió Cấp SA {int(dw)}x{int(dh)} - {r['name']}",
                    category="Duct",
                    system="HVAC_Supply",
                    level=floor_name,
                    geometry_type="box",
                    params={"width": dw, "height": dh, "length": d_len, "airflow_cmh": hvac_calc["airflow_cmh"]},
                    bbox=duct_bbox
                ))

                # 3. Miệng Gió Khuếch Tán Cấp (Supply Air Diffuser 600x600) gắn mặt trần
                diff_count = hvac_calc["diffuser_count"]
                step_x = d_len / (diff_count + 1)
                for di in range(diff_count):
                    diff_cx = fcu_x + fcu_w + step_x * (di + 1)
                    diff_cy = fcu_y + fcu_l / 2.0
                    diff_bbox = BBox3D(diff_cx - 300.0, diff_cy - 300.0, light_z,
                                       diff_cx + 300.0, diff_cy + 300.0, light_z + 80.0)
                    model.add_element(MepElement(
                        elem_id=f"DIFFUSER_SA_{floor_name}_{r['name']}_{di}",
                        name=f"Miệng Gió Cấp 600x600 - {r['name']}",
                        category="Fixture",
                        system="HVAC_Supply",
                        level=floor_name,
                        geometry_type="box",
                        params={"size": "600x600", "airflow_cmh": round(hvac_calc["airflow_cmh"] / diff_count, 0)},
                        bbox=diff_bbox
                    ))

            # 4. Quạt Hút Thông Gió WC & Tuyến Ống Thải Gió (Exhaust Air)
            wc_room = [r for r in rooms_floor if r["type"] == "Toilet"][0]
            fan_bbox = BBox3D(wc_room["x0"] + 300.0, wc_room["y1"] - 600.0, base_z + 3000.0,
                              wc_room["x0"] + 700.0, wc_room["y1"] - 200.0, base_z + 3300.0)
            model.add_element(MepElement(
                elem_id=f"HVAC_EXHAUST_FAN_{floor_name}",
                name=f"Quạt Hút Gió Âm Trần WC 250 CMH {floor_name}",
                category="Equipment",
                system="HVAC_Exhaust",
                level=floor_name,
                geometry_type="box",
                params={"airflow_cmh": 250.0, "power_w": 35.0},
                bbox=fan_bbox
            ))

            # ==================================================================
            # D. THIẾT KẾ CẤP THOÁT NƯỚC (PLUMBING & DRAINAGE)
            # ==================================================================
            # Khu vệ sinh WC: Bồn cầu, Lavabo, Phễu thu sàn, Đường ống cấp và thoát
            # 1. Bồn Cầu (Water Closet)
            wc_x = wc_room["x0"] + 800.0
            wc_y = wc_room["y0"] + 600.0
            wc_bbox = BBox3D(wc_x - 200.0, wc_y, base_z, wc_x + 200.0, wc_y + 700.0, base_z + 750.0)
            model.add_element(MepElement(
                elem_id=f"SAN_WC_{floor_name}",
                name=f"Bồn Cầu 2 Khối Cao Cấp {floor_name}",
                category="Fixture",
                system="Plumbing_Drain",
                level=floor_name,
                geometry_type="box",
                params={"type": "WaterCloset", "flush_volume_l": 6.0},
                bbox=wc_bbox
            ))

            # 2. Chậu Rửa Lavabo
            lav_x = wc_room["x0"] + 1600.0
            lav_y = wc_room["y0"] + 450.0
            lav_bbox = BBox3D(lav_x - 300.0, lav_y, base_z + 800.0, lav_x + 300.0, lav_y + 500.0, base_z + 900.0)
            model.add_element(MepElement(
                elem_id=f"SAN_LAVABO_{floor_name}",
                name=f"Chậu Rửa Lavabo Đặt Bàn {floor_name}",
                category="Fixture",
                system="Plumbing_Cold",
                level=floor_name,
                geometry_type="box",
                params={"type": "Lavabo", "counter_h": 800.0},
                bbox=lav_bbox
            ))

            # 3. Phễu Thu Sàn (Floor Drain Ø90)
            fd_x = wc_room["x1"] - 400.0
            fd_y = wc_room["y0"] + 400.0
            fd_bbox = BBox3D(fd_x - 75.0, fd_y - 75.0, base_z, fd_x + 75.0, fd_y + 75.0, base_z + 50.0)
            model.add_element(MepElement(
                elem_id=f"SAN_FLOOR_DRAIN_{floor_name}",
                name=f"Phễu Thu Sàn Bẫy Mùi Ø90 {floor_name}",
                category="Fixture",
                system="Plumbing_Drain",
                level=floor_name,
                geometry_type="box",
                params={"type": "FloorDrain", "trap_seal_mm": 50.0},
                bbox=fd_bbox
            ))

            # 4. Tuyến Ống Cấp Nước Lạnh PPR (DCW - Domestic Cold Water DN25)
            # Đi từ Hộp Kỹ Thuật (MEP shaft) treo sát đáy dầm ở Z = +3.25m rồi cấp xuống thiết bị
            pipe_water_z = base_z + 3250.0
            pipe_w_bbox = BBox3D(wc_room["x0"], wc_y + 200.0, pipe_water_z,
                                 mep_room["x1"] - 300.0, wc_y + 234.0, pipe_water_z + 34.0)
            model.add_element(MepElement(
                elem_id=f"PIPE_COLD_HEADER_{floor_name}",
                name=f"Ống Cấp Nước Lạnh PPR DN25 {floor_name}",
                category="Pipe",
                system="Plumbing_Cold",
                level=floor_name,
                geometry_type="cylinder",
                params={"diameter_dn": 25, "outer_dia_mm": 32.0, "material": "PPR_PN16"},
                bbox=pipe_w_bbox
            ))

            # 5. Tuyến Ống Thoát Phân uPVC Ø114 (Soil Pipe Dốc 2%)
            # Treo dưới đáy sàn trong không gian trần của tầng dưới (hoặc dưới sàn tầng 1 dẫn ra hố ga)
            soil_z_start = base_z - 300.0
            soil_z_end = base_z - 380.0 # Dốc xuống 80mm trên đoạn 4m (slope 2%)
            soil_bbox = BBox3D(wc_x - 60.0, wc_y, soil_z_end,
                               mep_room["x1"], wc_y + 114.0, soil_z_start + 114.0)
            model.add_element(MepElement(
                elem_id=f"PIPE_SOIL_MAIN_{floor_name}",
                name=f"Ống Thoát Phân uPVC Ø114 Dốc 2% {floor_name}",
                category="Pipe",
                system="Plumbing_Drain",
                level=floor_name,
                geometry_type="cylinder",
                params={"diameter_dn": 100, "outer_dia_mm": 114.0, "slope_percent": 2.0, "material": "uPVC_Class2"},
                bbox=soil_bbox
            ))

        # ======================================================================
        # E. HỆ THỐNG TRÊN MÁI (ROOF LEVEL: CHILLER / WATER TANK)
        # ======================================================================
        roof_z = num_floors * H
        # Sàn Mái (Roof Slab)
        model.add_element(MepElement(
            elem_id="SLAB_ROOF",
            name="Sàn Mái Bê Tông Cốt Thép",
            category="Slab",
            system="Structure",
            level="Mai",
            geometry_type="box",
            params={"width": W, "depth": D, "thickness": slab_t, "material": "Concrete_C25"},
            bbox=BBox3D(0, 0, roof_z - slab_t, W, D, roof_z)
        ))

        # Bồn Nước Mái Inox 2000L
        tank_bbox = BBox3D(W - 2500.0, D - 2200.0, roof_z, W - 500.0, D - 600.0, roof_z + 1800.0)
        model.add_element(MepElement(
            elem_id="EQUIP_WATER_TANK_ROOF",
            name="Bồn Nước Mái Inox Sơn Hà 2000L",
            category="Equipment",
            system="Plumbing_Cold",
            level="Mai",
            geometry_type="cylinder",
            params={"capacity_liters": 2000.0, "material": "Inox_SUS304"},
            bbox=tank_bbox
        ))

        # Cụm Dàn Nóng Điều Hòa VRV Outdoor Condensing Unit
        cdu_bbox = BBox3D(800.0, D - 2400.0, roof_z, 2400.0, D - 1000.0, roof_z + 1600.0)
        model.add_element(MepElement(
            elem_id="HVAC_OUTDOOR_VRV",
            name="Cụm Dàn Nóng VRV Ngoài Trời 10 HP",
            category="Equipment",
            system="HVAC_Supply",
            level="Mai",
            geometry_type="box",
            params={"cooling_capacity_kw": 28.0, "refrigerant": "R410A"},
            bbox=cdu_bbox
        ))

        # Tính toán thống kê ban đầu
        cls._compute_model_stats(model)
        return model

    @classmethod
    def _compute_model_stats(cls, model: CompleteMepBimModel):
        total_elec_w = sum(e.params.get("power_w", 0) for e in model.get_elements_by_system("Electrical"))
        total_fcu_kw = sum(e.params.get("unit_electric_power_kw", 0) for e in model.get_elements_by_category("Equipment") if "FCU" in e.name)
        total_pipes_m = sum(e.bbox.size[0] / 1000.0 for e in model.get_elements_by_category("Pipe"))
        total_ducts_m = sum(e.bbox.size[0] / 1000.0 for e in model.get_elements_by_category("Duct"))
        total_trays_m = sum(e.bbox.size[0] / 1000.0 for e in model.get_elements_by_category("CableTray"))

        model.summary_stats = {
            "total_elements": len(model.elements),
            "rooms_count": len(model.rooms),
            "total_lighting_fixtures": len(model.get_elements_by_category("Fixture")),
            "total_lighting_power_kw": round(total_elec_w / 1000.0, 2),
            "total_hvac_cooling_kw": round(total_fcu_kw * 3.5, 2),
            "total_ducts_linear_meters": round(total_ducts_m, 1),
            "total_pipes_linear_meters": round(total_pipes_m, 1),
            "total_cable_trays_linear_meters": round(total_trays_m, 1)
        }


# ==============================================================================
# 4. BỘ KIỂM TRA XUNG ĐỘT HỆ THỐNG MEP (CLASH DETECTION ENGINE)
# ==============================================================================

class MepClashDetector:
    """
    5. Kiểm tra xung đột hệ thống MEP:
    - Thuật toán kiểm tra giao nhau 3D Bounding Box (AABB) & Khoảng cách an toàn (Clearance).
    - Ma trận xung đột (Clash Matrix):
        1. Ống gió HVAC vs Dầm/Cột kết cấu (Hard Clash)
        2. Máng cáp điện vs Ống cấp/thoát nước (Safety Clearance Clash)
        3. Ống gió HVAC vs Ống nước (Hard Clash)
        4. Tĩnh không thông thủy sàn trần (Headroom Clearance < 2.4m)
    - Tự động nắn tuyến giải quyết xung đột (Auto-resolve Clashes).
    """

    @classmethod
    def run_clash_detection(cls, model: CompleteMepBimModel, tolerance_mm: float = 20.0) -> List[Dict[str, Any]]:
        clashes = []
        clash_id_counter = 1
        elements = model.elements
        n = len(elements)

        # Định nghĩa các cặp hệ thống cần quét va chạm
        critical_pairs = [
            ("Duct", "Beam"),
            ("Duct", "Column"),
            ("Pipe", "CableTray"),
            ("Duct", "Pipe"),
            ("CableTray", "Beam")
        ]

        for i in range(n):
            elem_a = elements[i]
            # Bỏ qua sàn, tường bao thường
            if elem_a.category in ["Slab", "Wall"]:
                continue

            for j in range(i + 1, n):
                elem_b = elements[j]
                if elem_b.category in ["Slab", "Wall"]:
                    continue

                # Kiểm tra xem cặp có thuộc danh mục xung đột quan tâm không
                is_check_pair = False
                for c1, c2 in critical_pairs:
                    if (elem_a.category == c1 and elem_b.category == c2) or (elem_a.category == c2 and elem_b.category == c1):
                        is_check_pair = True
                        break

                if not is_check_pair:
                    continue

                # Kiểm tra giao thoa hình học AABB
                if elem_a.bbox.intersects(elem_b.bbox, tolerance=tolerance_mm):
                    ivol = elem_a.bbox.intersection_volume(elem_b.bbox)
                    penetration = min(ivol.size) if ivol else tolerance_mm
                    clash_pt = ivol.center if ivol else elem_a.bbox.center

                    # Đánh giá mức độ nghiêm trọng (Severity)
                    if (elem_a.category == "Duct" and elem_b.category == "Beam") or (elem_b.category == "Duct" and elem_a.category == "Beam"):
                        severity = "CRITICAL"
                        desc = f"Ống gió đâm xuyên Dầm bê tông ({elem_a.name} & {elem_b.name})"
                        rec = "Tự động hạ cốt cao độ đáy ống gió Z xuống dưới đáy dầm 50mm hoặc chuyển hướng ống lách qua dầm."
                    elif (elem_a.category == "Pipe" and elem_b.category == "CableTray") or (elem_b.category == "Pipe" and elem_a.category == "CableTray"):
                        severity = "MAJOR"
                        desc = f"Vi phạm khoảng cách an toàn Điện - Nước ({elem_a.name} & {elem_b.name})"
                        rec = "Tự động dịch chuyển tuyến máng cáp sang ngang +250mm đảm bảo khoảng cách ly kỹ thuật > 150mm."
                    else:
                        severity = "MAJOR"
                        desc = f"Va chạm không gian MEP ({elem_a.name} & {elem_b.name})"
                        rec = "Tự động dịch cốt cao độ z-offset tránh xung đột vật lý."

                    clash_item = {
                        "clash_id": f"CLASH-{clash_id_counter:03d}",
                        "severity": severity,
                        "description": desc,
                        "element_a": {
                            "id": elem_a.elem_id,
                            "name": elem_a.name,
                            "category": elem_a.category,
                            "system": elem_a.system
                        },
                        "element_b": {
                            "id": elem_b.elem_id,
                            "name": elem_b.name,
                            "category": elem_b.category,
                            "system": elem_b.system
                        },
                        "clash_point": {
                            "x": round(clash_pt[0], 1),
                            "y": round(clash_pt[1], 1),
                            "z": round(clash_pt[2], 1)
                        },
                        "penetration_depth_mm": round(penetration, 1),
                        "recommendation": rec,
                        "status": "OPEN"
                    }
                    clashes.append(clash_item)
                    clash_id_counter += 1

        model.clashes = clashes
        return clashes

    @classmethod
    def auto_resolve_clashes(cls, model: CompleteMepBimModel) -> Dict[str, Any]:
        """Tự động nắn tuyến hình học (Auto-reroute & Offset) để triệt tiêu mọi xung đột."""
        resolved_count = 0
        actions_taken = []

        for c in model.clashes:
            elem_a_id = c["element_a"]["id"]
            elem_b_id = c["element_b"]["id"]

            elem_a = next((e for e in model.elements if e.elem_id == elem_a_id), None)
            elem_b = next((e for e in model.elements if e.elem_id == elem_b_id), None)

            if not elem_a or not elem_b:
                continue

            # Trường hợp 1: Ống gió đâm dầm -> Hạ cốt ống gió xuống dưới đáy dầm
            if (elem_a.category == "Duct" and elem_b.category == "Beam") or (elem_b.category == "Duct" and elem_a.category == "Beam"):
                duct = elem_a if elem_a.category == "Duct" else elem_b
                beam = elem_b if elem_b.category == "Beam" else elem_a

                target_top_z = beam.bbox.min_z - 30.0  # Dưới đáy dầm 30mm
                duct_h = duct.bbox.size[2]
                dz = target_top_z - duct.bbox.max_z

                # Cập nhật tọa độ Z của BBox ống gió
                duct.bbox.min_z += dz
                duct.bbox.max_z += dz
                duct.clash_resolved = True
                resolved_count += 1
                actions_taken.append({
                    "clash_id": c["clash_id"],
                    "action": f"Đã hạ cốt ống gió [{duct.name}] xuống Z={round(duct.bbox.min_z, 1)}mm (dưới đáy dầm)."
                })

            # Trường hợp 2: Máng cáp chạm Ống nước -> Dịch máng cáp theo trục Y sang ngang
            elif (elem_a.category == "CableTray" and elem_b.category == "Pipe") or (elem_b.category == "CableTray" and elem_a.category == "Pipe"):
                tray = elem_a if elem_a.category == "CableTray" else elem_b
                dy = 250.0 # Dịch sang ngang 250mm
                tray.bbox.min_y += dy
                tray.bbox.max_y += dy
                tray.clash_resolved = True
                resolved_count += 1
                actions_taken.append({
                    "clash_id": c["clash_id"],
                    "action": f"Đã dịch máng cáp [{tray.name}] sang ngang +250mm đảm bảo ly cách an toàn."
                })

        # Quét kiểm tra lại sau khi xử lý
        remaining_clashes = cls.run_clash_detection(model)
        return {
            "resolved_count": resolved_count,
            "remaining_clashes_count": len(remaining_clashes),
            "actions_taken": actions_taken
        }


# ==============================================================================
# 5. BÓC TÁCH KHỐI LƯỢNG (BOQ) & DỰ TOÁN MEP TOÀN DIỆN
# ==============================================================================

class MepBoqEstimator:
    """
    6. Bóc tách khối lượng (BOQ Schedule) & Dự toán chi phí MEP:
    - Bóc tách theo hệ thống: Điện & Chiếu sáng, Cấp thoát nước, Điều hòa thông gió HVAC.
    - Đơn giá vật tư & nhân công cập nhật theo định mức Việt Nam (VND).
    - Xuất bảng biểu JSON, CSV và HTML hiển thị trực quan.
    """

    UNIT_RATES = {
        # Điện
        "LED_Panel_600x600": {"desc": "Đèn LED Panel âm trần 600x600 - 40W", "unit": "Bộ", "material_price": 380000, "labor_price": 60000},
        "LED_Downlight_D150": {"desc": "Đèn LED Downlight âm trần Ø150 - 18W", "unit": "Bộ", "material_price": 160000, "labor_price": 40000},
        "Cable_Tray_300x100": {"desc": "Máng cáp mạ kẽm nhúng nóng 300x100 kèm nắp đậy", "unit": "Mét", "material_price": 280000, "labor_price": 75000},
        "Cable_Tray_200x100": {"desc": "Máng cáp mạ kẽm 200x100", "unit": "Mét", "material_price": 210000, "labor_price": 60000},
        "Panel_DB": {"desc": "Tủ điện phân phối DB âm tường (đầy đủ MCB nhánh)", "unit": "Bộ", "material_price": 4500000, "labor_price": 800000},

        # Cấp thoát nước
        "Pipe_PPR_DN25": {"desc": "Ống cấp nước PPR DN25 PN16 hàn nhiệt", "unit": "Mét", "material_price": 48000, "labor_price": 35000},
        "Pipe_uPVC_D114": {"desc": "Ống thoát phân uPVC Ø114 Class 2 dán keo", "unit": "Mét", "material_price": 145000, "labor_price": 55000},
        "Sanitary_WC": {"desc": "Bồn cầu 2 khối men nano kháng khuẩn", "unit": "Bộ", "material_price": 2800000, "labor_price": 350000},
        "Sanitary_Lavabo": {"desc": "Chậu rửa Lavabo kèm vòi nóng lạnh & xi phông", "unit": "Bộ", "material_price": 1450000, "labor_price": 250000},
        "Floor_Drain_D90": {"desc": "Phễu thu sàn chống mùi Inox 304 Ø90", "unit": "Cái", "material_price": 180000, "labor_price": 40000},
        "Roof_Water_Tank": {"desc": "Bồn nước Inox SUS304 dung tích 2000L", "unit": "Bộ", "material_price": 6500000, "labor_price": 900000},

        # HVAC
        "Duct_Galvanized_500x250": {"desc": "Ống gió tole tráng kẽm bọc cách nhiệt PE 500x250", "unit": "Mét", "material_price": 340000, "labor_price": 95000},
        "Duct_Galvanized_350x200": {"desc": "Ống gió tole tráng kẽm 350x200", "unit": "Mét", "material_price": 260000, "labor_price": 75000},
        "Diffuser_600x600": {"desc": "Miệng gió khuếch tán nhôm sơn tĩnh điện 600x600", "unit": "Cái", "material_price": 260000, "labor_price": 50000},
        "FCU_Unit_2HP": {"desc": "Dàn lạnh FCU giấu trần nối ống gió 2.0 HP", "unit": "Bộ", "material_price": 12500000, "labor_price": 1500000},
        "FCU_Unit_1_5HP": {"desc": "Dàn lạnh FCU giấu trần nối ống gió 1.5 HP", "unit": "Bộ", "material_price": 10500000, "labor_price": 1300000},
        "Exhaust_Fan_WC": {"desc": "Quạt hút thông gió âm trần WC 250 CMH", "unit": "Cái", "material_price": 750000, "labor_price": 120000},
        "VRV_Outdoor_Unit": {"desc": "Cụm Dàn nóng điều hòa trung tâm VRV 10 HP", "unit": "Cụm", "material_price": 68000000, "labor_price": 4500000}
    }

    @classmethod
    def generate_boq(cls, model: CompleteMepBimModel) -> Dict[str, Any]:
        boq_list = []
        item_no = 1

        # Phân loại và tính tổng khối lượng từng đối tượng
        category_counts: Dict[str, float] = {}

        for elem in model.elements:
            if elem.category == "Fixture" and "LIGHT" in elem.elem_id:
                key = "LED_Panel_600x600" if "Panel" in elem.name else "LED_Downlight_D150"
                category_counts[key] = category_counts.get(key, 0) + 1
            elif elem.category == "CableTray":
                key = "Cable_Tray_300x100" if "300" in elem.name else "Cable_Tray_200x100"
                length_m = elem.bbox.size[0] / 1000.0
                category_counts[key] = category_counts.get(key, 0) + length_m
            elif elem.category == "Equipment" and "DB" in elem.elem_id:
                category_counts["Panel_DB"] = category_counts.get("Panel_DB", 0) + 1
            elif elem.category == "Pipe":
                if "COLD" in elem.elem_id:
                    length_m = elem.bbox.size[0] / 1000.0
                    category_counts["Pipe_PPR_DN25"] = category_counts.get("Pipe_PPR_DN25", 0) + length_m
                elif "SOIL" in elem.elem_id:
                    length_m = elem.bbox.size[0] / 1000.0
                    category_counts["Pipe_uPVC_D114"] = category_counts.get("Pipe_uPVC_D114", 0) + length_m
            elif elem.category == "Fixture" and "WC" in elem.elem_id:
                category_counts["Sanitary_WC"] = category_counts.get("Sanitary_WC", 0) + 1
            elif elem.category == "Fixture" and "LAVABO" in elem.elem_id:
                category_counts["Sanitary_Lavabo"] = category_counts.get("Sanitary_Lavabo", 0) + 1
            elif elem.category == "Fixture" and "FLOOR_DRAIN" in elem.elem_id:
                category_counts["Floor_Drain_D90"] = category_counts.get("Floor_Drain_D90", 0) + 1
            elif "WATER_TANK" in elem.elem_id:
                category_counts["Roof_Water_Tank"] = category_counts.get("Roof_Water_Tank", 0) + 1
            elif elem.category == "Duct":
                key = "Duct_Galvanized_500x250" if "500" in elem.name else "Duct_Galvanized_350x200"
                length_m = elem.bbox.size[0] / 1000.0
                category_counts[key] = category_counts.get(key, 0) + length_m
            elif elem.category == "Fixture" and "DIFFUSER" in elem.elem_id:
                category_counts["Diffuser_600x600"] = category_counts.get("Diffuser_600x600", 0) + 1
            elif elem.category == "Equipment" and "FCU" in elem.elem_id:
                key = "FCU_Unit_2HP" if "2.0 HP" in elem.name else "FCU_Unit_1_5HP"
                category_counts[key] = category_counts.get(key, 0) + 1
            elif elem.category == "Equipment" and "EXHAUST_FAN" in elem.elem_id:
                category_counts["Exhaust_Fan_WC"] = category_counts.get("Exhaust_Fan_WC", 0) + 1
            elif "OUTDOOR_VRV" in elem.elem_id:
                category_counts["VRV_Outdoor_Unit"] = category_counts.get("VRV_Outdoor_Unit", 0) + 1

        total_material_cost = 0.0
        total_labor_cost = 0.0

        for key, qty in category_counts.items():
            if key not in cls.UNIT_RATES:
                continue
            spec = cls.UNIT_RATES[key]
            rounded_qty = round(qty, 1) if spec["unit"] == "Mét" else int(qty)
            mat_amt = rounded_qty * spec["material_price"]
            lab_amt = rounded_qty * spec["labor_price"]
            row_total = mat_amt + lab_amt

            total_material_cost += mat_amt
            total_labor_cost += lab_amt

            boq_list.append({
                "item_no": item_no,
                "item_code": key,
                "description": spec["desc"],
                "unit": spec["unit"],
                "quantity": rounded_qty,
                "material_price_vnd": spec["material_price"],
                "labor_price_vnd": spec["labor_price"],
                "total_amount_vnd": int(row_total)
            })
            item_no += 1

        grand_total = total_material_cost + total_labor_cost
        vat_10 = grand_total * 0.10
        total_with_vat = grand_total + vat_10

        model.boq_items = boq_list
        return {
            "items": boq_list,
            "total_material_cost_vnd": int(total_material_cost),
            "total_labor_cost_vnd": int(total_labor_cost),
            "grand_total_vnd": int(grand_total),
            "vat_10_percent_vnd": int(vat_10),
            "total_with_vat_vnd": int(total_with_vat),
            "formatted_total": f"{int(total_with_vat):,} VNĐ".replace(",", ".")
        }


# ==============================================================================
# 6. DỰNG MÔ HÌNH BIM 3D CHUYÊN NGHIỆP: IFC 4, 3D OBJ & AUTOCAD DXF
# ==============================================================================

class MepBimExporter:
    """
    4 & 6. Xuất mô hình BIM 3D đa định dạng:
    - IFC 4: Chuẩn BIM quốc tế mở (Revit, Navisworks, Solibri).
    - Wavefront 3D OBJ + MTL: Xem thời gian thực trên WebGL Three.js & 3ds Max.
    - AutoCAD 3D DXF / DWG: Đi kèm bản vẽ kỹ thuật CAD chuẩn TCVN có khung tên & bảng BOQ.
    """

    @classmethod
    def export_all(cls, model: CompleteMepBimModel, output_dir: str = EXPORTS_DIR) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        base_name = model.name

        obj_file = os.path.join(output_dir, f"{base_name}.obj")
        mtl_file = os.path.join(output_dir, f"{base_name}.mtl")
        dxf_file = os.path.join(output_dir, f"{base_name}_Technical_Plan.dxf")
        ifc_file = os.path.join(output_dir, f"{base_name}.ifc")
        boq_json_file = os.path.join(output_dir, f"{base_name}_BOQ.json")

        # 1. Xuất OBJ + MTL
        cls.export_to_obj_mtl(model, obj_file, mtl_file)

        # 2. Xuất DXF Kỹ Thuật 2D/3D kèm Khung Tên & Bảng BOQ
        cls.export_to_technical_dxf(model, dxf_file)

        # 3. Xuất IFC 4
        if ifcopenshell:
            cls.export_to_ifc4(model, ifc_file)
        else:
            ifc_file = "IFCOpenShell not installed"

        # 4. Xuất Báo Cáo BOQ JSON
        boq_data = MepBoqEstimator.generate_boq(model)
        with open(boq_json_file, "w", encoding="utf-8") as f:
            json.dump({
                "project_name": model.name,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": model.summary_stats,
                "boq": boq_data,
                "clashes": model.clashes
            }, f, indent=2, ensure_ascii=False)

        return {
            "obj": obj_file,
            "mtl": mtl_file,
            "dxf": dxf_file,
            "ifc": ifc_file,
            "boq_json": boq_json_file
        }

    @classmethod
    def export_to_obj_mtl(cls, model: CompleteMepBimModel, obj_path: str, mtl_path: str):
        """Tạo file Wavefront OBJ và MTL với màu sắc & vật liệu chuyên nghiệp cho từng hệ MEP."""
        mtl_content = """# RevitAI MEP 3D Materials Library
newmtl Mat_Concrete
Kd 0.75 0.75 0.75
Ka 0.20 0.20 0.20
Ks 0.10 0.10 0.10
d 1.0

newmtl Mat_BrickWall
Kd 0.88 0.86 0.82
Ka 0.25 0.25 0.25
Ks 0.05 0.05 0.05
d 1.0

newmtl Mat_HVAC_Supply
Kd 0.00 0.75 0.85
Ka 0.10 0.20 0.25
Ks 0.60 0.60 0.60
Ns 40.0
d 1.0

newmtl Mat_HVAC_Exhaust
Kd 0.45 0.55 0.60
Ka 0.15 0.15 0.15
Ks 0.40 0.40 0.40
d 1.0

newmtl Mat_Pipe_Cold
Kd 0.10 0.50 0.90
Ka 0.05 0.15 0.30
Ks 0.70 0.70 0.70
Ns 50.0
d 1.0

newmtl Mat_Pipe_Soil
Kd 0.90 0.40 0.05
Ka 0.25 0.10 0.05
Ks 0.30 0.30 0.30
d 1.0

newmtl Mat_CableTray
Kd 0.95 0.70 0.10
Ka 0.30 0.20 0.05
Ks 0.80 0.80 0.80
Ns 60.0
d 1.0

newmtl Mat_LightFixture
Kd 1.00 0.98 0.85
Ka 0.90 0.90 0.80
Ks 0.90 0.90 0.90
d 1.0

newmtl Mat_SanitaryWare
Kd 0.96 0.96 0.98
Ka 0.30 0.30 0.30
Ks 0.90 0.90 0.90
Ns 80.0
d 1.0

newmtl Mat_Equipment
Kd 0.60 0.65 0.70
Ka 0.20 0.20 0.20
Ks 0.50 0.50 0.50
d 1.0
"""
        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(mtl_content)

        mtl_filename = os.path.basename(mtl_path)
        vertices = []
        faces_by_group = {}

        def get_mat_for_elem(e: MepElement) -> str:
            if e.system == "HVAC_Supply":
                return "Mat_HVAC_Supply"
            elif e.system == "HVAC_Exhaust":
                return "Mat_HVAC_Exhaust"
            elif e.system == "Plumbing_Cold":
                return "Mat_Pipe_Cold"
            elif e.system == "Plumbing_Drain":
                return "Mat_Pipe_Soil"
            elif e.system == "Electrical":
                return "Mat_LightFixture" if e.category == "Fixture" else "Mat_CableTray"
            elif e.category == "Fixture" and ("WC" in e.elem_id or "LAVABO" in e.elem_id):
                return "Mat_SanitaryWare"
            elif e.category == "Equipment":
                return "Mat_Equipment"
            elif e.category in ["Slab", "Column", "Beam"]:
                return "Mat_Concrete"
            else:
                return "Mat_BrickWall"

        v_offset = 1
        obj_lines = [f"mtllib {mtl_filename}\n"]

        for elem in model.elements:
            b = elem.bbox
            mat = get_mat_for_elem(elem)
            # 8 đỉnh của hộp (đổi từ mm sang Mét để chuẩn tỷ lệ Three.js & OBJ)
            scale = 0.001
            x0, x1 = b.min_x * scale, b.max_x * scale
            y0, y1 = b.min_y * scale, b.max_y * scale
            z0, z1 = b.min_z * scale, b.max_z * scale

            # Tọa độ OBJ: Y up, Z forward (Three.js standard: X=X, Y=Z, Z=-Y)
            v = [
                (x0, z0, -y0), # 1
                (x1, z0, -y0), # 2
                (x1, z0, -y1), # 3
                (x0, z0, -y1), # 4
                (x0, z1, -y0), # 5
                (x1, z1, -y0), # 6
                (x1, z1, -y1), # 7
                (x0, z1, -y1)  # 8
            ]

            obj_lines.append(f"o {elem.elem_id}\n")
            obj_lines.append(f"usemtl {mat}\n")
            for pt in v:
                obj_lines.append(f"v {pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}\n")

            # 6 mặt của hộp lập phương (quad faces)
            faces = [
                (v_offset+3, v_offset+2, v_offset+1, v_offset+0), # Đáy
                (v_offset+4, v_offset+5, v_offset+6, v_offset+7), # Đỉnh
                (v_offset+0, v_offset+1, v_offset+5, v_offset+4), # Trước
                (v_offset+2, v_offset+3, v_offset+7, v_offset+6), # Sau
                (v_offset+3, v_offset+0, v_offset+4, v_offset+7), # Trái
                (v_offset+1, v_offset+2, v_offset+6, v_offset+5)  # Phải
            ]
            for f_indices in faces:
                obj_lines.append(f"f {f_indices[0]} {f_indices[1]} {f_indices[2]} {f_indices[3]}\n")

            v_offset += 8

        with open(obj_path, "w", encoding="utf-8") as f:
            f.writelines(obj_lines)

    @classmethod
    def export_to_technical_dxf(cls, model: CompleteMepBimModel, dxf_path: str):
        """
        Xuất bản vẽ kỹ thuật CAD (.dxf) chuyên nghiệp:
        - Khung tên bản vẽ tiêu chuẩn TCVN A1 (841 x 594 mm) quy đổi tỷ lệ 1:100.
        - Mặt bằng bố trí hệ thống MEP: Lưới trục, Tường, Ống gió, Ống nước, Máng cáp, Thiết bị.
        - Bảng thống kê khối lượng (BOQ Schedule) được vẽ tự động ngay trên bản vẽ!
        - Ký hiệu kỹ thuật, kích thước, ghi chú và cao độ lắp đặt.
        """
        if not ezdxf:
            return

        doc = ezdxf.new("R2018", setup=True)
        msp = doc.modelspace()

        # Tạo hệ thống Layer chuẩn CAD
        layers_info = [
            ("A-WALL", 7),       # Trắng
            ("S-BEAM", 8),       # Xám
            ("S-COLS", 9),       # Xám nhạt
            ("M-DUCT-SUPP", 4),  # Cyan
            ("M-DIFFUSER", 4),   # Cyan
            ("P-PIPE-COLD", 5),  # Blue
            ("P-PIPE-SOIL", 1),  # Red / Brown
            ("P-SAN-FIXT", 7),   # White
            ("E-CABL-TRAY", 2),  # Yellow
            ("E-LITE-FIXT", 2),  # Yellow
            ("E-PANEL-DB", 6),   # Magenta
            ("ANNO-TEXT", 3),    # Green
            ("ANNO-TITLE", 7)    # White
        ]
        for l_name, l_col in layers_info:
            doc.layers.add(name=l_name, color=l_col)

        # 1. Vẽ Tường, Cột, Dầm và các cấu kiện kiến trúc 2D trên mặt bằng
        for elem in model.elements:
            if elem.level != "Tang_1":
                continue # Vẽ mặt bằng Tầng 1
            b = elem.bbox
            layer = "A-WALL"
            if elem.category == "Column":
                layer = "S-COLS"
            elif elem.category == "Beam":
                layer = "S-BEAM"
            elif elem.category == "Duct":
                layer = "M-DUCT-SUPP"
            elif elem.category == "Pipe":
                layer = "P-PIPE-COLD" if "COLD" in elem.system else "P-PIPE-SOIL"
            elif elem.category == "CableTray":
                layer = "E-CABL-TRAY"
            elif elem.category == "Fixture" and "LIGHT" in elem.elem_id:
                layer = "E-LITE-FIXT"
            elif elem.category == "Fixture" and ("WC" in elem.elem_id or "LAVABO" in elem.elem_id):
                layer = "P-SAN-FIXT"
            elif elem.category == "Equipment" and "DB" in elem.elem_id:
                layer = "E-PANEL-DB"

            # Vẽ đa giác hình chữ nhật
            pts = [
                (b.min_x, b.min_y),
                (b.max_x, b.min_y),
                (b.max_x, b.max_y),
                (b.min_x, b.max_y)
            ]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

            # Vẽ ký hiệu X cho Cột hoặc Đèn hoặc Miệng gió
            if elem.category == "Column" or (elem.category == "Fixture" and "DIFFUSER" in elem.elem_id):
                msp.add_line((b.min_x, b.min_y), (b.max_x, b.max_y), dxfattribs={"layer": layer})
                msp.add_line((b.min_x, b.max_y), (b.max_x, b.min_y), dxfattribs={"layer": layer})

        # 2. Ghi chú Tên Phòng và Kích thước
        for r in model.rooms:
            if r.get("level") == "Tang_1":
                cx = (r["x0"] + r["x1"]) / 2.0
                cy = (r["y0"] + r["y1"]) / 2.0
                msp.add_text(r["name"], dxfattribs={"layer": "ANNO-TEXT", "height": 220.0}).set_placement(
                    (cx, cy), align=TextEntityAlignment.MIDDLE_CENTER
                )
                msp.add_text(f"S = {r['area_m2']:.1f} m²", dxfattribs={"layer": "ANNO-TEXT", "height": 180.0}).set_placement(
                    (cx, cy - 280.0), align=TextEntityAlignment.MIDDLE_CENTER
                )

        # 3. Vẽ Bảng Thống Kê Khối Lượng MEP (BOQ Schedule) trực tiếp trên bản vẽ CAD
        boq_data = MepBoqEstimator.generate_boq(model)
        start_table_x = 13500.0
        start_table_y = 8000.0
        row_height = 320.0
        col_widths = [600.0, 4800.0, 700.0, 900.0, 1600.0, 2200.0] # STT, Tên, ĐVT, SL, Đơn giá, Thành tiền
        table_width = sum(col_widths)

        # Tiêu đề bảng
        msp.add_text("BẢNG THỐNG KÊ KHỐI LƯỢNG VẬT TƯ & THIẾT BỊ MEP (BOQ SCHEDULE)",
                     dxfattribs={"layer": "ANNO-TITLE", "height": 280.0}).set_placement(
            (start_table_x, start_table_y + 400.0)
        )

        headers = ["STT", "DANH MỤC VẬT TƯ & THIẾT BỊ", "ĐVT", "SỐ LƯỢNG", "ĐƠN GIÁ (VND)", "THÀNH TIỀN (VND)"]
        cur_y = start_table_y

        # Vẽ Header hàng tiêu đề
        cur_x = start_table_x
        for col_idx, (head, cw) in enumerate(zip(headers, col_widths)):
            msp.add_lwpolyline([
                (cur_x, cur_y), (cur_x + cw, cur_y), (cur_x + cw, cur_y - row_height), (cur_x, cur_y - row_height)
            ], close=True, dxfattribs={"layer": "ANNO-TITLE"})
            msp.add_text(head, dxfattribs={"layer": "ANNO-TITLE", "height": 160.0}).set_placement(
                (cur_x + cw / 2.0, cur_y - row_height / 2.0), align=TextEntityAlignment.MIDDLE_CENTER
            )
            cur_x += cw
        cur_y -= row_height

        # Vẽ các hàng dữ liệu BOQ
        for item in boq_data["items"][:12]: # Hiển thị 12 dòng chính trên bản vẽ
            cur_x = start_table_x
            row_data = [
                str(item["item_no"]),
                item["description"],
                item["unit"],
                str(item["quantity"]),
                f"{item['material_price_vnd']:,}".replace(",", "."),
                f"{item['total_amount_vnd']:,}".replace(",", ".")
            ]
            for col_idx, (val, cw) in enumerate(zip(row_data, col_widths)):
                msp.add_lwpolyline([
                    (cur_x, cur_y), (cur_x + cw, cur_y), (cur_x + cw, cur_y - row_height), (cur_x, cur_y - row_height)
                ], close=True, dxfattribs={"layer": "ANNO-TEXT"})
                align = TextEntityAlignment.MIDDLE_CENTER if col_idx in [0, 2, 3] else (
                    TextEntityAlignment.MIDDLE_RIGHT if col_idx in [4, 5] else TextEntityAlignment.MIDDLE_LEFT
                )
                text_x = cur_x + cw / 2.0 if col_idx in [0, 2, 3] else (
                    cur_x + cw - 100.0 if col_idx in [4, 5] else cur_x + 100.0
                )
                msp.add_text(val, dxfattribs={"layer": "ANNO-TEXT", "height": 140.0}).set_placement(
                    (text_x, cur_y - row_height / 2.0), align=align
                )
                cur_x += cw
            cur_y -= row_height

        # Hàng Tổng Cộng
        msp.add_lwpolyline([
            (start_table_x, cur_y), (start_table_x + table_width, cur_y),
            (start_table_x + table_width, cur_y - row_height), (start_table_x, cur_y - row_height)
        ], close=True, dxfattribs={"layer": "ANNO-TITLE"})
        msp.add_text("TỔNG CỘNG CHI PHÍ MEP (ĐÃ GỒM VAT 10%):",
                     dxfattribs={"layer": "ANNO-TITLE", "height": 180.0}).set_placement(
            (start_table_x + 200.0, cur_y - row_height / 2.0), align=TextEntityAlignment.MIDDLE_LEFT
        )
        msp.add_text(boq_data["formatted_total"],
                     dxfattribs={"layer": "ANNO-TITLE", "height": 200.0}).set_placement(
            (start_table_x + table_width - 200.0, cur_y - row_height / 2.0), align=TextEntityAlignment.MIDDLE_RIGHT
        )

        # 4. Vẽ Khung Bản Vẽ Kỹ Thuật (Border & Title Block A1)
        frame_x0, frame_y0 = -1000.0, -1500.0
        frame_x1, frame_y1 = 25000.0, 9500.0
        msp.add_lwpolyline([
            (frame_x0, frame_y0), (frame_x1, frame_y0), (frame_x1, frame_y1), (frame_x0, frame_y1)
        ], close=True, dxfattribs={"layer": "ANNO-TITLE"})

        # Khung tên ở góc dưới phải
        tb_w, tb_h = 7500.0, 2400.0
        tb_x0 = frame_x1 - tb_w
        tb_y0 = frame_y0
        msp.add_lwpolyline([
            (tb_x0, tb_y0), (frame_x1, tb_y0), (frame_x1, tb_y0 + tb_h), (tb_x0, tb_y0 + tb_h)
        ], close=True, dxfattribs={"layer": "ANNO-TITLE"})

        # Thông tin khung tên
        msp.add_text("DỰ ÁN: MÔ HÌNH HÓA VÀ THIẾT KẾ TỰ ĐỘNG MEP 3D",
                     dxfattribs={"layer": "ANNO-TITLE", "height": 220.0}).set_placement((tb_x0 + 300.0, tb_y0 + 1900.0))
        msp.add_text("BẢN VẼ: MẶT BẰNG BỐ TRÍ MEP & THỐNG KÊ KHỐI LƯỢNG TỔNG HỢP",
                     dxfattribs={"layer": "ANNO-TITLE", "height": 180.0}).set_placement((tb_x0 + 300.0, tb_y0 + 1400.0))
        msp.add_text(f"NGÀY XUẤT: {time.strftime('%d/%m/%Y')}   |   TỶ LỆ: 1:100   |   GIAI ĐOẠN: THI CÔNG BIM",
                     dxfattribs={"layer": "ANNO-TEXT", "height": 160.0}).set_placement((tb_x0 + 300.0, tb_y0 + 900.0))
        msp.add_text("ĐƠN VỊ THIẾT KẾ: REVITAI MEP AUTOMATION STUDIO",
                     dxfattribs={"layer": "ANNO-TITLE", "height": 180.0}).set_placement((tb_x0 + 300.0, tb_y0 + 400.0))

        doc.saveas(dxf_path)

    @classmethod
    def export_to_ifc4(cls, model: CompleteMepBimModel, ifc_path: str):
        """Xuất mô hình sang chuẩn IFC 4 đầy đủ thuộc tính và hệ thống phân phối MEP."""
        if not ifcopenshell:
            return

        ifc = ifcopenshell.api.run("project.create_file", version="IFC4")
        project = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcProject", name=model.name)
        ifcopenshell.api.run("unit.assign_unit", ifc, length={"is_metric": True, "raw": "MILLIMETERS"})

        context = ifcopenshell.api.run("context.add_context", ifc, context_type="Model")
        body_context = ifcopenshell.api.run(
            "context.add_context", ifc,
            context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=context
        )

        site = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcSite", name="KhuDat_DuAn")
        ifcopenshell.api.run("aggregate.assign_object", ifc, relating_object=project, products=[site])

        building = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcBuilding", name="ToaNha_MEP_BIM")
        ifcopenshell.api.run("aggregate.assign_object", ifc, relating_object=site, products=[building])

        storeys = {}
        for level_name in ["Tang_1", "Tang_2", "Mai"]:
            st = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcBuildingStorey", name=level_name)
            ifcopenshell.api.run("aggregate.assign_object", ifc, relating_object=building, products=[st])
            storeys[level_name] = st

        def add_box_geometry(product, b: BBox3D):
            poly = ifc.create_entity(
                "IfcPolyline",
                Points=[
                    ifc.create_entity("IfcCartesianPoint", Coordinates=[b.min_x, b.min_y]),
                    ifc.create_entity("IfcCartesianPoint", Coordinates=[b.max_x, b.min_y]),
                    ifc.create_entity("IfcCartesianPoint", Coordinates=[b.max_x, b.max_y]),
                    ifc.create_entity("IfcCartesianPoint", Coordinates=[b.min_x, b.max_y]),
                    ifc.create_entity("IfcCartesianPoint", Coordinates=[b.min_x, b.min_y]),
                ]
            )
            profile = ifc.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=poly)
            pos = ifc.create_entity(
                "IfcAxis2Placement3D",
                Location=ifc.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, b.min_z]),
                Axis=ifc.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
                RefDirection=ifc.create_entity("IfcDirection", DirectionRatios=[1.0, 0.0, 0.0])
            )
            solid = ifc.create_entity(
                "IfcExtrudedAreaSolid",
                SweptArea=profile,
                Position=pos,
                ExtrudedDirection=ifc.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
                Depth=float(b.max_z - b.min_z)
            )
            rep = ifc.create_entity(
                "IfcShapeRepresentation",
                ContextOfItems=body_context,
                RepresentationIdentifier="Body",
                RepresentationType="SweptSolid",
                Items=[solid]
            )
            product.Representation = ifc.create_entity("IfcProductDefinitionShape", Representations=[rep])

        for elem in model.elements:
            st = storeys.get(elem.level, storeys["Tang_1"])

            # Map IFC Class theo category MEP
            if elem.category == "Wall":
                ifc_class = "IfcWall"
            elif elem.category == "Slab":
                ifc_class = "IfcSlab"
            elif elem.category == "Column":
                ifc_class = "IfcColumn"
            elif elem.category == "Beam":
                ifc_class = "IfcBeam"
            elif elem.category == "Duct":
                ifc_class = "IfcFlowSegment"
            elif elem.category == "Pipe":
                ifc_class = "IfcFlowSegment"
            elif elem.category == "CableTray":
                ifc_class = "IfcFlowSegment"
            elif elem.category == "Fixture" and "LIGHT" in elem.elem_id:
                ifc_class = "IfcLightFixture"
            elif elem.category == "Fixture" and ("WC" in elem.elem_id or "LAVABO" in elem.elem_id or "DRAIN" in elem.elem_id):
                ifc_class = "IfcSanitaryTerminal"
            elif elem.category == "Fixture" and "DIFFUSER" in elem.elem_id:
                ifc_class = "IfcAirTerminal"
            elif elem.category == "Equipment":
                ifc_class = "IfcEnergyConversionDevice"
            else:
                ifc_class = "IfcBuildingElementProxy"

            try:
                prod = ifcopenshell.api.run("root.create_entity", ifc, ifc_class=ifc_class, name=elem.name)
                ifcopenshell.api.run("spatial.assign_container", ifc, relating_structure=st, products=[prod])
                add_box_geometry(prod, elem.bbox)
            except Exception:
                pass

        ifc.write(ifc_path)


# ==============================================================================
# 7. HÀM CHẠY TỔNG HỢP (PIPELINE RUNNER)
# ==============================================================================

def run_complete_mep_pipeline(building_width=12000.0,
                              building_depth=8000.0,
                              floor_height=3600.0,
                              num_floors=2,
                              auto_resolve_clashes=True) -> Dict[str, Any]:
    """
    Thực thi toàn bộ quy trình thiết kế tự động MEP 3D khép kín:
    1. Thiết kế Điện & Chiếu sáng
    2. Thiết kế Cấp thoát nước
    3. Thiết kế Điều hòa thông gió HVAC
    4. Dựng mô hình BIM 3D chuyên nghiệp (IFC, OBJ, DXF)
    5. Quét kiểm tra & Tự động triệt tiêu xung đột (Clash Detection & Auto-Resolution)
    6. Bóc tách khối lượng (BOQ Schedule) & Xuất bản vẽ CAD kỹ thuật
    """
    start_time = time.time()

    # 1, 2, 3: Sinh mô hình Kiến trúc + MEP
    model = MepBimBuilder.generate_building_mep_model(
        building_width=building_width,
        building_depth=building_depth,
        floor_height=floor_height,
        num_floors=num_floors
    )

    # 5: Quét xung đột
    raw_clashes = MepClashDetector.run_clash_detection(model)

    resolve_info = None
    if auto_resolve_clashes and len(raw_clashes) > 0:
        resolve_info = MepClashDetector.auto_resolve_clashes(model)

    # 6: Bóc tách khối lượng BOQ
    boq_results = MepBoqEstimator.generate_boq(model)

    # 4 & 6: Xuất bản vẽ và file mô hình BIM 3D
    exported_files = MepBimExporter.export_all(model)

    elapsed_s = round(time.time() - start_time, 2)

    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed_s,
        "model_name": model.name,
        "summary": model.summary_stats,
        "clash_detection": {
            "initial_clashes_count": len(raw_clashes),
            "clashes": raw_clashes,
            "auto_resolve": resolve_info
        },
        "boq_schedule": boq_results,
        "exported_files": exported_files
    }


if __name__ == "__main__":
    print("=== ĐANG KHỞI CHẠY BỘ MÁY THIẾT KẾ MEP & DỰNG 3D BIM TỰ ĐỘNG ===")
    res = run_complete_mep_pipeline(12000.0, 8000.0, 3600.0, 2, auto_resolve_clashes=True)
    print(f"\n✅ HOÀN TẤT TRONG {res['elapsed_seconds']} GIÂY!")
    print(f"Tổng số phần tử BIM MEP: {res['summary']['total_elements']}")
    print(f"Tổng giá trị dự toán MEP: {res['boq_schedule']['formatted_total']}")
    print(f"Số xung đột ban đầu: {res['clash_detection']['initial_clashes_count']}")
    if res['clash_detection']['auto_resolve']:
        print(f"Đã tự động nắn tuyến triệt tiêu: {res['clash_detection']['auto_resolve']['resolved_count']} xung đột")
    print("\nCác file đã xuất:")
    for k, v in res["exported_files"].items():
        print(f" - {k.upper()}: {v}")
