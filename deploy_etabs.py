# -*- coding: utf-8 -*-
"""
deploy_etabs.py
Deployer for ETABS Structural AI Hub to VPS https://mr.pkld.online
(Root: /var/www/mr.pkld.online, Server: 103.163.219.87)
"""

import os
import sys
import json
import subprocess
import tempfile

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VPS_HOST = "103.163.219.87"
VPS_USER = "root"
VPS_TARGET_DIR = "/var/www/mr.pkld.online"

STANDALONE_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ETABS Structural AI Hub • mr.pkld.online</title>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f5f7ff',
              100: '#ebf0fe',
              500: '#4f46e5',
              600: '#4338ca',
              700: '#3730a3',
            }
          }
        }
      }
    }
  </script>
  <!-- Lucide Icons CDN -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- Three.js & OrbitControls for ETABS 3D Solid Cross-Section Model -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col font-sans antialiased">

  <!-- Navigation Bar -->
  <header class="bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40 shadow-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center text-white font-black text-lg shadow-md shadow-blue-500/20 border border-cyan-400/30">
          <i data-lucide="layers" class="w-5 h-5"></i>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold text-slate-900 tracking-tight">ETABS Structural AI Hub</h1>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">TCVN 5574-2012</span>
          </div>
          <p class="text-xs text-slate-500">Model: <span class="font-mono text-cyan-600 font-semibold">CAI_TAO_PHUONG_AN_B.EDB</span> (103 Dầm • 56 Cột • 5 Tầng)</p>
        </div>
      </div>

      <div class="flex items-center gap-2.5">
        <a href="https://mr.pkld.online" class="hidden sm:flex items-center gap-1.5 text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl font-bold">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          mr.pkld.online Live
        </a>
      </div>
    </div>
  </header>

  <!-- Main Content Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-5">
    
    <!-- 3-Way Segmented Switch Tab Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div class="inline-flex p-1.5 bg-slate-200/80 rounded-2xl border border-slate-300/80 shadow-inner gap-1">
        <button onclick="switchEtabsSubTab('etabs-3d')" id="subtab-btn-3d" class="etabs-subtab-btn py-2 px-4 rounded-xl font-bold text-xs flex items-center gap-2 bg-indigo-600 text-white shadow-md shadow-indigo-600/25 transition-all duration-150 cursor-pointer">
          <i data-lucide="box" class="w-4 h-4"></i> (1) Model 3D Đúng Tiết Diện & Moment
        </button>
        <button onclick="switchEtabsSubTab('etabs-2d')" id="subtab-btn-2d" class="etabs-subtab-btn py-2 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer">
          <i data-lucide="map" class="w-4 h-4"></i> (2) Mặt Bằng Dầm 2D Đúng Bề Rộng
        </button>
        <button onclick="switchEtabsSubTab('etabs-rebar')" id="subtab-btn-rebar" class="etabs-subtab-btn py-2 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer">
          <i data-lucide="table-2" class="w-4 h-4"></i> (3) Bảng Cốt Thép & Chọn Thép
        </button>
        <button onclick="switchEtabsSubTab('etabs-column-cad')" id="subtab-btn-column-cad" class="etabs-subtab-btn py-2 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer">
          <i data-lucide="columns" class="w-4 h-4 text-amber-500"></i> (4) Bản Vẽ Cột (15 Cột × 4 Tầng)
        </button>
        <button onclick="switchEtabsSubTab('etabs-tie-beam-cad')" id="subtab-btn-tie-beam-cad" class="etabs-subtab-btn py-2 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer">
          <i data-lucide="git-branch" class="w-4 h-4 text-emerald-500"></i> (5) Bản Vẽ Đà Kiềng (Trục A, B, C)
        </button>
        <!-- (6) DROPDOWN: BẢNG GHI CHÚ CHUNG KẾT CẤU (PLOT 1020) -->
        <div class="relative inline-block text-left" id="dropdown-notes-container">
          <button type="button" onclick="toggleNotesDropdown(event)" id="subtab-btn-notes" class="etabs-subtab-btn py-2 px-3.5 rounded-xl font-semibold text-xs flex items-center gap-1.5 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer" title="Xem Bảng Ghi Chú Chung Kết Cấu (Plot 1020)">
            <i data-lucide="file-text" class="w-4 h-4 text-orange-500"></i>
            <span>(6) Ghi Chú Chung</span>
            <i data-lucide="chevron-down" class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200" id="notes-dropdown-chevron"></i>
          </button>

          <!-- Dropdown Menu Box -->
          <div id="notes-dropdown-menu" class="hidden absolute right-0 sm:left-0 sm:right-auto mt-2 w-72 rounded-2xl bg-white/95 backdrop-blur-md shadow-2xl border border-slate-200/90 p-1.5 z-50 ring-1 ring-black/5 divide-y divide-slate-100 animate-in fade-in zoom-in-95 duration-150">
            <div class="px-3 py-2 bg-gradient-to-r from-amber-50 to-orange-50/60 rounded-xl mb-1 border border-amber-100">
              <div class="text-[10px] font-extrabold uppercase tracking-wider text-amber-800 flex items-center justify-between">
                <span class="flex items-center gap-1"><i data-lucide="file-text" class="w-3.5 h-3.5 text-amber-600"></i> Ghi Chú Chung Kết Cấu</span>
                <span class="text-[9px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 font-bold font-mono">TCVN</span>
              </div>
              <div class="text-[11px] text-slate-500 font-mono truncate mt-0.5" title="Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf">
                Plot_20261020_082443...pdf (144 KB)
              </div>
            </div>

            <div class="py-1">
              <button type="button" onclick="selectNotesViewAndSwitch('hd')" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 text-sm">🖼️</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">Bản Vẽ CAD HD</div>
                  <div class="text-[10px] text-slate-400 truncate">Xem tương tác zoom/pan trang giữa</div>
                </div>
              </button>

              <button type="button" onclick="selectNotesViewAndSwitch('pdf')" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-blue-50 hover:text-blue-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 text-sm">📄</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">Bản Vẽ PDF Gốc</div>
                  <div class="text-[10px] text-slate-400 truncate">Nhúng file PDF nguyên bản (Iframe)</div>
                </div>
              </button>

              <button type="button" onclick="selectNotesViewAndSwitch('text')" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-emerald-50 hover:text-emerald-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 text-sm">📝</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">Bóc Tách 24 Điều Khoản</div>
                  <div class="text-[10px] text-slate-400 truncate">Văn bản TCVN 5574 & bê tông bảo vệ</div>
                </div>
              </button>
            </div>

            <div class="py-1">
              <button type="button" onclick="openGeneralNotesModal('hd'); closeNotesDropdown();" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-orange-50 hover:text-orange-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-orange-100 text-orange-700 flex items-center justify-center shrink-0 text-sm">⛶</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">Xem Toàn Màn Hình</div>
                  <div class="text-[10px] text-slate-400 truncate">Mở modal riêng biệt tối đa diện tích</div>
                </div>
              </button>

              <button type="button" onclick="downloadGeneralNotesPdf(); closeNotesDropdown();" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-indigo-50 hover:text-indigo-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 text-sm">📥</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">Tải File PDF</div>
                  <div class="text-[10px] text-slate-400 truncate">Tải file 144 KB từ thư mục plot</div>
                </div>
              </button>

              <button type="button" onclick="printGeneralNotes(); closeNotesDropdown();" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center shrink-0 text-sm">🖨️</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">In Bản Vẽ</div>
                  <div class="text-[10px] text-slate-400 truncate">Kích hoạt hộp thoại in ấn</div>
                </div>
              </button>

              <button type="button" onclick="openGeneralNotesFolder(); closeNotesDropdown();" class="w-full text-left px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-2.5 transition cursor-pointer">
                <span class="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 text-sm">📁</span>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-slate-900 text-xs">Mở Thư Mục Plot</div>
                  <div class="text-[10px] text-slate-400 truncate">Mở Documents\\plot\\1020</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="hidden sm:flex items-center gap-2 text-xs text-slate-500 font-medium">
        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
        <span class="font-mono">CAI_TAO_PHUONG_AN_B.EDB</span>
      </div>
    </div>

    <!-- SUB-PANE 1: MODEL 3D ĐÚNG TIẾT DIỆN (THREE.JS SOLID BOXES + GRIDS + MOMENTS) -->
    <div id="subpane-etabs-3d" class="etabs-subpane space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 text-xs shadow-xs">
        <div class="flex items-center gap-3">
          <span class="font-bold text-slate-800 flex items-center gap-1.5">
            <i data-lucide="box" class="w-4 h-4 text-indigo-600"></i> Điều khiển 3D:
          </span>
          <span class="text-slate-500">Chuột trái: Xoay 360° • Lăn chuột: Phóng to/nhỏ • Chuột phải: Dời hình • Bấm vào dầm: Chọn cốt thép</span>
        </div>
      </div>

      <!-- 3D Three.js Container -->
      <div class="relative w-full h-[640px] bg-[#aaaaaa] rounded-3xl overflow-hidden border border-slate-400 shadow-xl group">
        <div id="etabs3DContainer" class="w-full h-full"></div>
        
        <!-- Top-Right Floating 3D Toolbar (Reset Camera, Moment 3D, Lưới Trục, Khung Dây) -->
        <div class="absolute top-3 right-3 z-20 flex flex-wrap items-center gap-1.5 bg-white/90 backdrop-blur-md p-1.5 rounded-2xl border border-slate-300 shadow-xl">
          <button onclick="toggle3DMoment()" id="btn3DMoment" class="py-1.5 px-3 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-800 font-bold text-xs flex items-center gap-1 border border-amber-400 transition active:scale-95 cursor-pointer" title="Bật/Tắt Biểu Đồ Moment M33 3D">
            <i data-lucide="activity" class="w-3.5 h-3.5 text-amber-600"></i> Moment 3D
          </button>
          <button onclick="toggle3DGrids()" id="btn3DGrids" class="py-1.5 px-3 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-800 font-bold text-xs flex items-center gap-1 border border-emerald-400 transition active:scale-95 cursor-pointer" title="Bật/Tắt Lưới Trục 1-7, A-C">
            <i data-lucide="grid" class="w-3.5 h-3.5 text-emerald-600"></i> Lưới Trục
          </button>
          <button onclick="toggle3DWireframe()" id="btn3DWireframe" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1 border border-slate-300 transition active:scale-95 cursor-pointer" title="Bật/Tắt Khung Dây">
            <i data-lucide="eye" class="w-3.5 h-3.5 text-indigo-600"></i> Khung Dây
          </button>
          <button onclick="reset3DCamera()" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1 border border-slate-300 transition active:scale-95 cursor-pointer" title="Đặt lại góc nhìn 3D">
            <i data-lucide="rotate-ccw" class="w-3.5 h-3.5 text-sky-600"></i> Reset Góc Nhìn
          </button>
        </div>

        <!-- 3D Beam Hover Tooltip -->
        <div id="etabs3DTooltip" class="absolute hidden bg-slate-900/95 text-white border border-cyan-400/80 rounded-2xl p-3 shadow-2xl pointer-events-none z-30 text-xs max-w-xs transition-opacity duration-150"></div>

        <!-- Legend Overlay (Collapsible) -->
        <div id="etabs3DLegendCard" class="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md border border-slate-300 rounded-2xl shadow-xl z-20 overflow-hidden text-[11px] text-slate-700 pointer-events-auto">
          <button type="button" onclick="toggle3DLegend()" class="w-full flex items-center justify-between gap-3 px-3 py-2 font-bold text-slate-900 hover:bg-slate-100/80 transition-colors cursor-pointer select-none">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-cyan-600"></span>
              <span>Chú Giải Model 3D:</span>
            </div>
            <i id="ico3DLegendToggle" data-lucide="chevron-up" class="w-3.5 h-3.5 text-slate-500 transition-transform duration-200"></i>
          </button>
          <div id="body3DLegend" class="px-3 pb-2.5 pt-0.5 space-y-1 border-t border-slate-100">
            <div class="flex items-center gap-2"><span class="w-3 h-3 bg-cyan-500 rounded-sm shrink-0"></span> Dầm Khung (Bấm trực tiếp để chọn cốt thép)</div>
            <div class="flex items-center gap-2"><span class="w-3 h-3 bg-indigo-500 rounded-sm shrink-0"></span> Cột Bê Tông (Solid Column)</div>
            <div class="flex items-center gap-2"><span class="w-3 h-3 bg-red-500 rounded-sm shrink-0"></span> Sàn & Bản Thang (Đã đóng kín ban công trục 7)</div>
            <div class="flex items-center gap-2"><span class="w-3 h-1 bg-amber-500 rounded-sm shrink-0"></span> Biểu Đồ Moment M33 Uốn Dầm</div>
          </div>
        </div>
      </div>
    </div>

    <!-- SUB-PANE 2: MẶT BẰNG DẦM 2D (ĐÚNG BỀ RỘNG DẦM + TEXT TIẾT DIỆN) -->
    <div id="subpane-etabs-2d" class="etabs-subpane hidden space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div class="flex items-center gap-2.5 flex-wrap">
          <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5 shrink-0">
            <i data-lucide="layers" class="w-3.5 h-3.5 text-indigo-600"></i> Chọn tầng xem mặt bằng:
          </span>
          <div id="etabs2DStoryButtons" class="flex items-center gap-1.5 flex-wrap">
            <button type="button" data-story="DK" onclick="selectEtabs2DStory('DK')" class="brm-story-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-300 hover:bg-indigo-50 hover:text-indigo-700 transition cursor-pointer" title="Mặt bằng Đà Kiềng / Móng">DK</button>
            <button type="button" data-story="T1" onclick="selectEtabs2DStory('T1')" class="brm-story-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-300 hover:bg-indigo-50 hover:text-indigo-700 transition cursor-pointer" title="Cao độ Z = 1.8m (T1)">T1</button>
            <button type="button" data-story="T2" onclick="selectEtabs2DStory('T2')" class="brm-story-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-300 hover:bg-indigo-50 hover:text-indigo-700 transition cursor-pointer" title="Cao độ Z = 7.6m (T2)">T2</button>
            <button type="button" data-story="T3" onclick="selectEtabs2DStory('T3')" class="brm-story-btn px-3 py-1.5 rounded-xl text-xs font-extrabold bg-indigo-600 text-white shadow-xs transition flex items-center gap-1 cursor-default" title="Cao độ Z = 11.8m (T3)">T3</button>
            <button type="button" data-story="T4" onclick="selectEtabs2DStory('T4')" class="brm-story-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-300 hover:bg-indigo-50 hover:text-indigo-700 transition cursor-pointer" title="Cao độ Z = 15.6m (T4)">T4</button>
            <button type="button" data-story="C" onclick="selectEtabs2DStory('C')" class="brm-story-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-300 hover:bg-indigo-50 hover:text-indigo-700 transition cursor-pointer" title="Mặt bằng Định vị & Bố trí Cột">C</button>
          </div>
          <input type="hidden" id="etabs2DStorySelect" value="T3">
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <button type="button" onclick="exportBeamPlanPdf()" class="py-1.5 px-2.5 rounded-xl bg-white hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-300 text-xs font-bold flex items-center gap-1 cursor-pointer transition shadow-2xs" title="Xuất file PDF Mặt Bằng Ký Hiệu Dầm (khổ A1)">
            <i data-lucide="file-text" class="w-3.5 h-3.5 text-indigo-600"></i> Xuất PDF Mặt Bằng
          </button>
          <button type="button" onclick="exportBeamPlanDxf()" class="py-1.5 px-2.5 rounded-xl bg-white hover:bg-amber-50 hover:text-amber-800 text-slate-700 border border-slate-300 text-xs font-bold flex items-center gap-1 cursor-pointer transition shadow-2xs" title="Xuất file AutoCAD DXF R2010 Mặt Bằng Ký Hiệu Dầm">
            <i data-lucide="download" class="w-3.5 h-3.5 text-amber-600"></i> Xuất DXF Mặt Bằng
          </button>
          <button onclick="zoomEtabs2D(1.2)" class="p-2 rounded-xl bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold" title="Phóng to">
            <i data-lucide="zoom-in" class="w-4 h-4"></i>
          </button>
          <button onclick="zoomEtabs2D(0.8)" class="p-2 rounded-xl bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold" title="Thu nhỏ">
            <i data-lucide="zoom-out" class="w-4 h-4"></i>
          </button>
          <button onclick="resetEtabs2DView()" class="py-1.5 px-3 rounded-xl bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold flex items-center gap-1" title="Vừa màn hình">
            <i data-lucide="maximize" class="w-3.5 h-3.5"></i> Vừa khung
          </button>
          <label class="flex items-center gap-1.5 text-xs font-medium text-slate-700 ml-1 cursor-pointer">
            <input type="checkbox" id="chkShow2DLabels" checked onchange="renderEtabs2DPlan()" class="rounded border-slate-300 text-indigo-600 focus:ring-0"> Hiện nhãn tiết diện
          </label>
        </div>
      </div>

      <!-- 2D Canvas Container -->
      <div class="relative w-full h-[640px] bg-[#aaaaaa] rounded-3xl overflow-hidden border border-slate-400 shadow-xl">
        <canvas id="etabs2DCanvas" class="w-full h-full cursor-grab active:cursor-grabbing"></canvas>
        
        <!-- 2D Legend Overlay (Collapsible) -->
        <div id="etabs2DLegendCard" class="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md border border-slate-300 rounded-2xl shadow-xl z-20 overflow-hidden text-[11px] text-slate-700 pointer-events-auto">
          <button type="button" onclick="toggle2DLegend()" class="w-full flex items-center justify-between gap-3 px-3 py-2 font-bold text-slate-900 hover:bg-slate-100/80 transition-colors cursor-pointer select-none">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-cyan-600"></span>
              <span>Chú Giải Tiết Diện Mặt Bằng</span>
            </div>
            <i id="ico2DLegendToggle" data-lucide="chevron-up" class="w-3.5 h-3.5 text-slate-500 transition-transform duration-200"></i>
          </button>
          <div id="body2DLegend" class="px-3 pb-2.5 pt-0.5 space-y-1 border-t border-slate-100">
            <div class="flex items-center gap-2"><span class="w-4 h-2 bg-sky-500 rounded-sm shrink-0"></span> Dầm BTCT</div>
            <div class="flex items-center gap-2"><span class="w-3 h-3 bg-slate-700 rounded-sm shrink-0"></span> Cột BTCT</div>
            <div class="flex items-center gap-2"><span class="w-4 h-0.5 border-t border-dashed border-emerald-600 shrink-0"></span> Lưới trục kiến trúc</div>
          </div>
        </div>

        <div id="etabs2DTooltip" class="absolute hidden bg-slate-900/95 text-white border border-indigo-400 text-xs rounded-xl p-2.5 shadow-xl pointer-events-none z-10 space-y-1"></div>
      </div>
    </div>

    <!-- SUB-PANE 3: BẢNG THÔNG SỐ CỐT THÉP & CHỌN THÉP TỪNG DẦM (TCVN) -->
    <div id="subpane-etabs-rebar" class="etabs-subpane hidden space-y-3">
      
      <!-- Filter Bar -->
      <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-xs">
        <div class="flex items-center gap-3">
          <div>
            <label class="text-[11px] font-bold text-slate-600 block mb-1">Lọc theo Tầng:</label>
            <select id="rebarFilterStory" onchange="filterRebarTable()" class="bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs font-bold text-indigo-900 focus:outline-none focus:ring-1 focus:ring-indigo-600 cursor-pointer">
              <option value="ALL">Tất cả các tầng (103 dầm)</option>
              <option value="T4">Tầng 4 (Sân Thượng / Mái)</option>
              <option value="T3">Tầng 3</option>
              <option value="T2">Tầng 2</option>
              <option value="T1">Tầng 1</option>
            </select>
          </div>
          <div>
            <label class="text-[11px] font-bold text-slate-600 block mb-1">Tìm dầm dài / tiết diện:</label>
            <input type="text" id="rebarSearchInput" oninput="filterRebarTable()" placeholder="VD: DX1, DY2, 200x400..." class="bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-600 placeholder-slate-400">
          </div>
        </div>

        <!-- Export Buttons -->
        <div class="flex items-center gap-2">
          <button onclick="exportRebarCSV()" class="py-2 px-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition cursor-pointer">
            <i data-lucide="file-spreadsheet" class="w-4 h-4"></i> Xuất CSV (Excel)
          </button>
          <button onclick="printRebarTable()" class="py-2 px-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1.5 border border-slate-300 transition cursor-pointer">
            <i data-lucide="printer" class="w-4 h-4"></i> In Bảng
          </button>
        </div>
      </div>

      <!-- Table Container -->
      <div class="overflow-x-auto rounded-2xl border border-slate-200 shadow-sm max-h-[560px] bg-white">
        <table id="rebarTable" class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-100 text-slate-700 font-bold uppercase text-[10px] tracking-wider sticky top-0 z-10 border-b border-slate-200 shadow-xs">
            <tr class="divide-x divide-slate-200">
              <th class="p-3 text-center">Tầng</th>
              <th class="p-3">Dầm Dài (DX/DY)</th>
              <th class="p-3">Tiết Diện</th>
              <th class="p-3 text-right">Nhịp L (m)</th>
              <th class="p-3 text-right bg-amber-50 text-amber-900">As Gối T (cm²)</th>
              <th class="p-3 text-right bg-amber-50 text-amber-900">As Bụng (cm²)</th>
              <th class="p-3 text-right bg-amber-50 text-amber-900">As Gối P (cm²)</th>
              <th class="p-3 text-right bg-sky-50 text-sky-900">As Đai (cm²/m)</th>
              <th class="p-3 bg-indigo-50 text-indigo-950 font-extrabold">Cốt Thép Chọn (Gối T / Nhịp / Gối P)</th>
              <th class="p-3 bg-indigo-50 text-indigo-950 font-extrabold text-center">Đai Chọn</th>
              <th class="p-3 text-center">Trạng Thái</th>
            </tr>
          </thead>
          <tbody id="rebarTableBody" class="divide-y divide-slate-100 font-mono text-[11px] bg-white text-slate-800">
          </tbody>
        </table>
      </div>

    </div>

    <!-- SUB-PANE 4: BẢN VẼ CỘT (GRID 18 CỘT × 4 TẦNG) -->
    <div id="subpane-etabs-column-cad" class="etabs-subpane hidden space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div class="flex items-center gap-2.5 flex-wrap">
          <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5 shrink-0">
            <i data-lucide="columns" class="w-4 h-4 text-amber-600"></i> Bảng Chi Tiết Tiết Diện Cột Toàn Nhà:
          </span>
          <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-extrabold font-mono">15 Cột × 4 Tầng</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">TCVN 5574:2018</span>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <button type="button" onclick="exportColumnSheetPdf()" class="py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Xuất PDF Bản Vẽ Cột
          </button>
          <button type="button" onclick="exportColumnSheetDxf()" class="py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Xuất DXF Bản Vẽ Cột
          </button>
          <button type="button" onclick="openColumnDrawingModal()" class="py-1.5 px-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center gap-1.5 border border-indigo-200 transition cursor-pointer">
            <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Phóng To Toàn Màn Hình
          </button>
        </div>
      </div>

      <!-- Canvas Container -->
      <div class="relative bg-slate-200/60 rounded-3xl border border-slate-300 overflow-hidden h-[680px]">
        <canvas id="tabColumnCadCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>

        <!-- HUD Controls -->
        <div class="absolute bottom-3 left-3 flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-300 shadow-md">
          <button type="button" onclick="zoomTabColumnCad(1.2)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>
          <button type="button" onclick="zoomTabColumnCad(0.833)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>
          <button type="button" onclick="resetTabColumnCadView()" class="px-2.5 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">100%</button>
          <button type="button" onclick="fitTabColumnCadView()" class="px-2.5 h-7 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">Vừa khung</button>
          <span class="text-[10px] text-slate-400 pl-1.5 border-l border-slate-200 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để di chuyển (Pan)</span>
        </div>

        <!-- Hover Tooltip Pill -->
        <div id="tabColumnCadHoverBadge" class="absolute top-3 right-3 flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-300 shadow-md text-xs font-semibold text-slate-700 pointer-events-none transition-all duration-150">
          <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          <span id="tabColumnCadHoverText">Rê chuột vào tiết diện cột để xem chi tiết</span>
        </div>
      </div>
    </div>

    <!-- SUB-PANE 5: BẢN VẼ ĐÀ KIỀNG (TRỤC A, B, C - T1 / MÓNG) -->
    <div id="subpane-etabs-tie-beam-cad" class="etabs-subpane hidden space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div class="flex items-center gap-2.5 flex-wrap">
          <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5 shrink-0">
            <i data-lucide="git-branch" class="w-4 h-4 text-emerald-600"></i> Bản Vẽ Chi Tiết Đà Kiềng (Trục A, B, C):
          </span>
          <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-extrabold font-mono">3 Trục • 12 Nhịp</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">TCVN 5574:2018</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-semibold" title="Bố trí thép xét phản lực đất đẩy lên từ dưới">Lưu ý: Phản Lực Đất Đẩy Lên</span>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <button type="button" onclick="exportTieBeamSheetPdf()" class="py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Xuất PDF Bản Vẽ Đà Kiềng
          </button>
          <button type="button" onclick="exportTieBeamSheetDxf()" class="py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <i data-lucide="download" class="w-3.5 h-3.5"></i> Xuất DXF Bản Vẽ Đà Kiềng
          </button>
          <button type="button" onclick="openTieBeamDrawingModal()" class="py-1.5 px-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center gap-1.5 border border-indigo-200 transition cursor-pointer">
            <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Phóng To Toàn Màn Hình
          </button>
        </div>
      </div>

      <!-- Canvas Container -->
      <div class="relative bg-slate-200/60 rounded-3xl border border-slate-300 overflow-hidden h-[680px]">
        <canvas id="tabTieBeamCadCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>

        <!-- HUD Controls -->
        <div class="absolute bottom-3 left-3 flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-300 shadow-md">
          <button type="button" onclick="zoomTabTieBeamCad(1.2)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>
          <button type="button" onclick="zoomTabTieBeamCad(0.833)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>
          <button type="button" onclick="resetTabTieBeamCadView()" class="px-2.5 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">100%</button>
          <button type="button" onclick="fitTabTieBeamCadView()" class="px-2.5 h-7 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">Vừa khung</button>
          <span class="text-[10px] text-slate-400 pl-1.5 border-l border-slate-200 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để di chuyển (Pan)</span>
        </div>

        <!-- Hover Tooltip Pill -->
        <div id="tabTieBeamCadHoverBadge" class="absolute top-3 right-3 flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-300 shadow-md text-xs font-semibold text-slate-700 pointer-events-none transition-all duration-150">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span id="tabTieBeamCadHoverText">Rê chuột vào dầm để xem chi tiết cốt thép đà kiềng</span>
        </div>
      </div>
    </div>


    <!-- SUB-PANE 6: BẢNG GHI CHÚ CHUNG KẾT CẤU (PLOT 1020) -->
    <div id="subpane-etabs-notes" class="etabs-subpane hidden space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
        <div class="flex items-center gap-2.5 flex-wrap">
          <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5 shrink-0">
            <i data-lucide="file-text" class="w-4 h-4 text-amber-600"></i> Bảng Ghi Chú Chung Kết Cấu:
          </span>
          <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-extrabold font-mono">TCVN 5574-2012</span>
          <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-bold flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> Plot_20261020_082443_WIN_1016103.pdf (144 KB)
          </span>
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">Bản vẽ CAD gốc Plot 1020</span>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <div class="inline-flex p-1 bg-white rounded-xl border border-slate-300 gap-1 text-xs shadow-2xs">
            <button type="button" id="gnTabBtn_hd" onclick="setNotesViewMode('hd', 'tab')" class="py-1.5 px-3 rounded-lg text-xs font-bold bg-amber-500 text-white shadow-xs transition cursor-pointer">🖼️ Bản Vẽ CAD HD</button>
            <button type="button" id="gnTabBtn_pdf" onclick="setNotesViewMode('pdf', 'tab')" class="py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition cursor-pointer">📄 PDF Gốc</button>
            <button type="button" id="gnTabBtn_text" onclick="setNotesViewMode('text', 'tab')" class="py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition cursor-pointer">📝 Bóc Tách Điều Khoản</button>
          </div>
          <button type="button" onclick="openGeneralNotesModal('hd')" class="py-1.5 px-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition active:scale-95 cursor-pointer" title="Phóng to toàn màn hình">
            <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Toàn màn hình
          </button>
          <button type="button" onclick="downloadGeneralNotesPdf()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="Tải PDF">
            <i data-lucide="download" class="w-3.5 h-3.5 text-indigo-600"></i> Tải PDF
          </button>
          <button type="button" onclick="printGeneralNotes()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="In">
            <i data-lucide="printer" class="w-3.5 h-3.5"></i> In
          </button>
          <button type="button" onclick="openGeneralNotesFolder()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="Mở thư mục plot 1020">
            <i data-lucide="folder" class="w-3.5 h-3.5 text-amber-600"></i> Thư mục
          </button>
        </div>
      </div>

      <div class="w-full bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-inner">
        <div id="gnTabPane_hd" class="relative w-full h-[720px] bg-slate-900">
          <canvas id="tabGnInteractiveCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>
          <div class="absolute bottom-4 left-4 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-700 shadow-xl text-white">
            <button type="button" onclick="zoomNotesCanvas(1.2, 'tabGnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>
            <button type="button" onclick="zoomNotesCanvas(0.833, 'tabGnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>
            <button type="button" onclick="resetNotesCanvas100('tabGnInteractiveCanvas')" class="px-2.5 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">100%</button>
            <button type="button" onclick="fitNotesCanvas('tabGnInteractiveCanvas')" class="px-3 h-8 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">Vừa khung</button>
            <span id="gnTabZoomBadge" class="text-xs font-mono font-bold text-amber-400 px-2 border-l border-slate-700">100%</span>
            <span class="text-[10px] text-slate-400 pl-2 border-l border-slate-700 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để Pan • Double click để vừa khung</span>
          </div>
        </div>

        <div id="gnTabPane_pdf" class="hidden w-full h-[720px] bg-slate-900">
          <iframe id="gnTabPdfIframe" src="about:blank" data-src="/static/general_notes_drawing.pdf#view=FitH" class="w-full h-full border-0"></iframe>
        </div>

        <div id="gnTabPane_text" class="hidden w-full h-[720px] bg-white p-6 overflow-y-auto space-y-6 text-slate-800">
          <div class="flex items-center justify-between border-b pb-4">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 flex items-center gap-2">
                📋 NỘI DUNG BẢN VẼ GHI CHÚ CHUNG KẾT CẤU
                <span class="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">TCVN 5574-2012</span>
              </h3>
              <p class="text-xs text-slate-500 mt-1">Nguồn: Documents/plot/1020/Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf</p>
            </div>
            <button type="button" onclick="copyNoteSection('gnTabClausesList')" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer">
              <i data-lucide="copy" class="w-3.5 h-3.5"></i> Sao chép toàn bộ
            </button>
          </div>

          <div class="bg-amber-50/70 border border-amber-200 rounded-2xl p-4">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-900 mb-3 flex items-center gap-2">
              <span>🛡️</span> II. BẢNG CHIỀU DÀY LỚP BÊ TÔNG BẢO VỆ CỐT THÉP (Cmin mm)
            </h4>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Móng Đáy / Bên</div>
                <div class="text-lg font-black text-amber-700 mt-1">70 / 40 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Tiếp xúc đất tự nhiên</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Cột Khung</div>
                <div class="text-lg font-black text-indigo-700 mt-1">25 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Thép đai min 15mm</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Dầm Khung</div>
                <div class="text-lg font-black text-blue-700 mt-1">25 - 30 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Dưới 25mm, Trên 30mm</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Sàn BTCT</div>
                <div class="text-lg font-black text-emerald-700 mt-1">15 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Sàn mái min 20mm</div>
              </div>
            </div>
          </div>

          <div class="bg-blue-50/70 border border-blue-200 rounded-2xl p-4">
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-3 flex items-center gap-2">
              <span>🔩</span> QUY CÁCH CỐT THÉP & BÊ TÔNG
            </h4>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div class="bg-white p-3 rounded-xl border border-blue-200 shadow-2xs">
                <div class="font-bold text-slate-800">Thép Gai D &gt; 10 mm</div>
                <div class="text-blue-700 font-mono font-bold mt-1">Ra = Ra' = 3650 kg/cm²</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Nhóm CB400-V / CII / CIII</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-blue-200 shadow-2xs">
                <div class="font-bold text-slate-800">Thép Tròn D &le; 10 mm</div>
                <div class="text-blue-700 font-mono font-bold mt-1">Ra = Ra' = 2300 kg/cm²</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Nhóm CB240-T / AI / CT3</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-blue-200 shadow-2xs">
                <div class="font-bold text-slate-800">Bê Tông Kết Cấu</div>
                <div class="text-emerald-700 font-mono font-bold mt-1">Mác #300 (B20 / B22.5)</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Rn = 130 kg/cm², Rk = 10 kg/cm²</div>
              </div>
            </div>
          </div>

          <div id="gnTabClausesList" class="space-y-2.5 text-xs text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200">
            <div class="font-bold text-slate-900 border-b pb-1 text-sm">I. 24 ĐIỀU QUY ĐỊNH KẾT CẤU CHÍNH</div>
            <p><strong>01.</strong> Việc thiết kế dựa trên TCVN hiện hành.</p>
            <p><strong>02.</strong> Những bản vẽ kết cấu cần xem đồng thời với bản vẽ kiến trúc.</p>
            <p><strong>03.</strong> Nếu có bất kỳ thông tin nào không hợp lý, đơn vị thi công phải báo cho bên tư vấn thiết kế để cùng giải quyết.</p>
            <p><strong>04.</strong> Cốt hoàn thiện được xét theo bản vẽ kiến trúc.</p>
            <p><strong>05.</strong> Tất cả các đơn vị ghi trong bản vẽ là mm, nếu như không có ghi chú nào khác.</p>
            <p><strong>06.</strong> Các sai số về kích thước, độ lệch, độ võng... cho phép của kết cấu tuân theo TCVN 4453-1995.</p>
            <p><strong>07.</strong> Áp lực gió tiêu chuẩn: <code class="px-1.5 py-0.5 bg-slate-200 rounded font-mono">Wo = 95 kg/m²</code> (vùng II-B).</p>
            <p><strong>08.</strong> Chất lượng bê tông khi thi công cần được kiểm tra đúng quy phạm.</p>
            <p><strong>09.</strong> Cát dùng làm bê tông phải thỏa mãn các yêu cầu TCVN hiện hành.</p>
            <p><strong>10.</strong> Nước dùng để trộn và dưỡng hộ bê tông phải đảm bảo yêu cầu TCVN 4506-87.</p>
            <p><strong>11.</strong> Không sử dụng các loại phụ gia không rõ nguồn gốc trong bê tông.</p>
            <p><strong>12.</strong> Thi công móng, cột, dầm, sàn phải dựa theo TCVN hiện hành.</p>
            <p><strong>13.</strong> Mạch ngừng thi công phải tuân theo TCVN hiện hành.</p>
            <p><strong>14.</strong> Yêu cầu chống thấm cột, dầm, sàn dưới cao trình &plusmn;0.00.</p>
            <p><strong>15.</strong> Dọc theo chiều cao cột có tường xây đặt thép râu neo vào tường &phi;6a500 dài 1000mm.</p>
            <p><strong>16.</strong> Cốt thép và bê tông: &phi; &le; 10 (Ra = Ra' = 2300 kg/cm²), &phi; &ge; 12 (Ra = Ra' = 3650 kg/cm²); Bê tông Mác #300.</p>
            <p><strong>17.</strong> Khi thi công cột, đà sàn kết hợp điện, nước, điện lạnh phải đặt các ống luồn trước khi đổ bê tông.</p>
            <p><strong>18.</strong> Có thể nối thép cột tại bất kỳ vị trí nào nhưng <strong>không nối quá 50%</strong> tiết diện trên cùng một mặt cắt.</p>
            <p><strong>19.</strong> Trường hợp đặt các đường ống ẩn trong kết cấu thì phải có thiết kế gia cố riêng.</p>
            <p><strong>20.</strong> Số lượng ống luồn lắp đặt ẩn trong kết cấu phải &lt; 3 ống song song, nếu &gt; 3 phải đặt lưới thép gia cường.</p>
            <p><strong>21.</strong> Thống nhất cao độ kết cấu thấp hơn cao độ hoàn thiện là 50mm.</p>
            <p><strong>22.</strong> Quy định neo thép, uốn cốt thép dầm: đoạn neo dầm vào cột tối thiểu 35d; dầm phụ vào dầm chính neo tối thiểu 30d.</p>
            <p><strong>23.</strong> Quy định bổ trụ và giằng tường: tường dài &gt; 4m bố trí bổ trụ BTCT 200x200; tường cao &gt; 3.6m bố trí giằng BTCT 200x100.</p>
            <p><strong>24.</strong> Tất cả tường xây liên kết với bê tông đều phải được đóng lưới mắt cáo chống nứt trước khi trát.</p>
          </div>
        </div>
      </div>
    </div>

  </main>

  <!-- ==================================================================== -->
  <!-- MODAL: CHI TIẾT BẢN VẼ DẦM, MẶT CẮT NGANG/DỌC & DẦM LIÊN TỤC         -->
  <!-- ==================================================================== -->
          <div id="beamRebarModal" class="fixed inset-0 z-50 bg-slate-900/75 backdrop-blur-sm hidden flex items-center justify-center p-2 sm:p-4">
          <div class="relative bg-white text-slate-800 w-[90vw] max-w-[90vw] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150 max-h-[94vh]">
            
            <!-- Toast notification pill inside modal -->
            <div id="brmToastNotification" class="absolute top-16 left-1/2 -translate-x-1/2 z-50 pointer-events-none transition-all duration-300 opacity-0 -translate-y-2 flex items-center gap-2 px-4 py-2 rounded-2xl shadow-xl font-bold text-xs"></div>

            <!-- Modal Header -->
            <div class="p-3.5 sm:p-4 bg-slate-50 text-slate-900 flex flex-wrap items-center justify-between border-b border-slate-200 gap-3">
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-200">
                  <i data-lucide="box" class="w-5 h-5"></i>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2 flex-wrap">
                    Dầm <span id="brmBeamName" class="font-mono text-indigo-600 font-extrabold text-base">B1</span>
                    <span id="brmStory" class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">T2</span>
                    <span id="brmSection" class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono">200x400</span>
                    <span id="brmLength" class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">5.90 m</span>
                    <span id="brmGridAxis" class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-bold flex items-center gap-1">
                      <i data-lucide="git-commit" class="w-3 h-3 text-amber-700"></i> <span id="brmGridAxisText">Trục A</span>
                    </span>
                  </h3>
                  <p class="text-[11px] text-slate-500">Mặt cắt kỹ thuật TCVN 5574-2012 & Chuỗi dầm liên tục đa nhịp</p>
                </div>
              </div>

              <div class="flex items-center gap-2 flex-wrap">
                <!-- Cảnh Báo An Toàn Cốt Thép Toàn Dự Án -->
                <div class="relative flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-2xl border border-slate-300 shadow-2xs select-none">
                  <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mr-0.5 whitespace-nowrap">Hồ sơ dầm:</span>
                  <div id="brmHeaderPassBadge" class="px-2 py-0.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-300 text-xs font-bold flex items-center gap-1 shadow-2xs" title="Số lượng dầm dài bố trí cốt thép ĐẠT TCVN">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Đạt:</span>
                    <strong id="brmHeaderPassCount" class="font-extrabold text-emerald-950 font-mono">--/--</strong>
                  </div>
                  
                  <div class="relative flex items-center">
                    <button type="button" id="brmHeaderFailBadge" onclick="jumpToNextFailingBeam()" class="px-2.5 py-0.5 rounded-xl bg-rose-50 text-rose-800 border border-rose-300 text-xs font-bold flex items-center gap-1 shadow-2xs transition active:scale-95 cursor-pointer" title="Bấm để chuyển nhanh tới dầm không đạt tiếp theo">
                      <span class="w-2 h-2 rounded-full bg-rose-500"></span>
                      <span>Không đạt:</span>
                      <strong id="brmHeaderFailCount" class="font-extrabold text-rose-950 font-mono">--/--</strong>
                      <span id="brmHeaderFailJumpHint" class="hidden items-center gap-0.5 ml-1 px-1.5 py-0.2 rounded-md bg-rose-200 text-rose-950 text-[10px] font-extrabold">
                        <span>Chuyển tới</span>
                        <svg class="w-3 h-3 text-rose-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                      </span>
                    </button>
                    
                    <button type="button" id="btnToggleFailingBeamsMenu" onclick="toggleFailingBeamsMenu(event)" class="hidden ml-1 p-1 rounded-lg bg-rose-100 hover:bg-rose-200 text-rose-800 border border-rose-300 transition cursor-pointer" title="Xem danh sách dầm chưa đạt">
                      <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="6 9 12 15 18 9"/></svg>
                    </button>

                    <!-- Popover dropdown danh sách các dầm chưa đạt -->
                    <div id="brmFailingBeamsDropdown" class="hidden absolute top-full right-0 mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-rose-300 p-2.5 z-50 text-xs animate-in fade-in zoom-in-95 duration-100">
                      <div class="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-100 font-bold text-rose-900">
                        <span class="flex items-center gap-1.5">
                          <svg class="w-4 h-4 text-rose-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                          <span>Dầm Chưa Đạt Chuẩn (<span id="brmFailingMenuCount">0</span>)</span>
                        </span>
                        <button type="button" onclick="closeFailingBeamsMenu()" class="text-slate-400 hover:text-slate-700 font-bold px-1.5 py-0.5 rounded cursor-pointer">✕</button>
                      </div>
                      <div id="brmFailingBeamsList" class="max-h-60 overflow-y-auto space-y-1 divide-y divide-slate-100 pr-1"></div>
                      <div class="pt-2 mt-1.5 border-t border-slate-100">
                        <button type="button" onclick="jumpToNextFailingBeam()" class="w-full py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm transition cursor-pointer">
                          <span>Chuyển tới dầm tiếp theo</span>
                          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Trạng Thái Dầm Hiện Tại Đang Xem -->
                <div id="brmHeaderCurrentBeamBadge" class="px-2.5 py-1 rounded-2xl text-xs font-extrabold flex items-center gap-1 shadow-2xs">
                  <!-- Populated dynamically by JS -->
                </div>

                <!-- Chế Độ Dầm Dài Liên Tục (Đã bỏ 3D dầm dài) -->
                <div class="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 border border-indigo-200 text-indigo-900 rounded-2xl text-xs font-bold shadow-2xs select-none">
                  <i data-lucide="layout" class="w-3.5 h-3.5 text-indigo-600"></i>
                  <span>Dầm Dài Liên Tục</span>
                  <span id="brmChainCountBadge" class="px-1.5 py-0.2 bg-indigo-200/90 text-indigo-950 rounded-full text-[10px] font-extrabold">4 nhịp</span>
                </div>

                <!-- Nút Mở Bản Vẽ Cột (15x4) -->
                <button type="button" onclick="openColumnDrawingModal()" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 rounded-2xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-2xs" title="Xem Bản Vẽ Tiết Diện Cột toàn nhà (Grid 15 Cột × 4 Tầng)">
                  <svg class="w-3.5 h-3.5 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 22h16"/><path d="M4 2h16"/><path d="M6 2v20"/><path d="M18 2v20"/><path d="M10 2v20"/><path d="M14 2v20"/></svg>
                  <span>Bản Vẽ Cột (15×4)</span>
                </button>

                <!-- Nút Mở Bản Vẽ Đà Kiềng (Trục A, B, C) -->
                <button type="button" onclick="openTieBeamDrawingModal()" class="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-900 rounded-2xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-2xs" title="Xem Bản Vẽ Chi Tiết Đà Kiềng (Trục A, B, C - Tầng 1 / Móng)">
                  <svg class="w-3.5 h-3.5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 3v12"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
                  <span>Đà Kiềng (Trục A,B,C)</span>
                </button>

                <button onclick="closeBeamRebarModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng">
                  <i data-lucide="x" class="w-5 h-5"></i>
                </button>
              </div>
            </div>

            <!-- Modal Body (No outer vertical scrollbar) -->
            <div class="p-3 sm:p-3.5 space-y-2.5 overflow-hidden flex-1 flex flex-col bg-slate-50/50 min-h-0">

              <!-- Continuous Chain Breadcrumbs Bar -->
              <div class="p-2 bg-white rounded-2xl border border-slate-200 flex items-center justify-between gap-2 shadow-xs text-xs shrink-0">
                <div class="flex items-center gap-1.5 overflow-x-auto py-0.5 flex-1" id="brmChainBreadcrumbs">
                  <!-- Rendered by JS -->
                </div>
                <span class="text-[10px] text-slate-400 font-medium whitespace-nowrap hidden sm:inline">Click để chuyển nhịp</span>
              </div>

              <!-- 2-COLUMN LAYOUT: CỘT 1 (BẢN VẼ CAD 4/5) & CỘT 2 (THÔNG SỐ & THÉP 1/5) -->
              <div class="grid grid-cols-1 lg:grid-cols-5 gap-3 items-stretch flex-1 min-h-0">

                <!-- CỘT 1 (4/5 BỀ RỘNG): CANVAS CAD VỚI ZOOM / PAN HUD -->
                <div class="lg:col-span-4 relative bg-white rounded-2xl border border-slate-300 shadow-xs overflow-hidden flex flex-col h-[580px] lg:h-full min-h-[500px]">
                  <canvas id="brmDrawingCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>

                  <!-- Top-Right Legend for 2D CAD -->
                  <div id="brmCadLegendBadge" class="absolute top-2.5 right-2.5 flex items-center gap-1.5 bg-white/95 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-slate-200 text-[10px] text-slate-600 font-medium shadow-xs pointer-events-none">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span id="brmCanvasLegend">Mặt cắt dọc chuỗi dầm liên tục đa nhịp</span>
                  </div>

                  <!-- Bottom-Left Zoom & Pan HUD Controls (for 2D CAD) -->
                  <div id="brmCadHudControls" class="absolute bottom-2.5 left-2.5 flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-200 shadow-md">
                    <button type="button" onclick="zoomBeamCad(1.2)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to (Zoom In)">+</button>
                    <button type="button" onclick="zoomBeamCad(0.833)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ (Zoom Out)">-</button>
                    <button type="button" onclick="resetBeamCadView()" class="px-2.5 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer" title="Vừa khung hình (Fit View)">Vừa khung</button>
                    <button type="button" onclick="focusActiveSpanCad()" class="px-2.5 h-7 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer" title="Xem nhịp đang chọn (Focus Selected Span 1:1)">Xem nhịp chọn</button>
                    <span class="text-[10px] text-slate-400 pl-1.5 border-l border-slate-200 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để pan</span>
                  </div>
                </div>

                <!-- CỘT 2 (1/3 BỀ RỘNG): BẢNG PROPERTIES & PANEL LAYOUT (MỖI PANEL CÓ SCROLLBAR RIÊNG) -->
                <div class="lg:col-span-1 flex flex-col gap-2.5 h-[580px] lg:h-full min-h-[500px] overflow-hidden pr-0.5">

                  <div class="bg-white border border-slate-300 rounded-xl shadow-xs overflow-hidden text-xs select-none flex flex-col basis-[56%] min-h-0 shrink-0">
                    <!-- Visual Studio Style Window Titlebar (Fixed) -->
                    <div class="bg-slate-100/90 border-b border-slate-200 px-3 py-1.5 flex items-center justify-between shrink-0">
                      <div class="flex items-center gap-1.5 font-bold text-slate-800 text-[11px]">
                        <svg class="w-3.5 h-3.5 text-indigo-600 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                          <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
                        </svg>
                        <span>Properties</span>
                        <span class="text-slate-400 font-normal">|</span>
                        <span id="brmVsPropTitle" class="text-indigo-700 font-mono font-bold truncate">Dầm</span>
                      </div>
                      <div class="flex items-center gap-1 text-[10px] text-slate-500 font-medium shrink-0">
                        <span class="px-1.5 py-0.2 rounded bg-slate-200/80 text-slate-600 font-mono font-semibold">TCVN 5574</span>
                      </div>
                    </div>

                    <!-- Scrollable Body for Properties -->
                    <div class="overflow-y-auto flex-1 min-h-0 divide-y divide-slate-100 pr-0.5">
                      <!-- Category 1: NỘI LỰC & AS YÊU CẦU -->
                      <div>
                        <div class="bg-slate-50 border-b border-slate-200 px-2.5 py-1 flex items-center justify-between text-[10px] font-bold text-slate-600 uppercase tracking-wider whitespace-nowrap shrink-0">
                        <span class="flex items-center gap-1 whitespace-nowrap shrink-0">
                          <span class="text-[8px] text-slate-500">▼</span> Nội Lực & As Yêu Cầu
                        </span>
                        <span class="text-[9px] text-slate-400 lowercase font-normal font-mono whitespace-nowrap shrink-0">kNm • cm²</span>
                      </div>
                      <div class="divide-y divide-slate-100 text-[11px]">
                        <!-- Gối Trái -->
                        <div class="grid grid-cols-12 px-2.5 py-1.5 hover:bg-indigo-50/30 transition items-center">
                          <div class="col-span-5 text-slate-600 font-medium whitespace-nowrap shrink-0 flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
                            <span class="whitespace-nowrap shrink-0">Gối Trái (M-)</span>
                          </div>
                          <div class="col-span-7 flex items-center justify-between font-mono whitespace-nowrap shrink-0">
                            <span id="brmMLeft" class="font-bold text-rose-700 whitespace-nowrap shrink-0">-28.5 kNm</span>
                            <span class="text-slate-500 text-[10px] whitespace-nowrap shrink-0">As: <strong id="brmAsLeftReq" class="text-rose-900 font-bold whitespace-nowrap shrink-0">2.55 cm²</strong></span>
                          </div>
                        </div>
                        <!-- Nhịp Giữa -->
                        <div class="grid grid-cols-12 px-2.5 py-1.5 hover:bg-indigo-50/30 transition items-center">
                          <div class="col-span-5 text-slate-600 font-medium whitespace-nowrap shrink-0 flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                            <span class="whitespace-nowrap shrink-0">Nhịp Giữa (M+)</span>
                          </div>
                          <div class="col-span-7 flex items-center justify-between font-mono whitespace-nowrap shrink-0">
                            <span id="brmMMid" class="font-bold text-emerald-700 whitespace-nowrap shrink-0">+24.4 kNm</span>
                            <span class="text-slate-500 text-[10px] whitespace-nowrap shrink-0">As: <strong id="brmAsMidReq" class="text-emerald-900 font-bold whitespace-nowrap shrink-0">2.18 cm²</strong></span>
                          </div>
                        </div>
                        <!-- Gối Phải -->
                        <div class="grid grid-cols-12 px-2.5 py-1 hover:bg-indigo-50/30 transition items-center">
                          <div class="col-span-5 text-slate-600 font-medium whitespace-nowrap shrink-0 flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
                            <span class="whitespace-nowrap shrink-0">Gối Phải (M-)</span>
                          </div>
                          <div class="col-span-7 flex items-center justify-between font-mono whitespace-nowrap shrink-0">
                            <span id="brmMRight" class="font-bold text-rose-700 whitespace-nowrap shrink-0">-30.2 kNm</span>
                            <span class="text-slate-500 text-[10px] whitespace-nowrap shrink-0">As: <strong id="brmAsRightReq" class="text-rose-900 font-bold whitespace-nowrap shrink-0">2.70 cm²</strong></span>
                          </div>
                        </div>
                        <!-- Lực Cắt -->
                        <div class="grid grid-cols-12 px-2.5 py-1 hover:bg-indigo-50/30 transition items-center">
                          <div class="col-span-5 text-slate-600 font-medium whitespace-nowrap shrink-0 flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0"></span>
                            <span class="whitespace-nowrap shrink-0">Cắt V (Đai Y/c)</span>
                          </div>
                          <div class="col-span-7 flex items-center justify-end font-mono whitespace-nowrap shrink-0">
                            <span class="text-slate-500 text-[10px] whitespace-nowrap shrink-0">As,w: <strong id="brmShearReq" class="text-indigo-800 font-bold whitespace-nowrap shrink-0">5.75 cm²/m</strong></span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Category 2: BỐ TRÍ CỐT THÉP -->
                    <div class="border-t border-slate-200">
                      <div class="bg-slate-50 border-b border-slate-200 px-2.5 py-1 flex items-center justify-between text-[10px] font-bold text-slate-600 uppercase tracking-wider whitespace-nowrap shrink-0">
                        <span class="flex items-center gap-1 whitespace-nowrap shrink-0">
                          <span class="text-[8px] text-slate-500">▼</span> Thiết Kế Cốt Thép Dầm
                        </span>
                        <span class="text-[9px] text-slate-400 lowercase font-normal whitespace-nowrap shrink-0">quy cách • an toàn</span>
                      </div>
                      <div class="divide-y divide-slate-100">
                        <!-- Thép Chủ Trên (Suốt Dầm) -->
                        <div class="px-2.5 py-1 hover:bg-blue-50/30 transition bg-blue-50/20">
                          <div class="text-slate-800 font-bold text-[11px] flex items-center justify-between mb-0.5 whitespace-nowrap shrink-0">
                            <div class="flex items-center gap-1.5 min-w-0">
                              <span class="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span>
                              <span class="whitespace-nowrap shrink-0" title="Thép Chủ Trên (Chạy suốt liên tục toàn bộ dầm)">Thép Chủ Trên (Suốt Dầm)</span>
                            </div>
                            <span class="text-[9px] text-blue-700 font-semibold uppercase whitespace-nowrap shrink-0">Lưng dầm</span>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelMainTop" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-blue-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-blue-900 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap"></select>
                            <span id="brmStatusMainTop" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-blue-100 text-blue-800 border border-blue-200 whitespace-nowrap shrink-0">Suốt dầm</span>
                          </div>
                        </div>

                        <!-- Thép Chủ Dưới (Suốt Dầm) -->
                        <div class="px-2.5 py-1 hover:bg-emerald-50/30 transition bg-emerald-50/20">
                          <div class="text-slate-800 font-bold text-[11px] flex items-center justify-between mb-0.5 whitespace-nowrap shrink-0">
                            <div class="flex items-center gap-1.5 min-w-0">
                              <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0"></span>
                              <span class="whitespace-nowrap shrink-0" title="Thép Chủ Dưới (Chạy suốt liên tục toàn bộ dầm)">Thép Chủ Dưới (Suốt Dầm)</span>
                            </div>
                            <span class="text-[9px] text-emerald-700 font-semibold uppercase whitespace-nowrap shrink-0">Bụng dầm</span>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelMainBot" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-emerald-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-emerald-900 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap"></select>
                            <span id="brmStatusMainBot" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 whitespace-nowrap shrink-0">Suốt dầm</span>
                          </div>
                        </div>

                        <!-- Thép Tăng Cường Gối Trái -->
                        <div class="px-2.5 py-1 hover:bg-indigo-50/20 transition">
                          <div class="text-slate-700 font-semibold text-[11px] flex items-center justify-between mb-0.5 whitespace-nowrap shrink-0">
                            <div class="flex items-center gap-1.5 min-w-0">
                              <span class="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
                              <span class="whitespace-nowrap shrink-0" title="Thép Tăng Cường Gối Trái (M-)">Tăng Cường Gối Trái (M-)</span>
                            </div>
                            <span class="text-[9px] text-slate-400 font-normal whitespace-nowrap shrink-0">Thêm vào Chủ Trên</span>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelLeft" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-slate-800 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap"></select>
                            <span id="brmStatusLeft" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold whitespace-nowrap shrink-0 cursor-pointer transition" title="Bấm để chuyển tới vị trí dầm">Đạt</span>
                          </div>
                        </div>

                        <!-- Thép Tăng Cường Bụng Nhịp -->
                        <div class="px-2.5 py-1 hover:bg-indigo-50/20 transition">
                          <div class="text-slate-700 font-semibold text-[11px] flex items-center justify-between mb-0.5 whitespace-nowrap shrink-0">
                            <div class="flex items-center gap-1.5 min-w-0">
                              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                              <span class="whitespace-nowrap shrink-0" title="Thép Tăng Cường Bụng Nhịp (M+)">Tăng Cường Bụng (M+)</span>
                            </div>
                            <span class="text-[9px] text-slate-400 font-normal whitespace-nowrap shrink-0">Thêm vào Chủ Dưới</span>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelMid" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-slate-800 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap"></select>
                            <span id="brmStatusMid" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold whitespace-nowrap shrink-0 cursor-pointer transition" title="Bấm để chuyển tới vị trí dầm">Đạt</span>
                          </div>
                        </div>

                        <!-- Thép Treo / Support / Giá -->
                        <div class="px-2.5 py-1 hover:bg-indigo-50/20 transition">
                          <div class="text-slate-700 font-semibold text-[11px] flex items-center gap-1.5 mb-0.5 whitespace-nowrap shrink-0">
                            <span class="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></span>
                            <span class="whitespace-nowrap shrink-0" title="Treo Đai / Giá">Treo Đai / Giá</span>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelHanger" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-slate-800 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap">
                              <option value="2D14 (3.08cm²)">2Φ14 (3.08 cm²)</option>
                              <option value="2D16 (4.02cm²)" selected>2Φ16 (4.02 cm²)</option>
                              <option value="3D14 (4.62cm²)">3Φ14 (4.62 cm²)</option>
                              <option value="3D16 (6.03cm²)">3Φ16 (6.03 cm²)</option>
                              <option value="2D18 (5.09cm²)">2Φ18 (5.09 cm²)</option>
                              <option value="3D18 (7.63cm²)">3Φ18 (7.63 cm²)</option>
                              <option value="2D20 (6.28cm²)">2Φ20 (6.28 cm²)</option>
                              <option value="3D20 (9.42cm²)">3Φ20 (9.42 cm²)</option>
                            </select>
                            <span id="brmStatusHanger" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 whitespace-nowrap shrink-0">Cấu tạo</span>
                          </div>
                        </div>

                        <!-- Thép Tăng Cường Gối Phải -->
                        <div class="px-2.5 py-1 hover:bg-indigo-50/20 transition">
                          <div class="text-slate-700 font-semibold text-[11px] flex items-center justify-between mb-0.5 whitespace-nowrap shrink-0">
                            <div class="flex items-center gap-1.5 min-w-0">
                              <span class="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
                              <span class="whitespace-nowrap shrink-0" title="Thép Tăng Cường Gối Phải (M-)">Tăng Cường Gối Phải (M-)</span>
                            </div>
                            <span class="text-[9px] text-slate-400 font-normal whitespace-nowrap shrink-0">Thêm vào Chủ Trên</span>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelRight" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-slate-800 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap"></select>
                            <span id="brmStatusRight" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold whitespace-nowrap shrink-0 cursor-pointer transition" title="Bấm để chuyển tới vị trí dầm">Đạt</span>
                          </div>
                        </div>

                        <!-- Cốt Đai Chống Cắt -->
                        <div class="px-2.5 py-1 hover:bg-indigo-50/20 transition">
                          <div class="text-slate-700 font-semibold text-[11px] flex items-center justify-between mb-0.5 whitespace-nowrap shrink-0">
                            <div class="flex items-center gap-1.5 min-w-0 whitespace-nowrap shrink-0">
                              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0"></span>
                              <span class="whitespace-nowrap shrink-0" title="Đai Chống Cắt">Đai Chống Cắt</span>
                            </div>
                            <!-- Radio chọn Phi 6 hoặc Phi 8, mặc định Phi 6 -->
                            <div class="flex items-center gap-2.5 text-[10px] font-bold whitespace-nowrap shrink-0">
                              <label class="flex items-center gap-1 cursor-pointer text-slate-700 hover:text-indigo-600 whitespace-nowrap shrink-0">
                                <input type="radio" name="brmStirrupDiam" value="6" checked onchange="onStirrupDiamRadioChange(6)" class="text-indigo-600 focus:ring-0 cursor-pointer shrink-0">
                                <span class="whitespace-nowrap shrink-0">Φ6</span>
                              </label>
                              <label class="flex items-center gap-1 cursor-pointer text-slate-700 hover:text-indigo-600 whitespace-nowrap shrink-0">
                                <input type="radio" name="brmStirrupDiam" value="8" onchange="onStirrupDiamRadioChange(8)" class="text-indigo-600 focus:ring-0 cursor-pointer shrink-0">
                                <span class="whitespace-nowrap shrink-0">Φ8</span>
                              </label>
                            </div>
                          </div>
                          <div class="flex items-center gap-1.5 min-w-0">
                            <select id="brmSelStirrup" onchange="onRebarSelectChange()" class="flex-1 min-w-0 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-slate-800 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-2xs whitespace-nowrap"></select>
                            <span class="text-[9px] text-slate-500 font-mono whitespace-nowrap shrink-0">Đai gối / đai nhịp</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  </div>

                  <!-- PANEL LAYOUT: BỐ CỤC BẢN VẼ & KÍCH THƯỚC (DỜI TỪ TOOLBAR NỔI) -->
                  <div id="brmLayoutSheetBar" class="bg-white border border-slate-300 rounded-xl shadow-xs overflow-hidden text-xs select-none flex flex-col flex-1 min-h-0">
                    <!-- Titlebar -->
                    <div class="bg-slate-100/90 border-b border-slate-200 px-3 py-1.5 flex items-center justify-between shrink-0 whitespace-nowrap">
                      <div class="flex items-center gap-1.5 font-bold text-slate-800 text-[11px] whitespace-nowrap shrink-0">
                        <svg class="w-3.5 h-3.5 text-indigo-600 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                          <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
                        </svg>
                        <span class="whitespace-nowrap shrink-0">Panel Layout</span>
                        <span class="text-slate-400 font-normal shrink-0">|</span>
                        <span class="text-indigo-700 font-bold whitespace-nowrap shrink-0">Bố Cục & Dim</span>
                      </div>
                      <span class="text-[9px] px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 whitespace-nowrap shrink-0">CAD Config</span>
                    </div>

                    <div class="overflow-y-auto flex-1 min-h-0 p-1.5 space-y-1.5 text-[11px] pr-0.5">
                      <!-- Nhóm 1: Tỉ Lệ & Zoom -->
                      <div class="bg-slate-50/80 p-1.5 rounded-lg border border-slate-200 space-y-1">
                        <div class="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between whitespace-nowrap shrink-0">
                          <span class="whitespace-nowrap shrink-0">📐 Khung Bản Vẽ & Tỉ Lệ</span>
                          <span class="text-slate-400 font-normal whitespace-nowrap shrink-0">Khổ A3</span>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                          <div class="min-w-0">
                            <label class="block text-slate-600 text-[10px] font-semibold mb-0.5 whitespace-nowrap shrink-0">Tỉ lệ in:</label>
                            <select id="brmSelScale" class="w-full px-2 py-1 rounded border border-slate-300 font-mono font-bold text-xs bg-white text-indigo-700 focus:border-indigo-500 focus:outline-none cursor-pointer whitespace-nowrap shrink-0">
                              <option value="1">1/1</option>
                              <option value="2">1/2</option>
                              <option value="5">1/5</option>
                              <option value="10">1/10</option>
                              <option value="20">1/20</option>
                              <option value="25">1/25</option>
                              <option value="50" selected>1/50</option>
                              <option value="100">1/100</option>
                            </select>
                          </div>
                          <div class="min-w-0">
                            <label class="block text-slate-600 text-[10px] font-semibold mb-0.5 whitespace-nowrap shrink-0">Zoom MC / Dầm:</label>
                            <select id="brmSelCsZoom" class="w-full px-2 py-1 rounded border border-slate-300 font-mono font-bold text-xs bg-white text-indigo-700 focus:border-indigo-500 focus:outline-none cursor-pointer whitespace-nowrap shrink-0">
                              <option value="1">1:1</option>
                              <option value="1.5">1.5:1</option>
                              <option value="2" selected>2:1</option>
                              <option value="2.5">2.5:1</option>
                              <option value="3">3:1</option>
                              <option value="3.5">3.5:1</option>
                              <option value="4">4:1</option>
                              <option value="5">5:1</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      <!-- Nhóm 2: Căn lề & Khoảng cách mặt cắt -->
                      <div class="bg-slate-50/80 p-1.5 rounded-lg border border-slate-200 space-y-1">
                        <div class="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between whitespace-nowrap shrink-0">
                          <span class="whitespace-nowrap shrink-0">↔ Căn Lề & Khoảng Cách MC</span>
                          <span class="text-slate-400 font-normal whitespace-nowrap shrink-0">mm</span>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0">Margin X:</span>
                            <input id="brmInputMarginX" type="number" step="50" min="-2000" max="5000" value="500" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Căn lề X dầm trong khung (mm)" />
                          </div>
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0">Margin Y:</span>
                            <input id="brmInputMarginY" type="number" step="50" min="-2000" max="5000" value="400" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Căn lề Y dầm trong khung (mm)" />
                          </div>
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0">Gap X (MC):</span>
                            <input id="brmInputGapX" type="number" step="50" min="-2000" max="5000" value="-100" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Khoảng cách ngang giữa các mặt cắt (mm)" />
                          </div>
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0">Gap Y (MC):</span>
                            <input id="brmInputGapY" type="number" step="50" min="-2000" max="5000" value="-100" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Khoảng cách đứng giữa các hàng mặt cắt (mm)" />
                          </div>
                        </div>
                      </div>

                      <!-- Nhóm 3: Quy cách Leader (Dài leader & Đến đích) -->
                      <div class="bg-slate-50/80 p-1.5 rounded-lg border border-slate-200 space-y-1">
                        <div class="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between whitespace-nowrap shrink-0">
                          <span class="whitespace-nowrap shrink-0">📍 Quy Cách Leader Chỉ Thép</span>
                          <span class="text-slate-400 font-normal whitespace-nowrap shrink-0">mm</span>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0" title="Chiều dài thanh nằm ngang của leader">Dài leader:</span>
                            <input id="brmInputLeaderLen" type="number" step="10" min="50" max="600" value="160" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Chiều dài thanh nằm ngang của leader (mm)" />
                          </div>
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0" title="Khoảng cách xiên từ leader đến tâm thanh thép">Đến đích:</span>
                            <input id="brmInputLeaderDist" type="number" step="10" min="20" max="400" value="60" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Khoảng cách leader đến điểm destination (mm)" />
                          </div>
                        </div>
                      </div>

                      <!-- Nhóm 4: Khoảng cách Dim & Dim Display Scale -->
                      <div class="bg-slate-50/80 p-1.5 rounded-lg border border-slate-200 space-y-1">
                        <div class="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between whitespace-nowrap shrink-0">
                          <span class="whitespace-nowrap shrink-0">📏 Khoảng Cách & Tỉ Lệ Dim</span>
                          <span class="text-slate-400 font-normal whitespace-nowrap shrink-0">Dọc & MC</span>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0" title="Khoảng cách từ dầm đến đường kích thước đầu tiên">Spacing Dim 1:</span>
                            <input id="brmInputDimSpace1" type="number" step="25" min="100" max="1500" value="350" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Khoảng cách dầm đến đường dim đầu tiên (mm)" />
                          </div>
                          <div class="flex items-center justify-between min-w-0">
                            <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0" title="Khoảng cách giữa các đường dim liên tiếp">Spacing Dim 2:</span>
                            <input id="brmInputDimSpace2" type="number" step="25" min="100" max="1500" value="260" class="w-16 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-center bg-white text-slate-800 focus:border-indigo-500 focus:outline-none whitespace-nowrap shrink-0" title="Khoảng cách giữa các đường dim liên tiếp (mm)" />
                          </div>
                        </div>
                        <div class="pt-1 flex items-center justify-between border-t border-slate-200 min-w-0">
                          <span class="text-slate-600 text-[10px] font-medium whitespace-nowrap shrink-0" title="Hệ số phóng to/thu nhỏ cỡ chữ và gạch chéo kích thước">Dim Display Scale:</span>
                          <select id="brmSelDimScale" class="w-24 px-1.5 py-0.5 rounded border border-slate-300 font-mono font-bold text-[11px] bg-white text-indigo-700 focus:border-indigo-500 focus:outline-none cursor-pointer whitespace-nowrap shrink-0">
                            <option value="0.75">0.75x</option>
                            <option value="0.9">0.90x</option>
                            <option value="1.0" selected>1.00x</option>
                            <option value="1.15">1.15x</option>
                            <option value="1.25">1.25x</option>
                            <option value="1.5">1.50x</option>
                          </select>
                      </div>
                    </div>
                  </div>

                </div>
              </div>

            </div>
          </div>

          <!-- Modal Footer -->
            <div class="p-3 bg-slate-100 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2.5">
              <div class="flex items-center gap-2">
                <button onclick="closeBeamRebarModal()" class="py-2 px-3.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs transition cursor-pointer shrink-0">
                  Đóng
                </button>
                <div id="brmDbBadge" class="text-[10px] px-2.5 py-1.5 rounded-xl bg-white border border-slate-300 font-bold flex items-center gap-1.5 text-slate-700 shadow-2xs" title="Trạng thái lưu trữ dữ liệu lâu dài">
                  <i data-lucide="database" class="w-3.5 h-3.5 text-indigo-600"></i>
                  <span id="brmDbText">DB: SQLite</span>
                </div>
              </div>

              <!-- Quick Beam Navigation Controls: Prev, Dropdown, Next -->
              <div class="flex items-center gap-2 bg-white px-3 py-1.5 rounded-xl border border-slate-300 shadow-2xs">
                <button type="button" id="brmBtnPrevBeam" onclick="navigateBeamRebarModal(-1)" class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 border border-slate-200 text-slate-700 text-xs font-bold transition flex items-center gap-1 cursor-pointer shrink-0" title="Xem dầm trước">
                  <i data-lucide="chevron-left" class="w-4 h-4"></i> Trước
                </button>

                <div class="flex items-center gap-1.5">
                  <span class="text-[11px] font-semibold text-slate-500 whitespace-nowrap shrink-0">Chọn dầm:</span>
                  <select id="brmBeamNavSelect" onchange="onBeamNavSelectChange(this.value)" class="max-w-[240px] sm:max-w-[320px] md:max-w-[380px] px-2 py-1 rounded-lg border border-slate-300 font-mono text-xs bg-slate-50 text-indigo-900 font-bold hover:bg-white focus:bg-white focus:border-indigo-500 focus:outline-none cursor-pointer truncate">
                    <!-- Populated dynamically with all beams -->
                  </select>
                </div>

                <button type="button" id="brmBtnNextBeam" onclick="navigateBeamRebarModal(1)" class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 border border-slate-200 text-slate-700 text-xs font-bold transition flex items-center gap-1 cursor-pointer shrink-0" title="Xem dầm tiếp theo">
                  Sau <i data-lucide="chevron-right" class="w-4 h-4"></i>
                </button>
              </div>

              <!-- Action & Export Controls -->
              <div class="flex items-center gap-2 flex-wrap">
                <!-- Ghép dầm ngắn -->
                <label class="flex items-center gap-1.5 text-[11px] text-slate-700 font-semibold cursor-pointer select-none bg-white px-2.5 py-1.5 rounded-xl border border-slate-300 shadow-2xs hover:bg-slate-50" title="Ghép 2 dầm ngắn (< 1/2 chiều cao khổ giấy) vào cùng 1 trang in A3">
                  <input type="checkbox" id="brmCheckCombineShort" checked onchange="updateExportScopeUI()" class="rounded text-indigo-600 focus:ring-0 cursor-pointer">
                  <span class="whitespace-nowrap">Ghép dầm ngắn (&lt; 1/2 trang)</span>
                </label>

                <!-- Tùy Chọn Trang In (All pages, Current page, Page ranges) -->
                <div class="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-xl border border-slate-300 shadow-2xs text-xs">
                  <span class="text-[11px] font-bold text-slate-600 whitespace-nowrap flex items-center gap-1">
                    <i data-lucide="printer" class="w-3.5 h-3.5 text-indigo-600"></i> Trang in:
                  </span>
                  <select id="brmExportPageScope" onchange="onExportScopeChange()" class="bg-slate-50 border border-slate-300 rounded-lg px-2 py-1 text-xs font-bold text-indigo-950 focus:outline-none focus:border-indigo-500 cursor-pointer">
                    <option value="current" selected>Trang hiện tại (Current page)</option>
                    <option value="all">Tất cả các trang (All pages)</option>
                    <option value="range">Khoảng trang (Page ranges)</option>
                  </select>
                  <div id="brmExportRangeBox" class="hidden items-center gap-1 pl-1 border-l border-slate-200">
                    <input type="text" id="brmExportPageRangeInput" placeholder="VD: 1-3, 5" class="w-20 px-1.5 py-0.5 rounded border border-slate-300 font-mono text-xs bg-slate-50 text-indigo-950 font-bold focus:bg-white focus:outline-none focus:border-indigo-500" title="Nhập danh sách trang cần xuất (VD: 1-3, 5)" />
                    <span id="brmExportRangeHint" class="text-[10px] text-slate-400 font-mono"></span>
                  </div>
                </div>

                <!-- Nút Xuất PDF -->
                <button type="button" onclick="exportBeamWithScope('pdf')" class="py-2 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer shrink-0" title="Xuất PDF A3 theo tùy chọn trang">
                  <i data-lucide="file-text" class="w-3.5 h-3.5"></i> <span id="brmBtnExportPdfLabel">Xuất PDF</span>
                </button>

                <!-- Nút Xuất DXF -->
                <button type="button" onclick="exportBeamWithScope('dxf')" class="py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer shrink-0" title="Xuất AutoCAD R2010 theo tùy chọn trang">
                  <i data-lucide="layers" class="w-3.5 h-3.5"></i> <span id="brmBtnExportDxfLabel">Xuất DXF</span>
                </button>

                <!-- Lưu Cốt Thép Dầm -->
                <button onclick="saveBeamRebarSelection()" class="py-2 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/30 transition active:scale-95 cursor-pointer shrink-0">
                  <i data-lucide="check" class="w-4 h-4"></i> Lưu Cốt Thép Dầm
                </button>
              </div>
            </div>

          </div>
        </div>

  <!-- ==================================================================== -->
  <!-- MODAL: BẢNG CHI TIẾT TIẾT DIỆN CỘT TOÀN NHÀ (GRID 18 CỘT × 4 TẦNG)    -->
  <!-- ==================================================================== -->
  <div id="columnDrawingModal" class="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-sm hidden flex items-center justify-center p-2 sm:p-4">
    <div class="relative bg-white text-slate-800 w-[95vw] max-w-[95vw] h-[95vh] max-h-[95vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150">
      
      <!-- Modal Header -->
      <div class="p-3.5 sm:p-4 bg-slate-50 text-slate-900 flex flex-wrap items-center justify-between border-b border-slate-200 gap-3 shrink-0">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-2xl bg-amber-500 text-white shadow-md shadow-amber-500/25">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 22h16"/><path d="M4 2h16"/><path d="M6 2v20"/><path d="M18 2v20"/><path d="M10 2v20"/><path d="M14 2v20"/></svg>
          </div>
          <div>
            <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2 flex-wrap">
              Bảng Chi Tiết Tiết Diện Cột Toàn Nhà
              <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-extrabold font-mono">15 Cột × 4 Tầng</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">TCVN 5574:2018</span>
            </h3>
            <p class="text-[11px] text-slate-500">Mặt cắt tiết diện C1 → C15 qua các tầng T1 → T4 đúng phong cách section_cross dầm</p>
          </div>
        </div>

        <!-- Action Buttons & Exports -->
        <div class="flex items-center gap-2 flex-wrap">
          <button type="button" onclick="exportColumnSheetPdf()" class="py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
            <span>Xuất PDF Bản Vẽ Cột</span>
          </button>

          <button type="button" onclick="exportColumnSheetDxf()" class="py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/></svg>
            <span>Xuất DXF Bản Vẽ Cột</span>
          </button>

          <button type="button" onclick="closeColumnDrawingModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>

      <!-- Modal Body: Interactive Canvas Viewport -->
      <div class="relative flex-1 bg-slate-200/60 overflow-hidden flex flex-col min-h-0">
        <canvas id="columnCadCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>

        <!-- Bottom-Left Zoom & Pan HUD Controls -->
        <div class="absolute bottom-3 left-3 flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-300 shadow-lg">
          <button type="button" onclick="zoomColumnCad(1.2)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>
          <button type="button" onclick="zoomColumnCad(0.833)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>
          <button type="button" onclick="resetColumnCadView()" class="px-2.5 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer" title="100%">100%</button>
          <button type="button" onclick="fitColumnCadView()" class="px-2.5 h-7 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer" title="Vừa toàn bộ khung hình">Vừa khung</button>
          <span class="text-[10px] text-slate-400 pl-1.5 border-l border-slate-200 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để di chuyển (Pan)</span>
        </div>

        <!-- Hover Tooltip / Status Info Pill at Top-Right -->
        <div id="columnCadHoverBadge" class="absolute top-3 right-3 flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-300 shadow-md text-xs font-semibold text-slate-700 pointer-events-none transition-all duration-150">
          <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          <span id="columnCadHoverText">Rê chuột vào tiết diện cột để xem chi tiết thông số</span>
        </div>
      </div>
    </div>
  </div>

  <!-- ==================================================================== -->
  <!-- MODAL: BẢN VẼ CHI TIẾT ĐÀ KIỀNG (TRỤC A, B, C - PHẢN LỰC ĐẤT LÊN)    -->
  <!-- ==================================================================== -->
  <div id="tieBeamDrawingModal" class="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-sm hidden flex items-center justify-center p-2 sm:p-4">
    <div class="relative bg-white text-slate-800 w-[95vw] max-w-[95vw] h-[95vh] max-h-[95vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150">
      
      <!-- Modal Header -->
      <div class="p-3.5 sm:p-4 bg-slate-50 text-slate-900 flex flex-wrap items-center justify-between border-b border-slate-200 gap-3 shrink-0">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-2xl bg-emerald-600 text-white shadow-md shadow-emerald-600/25">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 3v12"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
          </div>
          <div>
            <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2 flex-wrap">
              Bản Vẽ Chi Tiết Đà Kiềng Dọc Theo Trục A, B, C
              <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-extrabold font-mono">Tầng 1 (Cao độ +1.800)</span>
              <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-extrabold flex items-center gap-1">
                <span>⚠️ Phản Lực Đất Đẩy Lên</span>
              </span>
            </h3>
            <p class="text-[11px] text-slate-500">DK-A (14.7m, 3 nhịp) • DK-B (32.95m, 5 nhịp) • DK-C (21.85m, 4 nhịp) — Cốt thép tăng cường nhịp ở lưng dầm, tăng cường gối ở bụng dầm</p>
          </div>
        </div>

        <!-- Action Buttons & Exports -->
        <div class="flex items-center gap-2 flex-wrap">
          <button type="button" onclick="exportTieBeamSheetPdf()" class="py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
            <span>Xuất PDF Bản Vẽ Đà Kiềng</span>
          </button>

          <button type="button" onclick="exportTieBeamSheetDxf()" class="py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/></svg>
            <span>Xuất DXF Bản Vẽ Đà Kiềng</span>
          </button>

          <button type="button" onclick="closeTieBeamDrawingModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>

      <!-- Modal Body: Interactive Canvas Viewport -->
      <div class="relative flex-1 bg-slate-200/60 overflow-hidden flex flex-col min-h-0">
        <canvas id="tieBeamCadCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>

        <!-- Bottom-Left Zoom & Pan HUD Controls -->
        <div class="absolute bottom-3 left-3 flex items-center gap-1.5 bg-white/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-300 shadow-lg">
          <button type="button" onclick="zoomTieBeamCad(1.2)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>
          <button type="button" onclick="zoomTieBeamCad(0.833)" class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>
          <button type="button" onclick="resetTieBeamCadView()" class="px-2.5 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer" title="100%">100%</button>
          <button type="button" onclick="fitTieBeamCadView()" class="px-2.5 h-7 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer" title="Vừa toàn bộ khung hình">Vừa khung</button>
          <span class="text-[10px] text-slate-400 pl-1.5 border-l border-slate-200 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để di chuyển (Pan)</span>
        </div>

        <!-- Hover Tooltip / Status Info Pill at Top-Right -->
        <div id="tieBeamCadHoverBadge" class="absolute top-3 right-3 flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-300 shadow-md text-xs font-semibold text-slate-700 pointer-events-none transition-all duration-150">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span id="tieBeamCadHoverText">Rê chuột vào dầm để xem chi tiết cốt thép đà kiềng</span>
        </div>
      </div>
    </div>
  </div>


  <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
    <p>ETABS Structural AI Hub • Powered by RevitAI Studio & Three.js WebGL Engine</p>
    <p class="mt-1 font-mono text-[11px] text-slate-400">Production VPS: mr.pkld.online (103.163.219.87)</p>
  </footer>

  
  <!-- ==================================================================== -->
  <!-- MODAL: BẢNG GHI CHÚ CHUNG KẾT CẤU (PLOT 1020 FULLSCREEN VIEWER)      -->
  <!-- ==================================================================== -->
  <div id="modalGeneralNotes" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-2 sm:p-4">
    <div class="relative bg-white text-slate-800 w-[96vw] max-w-[1550px] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150 h-[95vh]">
      <div class="p-3.5 sm:p-4 bg-slate-50 text-slate-900 flex flex-wrap items-center justify-between border-b border-slate-200 gap-3 shrink-0">
        <div class="flex items-center gap-2.5">
          <span class="p-2 rounded-xl bg-amber-500 text-white shadow-sm">
            <i data-lucide="file-text" class="w-5 h-5"></i>
          </span>
          <div>
            <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
              BẢN VẼ GHI CHÚ CHUNG KẾT CẤU
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">TCVN 5574-2012</span>
            </h3>
            <p class="text-[11px] text-slate-500 font-mono">Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf • 144 KB • 20/10/2026 8:24 AM</p>
          </div>
        </div>

        <div class="flex items-center gap-2.5 flex-wrap">
          <div class="inline-flex p-1 bg-slate-200/80 rounded-xl border border-slate-300 gap-1 text-xs">
            <button type="button" id="gnModalBtn_hd" onclick="setNotesViewMode('hd', 'modal')" class="py-1.5 px-3 rounded-lg text-xs font-bold bg-amber-500 text-white shadow-xs transition cursor-pointer">🖼️ Bản Vẽ CAD HD</button>
            <button type="button" id="gnModalBtn_pdf" onclick="setNotesViewMode('pdf', 'modal')" class="py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition cursor-pointer">📄 PDF Gốc</button>
            <button type="button" id="gnModalBtn_text" onclick="setNotesViewMode('text', 'modal')" class="py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition cursor-pointer">📝 Bóc Tách Điều Khoản</button>
          </div>
          <button type="button" onclick="downloadGeneralNotesPdf()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="Tải PDF">
            <i data-lucide="download" class="w-3.5 h-3.5 text-indigo-600"></i> Tải PDF
          </button>
          <button type="button" onclick="printGeneralNotes()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="In">
            <i data-lucide="printer" class="w-3.5 h-3.5"></i> In
          </button>
          <button type="button" onclick="openGeneralNotesFolder()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="Mở thư mục plot 1020">
            <i data-lucide="folder" class="w-3.5 h-3.5 text-amber-600"></i> Thư mục
          </button>
          <button type="button" onclick="closeGeneralNotesModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng modal">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-hidden p-3 bg-slate-950 flex flex-col">
        <div id="gnModalPane_hd" class="relative w-full h-full rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex-1">
          <canvas id="gnInteractiveCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>
          <div class="absolute bottom-4 left-4 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-700 shadow-xl text-white">
            <button type="button" onclick="zoomNotesCanvas(1.2, 'gnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>
            <button type="button" onclick="zoomNotesCanvas(0.833, 'gnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>
            <button type="button" onclick="resetNotesCanvas100('gnInteractiveCanvas')" class="px-2.5 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">100%</button>
            <button type="button" onclick="fitNotesCanvas('gnInteractiveCanvas')" class="px-3 h-8 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">Vừa khung</button>
            <span id="gnModalZoomBadge" class="text-xs font-mono font-bold text-amber-400 px-2 border-l border-slate-700">100%</span>
            <span class="text-[10px] text-slate-400 pl-2 border-l border-slate-700 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để pan • Double click để vừa khung</span>
          </div>
        </div>

        <div id="gnModalPane_pdf" class="hidden w-full h-full rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex-1">
          <iframe id="gnModalPdfIframe" src="about:blank" data-src="/static/general_notes_drawing.pdf#view=FitH" class="w-full h-full border-0"></iframe>
        </div>

        <div id="gnModalPane_text" class="hidden w-full h-full rounded-2xl bg-white p-6 overflow-y-auto flex-1 space-y-6">
          <div class="flex items-center justify-between border-b pb-4">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 flex items-center gap-2">
                📋 NỘI DUNG BẢN VẼ GHI CHÚ CHUNG KẾT CẤU
                <span class="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">TCVN 5574-2012</span>
              </h3>
              <p class="text-xs text-slate-500 mt-1">Nguồn: Documents/plot/1020/Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf</p>
            </div>
            <button type="button" onclick="copyNoteSection('gnModalClausesList')" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer">
              <i data-lucide="copy" class="w-3.5 h-3.5"></i> Sao chép toàn bộ
            </button>
          </div>

          <div class="bg-amber-50/70 border border-amber-200 rounded-2xl p-4">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-900 mb-3 flex items-center gap-2">
              <span>🛡️</span> II. BẢNG CHIỀU DÀY LỚP BÊ TÔNG BẢO VỆ CỐT THÉP (Cmin mm)
            </h4>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Móng Đáy / Bên</div>
                <div class="text-lg font-black text-amber-700 mt-1">70 / 40 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Tiếp xúc đất tự nhiên</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Cột Khung</div>
                <div class="text-lg font-black text-indigo-700 mt-1">25 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Thép đai min 15mm</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Dầm Khung</div>
                <div class="text-lg font-black text-blue-700 mt-1">25 - 30 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Dưới 25mm, Trên 30mm</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-amber-200 shadow-2xs">
                <div class="text-slate-500 font-semibold">Sàn BTCT</div>
                <div class="text-lg font-black text-emerald-700 mt-1">15 <span class="text-xs font-normal">mm</span></div>
                <div class="text-[10px] text-slate-400 mt-0.5">Sàn mái min 20mm</div>
              </div>
            </div>
          </div>

          <div class="bg-blue-50/70 border border-blue-200 rounded-2xl p-4">
            <h4 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-3 flex items-center gap-2">
              <span>🔩</span> QUY CÁCH CỐT THÉP & BÊ TÔNG
            </h4>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div class="bg-white p-3 rounded-xl border border-blue-200 shadow-2xs">
                <div class="font-bold text-slate-800">Thép Gai D &gt; 10 mm</div>
                <div class="text-blue-700 font-mono font-bold mt-1">Ra = Ra' = 3650 kg/cm²</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Nhóm CB400-V / CII / CIII</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-blue-200 shadow-2xs">
                <div class="font-bold text-slate-800">Thép Tròn D &le; 10 mm</div>
                <div class="text-blue-700 font-mono font-bold mt-1">Ra = Ra' = 2300 kg/cm²</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Nhóm CB240-T / AI / CT3</div>
              </div>
              <div class="bg-white p-3 rounded-xl border border-blue-200 shadow-2xs">
                <div class="font-bold text-slate-800">Bê Tông Kết Cấu</div>
                <div class="text-emerald-700 font-mono font-bold mt-1">Mác #300 (B20 / B22.5)</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Rn = 130 kg/cm², Rk = 10 kg/cm²</div>
              </div>
            </div>
          </div>

          <div id="gnModalClausesList" class="space-y-2.5 text-xs text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200">
            <div class="font-bold text-slate-900 border-b pb-1 text-sm">I. 24 ĐIỀU QUY ĐỊNH KẾT CẤU CHÍNH</div>
            <p><strong>01.</strong> Việc thiết kế dựa trên TCVN hiện hành.</p>
            <p><strong>02.</strong> Những bản vẽ kết cấu cần xem đồng thời với bản vẽ kiến trúc.</p>
            <p><strong>03.</strong> Nếu có bất kỳ thông tin nào không hợp lý, đơn vị thi công phải báo cho bên tư vấn thiết kế để cùng giải quyết.</p>
            <p><strong>04.</strong> Cốt hoàn thiện được xét theo bản vẽ kiến trúc.</p>
            <p><strong>05.</strong> Tất cả các đơn vị ghi trong bản vẽ là mm, nếu như không có ghi chú nào khác.</p>
            <p><strong>06.</strong> Các sai số về kích thước, độ lệch, độ võng... cho phép của kết cấu tuân theo TCVN 4453-1995.</p>
            <p><strong>07.</strong> Áp lực gió tiêu chuẩn: <code class="px-1.5 py-0.5 bg-slate-200 rounded font-mono">Wo = 95 kg/m²</code> (vùng II-B).</p>
            <p><strong>08.</strong> Chất lượng bê tông khi thi công cần được kiểm tra đúng quy phạm.</p>
            <p><strong>09.</strong> Cát dùng làm bê tông phải thỏa mãn các yêu cầu TCVN hiện hành.</p>
            <p><strong>10.</strong> Nước dùng để trộn và dưỡng hộ bê tông phải đảm bảo yêu cầu TCVN 4506-87.</p>
            <p><strong>11.</strong> Không sử dụng các loại phụ gia không rõ nguồn gốc trong bê tông.</p>
            <p><strong>12.</strong> Thi công móng, cột, dầm, sàn phải dựa theo TCVN hiện hành.</p>
            <p><strong>13.</strong> Mạch ngừng thi công phải tuân theo TCVN hiện hành.</p>
            <p><strong>14.</strong> Yêu cầu chống thấm cột, dầm, sàn dưới cao trình &plusmn;0.00.</p>
            <p><strong>15.</strong> Dọc theo chiều cao cột có tường xây đặt thép râu neo vào tường &phi;6a500 dài 1000mm.</p>
            <p><strong>16.</strong> Cốt thép và bê tông: &phi; &le; 10 (Ra = Ra' = 2300 kg/cm²), &phi; &ge; 12 (Ra = Ra' = 3650 kg/cm²); Bê tông Mác #300.</p>
            <p><strong>17.</strong> Khi thi công cột, đà sàn kết hợp điện, nước, điện lạnh phải đặt các ống luồn trước khi đổ bê tông.</p>
            <p><strong>18.</strong> Có thể nối thép cột tại bất kỳ vị trí nào nhưng <strong>không nối quá 50%</strong> tiết diện trên cùng một mặt cắt.</p>
            <p><strong>19.</strong> Trường hợp đặt các đường ống ẩn trong kết cấu thì phải có thiết kế gia cố riêng.</p>
            <p><strong>20.</strong> Số lượng ống luồn lắp đặt ẩn trong kết cấu phải &lt; 3 ống song song, nếu &gt; 3 phải đặt lưới thép gia cường.</p>
            <p><strong>21.</strong> Thống nhất cao độ kết cấu thấp hơn cao độ hoàn thiện là 50mm.</p>
            <p><strong>22.</strong> Quy định neo thép, uốn cốt thép dầm: đoạn neo dầm vào cột tối thiểu 35d; dầm phụ vào dầm chính neo tối thiểu 30d.</p>
            <p><strong>23.</strong> Quy định bổ trụ và giằng tường: tường dài &gt; 4m bố trí bổ trụ BTCT 200x200; tường cao &gt; 3.6m bố trí giằng BTCT 200x100.</p>
            <p><strong>24.</strong> Tất cả tường xây liên kết với bê tông đều phải được đóng lưới mắt cáo chống nứt trước khi trát.</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- General Notes Controller Script -->
  <script src="/static/general_notes_hub.js?v=20261020_v2"></script>
  <script src="/general_notes_hub.js?v=20261020_v2"></script>

  <!-- Controller Script -->
  <script src="/etabs_hub.js?v=20261019_main_rebar_v2"></script>
  <script>
    if (window.lucide) lucide.createIcons();
    // Default open 3D tab
    document.addEventListener('DOMContentLoaded', () => {
      switchEtabsSubTab('etabs-3d');
    });
  </script>
</body>
</html>
"""

def deploy_hub_to_vps():
    """Builds standalone index.html and deploys assets to VPS via SCP including Column CAD Drawing."""
    try:
        temp_dir = tempfile.mkdtemp()
        index_file = os.path.join(temp_dir, 'index.html')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(STANDALONE_HTML)

        js_file = os.path.join(CURRENT_DIR, 'etabs_hub.js')
        json_file = os.path.join(CURRENT_DIR, 'etabs_beam_data.json')
        exporter_file = os.path.join(CURRENT_DIR, 'column_cad_exporter.py')

        if not os.path.exists(js_file):
            return {'success': False, 'message': 'Không tìm thấy etabs_hub.js'}
        if not os.path.exists(json_file):
            return {'success': False, 'message': 'Không tìm thấy etabs_beam_data.json'}

        # Sinh dữ liệu ma trận cột và bản vẽ PDF / DXF trước khi deploy
        import column_cad_exporter
        col_matrix = column_cad_exporter.get_column_matrix_data()
        col_matrix_file = os.path.join(temp_dir, 'column_matrix.json')
        with open(col_matrix_file, 'w', encoding='utf-8') as f:
            json.dump({'success': True, 'data': col_matrix}, f, ensure_ascii=False, indent=2)

        pdf_file = os.path.join(temp_dir, 'Bang_Chi_Tiet_Tiet_Dien_Cot_15x4.pdf')
        column_cad_exporter.generate_column_pdf(column_matrix=col_matrix, output_path=pdf_file)

        dxf_file = os.path.join(temp_dir, 'Bang_Chi_Tiet_Tiet_Dien_Cot_15x4.dxf')
        column_cad_exporter.generate_column_dxf(column_matrix=col_matrix, output_path=dxf_file)

        # Sinh dữ liệu đà kiềng và bản vẽ PDF / DXF trước khi deploy
        import tie_beam_cad_exporter
        tie_data = tie_beam_cad_exporter.get_tie_beam_data()
        tie_data_file = os.path.join(temp_dir, 'tie_beam_data.json')
        with open(tie_data_file, 'w', encoding='utf-8') as f:
            json.dump({'success': True, 'data': tie_data}, f, ensure_ascii=False, indent=2)

        tie_pdf_file = os.path.join(temp_dir, 'Bang_Chi_Tiet_Da_Kieng_Truc_ABC.pdf')
        tie_beam_cad_exporter.generate_tie_beam_pdf(output_path=tie_pdf_file)

        tie_dxf_file = os.path.join(temp_dir, 'Bang_Chi_Tiet_Da_Kieng_Truc_ABC.dxf')
        tie_beam_cad_exporter.generate_tie_beam_dxf(output_path=tie_dxf_file)
        tie_exporter_file = os.path.join(CURRENT_DIR, 'tie_beam_cad_exporter.py')

        # Sinh dữ liệu mặt bằng dầm và bản vẽ PDF / DXF trước khi deploy
        import beam_plan_cad_exporter
        beam_plan_pdf_file = os.path.join(temp_dir, 'Mat_Bang_Ket_Cau_Dam_T3.pdf')
        beam_plan_cad_exporter.generate_beam_plan_pdf(output_path=beam_plan_pdf_file, story='T3')
        beam_plan_dxf_file = os.path.join(temp_dir, 'Mat_Bang_Ket_Cau_Dam_T3.dxf')
        beam_plan_cad_exporter.generate_beam_plan_dxf(output_path=beam_plan_dxf_file, story='T3')
        beam_plan_exporter_file = os.path.join(CURRENT_DIR, 'beam_plan_cad_exporter.py')

        # Sinh dữ liệu mặt bằng cột và bản vẽ PDF / DXF trước khi deploy
        import column_plan_cad_exporter
        col_plan_pdf_file = os.path.join(temp_dir, 'Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.pdf')
        column_plan_cad_exporter.generate_column_plan_pdf(output_path=col_plan_pdf_file)
        col_plan_dxf_file = os.path.join(temp_dir, 'Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.dxf')
        column_plan_cad_exporter.generate_column_plan_dxf(output_path=col_plan_dxf_file)
        col_plan_exporter_file = os.path.join(CURRENT_DIR, 'column_plan_cad_exporter.py')

        # File helper và template DXF
        dxf_helper_file = os.path.join(CURRENT_DIR, 'dxf_template_helper.py')
        dim_template_file = os.path.join(CURRENT_DIR, 'templates', 'dim.dxf')
        beam_cad_exporter_file = os.path.join(CURRENT_DIR, 'beam_cad_exporter.py')

        # 1. SCP files to VPS
        scp_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
            index_file,
            js_file,
            json_file,
            exporter_file,
            beam_cad_exporter_file,
            col_matrix_file,
            pdf_file,
            dxf_file,
            tie_exporter_file,
            tie_data_file,
            tie_pdf_file,
            tie_dxf_file,
            beam_plan_exporter_file,
            beam_plan_pdf_file,
            beam_plan_dxf_file,
            col_plan_exporter_file,
            col_plan_pdf_file,
            col_plan_dxf_file,
            dxf_helper_file,
            dim_template_file,
            os.path.join(CURRENT_DIR, 'static', 'general_notes_hub.js'),
            os.path.join(CURRENT_DIR, 'static', 'general_notes_drawing.pdf'),
            os.path.join(CURRENT_DIR, 'static', 'general_notes_page1.png'),
            f"{VPS_USER}@{VPS_HOST}:{VPS_TARGET_DIR}/"
        ]
        proc = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return {'success': False, 'message': f'Lỗi SCP: {proc.stderr or proc.stdout}'}

        # 2. Setup symlinks/copies & dọn dẹp các file cũ trên VPS để web chạy cực nhanh
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            f"{VPS_USER}@{VPS_HOST}",
            f"mkdir -p {VPS_TARGET_DIR}/static {VPS_TARGET_DIR}/api {VPS_TARGET_DIR}/templates && "
            f"cp -f {VPS_TARGET_DIR}/dim.dxf {VPS_TARGET_DIR}/templates/dim.dxf && "
            f"cp -f {VPS_TARGET_DIR}/etabs_hub.js {VPS_TARGET_DIR}/static/etabs_hub.js && " f"cp -f {VPS_TARGET_DIR}/general_notes_hub.js {VPS_TARGET_DIR}/static/general_notes_hub.js && " f"cp -f {VPS_TARGET_DIR}/general_notes_drawing.pdf {VPS_TARGET_DIR}/static/general_notes_drawing.pdf && " f"cp -f {VPS_TARGET_DIR}/general_notes_page1.png {VPS_TARGET_DIR}/static/general_notes_page1.png && "
            f"cp -f {VPS_TARGET_DIR}/etabs_beam_data.json {VPS_TARGET_DIR}/api/etabs-data && "
            f"cp -f {VPS_TARGET_DIR}/column_matrix.json {VPS_TARGET_DIR}/api/column-matrix && "
            f"cp -f {VPS_TARGET_DIR}/Bang_Chi_Tiet_Tiet_Dien_Cot_15x4.pdf {VPS_TARGET_DIR}/api/export-column-pdf && "
            f"cp -f {VPS_TARGET_DIR}/Bang_Chi_Tiet_Tiet_Dien_Cot_15x4.dxf {VPS_TARGET_DIR}/api/export-column-dxf && "
            f"cp -f {VPS_TARGET_DIR}/tie_beam_data.json {VPS_TARGET_DIR}/api/tie-beam-data && "
            f"cp -f {VPS_TARGET_DIR}/Bang_Chi_Tiet_Da_Kieng_Truc_ABC.pdf {VPS_TARGET_DIR}/api/export-tie-beam-pdf && "
            f"cp -f {VPS_TARGET_DIR}/Bang_Chi_Tiet_Da_Kieng_Truc_ABC.dxf {VPS_TARGET_DIR}/api/export-tie-beam-dxf && "
            f"cp -f {VPS_TARGET_DIR}/Mat_Bang_Ket_Cau_Dam_T3.pdf {VPS_TARGET_DIR}/api/export-beam-plan-pdf && "
            f"cp -f {VPS_TARGET_DIR}/Mat_Bang_Ket_Cau_Dam_T3.dxf {VPS_TARGET_DIR}/api/export-beam-plan-dxf && "
            f"cp -f {VPS_TARGET_DIR}/Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.pdf {VPS_TARGET_DIR}/api/export-column-plan-pdf && "
            f"cp -f {VPS_TARGET_DIR}/Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.dxf {VPS_TARGET_DIR}/api/export-column-plan-dxf && "
            f"rm -f {VPS_TARGET_DIR}/rebar.obj {VPS_TARGET_DIR}/rebar.mtl {VPS_TARGET_DIR}/OBJLoader.js {VPS_TARGET_DIR}/MTLLoader.js "
            f"{VPS_TARGET_DIR}/static/rebar.obj {VPS_TARGET_DIR}/static/rebar.mtl {VPS_TARGET_DIR}/static/OBJLoader.js {VPS_TARGET_DIR}/static/MTLLoader.js && "
            f"chmod -R 755 {VPS_TARGET_DIR}"
        ]
        proc_ssh = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        if proc_ssh.returncode != 0:
            return {'success': False, 'message': f'Lỗi SSH setup: {proc_ssh.stderr or proc_ssh.stdout}'}

        return {
            'success': True,
            'url': 'https://mr.pkld.online',
            'message': 'Đã deploy thành công Bản Vẽ Đà Kiềng (Trục A, B, C) & Bản Vẽ Cột (15×4) lên https://mr.pkld.online!'
        }
    except Exception as e:
        return {'success': False, 'message': f'Ngoại lệ deploy: {str(e)}'}

if __name__ == '__main__':
    res = deploy_hub_to_vps()
    print("Deploy Result:", json.dumps(res, indent=2))

