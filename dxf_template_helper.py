#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dxf_template_helper.py
Module tiện ích khởi tạo DXF Document dùng template dim.dxf:
- Hỗ trợ font TrueType tahoma.ttf cho Unicode tiếng Việt (AutoCAD không bị lỗi font)
- Khởi tạo đầy đủ bảng Linetype chuẩn (CENTER, DASHDOT, DASHED...) chống lỗi 'Bad linetype name'
"""

import os
import ezdxf
from ezdxf.tools.standards import setup_linetypes

def get_template_dxf_doc():
    """
    Tạo hoặc tải AutoCAD DXF Document chuẩn từ template dim.dxf:
    - Font tiếng Việt chuẩn Unicode (tahoma.ttf) cho TextStyle 'Standard' & '1.5 mm Tahoma'.
    - Linetypes đầy đủ (CENTER, DASHDOT, DASHED, v.v.).
    - Modelspace được dọn sạch các đối tượng cũ nếu có.
    """
    template_candidates = [
        os.path.join(os.path.dirname(__file__), "templates", "dim.dxf"),
        os.path.expanduser(r"~\Downloads\dim.dxf"),
        os.path.join(os.path.dirname(__file__), "dim.dxf"),
    ]
    doc = None
    for p in template_candidates:
        if os.path.exists(p):
            try:
                doc = ezdxf.readfile(p)
                # Dọn dẹp modelspace
                msp = doc.modelspace()
                for e in list(msp):
                    msp.delete_entity(e)
                break
            except Exception as e:
                print(f"[DXF_TEMPLATE] Lỗi đọc template {p}: {e}")
                doc = None

    if doc is None:
        doc = ezdxf.new("R2010", setup=True)

    # Đảm bảo đăng ký đầy đủ linetypes chuẩn (CENTER, DASHDOT, DASHED, etc.)
    try:
        setup_linetypes(doc)
    except Exception:
        pass

    # Đảm bảo Text Style Standard và 1.5 mm Tahoma dùng font tahoma.ttf
    if "Standard" in doc.styles:
        doc.styles.get("Standard").dxf.font = "tahoma.ttf"
    else:
        doc.styles.new("Standard", dxfattribs={"font": "tahoma.ttf"})

    if "1.5 mm Tahoma" not in doc.styles:
        doc.styles.new("1.5 mm Tahoma", dxfattribs={"font": "tahoma.ttf"})

    return doc

def ensure_layer(doc, name, color=7, linetype="Continuous", lineweight=None):
    """Tạo layer an toàn nếu chưa tồn tại trong DXF Document."""
    if name not in doc.layers:
        attribs = {"color": color}
        if linetype and linetype in doc.linetypes:
            attribs["linetype"] = linetype
        elif linetype and linetype != "Continuous":
            try:
                setup_linetypes(doc)
                if linetype in doc.linetypes:
                    attribs["linetype"] = linetype
            except Exception:
                pass
        if lineweight is not None:
            attribs["lineweight"] = lineweight
        doc.layers.add(name, **attribs)
    return doc.layers.get(name)
