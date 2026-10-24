# -*- coding: utf-8 -*-
"""
etabs_service.py
Service for extracting and serving ETABS structural beam and column data,
2D floor framing plans with true beam width, 3D solid cross-sections,
and TCVN 5574-2012 rebar calculation & selection.
"""

import os
import sys
import json
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, 'etabs_beam_data.json')
EXTRACTOR_SCRIPT = os.path.join(CURRENT_DIR, 'extract_etabs_data.py')

def get_etabs_data():
    """Returns cached ETABS beam & structural data. If not cached, triggers extraction."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print("Error reading cached etabs_beam_data.json:", e)
    
    # Run extractor if cache missing
    refresh_etabs_data()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'model_name': 'CAI_TAO_PHUONG_AN_B.EDB',
        'grids': {'X': [], 'Y': []},
        'sections': {},
        'stories': [],
        'beams': [],
        'columns': [],
        'areas': []
    }

def refresh_etabs_data():
    """Runs extract_etabs_data.py via subprocess to refresh data from EDB."""
    try:
        proc = subprocess.run([sys.executable, EXTRACTOR_SCRIPT], capture_output=True, text=True, timeout=90)
        return {
            'success': proc.returncode == 0,
            'output': proc.stdout or proc.stderr,
            'message': 'Đã làm mới dữ liệu từ ETABS thành công!' if proc.returncode == 0 else f'Lỗi làm mới: {proc.stderr}'
        }
    except Exception as e:
        return {'success': False, 'message': f'Ngoại lệ khi gọi ETABS: {str(e)}'}
