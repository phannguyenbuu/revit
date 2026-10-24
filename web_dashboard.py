#!/usr/bin/env python



# -*- coding: utf-8 -*-



"""



web_dashboard.py



RevitAI Automation Hub - Bố cục 3 Cột (25% - 50% - 25%) • Theme Light Grey



- Cột 1 (25%): Danh mục công cụ điều hướng dọc (Vertical Tools Menu)



- Cột 2 (50%): Bảng thao tác công cụ đang chọn (Active Workspace & Forms)



- Cột 3 (25%): 3 Bước liên thông AutoCAD -> 3ds Max -> Revit xếp dọc + Trạng thái & Console



"""







import os



import sys



import time



import json



import urllib.request



import urllib.error



from flask import Flask, render_template_string, request, jsonify, send_from_directory, make_response, send_file







_SERVER_START_TIME = str(time.time())







# Thiết lập encoding UTF-8



if sys.stdout.encoding.lower() != 'utf-8':



    try:



        sys.stdout.reconfigure(encoding='utf-8')



    except Exception:



        pass







CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))



if CURRENT_DIR not in sys.path:



    sys.path.insert(0, CURRENT_DIR)







import revit_cli



from scripts.select_by_grid import select_elements_by_grid







app = Flask(__name__)







# ==============================================================================



# HTML TEMPLATE (3-Column Layout: 25% - 50% - 25% • Light Grey Theme)



# ==============================================================================



HTML_TEMPLATE = """



<!DOCTYPE html>



<html lang="vi">



<head>



  <meta charset="UTF-8">



  <meta name="viewport" content="width=device-width, initial-scale=1.0">



  <title>RevitAI Studio • CAD - 3ds Max - Revit Hub</title>



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



  <!-- Lucide Icons -->



  <script src="https://unpkg.com/lucide@latest"></script>



  <style>



    /* Custom light scrollbar */



    ::-webkit-scrollbar { width: 5px; height: 5px; }



    ::-webkit-scrollbar-track { background: #f1f5f9; }



    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }



    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }



  </style>



  <!-- Three.js & OrbitControls for ETABS 3D Solid Cross-Section Model -->



  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>



  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>



  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/MTLLoader.js"></script>



  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>



</head>



<body class="bg-slate-100 text-slate-800 min-h-screen flex flex-col font-sans antialiased">







  <!-- TOP HEADER WITH HORIZONTAL PIPELINE -->



  <header class="bg-white/95 backdrop-blur border-b border-slate-200 sticky top-0 z-50 px-5 py-2 flex items-center justify-between shadow-xs">



    <div class="flex items-center gap-3">



      <h1 class="text-base font-bold tracking-tight text-slate-900 flex items-center gap-2">



        <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>



        <span>RevitAI Studio</span>



      </h1>



      <!-- Nút Help CADLib LISP (Ẩn theo yêu cầu người dùng, truy cập trực tiếp qua Tab 2) -->



      <button type="button" onclick="openLispHelpModal()" id="btnHeaderLispHelp" class="hidden items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-sm hover:shadow group cursor-pointer" title="Trợ giúp: Tra cứu tính năng & lệnh tắt AutoCAD & LISP">



        <span class="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs font-black ring-1 ring-white/50 group-hover:scale-110 transition-transform">?</span>



        <span>Help CADLib LISP</span>



        <span class="text-[10px] px-1.5 py-0.2 rounded-full bg-white/25 text-white font-bold" id="headerLispCountBadge">433</span>



      </button>



    </div>







    <!-- HORIZONTAL PIPELINE STEPS (DÀN HÀNG NGANG CHO GỌN) -->



    <div class="hidden md:flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">



      <!-- Step 1: AutoCAD -->



      <div id="pipeAcad" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs transition" title="AutoCAD Status">



        <span id="cadStatusDot" class="w-2 h-2 rounded-full bg-slate-400"></span>



        <i data-lucide="file-code-2" class="w-3.5 h-3.5 text-cyan-600"></i>



        <span class="font-bold text-slate-800">1. AutoCAD (2D)</span>



        <span id="cadStatusBadge" class="text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-700 font-bold">DWG</span>



      </div>







      <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-slate-400"></i>







      <!-- Step 2: 3ds Max -->



      <div id="pipeMax" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs transition" title="3ds Max Status">



        <span id="maxStatusDot" class="w-2 h-2 rounded-full bg-slate-400"></span>



        <i data-lucide="box" class="w-3.5 h-3.5 text-amber-600"></i>



        <span class="font-bold text-slate-800">2. 3ds Max (3D)</span>



        <span id="maxStatusBadge" class="text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-700 font-bold">:8096</span>



      </div>







      <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-slate-400"></i>







      <!-- Step 3: Revit -->



      <div id="pipeRevit" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs transition" title="Revit Status">



        <span id="revitStatusDot" class="w-2 h-2 rounded-full bg-slate-400"></span>



        <i data-lucide="building-2" class="w-3.5 h-3.5 text-indigo-600"></i>



        <span class="font-bold text-slate-800">3. Autodesk Revit</span>



        <span id="revitStatusBadge" class="text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-700 font-bold">:8090</span>



      </div>



    </div>







    <!-- Live Status Pill -->



    <div class="flex items-center gap-2.5">



      <div id="revitStatusPill" class="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-50 border border-slate-200 text-xs font-semibold shadow-xs">



        <span class="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" id="statusDot"></span>



        <span id="statusText" class="text-slate-600 text-xs font-medium">AEC Hub: Đang kiểm tra...</span>



      </div>



      <button onclick="refreshModelInfo()" class="p-1.5 rounded-lg bg-slate-50 hover:bg-slate-200 text-slate-600 hover:text-slate-900 border border-slate-200 transition" title="Làm mới trạng thái">



        <i data-lucide="refresh-cw" class="w-4 h-4" id="refreshIcon"></i>



      </button>



    </div>



  </header>

<!-- Floating Sticky Expand Button (khi cuộn trang hoặc ở bất kỳ đâu) -->
  <button type="button" id="btnStickyExpandLeft" onclick="toggleLeftPanel(true)" class="hidden fixed left-0 top-36 z-50 bg-white/95 backdrop-blur-xs hover:bg-indigo-50 border border-l-0 border-slate-300 hover:border-indigo-400 rounded-r-xl px-1.5 py-3 shadow-lg cursor-pointer flex flex-col items-center gap-1 text-slate-600 hover:text-indigo-600 group transition-all" title="Mở danh mục công cụ (Arrow Right)">
    <i data-lucide="chevron-right" class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"></i>
    <span class="text-[9px] font-bold text-slate-500 group-hover:text-indigo-600 [writing-mode:vertical-lr] tracking-wider uppercase">Menu</span>
  </button>

  <!-- Floating Sticky Expand Button cho Right Panel (Arrow Left) -->
  <button type="button" id="btnStickyExpandRight" onclick="toggleRightPanel(true)" class="hidden fixed right-0 top-36 z-50 bg-white/95 backdrop-blur-xs hover:bg-indigo-50 border border-r-0 border-slate-300 hover:border-indigo-400 rounded-l-xl px-1.5 py-3 shadow-lg cursor-pointer flex flex-col items-center gap-1 text-slate-600 hover:text-indigo-600 group transition-all" title="Mở lề phải AEC Hub & Console (Arrow Left)">
    <i data-lucide="chevron-left" class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform"></i>
    <span class="text-[9px] font-bold text-slate-500 group-hover:text-indigo-600 [writing-mode:vertical-lr] tracking-wider uppercase">Hub</span>
  </button>








  <!-- 3-COLUMN MAIN LAYOUT: CỘT 1 (DANH MỤC) - CỘT 2 (WORKSPACE) - CỘT 3 (LỀ PHẢI: AEC HUB & CONSOLE) -->



  <main class="flex-1 w-full max-w-[1750px] mx-auto p-4 sm:p-5">



    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4.5 items-start">







      <!-- ==================================================================== -->



      <!-- CỘT 1: DANH MỤC CÔNG CỤ (2 CỘT NÚT BẤM GỌN GÀNG)                      -->



      <!-- ==================================================================== -->



      <aside id="colLeftPanel" class="col-span-12 lg:col-span-4 xl:col-span-3 space-y-3.5 relative transition-all duration-200">



        <div class="bg-white border border-slate-200 rounded-2xl p-3.5 shadow-sm relative">

          <!-- Nút Edge Toggle ép sát mép trong (Border Seam Arrow Left) -->
          <button type="button" id="btnEdgeCollapseLeft" onclick="toggleLeftPanel(false)" class="hidden lg:flex absolute -right-3 top-5 z-20 w-6 h-6 rounded-full bg-white border border-slate-200 shadow-sm hover:shadow-md text-slate-500 hover:text-indigo-600 hover:border-indigo-400 items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Thu gọn danh mục (Arrow Left)">
            <i data-lucide="chevron-left" class="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform"></i>
          </button>



          <!-- 3 Tabs Header Switcher (AEC Tools, CADLib LISP, Maxscript) -->



          <div class="border-b border-slate-100 pb-2.5 mb-3 flex items-center justify-between gap-1.5">

            <div class="flex-1 min-w-0 flex items-center bg-slate-100 p-1 rounded-xl gap-1">



              <!-- Tab 1: Công Cụ AEC (Hiện có) -->



              <button type="button" onclick="switchNavTab('tools')" id="navTabBtn-tools" class="flex-1 py-1.5 px-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1 bg-white text-indigo-700 shadow-xs cursor-pointer truncate" title="12 Công Cụ Revit & CAD">



                <i data-lucide="layout-grid" class="w-3.5 h-3.5 shrink-0"></i>



                <span class="truncate">AEC Tools</span>



                <span class="text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-700 font-bold shrink-0">12</span>



              </button>







              <!-- Tab 2: CadLib LISP & ACadScript -->



              <button type="button" onclick="switchNavTab('cadlib')" id="navTabBtn-cadlib" class="flex-1 py-1.5 px-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1 text-slate-600 hover:text-slate-900 cursor-pointer truncate" title="433 Files AutoCAD & LISP">



                <i data-lucide="file-code" class="w-3.5 h-3.5 shrink-0"></i>



                <span class="truncate">CADLib</span>



                <span class="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-700 font-bold shrink-0" id="cadlibNavBadge">433</span>



              </button>







              <!-- Tab 3: Maxscript -->



              <button type="button" onclick="switchNavTab('maxscript')" id="navTabBtn-maxscript" class="flex-1 py-1.5 px-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1 text-slate-600 hover:text-slate-900 cursor-pointer truncate" title="1,205 Scripts 3ds Max & Python">



                <i data-lucide="box" class="w-3.5 h-3.5 shrink-0"></i>



                <span class="truncate">Maxscript</span>



                <span class="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-700 font-bold shrink-0" id="maxscriptNavBadge">1205</span>



              </button>



            </div>

            <!-- Nút Thu Gọn Left Panel (Arrow Left ép sát mép trong) -->
            <button type="button" id="btnCollapseLeftHeader" onclick="toggleLeftPanel(false)" class="p-1.5 rounded-xl bg-slate-100 hover:bg-indigo-100 text-slate-500 hover:text-indigo-700 transition cursor-pointer shrink-0 border border-slate-200/60 hover:border-indigo-300 shadow-xs flex items-center justify-center w-8 h-8" title="Thu gọn danh mục (Arrow Left)">
              <i data-lucide="chevron-left" class="w-4 h-4"></i>
            </button>



          </div>







          <!-- TAB PANE 1: HIỆN CÓ (12 CÔNG CỤ 2 CỘT) -->



          <div id="navPane-tools" class="space-y-2">



            <!-- 2-Column Button Grid (No Icons, Compact View) -->



            <nav class="grid grid-cols-2 gap-2" id="verticalMenu">



              <!-- Item 1: Chọn theo Trục -->



              <button onclick="switchTab('tab-grid')" id="btn-tab-grid" title="1. Chọn theo Lưới Trục: Lọc theo Trục X, Y, Tầng, Category" class="tab-btn w-full text-left p-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 text-white shadow-md shadow-blue-500/20 border border-transparent flex flex-col justify-center transition group cursor-pointer hover:shadow">



                <div class="font-bold text-xs truncate">1. Chọn Lưới Trục</div>



                <div class="tab-subtitle text-[11px] opacity-80 truncate mt-0.5">Lọc Trục X, Y, Tầng, Cat</div>



              </button>







              <!-- Item 2: Cửa D7 mở 30° -->



              <button onclick="switchTab('tab-door')" id="btn-tab-door" title="2. Cửa D7 Mở 30°: Đổi cửa thoát hiểm Trục C" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">2. Cửa D7 Mở 30°</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Đổi cửa thoát hiểm Trục C</div>



              </button>







              <!-- Item 3: Đánh Dim tự động -->



              <button onclick="switchTab('tab-dim')" id="btn-tab-dim" title="3. Đánh Dim Tự Động: Dim 3 lớp bao ngoài & nội thất" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">3. Đánh Dim Tự Động</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Dim 3 lớp ngoài & nội thất</div>



              </button>







              <!-- Item 4: Xuất DWG -->



              <button onclick="switchTab('tab-dwg')" id="btn-tab-dwg" title="4. Xuất Bản Vẽ DWG: Bố cục cột dọc, font Unicode" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">4. Xuất Bản Vẽ DWG</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Bố cục cột dọc, font Unicode</div>



              </button>







              <!-- Item 5: AutoCAD 3D OBJ & Vision AI -->



              <button onclick="switchTab('tab-cad')" id="btn-tab-cad" title="5. AutoCAD AI Hub: Trích xuất Clipboard -> Nhận diện 2D & Sinh 3D OBJ" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate flex items-center gap-1.5">



                  <span class="w-2 h-2 rounded-full bg-cyan-500 shrink-0"></span>



                  <span>5. AutoCAD 3D & AI</span>



                </div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Clipboard &bull; 2D Vision &bull; 3D OBJ</div>



              </button>







              <!-- Item 6: Đồng bộ 3ds Max sang Revit -->



              <button onclick="switchTab('tab-max')" id="btn-tab-max" title="6. Đồng Bộ 3ds Max • Revit: Chuyển sảnh/mặt tiền sang Family" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">6. Max &rarr; Revit Family</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Đồng bộ sảnh sang Family</div>



              </button>







              <!-- Item 7: Xuất Revit sang 3ds Max Poly sạch -->



              <button onclick="switchTab('tab-revit-to-max')" id="btn-tab-revit-to-max" title="7. Xuất Sang 3ds Max: Editable Poly sạch, ko chia tam giác" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">7. Xuất Sang 3ds Max</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Poly sạch, ko vỡ tam giác</div>



              </button>







              <!-- Item 8: Chuyển Polyline AutoCAD sang Sàn Revit (Slab) -->



              <button onclick="switchTab('tab-cad-slab')" id="btn-tab-cad-slab" title="8. Polyline CAD -> Sàn Revit: Tạo / Thay thế Sàn thường & WC" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">8. Poly CAD &rarr; Sàn</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Tạo / Đổi Sàn & WC</div>



              </button>







              <!-- Item 9: Đồng bộ Vị Trí Cửa Các Tầng Theo Tầng 1 (Trục X hoặc Y) -->



              <button onclick="switchTab('tab-sync-openings')" id="btn-tab-sync-openings" title="9. Căn Cửa Theo Tầng 1: Căn tọa độ theo trục X hoặc Y" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">9. Căn Cửa Theo Tầng 1</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Căn tọa độ trục X hoặc Y</div>



              </button>







              <!-- Item 10: Ẩn / Hiện Tag Cửa Đi & Cửa Sổ -->



              <button onclick="switchTab('tab-tags')" id="btn-tab-tags" title="10. Ẩn / Hiện Tag Cửa: Bật/tắt tag cửa theo từng tầng hoặc all tầng" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">10. Ẩn/Hiện Tag Cửa</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Bật/tắt tag theo tầng / all</div>



              </button>







              <!-- Item 11: Xóa Hatch Solid & Kéo Leader MEP -->



              <button onclick="switchTab('tab-mep-cad')" id="btn-tab-mep-cad" title="11. Xử Lý CAD & Leader Cao Độ: Xóa solid trong block & kéo leader cos (+)" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">11. Xử Lý CAD & Leader</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Xóa solid & kéo leader (+)</div>



              </button>







              <!-- Item 12: Lọc Khung Tên & In Hàng Loạt AutoCAD -->



              <button onclick="switchTab('tab-cad-plot')" id="btn-tab-cad-plot" title="12. Lọc Khung Tên & In Hàng Loạt: Bóc tách Array, lọc nội dung & Batch Plot" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate">12. Lọc Khung & In CAD</div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Bóc Array & Batch Plot</div>



              </button>







              <!-- Item 13: SketchUp Ruby .RB -> 3D OBJ & WebGL Viewer -->



              <button onclick="switchTab('tab-rb-obj')" id="btn-tab-rb-obj" title="13. Ruby .RB -> 3D OBJ: Chuyển file hoặc dán code SketchUp Ruby sang 3D Wavefront OBJ và xem preview WebGL" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">



                <div class="font-bold text-xs truncate flex items-center gap-1.5">



                  <span class="w-2 h-2 rounded-full bg-rose-500 shrink-0"></span>



                  <span>13. Ruby .RB &rarr; 3D OBJ</span>



                </div>



                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Code / File .rb &bull; 3D OBJ Preview</div>



              </button>

              <!-- Item 14: MEP AI Studio 3D • Điện, Nước, HVAC, BIM & Bóc Tách Khối Lượng -->
              <button onclick="switchTab('tab-mep-ai')" id="btn-tab-mep-ai" title="14. MEP AI Studio: Thiết kế tự động Điện, Nước, HVAC, Dựng BIM 3D, Clash Detection & BOQ" class="tab-btn w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 flex flex-col justify-center transition group cursor-pointer hover:shadow-xs">
                <div class="font-bold text-xs truncate flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-cyan-500 shrink-0"></span>
                  <span>14. MEP AI Studio 3D</span>
                </div>
                <div class="tab-subtitle text-[11px] text-slate-500 truncate mt-0.5">Điện, Nước, HVAC &bull; BIM 3D & BOQ</div>
              </button>



            </nav>



          </div>







          <!-- TAB PANE 2: CADLIB LISP & ACADSCRIPT (TỔNG HỢP 433 SCRIPTS CAD) -->



          <div id="navPane-cadlib" class="hidden space-y-2.5">



            <!-- Header Info Badge -->



            <div class="p-2.5 rounded-xl bg-indigo-50/80 border border-indigo-100 flex items-center justify-between">



              <div class="flex items-center gap-2 min-w-0">



                <div class="p-1.5 rounded-lg bg-indigo-600 text-white shrink-0">



                  <i data-lucide="book-open" class="w-4 h-4"></i>



                </div>



                <div class="min-w-0">



                  <div class="text-xs font-bold text-slate-900 truncate">Thư Viện AutoCAD & LISP</div>



                  <div class="text-[10px] text-slate-500 font-mono truncate">CADLib • ACadScript</div>



                </div>



              </div>



              <span id="modalLispBadgeTotal" class="text-[10px] px-2 py-0.5 rounded-full bg-white text-indigo-700 font-bold border border-indigo-200 shadow-2xs whitespace-nowrap shrink-0">



                433 Scripts



              </span>



            </div>







            <!-- Search box -->



            <div class="relative">



              <i data-lucide="search" class="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400"></i>



              <input type="text" id="lispSearchInput" oninput="filterLispCards()" placeholder="🔍 Tìm tính năng, lệnh (ALX, CVT...), tên file, C#..." class="w-full pl-8.5 pr-8 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 font-medium focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500">



              <button id="btnClearLispSearch" onclick="clearLispSearch()" class="absolute right-2.5 top-2 text-slate-400 hover:text-slate-700 hidden text-xs p-0.5 rounded cursor-pointer" title="Xóa tìm kiếm">



                <i data-lucide="x" class="w-3.5 h-3.5"></i>



              </button>



            </div>







            <!-- Source Filter & Category Filter Tabs -->



            <div class="space-y-1.5">



              <!-- Nguồn Source Pills -->



              <div class="flex items-center justify-between text-xs">



                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nguồn:</span>



                <span id="lispFilterCount" class="text-[10.5px] font-bold text-slate-500 whitespace-nowrap">



                  Hiển thị 433 / 433



                </span>



              </div>



              <div class="flex items-center gap-1.5" id="cadlibSourceTabs">



                <button onclick="setCadlibSource('all')" id="btnCadSrc-all" class="px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-indigo-600 text-white shadow-xs">



                  Tất cả (433)



                </button>



                <button onclick="setCadlibSource('CADLib LISP')" id="btnCadSrc-cadlib" class="px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-slate-100 hover:bg-slate-200 text-slate-700">



                  CADLib (106)



                </button>



                <button onclick="setCadlibSource('ACadScript')" id="btnCadSrc-acadscript" class="px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-slate-100 hover:bg-slate-200 text-slate-700">



                  ACadScript (327)



                </button>



              </div>







              <!-- Chủ đề Pills Header (Click để Collapse/Expand) -->



              <button type="button" onclick="toggleCadlibCategories()" class="w-full flex items-center justify-between pt-1 pb-0.5 text-left group cursor-pointer select-none" title="Bấm để thu gọn / mở rộng danh sách chủ đề">



                <div class="flex items-center gap-1.5 min-w-0">



                  <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 group-hover:text-indigo-600 transition-colors shrink-0">Chủ đề:</span>



                  <span id="cadlibActiveCatBadge" class="text-[9.5px] px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200 truncate max-w-[170px]">



                    Tất cả (433)



                  </span>



                </div>



                <div class="flex items-center gap-1 text-slate-400 group-hover:text-indigo-600 transition-colors shrink-0">



                  <span id="cadlibCatToggleText" class="text-[10px] font-medium text-slate-400 group-hover:text-indigo-600">Thu gọn</span>



                  <i data-lucide="chevron-up" id="cadlibCatArrow" class="w-3.5 h-3.5 transition-transform duration-200"></i>



                </div>



              </button>



              <div class="flex flex-wrap items-center gap-1.5 pt-0.5" id="lispCategoryTabs">



                <!-- Dynamically populated categories -->



              </div>



            </div>







            <!-- Scrollable Cards Container -->



            <div class="max-h-[600px] overflow-y-auto pr-1 space-y-2.5" id="lispGridContainer">



              <!-- Dynamically populated cards -->



            </div>







            <!-- Quick Footer Tip -->



            <div class="p-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-500 flex items-center gap-1.5 text-[10px]">



              <i data-lucide="info" class="w-3.5 h-3.5 text-indigo-500 shrink-0"></i>



              <span>Click tên lệnh để copy • <strong>Nạp CAD</strong> với LISP/Script • <strong>Mở Code</strong> xem C#/LISP.</span>



            </div>



          </div>







          <!-- TAB PANE 3: MAXSCRIPT (TỔNG HỢP 1,205 SCRIPTS TỪ SKMSTOOL & 3DS MAX 2022) -->



          <div id="navPane-maxscript" class="hidden space-y-2.5">



            <!-- Header Info Badge -->



            <div class="p-2.5 rounded-xl bg-amber-50/80 border border-amber-200/70 flex items-center justify-between">



              <div class="flex items-center gap-2 min-w-0">



                <div class="p-1.5 rounded-lg bg-amber-600 text-white shrink-0">



                  <i data-lucide="layers" class="w-4 h-4"></i>



                </div>



                <div class="min-w-0">



                  <div class="text-xs font-bold text-slate-900 truncate">MaxScript & Python 3ds Max</div>



                  <div class="text-[10px] text-slate-500 font-mono truncate">skMSTool • 3ds Max 2022</div>



                </div>



              </div>



              <span id="maxscriptBadgeTotal" class="text-[10px] px-2 py-0.5 rounded-full bg-white text-amber-700 font-bold border border-amber-200 shadow-2xs whitespace-nowrap shrink-0">



                1,205 Scripts



              </span>



            </div>







            <!-- Search box -->



            <div class="relative">



              <i data-lucide="search" class="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400"></i>



              <input type="text" id="maxscriptSearchInput" oninput="filterMaxscriptCards()" placeholder="🔍 Tìm script (Detach, Remesh, Mtl, V-Ray, Rebar...)" class="w-full pl-8.5 pr-8 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 font-medium focus:bg-white focus:outline-none focus:ring-1 focus:ring-amber-500">



              <button id="btnClearMaxscriptSearch" onclick="clearMaxscriptSearch()" class="absolute right-2.5 top-2 text-slate-400 hover:text-slate-700 hidden text-xs p-0.5 rounded cursor-pointer" title="Xóa tìm kiếm">



                <i data-lucide="x" class="w-3.5 h-3.5"></i>



              </button>



            </div>







            <!-- Source Filter & Category Filter Tabs -->



            <div class="space-y-1.5">



              <!-- Nguồn Source Pills -->



              <div class="flex items-center justify-between text-xs">



                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nguồn:</span>



                <span id="maxscriptFilterCount" class="text-[10.5px] font-bold text-slate-500 whitespace-nowrap">



                  Hiển thị 1,205 / 1,205



                </span>



              </div>



              <div class="flex items-center gap-1.5" id="maxscriptSourceTabs">



                <button onclick="setMaxscriptSource('all')" id="btnMsSrc-all" class="px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-amber-600 text-white shadow-xs">



                  Tất cả (1205)



                </button>



                <button onclick="setMaxscriptSource('skMSTool')" id="btnMsSrc-skMSTool" class="px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-slate-100 hover:bg-slate-200 text-slate-700">



                  skMSTool (1105)



                </button>



                <button onclick="setMaxscriptSource('3ds Max 2022')" id="btnMsSrc-user3dsmax" class="px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-slate-100 hover:bg-slate-200 text-slate-700">



                  3ds Max 2022 (100)



                </button>



              </div>







              <!-- Chủ đề Pills Header (Click để Collapse/Expand) -->



              <button type="button" onclick="toggleMaxscriptCategories()" class="w-full flex items-center justify-between pt-1 pb-0.5 text-left group cursor-pointer select-none" title="Bấm để thu gọn / mở rộng danh sách chủ đề">



                <div class="flex items-center gap-1.5 min-w-0">



                  <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 group-hover:text-amber-600 transition-colors shrink-0">Chủ đề:</span>



                  <span id="maxscriptActiveCatBadge" class="text-[9.5px] px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 font-semibold border border-amber-200 truncate max-w-[170px]">



                    Tất cả (1,205)



                  </span>



                </div>



                <div class="flex items-center gap-1 text-slate-400 group-hover:text-amber-600 transition-colors shrink-0">



                  <span id="maxscriptCatToggleText" class="text-[10px] font-medium text-slate-400 group-hover:text-amber-600">Thu gọn</span>



                  <i data-lucide="chevron-up" id="maxscriptCatArrow" class="w-3.5 h-3.5 transition-transform duration-200"></i>



                </div>



              </button>



              <div class="flex flex-wrap items-center gap-1.5 pt-0.5" id="maxscriptCategoryTabs">



                <!-- Dynamically populated categories -->



              </div>



            </div>







            <!-- Scrollable Cards Container -->



            <div class="max-h-[600px] overflow-y-auto pr-1 space-y-2.5" id="maxscriptGridContainer">



              <!-- Dynamically populated cards -->



            </div>







            <!-- Quick Footer Tip -->



            <div class="p-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-500 flex items-center gap-1.5 text-[10px]">



              <i data-lucide="info" class="w-3.5 h-3.5 text-amber-500 shrink-0"></i>



              <span>Click <strong>"fileIn"</strong> để copy lệnh nạp F11 • Click <strong>"Mở"</strong> để xem code.</span>



            </div>



          </div>



        </div>



      </aside>







      <!-- ==================================================================== -->



      <!-- CỘT 2: BẢNG THAO TÁC CÔNG CỤ (ACTIVE WORKSPACE)                       -->



      <!-- ==================================================================== -->



      <section id="colCenterWorkspace" class="col-span-12 lg:col-span-5 xl:col-span-6 space-y-4 relative transition-all duration-200">

        <!-- Nút Edge Toggle Mở Rộng (Border Seam Arrow Right khi Left Panel bị thu gọn) -->
        <!-- Nút Edge Toggle Mở Rộng Left Panel (Border Seam Arrow Right khi Left Panel bị thu gọn) -->
        <button type="button" id="btnEdgeExpandLeft" onclick="toggleLeftPanel(true)" class="hidden absolute -left-3 top-5 z-20 w-6 h-6 rounded-full bg-indigo-600 border border-indigo-700 shadow-md hover:bg-indigo-700 text-white items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Mở rộng danh mục (Arrow Right)">
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform"></i>
        </button>

        <!-- Nút Edge Toggle Mở Rộng Right Panel (Border Seam Arrow Left khi Right Panel bị thu gọn) -->
        <button type="button" id="btnEdgeExpandRight" onclick="toggleRightPanel(true)" class="hidden absolute -right-3 top-5 z-20 w-6 h-6 rounded-full bg-indigo-600 border border-indigo-700 shadow-md hover:bg-indigo-700 text-white items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Mở rộng lề phải (Arrow Left)">
          <i data-lucide="chevron-left" class="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform"></i>
        </button>

        <div id="leftPanelExpandBar" class="hidden"></div>
          <span class="text-[11px] text-slate-400 hidden md:inline">Không gian làm việc mở rộng tối đa (9 Cột)</span>
        </div>







        <!-- ==================================================================== -->



        <!-- TAB CONTENT: ETABS STRUCTURAL AI HUB (ACTIVE WORKSPACE - TRANG GIỮA) -->



        <!-- ==================================================================== -->



        <div id="tab-etabs-hub" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-5">



          



          <!-- SUB-PANE 1: MẶT BẰNG DẦM 2D (ĐÚNG BỀ RỘNG DẦM + TEXT TIẾT DIỆN) -->



          <div id="subpane-etabs-2d" class="etabs-subpane hidden space-y-3">



            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">



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







              <!-- Controls & Exports -->



              <div class="flex items-center gap-2 flex-wrap">



                <button type="button" onclick="exportBeamPlanPdf()" class="py-1.5 px-2.5 rounded-xl bg-white hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-300 text-xs font-bold flex items-center gap-1 cursor-pointer transition shadow-2xs" title="Xuất file PDF Mặt Bằng Ký Hiệu Dầm (khổ A1)">



                  <i data-lucide="file-text" class="w-3.5 h-3.5 text-indigo-600"></i> Xuất PDF Mặt Bằng



                </button>



                <button type="button" onclick="exportBeamPlanDxf()" class="py-1.5 px-2.5 rounded-xl bg-white hover:bg-amber-50 hover:text-amber-800 text-slate-700 border border-slate-300 text-xs font-bold flex items-center gap-1 cursor-pointer transition shadow-2xs" title="Xuất file AutoCAD DXF R2010 Mặt Bằng Ký Hiệu Dầm">



                  <i data-lucide="download" class="w-3.5 h-3.5 text-amber-600"></i> Xuất DXF Mặt Bằng



                </button>



                <button onclick="zoomEtabs2D(1.2)" class="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold" title="Phóng to">



                  <i data-lucide="zoom-in" class="w-4 h-4"></i>



                </button>



                <button onclick="zoomEtabs2D(0.8)" class="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold" title="Thu nhỏ">



                  <i data-lucide="zoom-out" class="w-4 h-4"></i>



                </button>



                <button onclick="resetEtabs2DView()" class="py-1.5 px-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold flex items-center gap-1" title="Vừa màn hình">



                  <i data-lucide="maximize" class="w-3.5 h-3.5"></i> Vừa khung



                </button>



                <label class="flex items-center gap-1.5 text-xs font-medium text-slate-700 ml-1 cursor-pointer">



                  <input type="checkbox" id="chkShow2DLabels" checked onchange="renderEtabs2DPlan()" class="rounded border-slate-300 text-indigo-600 focus:ring-0"> Hiện nhãn tiết diện



                </label>



              </div>



            </div>







            <!-- 2D Canvas Container -->



            <div class="relative w-full h-[580px] bg-[#aaaaaa] rounded-2xl overflow-hidden border border-slate-400 shadow-inner">



              <canvas id="etabs2DCanvas" class="w-full h-full cursor-grab active:cursor-grabbing"></canvas>



              



              <!-- 2D Legend Overlay (Collapsible) -->



              <div id="etabs2DLegendCard" class="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md border border-slate-300 rounded-xl shadow-lg z-20 overflow-hidden text-[11px] text-slate-700 pointer-events-auto">



                <button type="button" onclick="toggle2DLegend()" class="w-full flex items-center justify-between gap-3 px-3 py-1.5 font-bold text-slate-900 hover:bg-slate-100/80 transition-colors cursor-pointer select-none">



                  <div class="flex items-center gap-1.5">



                    <span class="w-2 h-2 rounded-full bg-cyan-600"></span>



                    <span>Chú Giải Tiết Diện Mặt Bằng</span>



                  </div>



                  <i id="ico2DLegendToggle" data-lucide="chevron-up" class="w-3.5 h-3.5 text-slate-500 transition-transform duration-200"></i>



                </button>



                <div id="body2DLegend" class="px-3 pb-2 pt-0.5 space-y-1 border-t border-slate-100">



                  <div class="flex items-center gap-2"><span class="w-4 h-2 bg-sky-500 rounded-sm shrink-0"></span> Dầm BTCT</div>



                  <div class="flex items-center gap-2"><span class="w-3 h-3 bg-slate-700 rounded-sm shrink-0"></span> Cột BTCT</div>



                  <div class="flex items-center gap-2"><span class="w-4 h-0.5 border-t border-dashed border-emerald-600 shrink-0"></span> Lưới trục kiến trúc</div>



                </div>



              </div>







              <!-- Beam hover tooltip -->



              <div id="etabs2DTooltip" class="absolute hidden bg-slate-900/95 text-white border border-indigo-400 text-xs rounded-xl p-2.5 shadow-xl pointer-events-none z-10 space-y-1"></div>



            </div>



          </div>







          <!-- SUB-PANE 2: MODEL 3D ĐÚNG TIẾT DIỆN (THREE.JS SOLID BOXES) -->



          <div id="subpane-etabs-3d" class="etabs-subpane space-y-3">

            <!-- AEC 3D Interactive Studio Toolbar (Wall Line, Door Block, Snap & Round 50/100) -->
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2">
              <div class="flex flex-wrap items-center justify-between gap-2.5">
                <!-- 1. Tool Modes -->
                <div class="inline-flex items-center gap-1 p-1 bg-slate-200/90 rounded-xl border border-slate-300">
                  <button type="button" onclick="setAecToolMode('select')" id="aecBtnModeSelect" class="py-1 px-3 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-xs transition cursor-pointer flex items-center gap-1.5" title="Chế độ xoay, phóng to và chọn đối tượng">
                    🖐️ Xem 3D
                  </button>
                  <button type="button" onclick="setAecToolMode('wall')" id="aecBtnModeWall" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-white/80 transition cursor-pointer flex items-center gap-1.5" title="Vẽ Tường dạng đường Line (Bấm điểm đầu, rê chuột, bấm điểm cuối)">
                    🧱 Vẽ Tường (Line)
                  </button>
                  <button type="button" onclick="setAecToolMode('door')" id="aecBtnModeDoor" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-white/80 transition cursor-pointer flex items-center gap-1.5" title="Đặt Cửa dạng Block (Phím Space để xoay 90°)">
                    🚪 Đặt Cửa (Block)
                  </button>
                </div>

                <!-- 2. Snap & Round 50 / 100 -->
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-slate-700 flex items-center gap-1">
                    🧲 Snap & Round:
                  </span>
                  <div class="inline-flex items-center gap-0.5 p-0.5 bg-slate-200/90 rounded-lg border border-slate-300 text-xs font-bold">
                    <button type="button" onclick="setAecSnapRound(50)" id="aecBtnSnap50" class="py-1 px-2.5 rounded text-slate-700 hover:bg-white/80 transition cursor-pointer" title="Làm tròn tọa độ 50 mm">
                      50 mm
                    </button>
                    <button type="button" onclick="setAecSnapRound(100)" id="aecBtnSnap100" class="py-1 px-2.5 rounded bg-indigo-600 text-white shadow-xs transition cursor-pointer" title="Làm tròn tọa độ 100 mm">
                      100 mm
                    </button>
                    <button type="button" onclick="setAecSnapRound(0)" id="aecBtnSnapOff" class="py-1 px-2 rounded text-slate-500 hover:bg-white/80 transition cursor-pointer" title="Tắt làm tròn tọa độ">
                      Tắt
                    </button>
                  </div>

                  <label class="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer select-none ml-1 font-semibold">
                    <input type="checkbox" id="aecChkSnapGeom" checked onchange="toggleAecSnapGeom(this.checked)" class="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
                    <span>Snap Cột/Dầm</span>
                  </label>
                </div>

                <!-- 3. Story Elevation Selection & Actions -->
                <div class="flex items-center gap-2">
                  <div class="flex items-center gap-1 text-xs">
                    <span class="font-bold text-slate-700">Tầng:</span>
                    <select id="aecStorySelect" onchange="changeAecStory(this.value)" class="py-1 px-2 rounded-lg border border-slate-300 bg-white text-xs font-bold text-slate-700 shadow-xs focus:ring-1 focus:ring-indigo-500">
                      <option value="T1">Tầng 1 (0.0 m)</option>
                      <option value="T2">Tầng 2 (7.6 m)</option>
                      <option value="T3" selected>Tầng 3 (11.8 m)</option>
                      <option value="T4">Tầng 4 (15.6 m)</option>
                      <option value="TM">Mái (18.4 m)</option>
                    </select>
                  </div>

                  <button type="button" onclick="undoLastAecElement()" class="py-1 px-2.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-bold transition flex items-center gap-1 cursor-pointer" title="Hoàn tác vật thể vừa vẽ (Ctrl+Z)">
                    ↩️ Hoàn Tác
                  </button>

                  <button type="button" onclick="clearAllAecElements()" class="py-1 px-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold transition flex items-center gap-1 cursor-pointer" title="Xóa toàn bộ Tường & Cửa đã vẽ">
                    🗑️ Xóa AEC
                  </button>

                  <span id="aecBadgeCount" class="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold">
                    0 Tường • 0 Cửa
                  </span>
                </div>
              </div>

              <!-- Parameter Sub-Row: Wall & Door Quick Options -->
              <div id="aecParamSubRow" class="flex flex-wrap items-center justify-between text-xs pt-1.5 border-t border-slate-200 text-slate-600">
                <div id="aecWallParams" class="flex items-center gap-3">
                  <span class="font-bold text-amber-700 flex items-center gap-1">🧱 Tường Line:</span>
                  <span class="text-slate-500 font-medium">Bề dày:</span>
                  <div class="inline-flex p-0.5 bg-slate-200 rounded border border-slate-300 text-[11px] font-bold">
                    <button type="button" onclick="setAecWallThickness(100)" id="aecBtnWall100" class="px-2 py-0.5 rounded bg-amber-600 text-white cursor-pointer">100 mm</button>
                    <button type="button" onclick="setAecWallThickness(200)" id="aecBtnWall200" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">200 mm</button>
                  </div>
                  <span class="text-slate-500 font-medium ml-1">Chiều cao:</span>
                  <div class="inline-flex p-0.5 bg-slate-200 rounded border border-slate-300 text-[11px] font-bold">
                    <button type="button" onclick="setAecWallHeight(3000)" id="aecBtnWallH3000" class="px-2 py-0.5 rounded bg-amber-600 text-white cursor-pointer">3,000 mm</button>
                    <button type="button" onclick="setAecWallHeight(3800)" id="aecBtnWallH3800" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">3,800 mm</button>
                  </div>
                  <span class="text-[11px] text-slate-400 italic">💡 Bấm điểm đầu ➔ kéo chuột ➔ bấm điểm cuối (Giữ Shift khóa trục, Esc hủy)</span>
                </div>

                <div id="aecDoorParams" class="hidden flex items-center gap-3">
                  <span class="font-bold text-emerald-700 flex items-center gap-1">🚪 Cửa Block:</span>
                  <span class="text-slate-500 font-medium">Bề rộng:</span>
                  <div class="inline-flex p-0.5 bg-slate-200 rounded border border-slate-300 text-[11px] font-bold">
                    <button type="button" onclick="setAecDoorWidth(800)" id="aecBtnDoor800" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">800 mm</button>
                    <button type="button" onclick="setAecDoorWidth(900)" id="aecBtnDoor900" class="px-2 py-0.5 rounded bg-emerald-600 text-white cursor-pointer">900 mm</button>
                    <button type="button" onclick="setAecDoorWidth(1200)" id="aecBtnDoor1200" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">1,200 mm</button>
                  </div>
                  <button type="button" onclick="rotateAecDoor()" class="py-0.5 px-2.5 rounded bg-slate-200 hover:bg-slate-300 font-bold text-[11px] flex items-center gap-1 cursor-pointer" title="Xoay hướng cửa 90° (hoặc bấm phím Space)">
                    🔄 Xoay: <span id="aecDoorAngleLabel" class="text-indigo-600 font-mono">0°</span> (Phím Space)
                  </button>
                  <span class="text-[11px] text-slate-400 italic">💡 Rê chuột đến tường hoặc mặt bằng ➔ bấm chuột để đặt</span>
                </div>
              </div>
            </div>







            <!-- 3D Three.js Container -->



            <div class="relative w-full h-[580px] bg-[#aaaaaa] rounded-2xl overflow-hidden border border-slate-400 shadow-inner group">



              <div id="etabs3DContainer" class="w-full h-full"></div>

              <!-- Floating 3D AEC HUD Hint & Coordinates -->
              <div id="aec3DHintHUD" class="absolute bottom-3 right-3 z-20 hidden bg-slate-900/90 backdrop-blur-md text-white text-xs px-3.5 py-2 rounded-xl border border-indigo-400/50 shadow-xl pointer-events-none transition-all space-y-1">
                <div class="flex items-center gap-2">
                  <span id="aec3DHintIcon" class="text-base">🧱</span>
                  <span id="aec3DHintText" class="font-bold text-amber-300">Vẽ Tường (Line)</span>
                </div>
                <div id="aec3DHintCoord" class="text-[11px] font-mono text-slate-300">Snap: 100mm • Bấm điểm đầu</div>
              </div>



              



              <!-- Top-Right Floating 3D Toolbar (Moment 3D, Lưới Trục, Khung Dây, Reset Camera, Deploy) -->



              <div class="absolute top-3 right-3 z-20 flex flex-wrap items-center gap-1.5 bg-white/90 backdrop-blur-md p-1.5 rounded-xl border border-slate-300 shadow-xl">



                <button onclick="toggle3DMoment()" id="btn3DMoment" class="py-1 px-2.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-800 font-bold text-xs flex items-center gap-1 border border-amber-400 transition active:scale-95 cursor-pointer" title="Bật/Tắt Biểu Đồ Moment M33 3D">



                  <i data-lucide="activity" class="w-3.5 h-3.5 text-amber-600"></i> Moment 3D



                </button>



                <button onclick="toggle3DGrids()" id="btn3DGrids" class="py-1 px-2.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-800 font-bold text-xs flex items-center gap-1 border border-emerald-400 transition active:scale-95 cursor-pointer" title="Bật/Tắt Lưới Trục 1-7, A-C">



                  <i data-lucide="grid" class="w-3.5 h-3.5 text-emerald-600"></i> Lưới Trục



                </button>



                <button onclick="toggle3DWireframe()" id="btn3DWireframe" class="py-1 px-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1 border border-slate-300 transition active:scale-95 cursor-pointer" title="Bật/Tắt Khung Dây">



                  <i data-lucide="eye" class="w-3.5 h-3.5 text-indigo-600"></i> Khung Dây



                </button>



                <button onclick="reset3DCamera()" class="py-1 px-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1 border border-slate-300 transition active:scale-95 cursor-pointer" title="Đặt lại góc nhìn 3D">



                  <i data-lucide="rotate-ccw" class="w-3.5 h-3.5 text-sky-600"></i> Reset Góc Nhìn



                </button>



                <button onclick="deployToVps()" id="btnDeployVps" class="py-1 px-3 rounded-lg bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/30 border border-cyan-400/30 transition active:scale-95 cursor-pointer" title="Deploy toàn bộ trang giữa lên https://mr.pkld.online">



                  <i data-lucide="send" class="w-3.5 h-3.5 text-amber-200"></i> Deploy mr.pkld.online



                </button>



              </div>







              <!-- 3D Beam Hover Tooltip -->



              <div id="etabs3DTooltip" class="absolute hidden bg-slate-900/95 text-white border border-cyan-400/80 rounded-xl p-2.5 shadow-2xl pointer-events-none z-30 text-xs max-w-xs transition-opacity duration-150"></div>







              <!-- 3D Legend Overlay (Collapsible) -->



              <div id="etabs3DLegendCard" class="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md border border-slate-300 rounded-xl shadow-lg z-20 overflow-hidden text-[11px] text-slate-700 pointer-events-auto">



                <button type="button" onclick="toggle3DLegend()" class="w-full flex items-center justify-between gap-3 px-3 py-1.5 font-bold text-slate-900 hover:bg-slate-100/80 transition-colors cursor-pointer select-none">



                  <div class="flex items-center gap-1.5">



                    <span class="w-2 h-2 rounded-full bg-cyan-600"></span>



                    <span>Chú Giải Model 3D:</span>



                  </div>



                  <i id="ico3DLegendToggle" data-lucide="chevron-up" class="w-3.5 h-3.5 text-slate-500 transition-transform duration-200"></i>



                </button>



                <div id="body3DLegend" class="px-3 pb-2 pt-0.5 space-y-1 border-t border-slate-100">



                  <div class="flex items-center gap-2"><span class="w-3 h-3 bg-cyan-500 rounded-sm shrink-0"></span> Dầm Khung (Bấm trực tiếp để chọn cốt thép)</div>



                  <div class="flex items-center gap-2"><span class="w-3 h-3 bg-indigo-500 rounded-sm shrink-0"></span> Cột Bê Tông (Solid Column)</div>



                  <div class="flex items-center gap-2"><span class="w-3 h-3 bg-red-500 rounded-sm shrink-0"></span> Sàn & Bản Thang (Đã đóng kín ban công trục 7)</div>



                  <div class="flex items-center gap-2"><span class="w-3 h-1 bg-amber-500 rounded-sm shrink-0"></span> Biểu Đồ Moment M33 Uốn Dầm</div>



                </div>



              </div>



            </div>



          </div>







          <!-- SUB-PANE 3: BẢNG THÔNG SỐ CỐT THÉP & CHỌN THÉP TỪNG DẦM (TCVN) -->



          <div id="subpane-etabs-rebar" class="etabs-subpane hidden space-y-3">



            



            <!-- Filter Bar -->



            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">



              <div class="flex items-center gap-3">



                <div>



                  <label class="text-[11px] font-bold text-slate-500 block">Lọc theo Tầng:</label>



                  <select id="rebarFilterStory" onchange="filterRebarTable()" class="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-600 cursor-pointer">



                    <option value="ALL">Tất cả các tầng (103 dầm)</option>



                    <option value="T4">Tầng 4 (Sân Thượng / Mái)</option>



                    <option value="T3">Tầng 3</option>



                    <option value="T2">Tầng 2</option>



                    <option value="T1">Tầng 1</option>



                  </select>



                </div>



                <div>



                  <label class="text-[11px] font-bold text-slate-500 block">Tìm dầm dài / tiết diện:</label>



                  <input type="text" id="rebarSearchInput" oninput="filterRebarTable()" placeholder="VD: DX1, DY2, 200x400..." class="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-600">



                </div>



                <div>



                  <label class="text-[11px] font-bold text-slate-500 block">Lọc an toàn TCVN:</label>



                  <button type="button" id="btnFilterFailingRebar" onclick="toggleFilterFailingRebar()" class="px-3 py-1.5 rounded-lg text-xs font-bold border border-rose-300 bg-rose-50 text-rose-800 hover:bg-rose-100 transition flex items-center gap-1.5 cursor-pointer shadow-2xs" title="Bấm để chỉ hiển thị các dầm chưa đạt yêu cầu">



                    <span class="w-2 h-2 rounded-full bg-rose-500"></span>



                    <span>Chỉ xem dầm chưa đạt</span>



                    <strong id="tableFailCountBadge" class="px-1.5 py-0.2 bg-rose-200 text-rose-950 rounded-full font-mono text-[10px]">0</strong>



                  </button>



                </div>



              </div>







              <!-- Export & Database Buttons -->



              <div class="flex items-center gap-2 flex-wrap">



                <div id="tableDbBadge" class="text-[10px] px-2.5 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold flex items-center gap-1.5 shadow-2xs" title="Trạng thái lưu trữ dữ liệu lâu dài">



                  <i data-lucide="database" class="w-3.5 h-3.5 text-indigo-600"></i>



                  <span id="tableDbText">DB: SQLite</span>



                </div>



                <button type="button" onclick="saveAllBeamsToDb()" class="py-1.5 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition cursor-pointer" title="Lưu toàn bộ thiết kế dầm hiện tại vào CSDL PostgreSQL / SQLite">



                  <i data-lucide="save" class="w-3.5 h-3.5"></i> Lưu CSDL Tất Cả



                </button>



                <button type="button" onclick="exportAllBeamsPdf()" class="py-1.5 px-3 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition cursor-pointer" title="Xuất toàn bộ dầm ra file PDF khổ A3 chuẩn TCVN">



                  <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Xuất Tất Cả PDF



                </button>



                <button type="button" onclick="exportAllBeamsDxf()" class="py-1.5 px-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition cursor-pointer" title="Xuất toàn bộ dầm ra file DXF AutoCAD R2010 theo layer & nét in chuẩn">



                  <i data-lucide="layers" class="w-3.5 h-3.5"></i> Xuất Tất Cả DXF



                </button>



                <button onclick="exportRebarCSV()" class="py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition cursor-pointer">



                  <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5"></i> Xuất CSV (Excel)



                </button>



                <button onclick="printRebarTable()" class="py-1.5 px-3 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer">



                  <i data-lucide="printer" class="w-3.5 h-3.5"></i> In Bảng



                </button>



              </div>



            </div>







            <!-- Table Container -->



            <div class="overflow-x-auto rounded-xl border border-slate-200 shadow-sm max-h-[500px]">



              <table id="rebarTable" class="w-full text-left text-xs border-collapse">



                <thead class="bg-slate-100 text-slate-700 font-bold uppercase text-[10px] tracking-wider sticky top-0 z-10 shadow-sm">



                  <tr class="divide-x divide-slate-200">



                    <th class="p-2.5 text-center">Tầng</th>



                    <th class="p-2.5">Dầm Dài (DX/DY)</th>



                    <th class="p-2.5">Tiết Diện</th>



                    <th class="p-2.5 text-right">Nhịp L (m)</th>



                    <th class="p-2.5 text-right bg-amber-50 text-amber-900">As Gối T (cm²)</th>



                    <th class="p-2.5 text-right bg-amber-50 text-amber-900">As Bụng (cm²)</th>



                    <th class="p-2.5 text-right bg-amber-50 text-amber-900">As Gối P (cm²)</th>



                    <th class="p-2.5 text-right bg-sky-50 text-sky-900">As Đai (cm²/m)</th>



                    <th class="p-2.5 bg-indigo-50 text-indigo-900 font-extrabold">Cốt Thép Chọn (Gối T / Nhịp / Gối P)</th>



                    <th class="p-2.5 bg-indigo-50 text-indigo-900 font-extrabold text-center">Đai Chọn</th>



                    <th class="p-2.5 text-center">Trạng Thái</th>



                  </tr>



                </thead>



                <tbody id="rebarTableBody" class="divide-y divide-slate-200 font-mono text-[11px] bg-white">



                  <!-- Loaded via JS -->



                </tbody>



              </table>



            </div>







          </div>







          <!-- SUB-PANE 4: BẢN VẼ CỘT (GRID 18 CỘT × 4 TẦNG) -->



          <div id="subpane-etabs-column-cad" class="etabs-subpane hidden space-y-3">



            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">



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



            <div class="relative bg-slate-200/60 rounded-2xl border border-slate-300 overflow-hidden h-[680px]">



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







          <!-- SUB-PANE 5: BẢN VẼ ĐÀ KIỀNG (TRỤC A, B, C - CHỊU PHẢN LỰC ĐẤT) -->



          <div id="subpane-etabs-tie-beam-cad" class="etabs-subpane hidden space-y-3">



            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">



              <div class="flex items-center gap-2.5 flex-wrap">



                <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5 shrink-0">



                  <i data-lucide="git-branch" class="w-4 h-4 text-emerald-600"></i> Bản Vẽ Chi Tiết Đà Kiềng Trục A, B, C (Tầng 1 / Móng):



                </span>



                <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-extrabold font-mono">3 Tuyến • Trục A, B, C</span>



                <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-bold flex items-center gap-1">



                  <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> Phản Lực Đất Đẩy Lên (q_đất &gt; 0)



                </span>



                <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">TCVN 5574:2018</span>



              </div>







              <div class="flex items-center gap-2 flex-wrap">



                <button type="button" onclick="exportTieBeamSheetPdf()" class="py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">



                  <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Xuất PDF Đà Kiềng



                </button>



                <button type="button" onclick="exportTieBeamSheetDxf()" class="py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">



                  <i data-lucide="download" class="w-3.5 h-3.5"></i> Xuất DXF Đà Kiềng



                </button>



                <button type="button" onclick="openTieBeamDrawingModal()" class="py-1.5 px-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center gap-1.5 border border-indigo-200 transition cursor-pointer">



                  <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Phóng To Toàn Màn Hình



                </button>



              </div>



            </div>







            <!-- Canvas Container -->



            <div class="relative bg-slate-200/60 rounded-2xl border border-slate-300 overflow-hidden h-[680px]">



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



                <span id="tabTieBeamCadHoverText">Rê chuột vào nhịp đà kiềng để xem quy cách thép</span>



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







              <!-- Mode Switcher & Tools -->



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







            <!-- Tab Body -->



            <div class="w-full bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-inner">



              <!-- View 1: HD Interactive Canvas -->



              <div id="gnTabPane_hd" class="relative w-full h-[720px] bg-slate-900">



                <canvas id="tabGnInteractiveCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>



                



                <!-- HUD Controls -->



                <div class="absolute bottom-4 left-4 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-700 shadow-xl text-white">



                  <button type="button" onclick="zoomNotesCanvas(1.2, 'tabGnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>



                  <button type="button" onclick="zoomNotesCanvas(0.833, 'tabGnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>



                  <button type="button" onclick="resetNotesCanvas100('tabGnInteractiveCanvas')" class="px-2.5 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">100%</button>



                  <button type="button" onclick="fitNotesCanvas('tabGnInteractiveCanvas')" class="px-3 h-8 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">Vừa khung</button>



                  <span id="gnTabZoomBadge" class="text-xs font-mono font-bold text-amber-400 px-2 border-l border-slate-700">100%</span>



                  <span class="text-[10px] text-slate-400 pl-2 border-l border-slate-700 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để Pan • Double click để vừa khung</span>



                </div>



              </div>







              <!-- View 2: Native PDF Iframe -->



              <div id="gnTabPane_pdf" class="hidden w-full h-[720px] bg-slate-900">



                <iframe id="gnTabPdfIframe" src="about:blank" data-src="/static/general_notes_drawing.pdf#view=FitH" class="w-full h-full border-0"></iframe>



              </div>







              <!-- View 3: Structured Text Clauses -->



              <div id="gnTabPane_text" class="hidden w-full h-[720px] bg-white p-6 overflow-y-auto space-y-6 text-slate-800">



                <div class="flex items-center justify-between border-b pb-4">



                  <div>



                    <h3 class="text-base font-extrabold text-slate-900 flex items-center gap-2">



                      📋 NỘI DUNG BẢN VẼ GHI CHÚ CHUNG KẾT CẤU



                      <span class="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">TCVN 5574-2012</span>



                    </h3>



                    <p class="text-xs text-slate-500 mt-1">Nguồn: Documents\\plot\\1020/Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf</p>



                  </div>



                  <button type="button" onclick="copyNoteSection('gnTabClausesList')" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer">



                    <i data-lucide="copy" class="w-3.5 h-3.5"></i> Sao chép toàn bộ



                  </button>



                </div>







                <!-- Section 1: Concrete Cover Table -->



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







                <!-- Section 2: Materials specification -->



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







                <!-- Section 3: Full Clauses list -->



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







        

<!-- CỤM ĐIỀU HƯỚNG & THAO TÁC 2 CỘT GỌN GÀNG (ĐƯA XUỐNG DƯỚI CANVAS 3D)    -->
          <!-- ==================================================================== -->
          <div class="border-t border-slate-200 pt-3.5 mt-2 grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-stretch">

            <!-- CỘT 1 (Trái): THÔNG TIN MODEL & 6 CHẾ ĐỘ XEM (lg:col-span-7) -->
            <div class="bg-slate-50/90 border border-slate-200/90 rounded-2xl p-3.5 flex flex-col justify-between gap-3 shadow-xs">
              <div class="flex items-center gap-2.5">
                <span class="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 shrink-0">
                  <i data-lucide="layers" class="w-5 h-5"></i>
                </span>
                <div class="min-w-0">
                  <h2 class="text-sm font-bold text-slate-900 flex items-center gap-2 flex-wrap">
                    <span>Hồ Sơ Kết Cấu Dầm & Cốt Thép ETABS</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">TCVN 5574-2012</span>
                  </h2>
                  <p class="text-xs text-slate-500 mt-0.5 truncate">
                    Model: <span class="font-mono font-semibold text-slate-700">CAI_TAO_PHUONG_AN_B.EDB</span> (103 Dầm • 56 Cột • 5 Tầng)
                  </p>
                </div>
              </div>

              <!-- Segmented Sub-Tab Switcher Bar (1-6) -->
              <div class="p-1 bg-slate-200/80 rounded-xl border border-slate-300/80 flex flex-wrap items-center gap-1">
                <button type="button" onclick="switchEtabsSubTab('etabs-3d')" id="subtab-btn-3d" class="etabs-subtab-btn py-1.5 px-3 rounded-lg font-bold text-xs flex items-center gap-1.5 bg-indigo-600 text-white shadow-xs transition-all duration-150 cursor-pointer" title="(2) Mô hình 3D Solid Boxes kết cấu">
                  <i data-lucide="box" class="w-3.5 h-3.5"></i> (2) Model 3D
                </button>
                <button type="button" onclick="switchEtabsSubTab('etabs-2d')" id="subtab-btn-2d" class="etabs-subtab-btn py-1.5 px-3 rounded-lg font-semibold text-xs flex items-center gap-1.5 text-slate-700 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer" title="(1) Mặt bằng dầm 2D từng tầng">
                  <i data-lucide="map" class="w-3.5 h-3.5"></i> (1) Mặt Bằng 2D
                </button>
                <button type="button" onclick="switchEtabsSubTab('etabs-rebar')" id="subtab-btn-rebar" class="etabs-subtab-btn py-1.5 px-3 rounded-lg font-semibold text-xs flex items-center gap-1.5 text-slate-700 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer" title="(3) Bảng khối lượng thép dầm">
                  <i data-lucide="table-2" class="w-3.5 h-3.5"></i> (3) Bảng Thép
                </button>
                <button type="button" onclick="switchEtabsSubTab('etabs-column-cad')" id="subtab-btn-column-cad" class="etabs-subtab-btn py-1.5 px-3 rounded-lg font-semibold text-xs flex items-center gap-1.5 text-slate-700 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer" title="(4) Bản vẽ mặt cắt cột 15×4">
                  <i data-lucide="columns" class="w-3.5 h-3.5 text-amber-500"></i> (4) Bản Vẽ Cột
                </button>
                <button type="button" onclick="switchEtabsSubTab('etabs-tie-beam-cad')" id="subtab-btn-tie-beam-cad" class="etabs-subtab-btn py-1.5 px-3 rounded-lg font-semibold text-xs flex items-center gap-1.5 text-slate-700 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer" title="(5) Bản vẽ đà kiềng móng">
                  <i data-lucide="git-branch" class="w-3.5 h-3.5 text-emerald-600"></i> (5) Đà Kiềng
                </button>

                <!-- (6) DROPDOWN: BẢNG GHI CHÚ CHUNG KẾT CẤU (PLOT 1020) -->
                <div class="relative inline-block text-left" id="dropdown-notes-container">
                  <button type="button" onclick="toggleNotesDropdown(event)" id="subtab-btn-notes" class="etabs-subtab-btn py-1.5 px-3 rounded-lg font-semibold text-xs flex items-center gap-1 text-slate-700 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer" title="Xem Bảng Ghi Chú Chung Kết Cấu (Plot 1020)">
                    <i data-lucide="file-text" class="w-3.5 h-3.5 text-orange-500"></i>
                    <span>(6) Ghi Chú Chung</span>
                    <i data-lucide="chevron-down" class="w-3 h-3 text-slate-400 transition-transform duration-200" id="notes-dropdown-chevron"></i>
                  </button>

                  <!-- Dropdown Menu Box (Upward pop) -->
                  <div id="notes-dropdown-menu" class="hidden absolute left-0 bottom-full mb-2 w-72 rounded-2xl bg-white/95 backdrop-blur-md shadow-2xl border border-slate-200/90 p-1.5 z-50 ring-1 ring-black/5 divide-y divide-slate-100 animate-in fade-in zoom-in-95 duration-150">
                    <div class="px-3 py-2 bg-gradient-to-r from-amber-50 to-orange-50/60 rounded-xl mb-1 border border-amber-100">
                      <div class="text-[10px] font-extrabold uppercase tracking-wider text-amber-800 flex items-center justify-between">
                        <span class="flex items-center gap-1"><i data-lucide="file-text" class="w-3.5 h-3.5 text-amber-600"></i> Ghi Chú Chung Kết Cấu</span>
                        <span class="text-[9px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 font-bold font-mono">TCVN</span>
                      </div>
                      <div class="text-[11px] text-slate-500 font-mono truncate mt-0.5" title="Plot_20261020_082443_WIN_1016103.pdf">
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
                          <div class="text-[10px] text-slate-400 truncate">Mở Documents/plot/1020</div>
                        </div>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- CỘT 2 (Phải): THAO TÁC NHANH, BÁO CÁO & PHÓNG TO MODAL (lg:col-span-5) -->
            <div class="bg-slate-50/90 border border-slate-200/90 rounded-2xl p-3.5 flex flex-col justify-between gap-3 shadow-xs">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                  <i data-lucide="zap" class="w-4 h-4 text-amber-500"></i> Thao Tác & Xem Toàn Cảnh
                </span>
                <div class="flex items-center gap-1.5">
                  <a href="/3d" class="text-[11px] font-mono text-indigo-700 font-bold bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded-full border border-indigo-200 flex items-center gap-1 transition" title="Mở route riêng /3d toàn màn hình (Minimin sidebars)">
                    <i data-lucide="maximize" class="w-3 h-3"></i> Route /3d
                  </a>
                  <span class="text-[11px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> 103 Dầm • 56 Cột
                  </span>
                </div>
              </div>

              <!-- Action Buttons Grid -->
              <div class="grid grid-cols-2 gap-2">
                <button type="button" onclick="openGeneralNotesModal()" class="py-2 px-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs transition active:scale-95 cursor-pointer" title="Xem Bảng Ghi Chú Chung Kết Cấu (Plot 1020)">
                  <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Ghi Chú Chung
                </button>
                <button type="button" onclick="openColumnDrawingModal()" class="py-2 px-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs transition active:scale-95 cursor-pointer" title="Xem Bản Vẽ Tiết Diện Cột toàn nhà (Grid 15 Cột × 4 Tầng)">
                  <i data-lucide="columns" class="w-3.5 h-3.5"></i> Bản Vẽ Cột (15×4)
                </button>
                <button type="button" onclick="refreshEtabsDataLive()" id="btnRefreshEtabs" class="py-2 px-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 font-semibold text-xs flex items-center justify-center gap-1.5 shadow-xs transition cursor-pointer" title="Làm mới lại dữ liệu trực tiếp từ ETABS">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-indigo-600"></i> Làm mới EDB
                </button>
                <button type="button" onclick="openEtabsHub('modal')" class="py-2 px-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs transition cursor-pointer" title="Phóng to Modal 3D toàn màn hình">
                  <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Phóng to Modal
                </button>
              </div>
            </div>
          </div>

        </div>







        <!-- ==================================================================== -->



        <!-- ==================================================================== -->



        <!-- MODAL: CHI TIẾT BẢN VẼ DẦM, MẶT CẮT NGANG/DỌC & DẦM LIÊN TỤC         -->



        <!-- ==================================================================== -->



        



  <!-- ==================================================================== -->



  <!-- MODAL: BẢNG GHI CHÚ CHUNG KẾT CẤU (PLOT 1020 FULLSCREEN VIEWER)      -->



  <!-- ==================================================================== -->



  <div id="modalGeneralNotes" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-2 sm:p-4">



    <div class="relative bg-white text-slate-800 w-[96vw] max-w-[1550px] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150 h-[95vh]">



      



      <!-- Modal Header -->



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







        <!-- Mode Switcher & Tools -->



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



          <button type="button" onclick="openGeneralNotesFolder()" class="py-1.5 px-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1 shadow-2xs transition cursor-pointer" title="Mở thư mục plot\1020">



            <i data-lucide="folder" class="w-3.5 h-3.5 text-amber-600"></i> Thư mục



          </button>



          <button type="button" onclick="closeGeneralNotesModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng modal">



            <i data-lucide="x" class="w-5 h-5"></i>



          </button>



        </div>



      </div>







      <!-- Modal Body -->



      <div class="flex-1 overflow-hidden p-3 bg-slate-950 flex flex-col">



        <!-- View 1: HD Canvas -->



        <div id="gnModalPane_hd" class="relative w-full h-full rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex-1">



          <canvas id="gnInteractiveCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>



          



          <!-- HUD Controls -->



          <div class="absolute bottom-4 left-4 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-700 shadow-xl text-white">



            <button type="button" onclick="zoomNotesCanvas(1.2, 'gnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Phóng to">+</button>



            <button type="button" onclick="zoomNotesCanvas(0.833, 'gnInteractiveCanvas')" class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center transition active:scale-95 cursor-pointer" title="Thu nhỏ">-</button>



            <button type="button" onclick="resetNotesCanvas100('gnInteractiveCanvas')" class="px-2.5 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">100%</button>



            <button type="button" onclick="fitNotesCanvas('gnInteractiveCanvas')" class="px-3 h-8 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center transition active:scale-95 cursor-pointer">Vừa khung</button>



            <span id="gnModalZoomBadge" class="text-xs font-mono font-bold text-amber-400 px-2 border-l border-slate-700">100%</span>



            <span class="text-[10px] text-slate-400 pl-2 border-l border-slate-700 hidden sm:inline">Cuộn chuột để zoom • Kéo chuột để pan • Double click để vừa khung</span>



          </div>



        </div>







        <!-- View 2: Native PDF Iframe -->



        <div id="gnModalPane_pdf" class="hidden w-full h-full rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex-1">



          <iframe id="gnModalPdfIframe" src="about:blank" data-src="/static/general_notes_drawing.pdf#view=FitH" class="w-full h-full border-0"></iframe>



        </div>







        <!-- View 3: Structured Text Clauses -->



        <div id="gnModalPane_text" class="hidden w-full h-full rounded-2xl bg-white p-6 overflow-y-auto flex-1 space-y-6">



          <div class="flex items-center justify-between border-b pb-4">



            <div>



              <h3 class="text-base font-extrabold text-slate-900 flex items-center gap-2">



                📋 NỘI DUNG BẢN VẼ GHI CHÚ CHUNG KẾT CẤU



                <span class="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">TCVN 5574-2012</span>



              </h3>



              <p class="text-xs text-slate-500 mt-1">Nguồn: Documents\\plot\\1020/Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf</p>



            </div>



            <button type="button" onclick="copyNoteSection('gnModalClausesList')" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer">



              <i data-lucide="copy" class="w-3.5 h-3.5"></i> Sao chép toàn bộ



            </button>



          </div>







          <!-- Section 1: Concrete Cover Table -->



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







          <!-- Section 2: Materials specification -->



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







          <!-- Section 3: Full Clauses list -->



          <div id="gnModalClausesList" class="space-y-2.5 text-xs text-slate-700 leading-relaxed font-sans">



            <div class="font-bold text-slate-900 border-b pb-1 text-sm">I. 24 ĐIỀU QUY ĐỊNH THIẾT KẾ & THI CÔNG:</div>



            <p><strong>01.</strong> Việc thiết kế dựa trên TCVN hiện hành.</p>



            <p><strong>02.</strong> Những bản vẽ kết cấu cần xem đồng thời với bản vẽ kiến trúc tương ứng.</p>



            <p><strong>03.</strong> Nếu có bất kỳ thông tin nào không hợp lý, đơn vị thi công cần liên hệ ngay với đơn vị thiết kế và TVXD để hiệu chỉnh chứ không tự ý sửa chữa.</p>



            <p><strong>04.</strong> Cốt hoàn thiện được xét theo bản vẽ kiến trúc.</p>



            <p><strong>05.</strong> Tất cả các đơn vị ghi trong bản vẽ là mm, nếu như không có ghi chú nào khác.</p>



            <p><strong>06.</strong> Các sai số về kích thước, độ lệch, độ võng... cho phép trước và sau khi thi công cần tuân theo TCVN hiện hành.</p>



            <p><strong>07.</strong> Áp lực gió tiêu chuẩn: <code class="px-1.5 py-0.5 bg-slate-100 rounded text-indigo-700 font-bold">qtc = 80 kg/m²</code>.</p>



            <p><strong>08.</strong> Chất lượng bê tông khi thi công cần được kiểm tra đúng điều kiện kỹ thuật yêu cầu của TCVN hiện hành.</p>



            <p><strong>09.</strong> Cát dùng làm bê tông phải thỏa mãn các yêu cầu TCVN hiện hành.</p>



            <p><strong>10.</strong> Nước dùng để trộn và dưỡng hộ bê tông phải đảm bảo yêu cầu của TCVN hiện hành.</p>



            <p><strong>11.</strong> Không sử dụng các loại phụ gia không rõ nguồn gốc trong quá trình chế tạo bê tông.</p>



            <p><strong>12.</strong> Thi công móng, cột, dầm, sàn phải dựa theo TCVN hiện hành.</p>



            <p><strong>13.</strong> Mạch ngừng thi công phải tuân theo TCVN hiện hành.</p>



            <p><strong>14.</strong> Yêu cầu chống thấm cột, dầm, sàn dưới cao trình &plusmn;0.000.</p>



            <p><strong>15.</strong> Dọc theo chiều cao cột có tường xây đặt thép râu neo vào cột: <strong>2&phi;6</strong> (với tường dày &ge; 200 mm), <strong>1&phi;6</strong> (với tường dày 100 mm), bước <strong>a400</strong> theo chiều cao cột.</p>



            <p><strong>16.</strong> Cốt thép và bê tông: &phi; &le; 10 (Ra = Ra' = 2300 kg/cm²); &phi; &gt; 10 (Ra = Ra' = 3650 kg/cm²); Bê tông #300 (Rn = 130 kg/cm², Rk = 10 kg/cm²); Bê tông #400 (Rn = 170 kg/cm², Rk = 12 kg/cm²).</p>



            <p><strong>17.</strong> Khi thi công cột, đà sàn kết hợp điện, nước, điện lạnh để lắp đặt các đường ống cấp thoát nước, ống dẫn điện.</p>



            <p><strong>18.</strong> Có thể nối thép cột tại bất kỳ vị trí nào nhưng <strong>không được nối quá 50%</strong> lượng thép trong cùng một mặt cắt - nối thép so le.</p>



            <p><strong>19.</strong> Trường hợp đặt các đường ống ẩn trong kết cấu thì phải đặt tại vị trí có lực cắt và mô men tương đối nhỏ, đồng thời gia cường thép tại vị trí đó.</p>



            <p><strong>20.</strong> Số lượng ống luồn lắp đặt ẩn trong kết cấu phải &lt; 30% tiết diện.</p>



            <p><strong>21.</strong> Thống nhất cao độ kết cấu thấp hơn cao độ hoàn thiện là <strong>50 mm</strong>.</p>



            <p><strong>22.</strong> Quy định neo thép, uốn cốt thép dầm: đoạn neo dầm vào cột min 30d đến 40d.</p>



            <p><strong>23.</strong> Quy định bổ trụ và giằng tường: tường dài &gt; 4m bố trí bổ trụ BTCT 100&times;200 hoặc 200&times;200, tường cao &gt; 3.5m bổ sung giằng tường.</p>



            <p><strong>24.</strong> Tất cả tường xây liên kết với bê tông đều phải được đóng lưới tô hoàn thiện chống nứt.</p>



          </div>



        </div>



      </div>







    </div>



  </div>











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



                <!-- ========================================================== -->



                <!-- HỒ SƠ DẦM: DROPDOWN PANEL THEO CHIỀU DỌC (HOVER HEADER)     -->



                <!-- ========================================================== -->



                <div class="relative group select-none" id="brmHoSoDamWrapper">



                  <!-- Header Trigger Button (gọn gàng trên header bar) -->



                  <button type="button" id="brmHoSoDamTrigger" class="flex items-center gap-1.5 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-2xl border border-slate-300 shadow-2xs cursor-pointer transition">



                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>



                    <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">Hồ sơ dầm:</span>



                    <span id="brmHeaderSummaryPass" class="px-2 py-0.2 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300 text-[11px] font-extrabold font-mono">--/-- Đạt</span>



                    <svg class="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 group-hover:rotate-180 transition-transform duration-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>



                  </button>







                  <!-- Vertical Dropdown Panel (xổ xuống khi hover header hoặc khi đang focus input) -->



                  <div id="brmHoSoDamDropdown" class="absolute top-full left-0 pt-1.5 z-50 hidden group-hover:block group-focus-within:block transition-all duration-150">



                    <div class="w-88 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-300/80 p-3.5 space-y-2.5 text-xs text-slate-800 animate-in fade-in zoom-in-95 duration-100">



                      



                      <!-- Header Panel -->



                      <div class="flex items-center justify-between pb-2 border-b border-slate-100">



                        <div class="flex items-center gap-2">



                          <div class="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-200">



                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>



                          </div>



                          <div>



                            <h4 class="font-bold text-slate-900 text-xs">HỒ SƠ CỐT THÉP DẦM</h4>



                            <p class="text-[10px] text-slate-500 font-medium">TCVN 5574-2012 • 60 dầm dài liên tục</p>



                          </div>



                        </div>



                        <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">Toàn dự án</span>



                      </div>







                      <!-- Danh sách thống kê theo chiều dọc -->



                      <div class="space-y-1.5">







                        <!-- 1. Dầm Đạt chuẩn TCVN -->



                        <div class="p-2 rounded-xl bg-emerald-50/80 border border-emerald-200 flex items-center justify-between shadow-2xs">



                          <div class="flex items-center gap-2">



                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></span>



                            <span class="font-semibold text-emerald-900">Dầm Đạt chuẩn TCVN:</span>



                          </div>



                          <strong id="brmHeaderPassCount" class="font-extrabold text-emerald-950 font-mono text-sm">--/--</strong>



                        </div>







                        <!-- 2. Thép tăng cường Lưng (Accordion) -->



                        <div class="rounded-xl border border-purple-200 bg-purple-50/50 overflow-hidden shadow-2xs">



                          <div onclick="toggleTcLungAccordion()" class="p-2 flex items-center justify-between cursor-pointer hover:bg-purple-100/70 transition select-none">



                            <div class="flex items-center gap-2">



                              <span class="w-2.5 h-2.5 rounded-full bg-purple-600 shrink-0"></span>



                              <span class="font-semibold text-purple-900">Thép TC Lưng (Gối):</span>



                            </div>



                            <div class="flex items-center gap-1.5">



                              <strong id="brmHeaderTcLungCount" class="font-extrabold text-purple-950 font-mono text-sm">--</strong>



                              <svg id="brmTcLungArrow" class="w-3.5 h-3.5 text-purple-500 transition-transform duration-150" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="6 9 12 15 18 9"/></svg>



                            </div>



                          </div>



                          <div id="brmTcLungListContainer" class="hidden px-2 pb-2 pt-1 border-t border-purple-100 bg-white">



                            <div class="flex items-center justify-between pb-1 mb-1 text-[10px] text-slate-400 font-bold border-b border-slate-50">



                              <span>Danh sách dầm có thép TC Lưng (<span id="brmTcLungMenuCount">0</span>)</span>



                              <span>Click để chuyển tới</span>



                            </div>



                            <div id="brmTcLungList" class="max-h-36 overflow-y-auto space-y-1 divide-y divide-slate-100 pr-1 text-[11px]"></div>



                          </div>



                        </div>







                        <!-- 3. Thép tăng cường Bụng (Accordion) -->



                        <div class="rounded-xl border border-amber-200 bg-amber-50/50 overflow-hidden shadow-2xs">



                          <div onclick="toggleTcBungAccordion()" class="p-2 flex items-center justify-between cursor-pointer hover:bg-amber-100/70 transition select-none">



                            <div class="flex items-center gap-2">



                              <span class="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0"></span>



                              <span class="font-semibold text-amber-900">Thép TC Bụng (Nhịp):</span>



                            </div>



                            <div class="flex items-center gap-1.5">



                              <strong id="brmHeaderTcBungCount" class="font-extrabold text-amber-950 font-mono text-sm">--</strong>



                              <svg id="brmTcBungArrow" class="w-3.5 h-3.5 text-amber-500 transition-transform duration-150" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="6 9 12 15 18 9"/></svg>



                            </div>



                          </div>



                          <div id="brmTcBungListContainer" class="hidden px-2 pb-2 pt-1 border-t border-amber-100 bg-white">



                            <div class="flex items-center justify-between pb-1 mb-1 text-[10px] text-slate-400 font-bold border-b border-slate-50">



                              <span>Danh sách dầm có thép TC Bụng (<span id="brmTcBungMenuCount">0</span>)</span>



                              <span>Click để chuyển tới</span>



                            </div>



                            <div id="brmTcBungList" class="max-h-36 overflow-y-auto space-y-1 divide-y divide-slate-100 pr-1 text-[11px]"></div>



                          </div>



                        </div>







                        <!-- 4. Dầm Không Đạt chuẩn (Accordion) -->



                        <div class="rounded-xl border border-rose-200 bg-rose-50/50 overflow-hidden shadow-2xs">



                          <div onclick="toggleFailAccordion()" class="p-2 flex items-center justify-between cursor-pointer hover:bg-rose-100/70 transition select-none">



                            <div class="flex items-center gap-2">



                              <span class="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0"></span>



                              <span class="font-semibold text-rose-900">Không đạt chuẩn:</span>



                            </div>



                            <div class="flex items-center gap-1.5">



                              <strong id="brmHeaderFailCount" class="font-extrabold text-rose-950 font-mono text-sm">--/--</strong>



                              <svg id="brmFailArrow" class="w-3.5 h-3.5 text-rose-500 transition-transform duration-150" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="6 9 12 15 18 9"/></svg>



                            </div>



                          </div>



                          <div id="brmFailListContainer" class="hidden px-2 pb-2 pt-1 border-t border-rose-100 bg-white">



                            <div id="brmFailingBeamsList" class="max-h-36 overflow-y-auto space-y-1 divide-y divide-slate-100 pr-1 text-[11px]"></div>



                            <div class="pt-1.5 mt-1 border-t border-slate-100">



                              <button type="button" onclick="jumpToNextFailingBeam()" class="w-full py-1.5 px-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-[11px] flex items-center justify-center gap-1.5 shadow-xs transition cursor-pointer">



                                <span>Chuyển tới dầm tiếp theo</span>



                                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>



                              </button>



                            </div>



                          </div>



                        </div>







                        <!-- 5. Thống Kê Thép Tăng Cường < [INPUT] mm (Accordion) -->



                        <div class="rounded-xl border border-indigo-200 bg-indigo-50/60 overflow-hidden shadow-2xs">



                          <div class="p-2 space-y-1.5">



                            <div class="flex items-center justify-between gap-1">



                              <div class="flex items-center gap-1.5 min-w-0">



                                <span class="w-2.5 h-2.5 rounded-full bg-indigo-600 shrink-0"></span>



                                <span class="font-semibold text-indigo-900 whitespace-nowrap">Thép TC &lt;</span>



                                <div class="inline-flex items-center bg-white border border-indigo-300 rounded-lg px-1.5 py-0.5 shadow-2xs">



                                  <input type="number" id="brmShortRebarThreshold" value="600" min="100" max="5000" step="50"



                                    oninput="onShortRebarThresholdChange(this.value)"



                                    onclick="event.stopPropagation()"



                                    class="w-14 text-center text-xs font-bold font-mono text-indigo-950 focus:outline-none focus:ring-1 focus:ring-indigo-500"



                                    title="Nhập chiều dài giới hạn thép tăng cường (mm) để thống kê">



                                  <span class="text-[10px] text-slate-400 font-bold ml-0.5">mm</span>



                                </div>



                              </div>



                              <div class="flex items-center gap-1">



                                <span id="brmShortRebarBadge" onclick="toggleShortRebarAccordion()" class="font-extrabold text-indigo-950 font-mono text-sm bg-indigo-100 hover:bg-indigo-200 px-2 py-0.5 rounded-md border border-indigo-300 cursor-pointer transition select-none flex items-center gap-1" title="Bấm để xem danh sách dầm">



                                  <span id="brmShortRebarCount">--</span>



                                  <svg id="brmShortRebarArrow" class="w-3.5 h-3.5 text-indigo-600 transition-transform duration-150" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="6 9 12 15 18 9"/></svg>



                                </span>



                              </div>



                            </div>



                            <p class="text-[10px] text-indigo-700/80 leading-tight">Chiều dài thực tế thanh thép tăng cường gối/bụng &lt; ngưỡng đã nhập</p>



                          </div>



                          <div id="brmShortRebarListContainer" class="hidden px-2 pb-2 pt-1 border-t border-indigo-100 bg-white">



                            <div class="flex items-center justify-between pb-1 mb-1 text-[10px] text-slate-400 font-bold border-b border-slate-50">



                              <span>Danh sách dầm thép TC &lt; <span id="brmShortRebarThresholdLabel">600</span>mm</span>



                              <span>Click để chuyển tới</span>



                            </div>



                            <div id="brmShortRebarList" class="max-h-36 overflow-y-auto space-y-1 divide-y divide-slate-100 pr-1 text-[11px]"></div>



                          </div>



                        </div>







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







                <!-- Nút Xem Bản Vẽ Cột (15 Cột × 4 Tầng) -->



                <button type="button" onclick="openColumnDrawingModal()" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 rounded-2xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-2xs" title="Xem Bản Vẽ Tiết Diện Cột toàn nhà (Grid 15 Cột × 4 Tầng)">



                  <i data-lucide="columns" class="w-3.5 h-3.5 text-amber-600"></i>



                  <span>Bản Vẽ Cột (15×4)</span>



                </button>







                <!-- Nút Xem Bản Vẽ Đà Kiềng (Trục A, B, C) -->



                <button type="button" onclick="openTieBeamDrawingModal()" class="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-900 rounded-2xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-2xs" title="Xem Bản Vẽ Chi Tiết Đà Kiềng Trục A, B, C (Chịu Phản Lực Đất Đẩy Lên)">



                  <i data-lucide="git-branch" class="w-3.5 h-3.5 text-emerald-600"></i>



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



                  <div id="brmCadSvgContainer" class="w-full h-full absolute inset-0 pointer-events-none hidden"></div>







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



                      <button type="button" onclick="openCadLayerSettingsModal()" class="text-[10px] px-2 py-0.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold border border-indigo-200 hover:border-indigo-300 transition shadow-2xs flex items-center gap-1 cursor-pointer whitespace-nowrap shrink-0" title="Cấu hình Màu sắc ACI, Kiểu nét và Độ dày các Layer CAD">



                        <svg class="w-3 h-3 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>



                        <span>Setting Layer</span>



                      </button>



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







                <!-- Nút Setting Layer CAD -->



                <button type="button" onclick="openCadLayerSettingsModal()" class="py-2 px-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1 border border-slate-300 transition active:scale-95 cursor-pointer shrink-0" title="Cấu hình Màu sắc ACI, Kiểu nét và Độ dày các Layer AutoCAD">



                  <svg class="w-3.5 h-3.5 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>



                  <span>Setting Layer</span>



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



        <!-- MODAL: THIẾT LẬP LAYER XUẤT CAD (AUTOCAD DXF / DWG)                    -->



        <!-- ==================================================================== -->



        <div id="cadLayerSettingsModal" class="fixed inset-0 z-[100] bg-slate-900/80 backdrop-blur-sm hidden flex items-center justify-center p-3 sm:p-6 select-none">



          <div class="relative bg-white text-slate-800 w-full max-w-4xl max-h-[92vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150">



            



            <!-- Modal Header -->



            <div class="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between shrink-0">



              <div class="flex items-center gap-3">



                <div class="p-2.5 rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-600/25">



                  <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>



                </div>



                <div>



                  <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">



                    Thiết Lập Layer Xuất CAD (AutoCAD DXF)



                    <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-900 border border-indigo-200 font-extrabold font-mono">8 Layer Chuẩn TCVN</span>



                  </h3>



                  <p class="text-xs text-slate-500 font-medium mt-0.5">Tùy chỉnh mã màu AutoCAD (ACI Index 1-255), kiểu nét (Linetype) và độ dày nét in (Lineweight). Tự động lưu LocalStorage.</p>



                </div>



              </div>



              <button type="button" onclick="closeCadLayerSettingsModal()" class="w-8 h-8 rounded-full bg-slate-200/70 hover:bg-slate-300 text-slate-600 flex items-center justify-center transition cursor-pointer">



                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>



              </button>



            </div>







            <!-- Modal Body (Table) -->



            <div class="p-4 overflow-y-auto flex-1 space-y-3">



              <div class="overflow-x-auto rounded-2xl border border-slate-200 shadow-2xs">



                <table class="w-full text-left text-xs border-collapse">



                  <thead>



                    <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 text-[11px]">



                      <th class="p-2.5 whitespace-nowrap">Tên Layer</th>



                      <th class="p-2.5 whitespace-nowrap">Dạng Đối Tượng (Object Type)</th>



                      <th class="p-2.5 whitespace-nowrap w-44">Màu ACI (Index 1-255)</th>



                      <th class="p-2.5 whitespace-nowrap w-36">Kiểu Nét (Linetype)</th>



                      <th class="p-2.5 whitespace-nowrap w-36">Độ Dày Nét In</th>



                    </tr>



                  </thead>



                  <tbody id="cadLayerTableBody" class="divide-y divide-slate-100 bg-white">



                    <!-- Nạp động từ etabs_hub.js -->



                  </tbody>



                </table>



              </div>







              <!-- Gợi ý bảng màu ACI -->



              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs text-slate-600 flex-wrap gap-2">



                <div class="flex items-center gap-2">



                  <span class="font-bold text-slate-700">Mã màu AutoCAD (ACI) thông dụng:</span>



                  <div class="flex items-center gap-1.5 flex-wrap">



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 border border-red-200">1: Red</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-yellow-100 text-yellow-800 border border-yellow-200">2: Yellow</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-700 border border-green-200">3: Green</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-100 text-cyan-800 border border-cyan-200">4: Cyan</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 border border-blue-200">5: Blue</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-fuchsia-100 text-fuchsia-700 border border-fuchsia-200">6: Magenta</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-800 border border-slate-300">7: White/Black</span>



                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">8: Dark Gray</span>



                  </div>



                </div>



                <span class="text-[11px] text-slate-400 font-mono">AutoCAD ACI 1-255</span>



              </div>



            </div>







            <!-- Modal Footer -->



            <div class="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">



              <button type="button" onclick="resetCadLayerConfigToDefault()" class="px-3 py-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs cursor-pointer">



                <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>



                <span>Khôi phục chuẩn TCVN mặc định</span>



              </button>



              <div class="flex items-center gap-2">



                <button type="button" onclick="closeCadLayerSettingsModal()" class="px-4 py-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold transition cursor-pointer">



                  Đóng



                </button>



                <button type="button" onclick="saveCadLayerConfigFromUI()" class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-sm flex items-center gap-1.5 cursor-pointer">



                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>



                  <span>Lưu & Áp Dụng Cho Bản Vẽ</span>



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



        <!-- MODAL: BẢNG CHI TIẾT ĐÀ KIỀNG TRỤC A, B, C (CHỊU PHẢN LỰC ĐẤT)       -->



        <!-- ==================================================================== -->



        <div id="tieBeamDrawingModal" class="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-sm hidden flex items-center justify-center p-2 sm:p-4">



          <div class="relative bg-white text-slate-800 w-[95vw] max-w-[95vw] h-[95vh] max-h-[95vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150">



            



            <!-- Modal Header -->



            <div class="p-3.5 sm:p-4 bg-slate-50 text-slate-900 flex flex-wrap items-center justify-between border-b border-slate-200 gap-3 shrink-0">



              <div class="flex items-center gap-3">



                <div class="p-2.5 rounded-2xl bg-emerald-600 text-white shadow-md shadow-emerald-600/25">



                  <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 22h16"/><path d="M4 2h16"/><path d="M6 2v20"/><path d="M18 2v20"/><line x1="6" y1="12" x2="18" y2="12"/></svg>



                </div>



                <div>



                  <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2 flex-wrap">



                    Bản Vẽ Chi Tiết Đà Kiềng Dọc Trục A, B, C



                    <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-extrabold font-mono">Tầng 1 / Móng</span>



                    <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-bold flex items-center gap-1">



                      <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> Phản Lực Đất Đẩy Lên (q_đất &gt; 0)



                    </span>



                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">TCVN 5574:2018</span>



                  </h3>



                  <p class="text-[11px] text-slate-500">Mô phỏng hình học, cốt thép dọc &amp; mặt cắt ngang xét đến mô-men đảo chiều do phản lực đất</p>



                </div>



              </div>







              <!-- Action Buttons & Exports -->



              <div class="flex items-center gap-2 flex-wrap">



                <button type="button" onclick="exportTieBeamSheetPdf()" class="py-1.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">



                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>



                  <span>Xuất PDF Đà Kiềng</span>



                </button>







                <button type="button" onclick="exportTieBeamSheetDxf()" class="py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">



                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/></svg>



                  <span>Xuất DXF Đà Kiềng</span>



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



                <span id="tieBeamCadHoverText">Rê chuột vào nhịp đà kiềng để xem chi tiết thông số &amp; thép</span>



              </div>



            </div>



          </div>



        
          <!-- ==================================================================== -->
          


        </div>















        <!-- TAB CONTENT 1: CHỌN THEO TRỤC -->



        <div id="tab-grid" class="tab-content bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="crosshair" class="w-5 h-5 text-indigo-600"></i> Chọn đối tượng trong phạm vi Lưới Trục



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">Revit Selection</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Lọc nhanh theo Trục X, Trục Y, từng tầng hoặc tất cả các tầng. Tự động highlight trên màn hình Revit.</p>



          </div>







          <div class="grid grid-cols-2 gap-4 text-xs">



            <div>



              <label class="block font-bold text-slate-700 mb-1">Trục X (Ví dụ: 9 10 hoặc 1 5):</label>



              <input type="text" id="gridXInput" value="9 10" placeholder="VD: 9 10" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600">



            </div>



            <div>



              <label class="block font-bold text-slate-700 mb-1">Trục Y (Ví dụ: C hoặc A C):</label>



              <input type="text" id="gridYInput" value="C" placeholder="VD: C hoặc A C" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600">



            </div>



            <div>



              <label class="block font-bold text-slate-700 mb-1">Dung sai Y (mm, nếu chỉ chọn 1 trục):</label>



              <input type="number" id="toleranceYInput" value="1500" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600">



            </div>



            <div>



              <label class="block font-bold text-slate-700 mb-1">Tầng áp dụng:</label>



              <select id="gridLevelSelect" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600">



                <option value="all">Tất cả các tầng</option>



                <option value="active">Tầng của View hiện hành</option>



                <option value="tang1">01. Tầng 1</option>



                <option value="tang2">02. Tầng 2</option>



                <option value="tang3">03. Tầng 3</option>



                <option value="tang4">04. Tầng 4</option>



                <option value="tum">06. Tầng Tum</option>



                <option value="mai">07. Mái</option>



              </select>



            </div>



            <div class="col-span-2">



              <label class="block font-bold text-slate-700 mb-1">Loại đối tượng (Category):</label>



              <select id="gridCatSelect" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600">



                <option value="doors">Cửa đi (Doors)</option>



                <option value="windows">Cửa sổ (Windows)</option>



                <option value="walls">Tường (Walls)</option>



                <option value="columns">Cột (Columns)</option>



                <option value="all">Tất cả đối tượng (All Categories)</option>



              </select>



            </div>



          </div>







          <div class="flex items-center gap-5 text-xs text-slate-700 pt-1">



            <label class="flex items-center gap-2 cursor-pointer font-medium">



              <input type="checkbox" id="gridZoomCheck" class="rounded border-slate-300 text-indigo-600 focus:ring-0">



              Zoom đến đối tượng



            </label>



            <label class="flex items-center gap-2 cursor-pointer font-medium">



              <input type="checkbox" id="gridIsolateCheck" class="rounded border-slate-300 text-indigo-600 focus:ring-0">



              Isolate tạm thời trong view



            </label>



          </div>







          <div class="pt-3">



            <button onclick="runSelectByGrid()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Thực thi: Chọn & Highlight trên Revit">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 2: ĐỔI CỬA D7 MỞ 30% -->



        <div id="tab-door" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="door-open" class="w-5 h-5 text-emerald-600"></i> Đổi cửa thoát hiểm Trục C thành D7 mở 30°



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">PCCC Standard</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Chuyển loại cửa tại buồng thang 2 sang Cua_Chong_Chay_D7_1Canh: D7_1200x2200 với cung mở 30° chuẩn PCCC.</p>



          </div>







          <div class="space-y-3.5 text-xs">



            <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">



              <div class="flex items-center justify-between text-slate-600">



                <span>Vị trí mục tiêu:</span>



                <span class="font-bold text-slate-900">Trục C (Y=7800mm), giữa Trục 9 & 10</span>



              </div>



              <div class="flex items-center justify-between text-slate-600">



                <span>Loại cửa mới:</span>



                <span class="font-bold text-emerald-700">Cua_Chong_Chay_D7_1Canh: D7_1200x2200</span>



              </div>



              <div class="flex items-center justify-between text-slate-600">



                <span>Góc mở hiển thị (2D Plan Swing):</span>



                <span class="font-bold text-amber-700">30 độ (chuẩn chống cháy)</span>



              </div>



            </div>







            <div>



              <label class="block font-bold text-slate-700 mb-1">Tầng áp dụng chuyển đổi:</label>



              <select id="doorFloorSelect" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600">



                <option value="all">Tất cả các tầng (Tầng 1, 2, 3, 4, Tum)</option>



                <option value="tang1">Chỉ Tầng 1</option>



                <option value="tang2">Chỉ Tầng 2</option>



                <option value="tang3">Chỉ Tầng 3</option>



                <option value="tang4">Chỉ Tầng 4</option>



                <option value="tum">Chỉ Tầng Tum</option>



              </select>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runChangeDoorsD7()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Thực hiện đổi sang cửa D7 mở 30°">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 3: ĐÁNH KÍCH THƯỚC TỰ ĐỘNG -->



        <div id="tab-dim" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="ruler" class="w-5 h-5 text-indigo-600"></i> Đánh Dim 3 Lớp & Nội Thất Tự Động



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">Auto Dims</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Tự động sinh chuỗi kích thước trục bao ngoài 3 lớp và 2 chuỗi dim ngang nội thất (AB & CD).</p>



          </div>







          <div class="grid grid-cols-2 gap-4 text-xs">



            <div class="col-span-2">



              <label class="block font-bold text-slate-700 mb-1">Mặt bằng tầng cần đánh Dim:</label>



              <select id="dimViewSelect" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600">



                <option value="all">Tất cả các tầng (01 &rarr; 07)</option>



                <option value="312">01 - MẶT BẰNG TẦNG 1</option>



                <option value="695">02 - MẶT BẰNG TẦNG 2</option>



                <option value="1727585">03 - MẶT BẰNG TẦNG 3</option>



                <option value="2361036">04 - MẶT BẰNG TẦNG 4</option>



                <option value="2361048">06 - MẶT BẰNG TẦNG TUM</option>



                <option value="1209119">07 - MẶT BẰNG MÁI</option>



              </select>



            </div>



            <div>



              <label class="block font-bold text-slate-700 mb-1">Khoảng cách Dim AB đến trục B (mm):</label>



              <input type="number" id="offsetBInput" value="1500" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600">



            </div>



            <div>



              <label class="block font-bold text-slate-700 mb-1">Khoảng cách Dim CD đến trục C (mm):</label>



              <input type="number" id="offsetCInput" value="1500" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600">



            </div>



            <div class="col-span-2 pt-1">



              <label class="flex items-center gap-2 cursor-pointer text-slate-700 font-medium">



                <input type="checkbox" id="cleanDimCheck" checked class="rounded border-slate-300 text-indigo-600 focus:ring-0">



                Tự động xóa dim cũ trùng lặp trước khi tạo mới



              </label>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runCreateDimensions()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Khởi tạo hệ thống Dim Revit">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 4: XUẤT DWG (TREEVIEW & TITLEBLOCK OVERLAY) -->



        <div id="tab-dwg" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="download" class="w-5 h-5 text-cyan-600"></i> Xuất Bản Vẽ DWG (Views & Sheets)



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-cyan-50 text-cyan-700 font-bold border border-cyan-200">CAD Export</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Chọn các View / Bản vẽ theo danh sách cây thư mục (TreeView). Hỗ trợ tùy chọn Overlay khung tên, thông tin bản vẽ & dự án hoặc xuất hình học sạch không khung tên.</p>



          </div>







          <div class="space-y-4 text-xs">



            <!-- 1. CÂY THƯ MỤC VIEW / SHEET (TREEVIEW) -->



            <div class="space-y-2">



              <div class="flex items-center justify-between">



                <label class="font-bold text-slate-700 flex items-center gap-1.5">



                  <i data-lucide="folder-tree" class="w-4 h-4 text-cyan-600"></i> Danh sách Bản vẽ & View trong Revit:



                </label>



                <div class="flex items-center gap-2 text-[11px]">



                  <span id="dwgSelectedSummary" class="font-bold text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded-full border border-cyan-200">Đang tải...</span>



                  <button type="button" onclick="loadDwgTreeView(true)" class="p-1 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition" title="Làm mới danh sách từ Revit">



                    <i data-lucide="rotate-cw" class="w-3.5 h-3.5"></i>



                  </button>



                </div>



              </div>







              <!-- TreeView Toolbar: Search + Quick Select Buttons -->



              <div class="flex items-center gap-2">



                <div class="relative flex-1">



                  <input type="text" id="dwgSearchInput" oninput="onDwgSearchInput(this.value)" placeholder="🔍 Tìm kiếm view / bản vẽ theo tên..." class="w-full bg-slate-50 border border-slate-300 rounded-lg pl-3 pr-8 py-1.5 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                  <button type="button" onclick="clearDwgSearch()" class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 hidden" id="dwgSearchClearBtn">✕</button>



                </div>



                <div class="flex items-center gap-1 flex-shrink-0">



                  <button type="button" onclick="setAllDwgSelection(true)" class="px-2 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] border border-slate-200 transition" title="Chọn tất cả bản vẽ">



                    ✓ Tất cả



                  </button>



                  <button type="button" onclick="setAllDwgSelection(false)" class="px-2 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] border border-slate-200 transition" title="Bỏ chọn tất cả">



                    ✕ Bỏ chọn



                  </button>



                  <button type="button" onclick="setAllDwgExpansion(true)" class="px-2 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] border border-slate-200 transition" title="Mở rộng tất cả nhóm">



                    ▼ Mở



                  </button>



                  <button type="button" onclick="setAllDwgExpansion(false)" class="px-2 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] border border-slate-200 transition" title="Thu gọn tất cả nhóm">



                    ▶ Đóng



                  </button>



                </div>



              </div>







              <!-- TreeView List Container -->



              <div id="dwgTreeContainer" class="max-h-[300px] overflow-y-auto bg-slate-50/70 border border-slate-200 rounded-xl p-2.5 space-y-1.5 text-xs shadow-inner">



                <div class="text-slate-400 p-4 text-center">Đang tải danh sách view từ Revit...</div>



              </div>



            </div>







            <!-- 2. TÙY CHỌN KHUNG TÊN (OVERLAY TITLEBLOCK VS NO OVERLAY) -->



            <div class="space-y-2 pt-1 border-t border-slate-100">



              <label class="block font-bold text-slate-700 mb-1">Chế độ khung tên (Titleblock Mode):</label>



              <div class="grid grid-cols-2 gap-3">



                <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="dwgTitleblockMode" value="none" checked onchange="toggleTitleblockPanel()" class="mt-0.5 text-cyan-600 focus:ring-cyan-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1.5">



                      <span>🔲 Không Overlay Khung Tên</span>



                      <span class="text-[10px] px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 font-semibold">Model Only</span>



                    </div>



                    <div class="text-[11px] text-slate-500 mt-1 leading-snug">



                      Xuất trực tiếp mô hình view sạch sẽ, giữ nguyên tọa độ gốc của dự án, không chèn viền khung tên bên ngoài.



                    </div>



                  </div>



                </label>







                <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="dwgTitleblockMode" value="overlay" onchange="toggleTitleblockPanel()" class="mt-0.5 text-cyan-600 focus:ring-cyan-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1.5">



                      <span>🖼️ Overlay Khung Tên & Thông Tin</span>



                      <span class="text-[10px] px-1.5 py-0.2 rounded bg-cyan-100 text-cyan-800 font-semibold">Full Sheet</span>



                    </div>



                    <div class="text-[11px] text-slate-500 mt-1 leading-snug">



                      Chèn khung tên DWG và điền đầy đủ Thông tin bản vẽ (Tên, Số hiệu, Tỷ lệ) & Thông tin dự án (Tên DA, Chủ đầu tư...).



                    </div>



                  </div>



                </label>



              </div>







              <!-- PANEL CHI TIẾT KHUNG TÊN (HIỆN KHI CHỌN OVERLAY) -->



              <div id="panelTitleblockSettings" class="hidden p-3.5 rounded-xl bg-cyan-50/50 border border-cyan-200 space-y-3 animate-in fade-in duration-150">



                <!-- Chọn file DWG Khung tên -->



                <div>



                  <label class="block font-bold text-cyan-900 mb-1">Mẫu Khung tên DWG (Titleblock File):</label>



                  <div class="flex gap-2">



                    <select id="dwgTitleblockPreset" onchange="applyTitleblockPreset()" class="bg-white border border-cyan-300 rounded-lg px-2.5 py-1.5 text-slate-900 font-medium text-xs focus:outline-none focus:border-cyan-600">



                      <option value="khung_ten_A1.dwg">Khung tên A1 Chuẩn (841 x 594 mm)</option>



                      <option value="khung_ten_A2.dwg">Khung tên A2 Chuẩn (594 x 420 mm)</option>



                      <option value="khung_ten_A3.dwg">Khung tên A3 Chuẩn (420 x 297 mm)</option>



                      <option value="custom">File DWG tùy chỉnh...</option>



                    </select>



                    <input type="text" id="dwgTitleblockFilePath" value="khung_ten_A1.dwg" placeholder="Đường dẫn file DWG khung tên..." class="flex-1 bg-white border border-cyan-300 rounded-lg px-3 py-1.5 text-slate-900 text-xs focus:outline-none focus:border-cyan-600">



                  </div>



                </div>







                <!-- Thông tin dự án (Project Information) -->



                <div class="bg-white/80 p-3 rounded-xl border border-cyan-200/80 space-y-2.5">



                  <div class="flex items-center justify-between">



                    <span class="font-bold text-cyan-950 flex items-center gap-1.5">



                      <i data-lucide="info" class="w-3.5 h-3.5 text-cyan-600"></i> Thông Tin Dự Án (Project Info)



                    </span>



                    <button type="button" onclick="reloadProjectInfoFromRevit()" class="text-[10px] text-cyan-700 hover:text-cyan-900 font-semibold flex items-center gap-1">



                      <i data-lucide="rotate-cw" class="w-3 h-3"></i> Tải lại từ Revit



                    </button>



                  </div>







                  <div class="grid grid-cols-2 gap-2 text-xs">



                    <div>



                      <span class="text-[10px] text-slate-500 font-semibold">Tên Dự Án:</span>



                      <input type="text" id="piProjectName" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                    </div>



                    <div>



                      <span class="text-[10px] text-slate-500 font-semibold">Hạng Mục / Công Trình:</span>



                      <input type="text" id="piBuildingName" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                    </div>



                    <div>



                      <span class="text-[10px] text-slate-500 font-semibold">Địa Điểm Xây Dựng:</span>



                      <input type="text" id="piProjectAddress" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                    </div>



                    <div>



                      <span class="text-[10px] text-slate-500 font-semibold">Chủ Đầu Tư:</span>



                      <input type="text" id="piClientName" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                    </div>



                    <div>



                      <span class="text-[10px] text-slate-500 font-semibold">Ngày Phát Hành:</span>



                      <input type="text" id="piIssueDate" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                    </div>



                    <div>



                      <span class="text-[10px] text-slate-500 font-semibold">Đơn Vị Thiết Kế / Tác Giả:</span>



                      <input type="text" id="piAuthor" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 text-xs focus:bg-white focus:outline-none focus:border-cyan-600">



                    </div>



                  </div>



                </div>







                <!-- Thông tin bản vẽ (Drawing Information Guide) -->



                <div class="text-[11px] text-cyan-800 leading-relaxed bg-cyan-100/50 p-2.5 rounded-lg border border-cyan-200">



                  <p>&bull; <strong>Thông tin Bản vẽ:</strong> Số hiệu bản vẽ (Sheet Number), Tên bản vẽ (Sheet Name) và Tỷ lệ (Scale) sẽ được tự động điền theo từng mục bạn đã tích chọn trong TreeView.</p>



                </div>



              </div>



            </div>







            <!-- 3. BỐ CỤC XUẤT FILE DWG -->



            <div class="space-y-1.5 pt-1 border-t border-slate-100">



              <label class="block font-bold text-slate-700">Định dạng bố cục đầu ra:</label>



              <div class="grid grid-cols-2 gap-3">



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-cyan-200 bg-cyan-50/50 hover:bg-cyan-100/60 cursor-pointer transition select-none">



                  <input type="radio" name="dwgLayoutMode" value="vertical" checked class="text-cyan-600 focus:ring-cyan-500">



                  <div>



                    <div class="font-bold text-cyan-950">📑 Gộp thành 1 file (Merge CAD)</div>



                    <div class="text-[10px] text-cyan-700">Tự động xếp hàng dọc, layer màu chuẩn</div>



                  </div>



                </label>



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="dwgLayoutMode" value="individual" class="text-cyan-600 focus:ring-cyan-500">



                  <div>



                    <div class="font-bold text-slate-900">📁 Từng file DWG riêng biệt</div>



                    <div class="text-[10px] text-slate-500">Lưu vào thư mục Downloads</div>



                  </div>



                </label>



              </div>



            </div>







            <!-- 4. NƠI LƯU & QUY TẮC ĐẶT TÊN FILE (DOWNLOADS + PROJECT + TIMESTAMP) -->



            <div class="space-y-2 pt-2 border-t border-slate-100">



              <div class="flex items-center justify-between">



                <label class="block font-bold text-slate-700">Thư mục lưu & Quy tắc đặt tên file:</label>



                <button type="button" onclick="openDownloadsFolder()" class="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold border border-slate-200 flex items-center gap-1.5 transition" title="Mở thư mục Downloads trong Explorer">



                  <i data-lucide="folder" class="w-3.5 h-3.5 text-amber-600"></i>



                  <span>Mở Downloads</span>



                </button>



              </div>







              <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">



                <div>



                  <span class="text-[10px] text-slate-500 font-semibold">Thư mục xuất DWG:</span>



                  <input type="text" id="dwgOutputFolder" value="~/Downloads" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-900 font-mono text-[11px] focus:bg-white focus:outline-none focus:border-cyan-600">



                </div>



                <div>



                  <span class="text-[10px] text-slate-500 font-semibold">Tên dự án (Project Tag):</span>



                  <input type="text" id="dwgProjectTag" value="Mau_40_CBS" oninput="updateDwgPreviewName()" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-900 font-semibold text-[11px] focus:bg-white focus:outline-none focus:border-cyan-600">



                </div>



              </div>







              <div class="p-2 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 flex items-center gap-1.5">



                <i data-lucide="file-code" class="w-3.5 h-3.5 text-cyan-600 flex-shrink-0"></i>



                <span>Tên file gộp dự kiến:</span>



                <span id="dwgFileNamePreview" class="font-mono text-cyan-800 font-bold break-all">Mau_40_CBS_{timestamp}_merge_cad.dwg</span>



              </div>



            </div>







            <!-- TIẾN TRÌNH TỔNG (OVERALL PROGRESS BAR) -->



            <div id="dwgProgressSection" class="hidden p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2 animate-in fade-in duration-200">



              <div class="flex items-center justify-between text-xs">



                <span id="dwgProgressStatus" class="font-bold text-slate-800 flex items-center gap-2">



                  <i id="dwgProgressSpinner" data-lucide="loader-2" class="w-4 h-4 animate-spin text-cyan-600"></i>



                  <span id="dwgProgressText">Đang chuẩn bị xuất bản vẽ...</span>



                </span>



                <span id="dwgProgressPercent" class="font-mono font-bold text-cyan-800 bg-cyan-100 px-2.5 py-0.5 rounded-full text-xs">0%</span>



              </div>







              <!-- Thanh tiến trình chính -->



              <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden shadow-inner relative">



                <div id="dwgProgressBar" class="h-full bg-gradient-to-r from-cyan-500 to-indigo-600 rounded-full transition-all duration-300 ease-out" style="width: 0%;"></div>



              </div>







              <!-- Chi tiết tiến độ từng view & số lượng -->



              <div class="flex items-center justify-between text-[11px] text-slate-500">



                <span id="dwgProgressDetail" class="truncate max-w-[70%]">Đang khởi tạo tiến trình...</span>



                <span id="dwgProgressCount" class="font-semibold text-slate-700 flex-shrink-0">0 / 0 bản vẽ</span>



              </div>



            </div>



          </div>







          <div class="pt-3">



            <button id="btnRunDwgExport" onclick="runCustomDwgExport()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Bắt đầu xuất bản vẽ DWG">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 5: AUTOCAD 3D OBJ & 2D VISION PIPELINE & DÁN TEXT -->



        <div id="tab-cad" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">



          <!-- Main Header with Live Status & Sub-tab switcher -->



          <div class="border-b border-slate-100 pb-3 flex flex-wrap items-center justify-between gap-3">



            <div>



              <div class="flex items-center gap-2">



                <span class="p-1.5 rounded-xl bg-cyan-50 text-cyan-700 border border-cyan-100">



                  <i data-lucide="box" class="w-5 h-5"></i>



                </span>



                <h2 class="text-base font-bold text-slate-900">AutoCAD AI Hub: 3D OBJ & 2D Vision</h2>



                <span id="cadAccoreBadge" class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">AutoCAD 2022 Accore</span>



                <span id="cadClipboardBadge" class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium border border-slate-200 flex items-center gap-1">



                  <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Đang kiểm tra...



                </span>



              </div>



              <p class="text-xs text-slate-500 mt-1">



                Trích xuất Clipboard AutoCAD OLE &rarr; DWG &rarr; DXF &rarr; Nhận diện Tường, Cửa, Cột &rarr; Tự động sinh mô hình 3D Wavefront OBJ.



              </p>



            </div>







            <!-- 3 Subtabs Nav Buttons -->



            <div class="flex items-center bg-slate-100 p-1 rounded-xl gap-1">



              <button onclick="switchCadSubTab('cad-subtab-3d')" id="btn-cad-subtab-3d" class="py-1.5 px-3 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-indigo-600 text-white shadow-xs cursor-pointer">



                <i data-lucide="box" class="w-3.5 h-3.5"></i> 3D OBJ Viewer



              </button>



              <button onclick="switchCadSubTab('cad-subtab-2d')" id="btn-cad-subtab-2d" class="py-1.5 px-3 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer">



                <i data-lucide="eye" class="w-3.5 h-3.5"></i> Nhận Diện 2D Vision



              </button>



              <button onclick="switchCadSubTab('cad-subtab-text')" id="btn-cad-subtab-text" class="py-1.5 px-3 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer">



                <i data-lucide="type" class="w-3.5 h-3.5"></i> Dán Text sang Revit



              </button>



            </div>



          </div>







          <!-- SUBTAB 1: 3D OBJ VIEWER & GENERATION -->



          <div id="cad-subtab-3d" class="space-y-4">



            <!-- Action Toolbar Card -->



            <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-3">



              <div class="flex flex-wrap items-center gap-2">



                <div class="flex items-center gap-1.5">



                  <label class="text-xs font-bold text-slate-700 whitespace-nowrap">Nguồn CAD:</label>



                  <select id="cadPipelineSource" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-indigo-600">



                    <option value="clipboard">Windows Clipboard (Quét chọn trong CAD & Ctrl+C)</option>



                    <option value="sample">Mẫu Dự Án (clipboard_converted.dxf)</option>



                    <option value="custom">File DXF/DWG Tùy Chọn...</option>



                  </select>



                </div>



                <input type="text" id="cadCustomDxfPath" placeholder="D:/du_an/mat_bang.dxf" class="hidden bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 w-52 focus:outline-none">

                <div class="flex items-center gap-1.5 bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 font-medium shadow-2xs">
                  <label for="cadExpectedStairsSelect" class="text-xs font-bold text-slate-700 whitespace-nowrap flex items-center gap-1 cursor-pointer">
                    <i data-lucide="git-merge" class="w-3.5 h-3.5 text-orange-500"></i>
                    <span>Số cầu thang:</span>
                  </label>
                  <select id="cadExpectedStairsSelect" onchange="onCadExpectedStairsChange(this.value)" class="bg-slate-50 border border-slate-300 rounded px-2 py-0.5 text-xs font-bold text-slate-800 focus:outline-none focus:border-indigo-600 cursor-pointer" title="Quy định số lượng cầu thang thực tế của tầng để tránh nhầm sọc cửa sổ/tường">
                    <option value="auto">Tự động (Lọc hình học chuẩn)</option>
                    <option value="0">0 (Không có thang)</option>
                    <option value="1">1 thang</option>
                    <option value="2" selected>2 thang (Chuẩn mẫu này)</option>
                    <option value="3">3 thang</option>
                    <option value="4">4 thang</option>
                  </select>
                </div>

              </div>







              <div class="flex flex-wrap items-center gap-2">



                <button onclick="runCadClipboardPipeline()" id="btnRunCadPipeline" class="py-1.5 px-3 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/20 transition active:scale-95 cursor-pointer">



                  <i data-lucide="play" class="w-4 h-4 fill-white"></i> 1-Click Clipboard &rarr; 2D Vision



                </button>



                <button onclick="runCadGenerate3d()" id="btnRunCadGenerate3d" class="py-1.5 px-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-500/20 transition active:scale-95 cursor-pointer">



                  <i data-lucide="box" class="w-4 h-4"></i> Sinh Model 3D OBJ



                </button>



                <button onclick="openCadModelFolder()" class="p-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition cursor-pointer" title="Mở thư mục chứa file OBJ trên Explorer">



                  <i data-lucide="folder" class="w-4 h-4"></i>



                </button>



              </div>



            </div>







            <!-- 3D Canvas + Layer Sidebar Layout -->



            <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5">



              <!-- Left/Center: WebGL Canvas (col-span-8 or 9) -->



              <div class="lg:col-span-8 xl:col-span-9 bg-zinc-900 border border-slate-800 rounded-2xl overflow-hidden relative shadow-inner flex flex-col" style="height: 520px;">



                <!-- Canvas Header Bar -->



                <div class="px-3 py-2 bg-zinc-900/90 border-b border-zinc-800 flex items-center justify-between text-xs text-zinc-300 z-10">



                  <div class="flex items-center gap-2 min-w-0">



                    <span class="w-2 h-2 rounded-full bg-emerald-400"></span>



                    <span class="font-bold text-white font-mono text-[11px] truncate" id="cad3dCurrentTitle">building_full.obj</span>



                    <span class="text-[10px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono" id="cad3dDimensions">44.8m x 16.0m • Cao 3.9m</span>



                  </div>



                  <div class="flex items-center gap-1.5">



                    <button onclick="resetCad3dCamera()" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[10.5px] px-2 transition cursor-pointer" title="Góc nhìn Isometric chuẩn">



                      Iso View



                    </button>



                    <button onclick="setCad3dViewTop()" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[10.5px] px-2 transition cursor-pointer" title="Góc nhìn Top Mặt Bằng">



                      Top View



                    </button>



                    <button onclick="toggleCad3dWireframe()" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[10.5px] px-2 transition cursor-pointer" title="Bật/tắt chế độ khung dây Wireframe">



                      Wireframe



                    </button>



                  </div>



                </div>







                <!-- Three.js Canvas Element -->



                <div id="cad3dCanvasContainer" class="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing">



                  <!-- Overlay Spinner -->



                  <div id="cad3dLoadingOverlay" class="absolute inset-0 bg-zinc-900/80 backdrop-blur-xs flex flex-col items-center justify-center text-white z-20 hidden">



                    <div class="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2"></div>



                    <div class="text-xs font-semibold">Đang nạp mô hình 3D Wavefront OBJ...</div>



                  </div>



                </div>







                <!-- Layer Filter Bar at Bottom of Canvas -->



                <div class="px-3 py-1.5 bg-zinc-900/95 border-t border-zinc-800 flex flex-wrap items-center gap-1.5 text-[11px] z-10">



                  <span class="text-zinc-500 text-[10px] font-bold uppercase tracking-wider mr-1">Lớp đối tượng:</span>



                  <button onclick="filterCad3dLayer('all')" id="cadLayerBtn-all" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 ring-2 ring-indigo-400 font-bold transition cursor-pointer">Tất cả</button>



                  <button onclick="filterCad3dLayer('wall')" id="cadLayerBtn-wall" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition cursor-pointer">🧱 Tường & Cột</button>



                  <button onclick="filterCad3dLayer('door')" id="cadLayerBtn-door" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-emerald-400 transition cursor-pointer">🚪 Cửa đi</button>



                  <button onclick="filterCad3dLayer('window')" id="cadLayerBtn-window" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-cyan-400 transition cursor-pointer">🪟 Cửa sổ</button>



                  <button onclick="filterCad3dLayer('stair')" id="cadLayerBtn-stair" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-amber-400 transition cursor-pointer">🪜 Cầu thang & Tam cấp</button>



                  <button onclick="filterCad3dLayer('ramp')" id="cadLayerBtn-ramp" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-rose-400 transition cursor-pointer">♿ Ram dốc</button>



                </div>



              </div>







              <!-- Right: OBJ File Components & Downloads (col-span-4 or 3) -->



              <div class="lg:col-span-4 xl:col-span-3 space-y-3">



                <div class="bg-slate-50 border border-slate-200 rounded-2xl p-3.5 space-y-2.5">



                  <div class="flex items-center justify-between">



                    <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5">



                      <i data-lucide="layers" class="w-4 h-4 text-indigo-600"></i> Các Tệp Model OBJ



                    </span>



                    <span class="text-[10px] text-slate-500 font-mono">Hệ mét & mm</span>



                  </div>



                  <div id="cadModelsList" class="space-y-1.5 max-h-[440px] overflow-y-auto pr-1">



                    <!-- Populated dynamically -->



                  </div>



                </div>



              </div>



            </div>



          </div>







          <!-- SUBTAB 2: 2D VISION & FLOORPLAN DETECTION -->



          <div id="cad-subtab-2d" class="hidden space-y-3">
            <!-- Detection Summary Pills (7 Categories) -->
            <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
              <div class="p-2.5 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-emerald-700 font-semibold">Cửa đi (Doors)</div>
                  <div class="text-base font-extrabold text-emerald-900" id="cadCountDoors">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-emerald-600 text-white"><i data-lucide="door-open" class="w-3.5 h-3.5"></i></div>
              </div>
              <div class="p-2.5 rounded-xl bg-cyan-50 border border-cyan-100 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-cyan-700 font-semibold">Cửa sổ (Windows)</div>
                  <div class="text-base font-extrabold text-cyan-900" id="cadCountWindows">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-cyan-600 text-white"><i data-lucide="maximize" class="w-3.5 h-3.5"></i></div>
              </div>
              <div class="p-2.5 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-amber-700 font-semibold">Cột kết cấu</div>
                  <div class="text-base font-extrabold text-amber-900" id="cadCountColumns">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-amber-600 text-white"><i data-lucide="columns" class="w-3.5 h-3.5"></i></div>
              </div>
              <div class="p-2.5 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-rose-700 font-semibold">Tường Major</div>
                  <div class="text-base font-extrabold text-rose-900" id="cadCountWalls">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-rose-600 text-white"><i data-lucide="square" class="w-3.5 h-3.5"></i></div>
              </div>
              <div class="p-2.5 rounded-xl bg-orange-50 border border-orange-200 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-orange-700 font-semibold">🪜 Cầu thang</div>
                  <div class="text-base font-extrabold text-orange-900" id="cadCountStairs">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-orange-500 text-white"><i data-lucide="git-merge" class="w-3.5 h-3.5"></i></div>
              </div>
              <div class="p-2.5 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-purple-700 font-semibold">🏛️ Tam cấp</div>
                  <div class="text-base font-extrabold text-purple-900" id="cadCountTamCap">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-purple-600 text-white"><i data-lucide="layers" class="w-3.5 h-3.5"></i></div>
              </div>
              <div class="p-2.5 rounded-xl bg-pink-50 border border-pink-200 flex items-center justify-between">
                <div>
                  <div class="text-[10.5px] text-pink-700 font-semibold">📐 Ram dốc</div>
                  <div class="text-base font-extrabold text-pink-900" id="cadCountRamps">--</div>
                </div>
                <div class="p-1.5 rounded-lg bg-pink-600 text-white"><i data-lucide="trending-up" class="w-3.5 h-3.5"></i></div>
              </div>
            </div>

            <!-- Interactive Vision Studio Canvas -->
            <div class="bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden p-3 relative flex flex-col gap-2.5 shadow-xl">
              <!-- Studio Control Bar -->
              <div class="flex flex-wrap items-center justify-between gap-2.5 pb-2 border-b border-zinc-800/80">
                <!-- Mode Switch & Drawing Selector -->
                <div class="flex flex-wrap items-center gap-2">
                  <div class="inline-flex rounded-lg bg-zinc-900 p-0.5 border border-zinc-700/60 text-xs">
                    <button id="cadCanvasModePan" onclick="setCadCanvasMode('pan')" class="px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 bg-indigo-600 text-white shadow">
                      <i data-lucide="hand" class="w-3.5 h-3.5"></i> Duyệt / Chọn
                    </button>
                    <button id="cadCanvasModeDraw" onclick="setCadCanvasMode('draw')" class="px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 text-zinc-400 hover:text-white">
                      <i data-lucide="edit-3" class="w-3.5 h-3.5"></i> Vẽ Vùng (BBox)
                    </button>
                  </div>

                  <!-- Category to draw -->
                  <div class="flex items-center gap-1.5 bg-zinc-900/90 border border-zinc-700/60 rounded-lg px-2 py-1 text-xs">
                    <span class="text-zinc-400 font-medium text-[11px]">Loại vẽ:</span>
                    <select id="cadDrawCategory" class="bg-zinc-800 text-zinc-200 rounded px-2 py-0.5 text-xs font-semibold focus:outline-none border border-zinc-700">
                      <option value="stairs">🪜 Cầu thang (Stair)</option>
                      <option value="tam_cap">🏛️ Tam cấp (Steps)</option>
                      <option value="ramps">📐 Ram dốc (Ramp)</option>
                      <option value="doors">🚪 Cửa đi (Door)</option>
                      <option value="windows">🪟 Cửa sổ (Window)</option>
                      <option value="columns">🏛️ Cột (Column)</option>
                      <option value="walls">🧱 Tường (Wall)</option>
                    </select>
                  </div>
                </div>

                <!-- Visibility Toggles Chips -->
                <div class="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-950/60 text-orange-300 border border-orange-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleStairs" checked onchange="toggleCadCategoryVis('stairs', this.checked)" class="accent-orange-500"> Thang
                  </label>
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-950/60 text-purple-300 border border-purple-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleTamCap" checked onchange="toggleCadCategoryVis('tam_cap', this.checked)" class="accent-purple-500"> Tam cấp
                  </label>
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-pink-950/60 text-pink-300 border border-pink-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleRamps" checked onchange="toggleCadCategoryVis('ramps', this.checked)" class="accent-pink-500"> Ram dốc
                  </label>
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleDoors" checked onchange="toggleCadCategoryVis('doors', this.checked)" class="accent-emerald-500"> Cửa đi
                  </label>
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleWindows" checked onchange="toggleCadCategoryVis('windows', this.checked)" class="accent-cyan-500"> Cửa sổ
                  </label>
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-950/60 text-yellow-300 border border-yellow-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleColumns" checked onchange="toggleCadCategoryVis('columns', this.checked)" class="accent-yellow-500"> Cột
                  </label>
                  <label class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-950/60 text-rose-300 border border-rose-800/60 cursor-pointer select-none">
                    <input type="checkbox" id="cadVisToggleWalls" onchange="toggleCadCategoryVis('walls', this.checked)" class="accent-rose-500"> Tường
                  </label>
                </div>

                <!-- Action Buttons -->
                <div class="flex items-center gap-2">
                  <button id="btnCadSaveAnnotations" onclick="saveCadVisionAnnotations()" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 cursor-pointer shadow">
                    <i data-lucide="save" class="w-3.5 h-3.5"></i> Lưu Chỉ Định
                  </button>
                  <button id="btnCadGen3DFromStudio" onclick="generate3dFromVisionStudio()" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5 cursor-pointer shadow">
                    <i data-lucide="box" class="w-3.5 h-3.5"></i> Sinh 3D OBJ
                  </button>
                  <button onclick="resetCadVisionAnnotations()" title="Khôi phục nhận diện gốc" class="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition cursor-pointer">
                    <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                  </button>
                </div>
              </div>

              <!-- Main Canvas Viewport Area -->
              <div id="cadCanvasContainer" class="w-full h-[620px] relative rounded-xl overflow-hidden bg-[#18181b] border border-zinc-800 flex items-center justify-center select-none">
                <canvas id="cadVisionCanvas" class="w-full h-full block cursor-grab"></canvas>

                <!-- Floating HUD Zoom Controls (Top-Right) -->
                <div class="absolute top-3 right-3 flex items-center gap-1 bg-zinc-900/90 backdrop-blur border border-zinc-700/70 rounded-xl p-1 shadow-2xl z-20">
                  <button onclick="cadCanvasZoomIn()" title="Phóng to (+)" class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white font-bold text-xs flex items-center justify-center transition cursor-pointer">
                    <i data-lucide="zoom-in" class="w-3.5 h-3.5"></i>
                  </button>
                  <button onclick="cadCanvasZoomOut()" title="Thu nhỏ (-)" class="w-7 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white font-bold text-xs flex items-center justify-center transition cursor-pointer">
                    <i data-lucide="zoom-out" class="w-3.5 h-3.5"></i>
                  </button>
                  <button onclick="cadCanvasZoom100()" title="Tỉ lệ chuẩn 100%" class="px-2 h-7 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-mono text-[11px] flex items-center justify-center transition cursor-pointer">
                    100%
                  </button>
                  <button onclick="cadCanvasFitView()" title="Vừa vặn khung nhìn (Double-click)" class="px-2 h-7 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white font-bold text-[11px] flex items-center gap-1 transition cursor-pointer">
                    <i data-lucide="maximize" class="w-3 h-3"></i> Vừa khung
                  </button>
                  <span id="cadCanvasZoomBadge" class="px-2 py-0.5 text-[10.5px] font-mono text-zinc-400 border-l border-zinc-700 pl-2">100%</span>
                </div>

                <!-- Floating HUD Coordinates (Bottom-Left) -->
                <div class="absolute bottom-3 left-3 bg-zinc-900/90 backdrop-blur border border-zinc-700/70 rounded-lg px-2.5 py-1 text-[11px] font-mono text-zinc-300 shadow-xl pointer-events-none z-20 flex items-center gap-3">
                  <span id="cadHudCoords">CAD: X: -- mm | Y: -- mm</span>
                  <span id="cadHudBoxInfo" class="text-zinc-500 border-l border-zinc-700 pl-2">Cuộn: Zoom • Chuột giữa: Pan • Kéo Grip: Sửa kích thước • Kéo hộp: Di chuyển</span>
                </div>

                <!-- Floating Selected Entity Inspector (Bottom-Right) -->
                <div id="cadSelectedBoxInspector" class="hidden absolute bottom-3 right-3 bg-zinc-900/95 backdrop-blur border border-indigo-500/60 rounded-xl p-3 shadow-2xl z-20 w-80 space-y-2 text-xs">
                  <div class="flex items-center justify-between pb-1.5 border-b border-zinc-800">
                    <div class="flex items-center gap-1.5">
                      <span id="cadInspectorTypeIcon">🪜</span>
                      <span id="cadInspectorId" class="font-bold text-white text-xs">STAIR_01</span>
                    </div>
                    <button onclick="deleteSelectedCadBox()" class="text-rose-400 hover:text-rose-300 p-1 rounded hover:bg-rose-950/60 transition cursor-pointer flex items-center gap-1">
                      <i data-lucide="trash-2" class="w-3.5 h-3.5"></i> Xóa
                    </button>
                  </div>
                  <div class="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span class="text-zinc-400">Kích thước:</span>
                      <div id="cadInspectorDims" class="font-mono text-zinc-200 font-bold">3500 x 3150 mm</div>
                    </div>
                    <div>
                      <span class="text-zinc-400">Tọa độ tâm CAD:</span>
                      <div id="cadInspectorCenter" class="font-mono text-zinc-300">475151, -1475212</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 pt-1 border-t border-zinc-800/80">
                    <label class="text-[11px] text-zinc-400 whitespace-nowrap">Đổi loại:</label>
                    <select id="cadInspectorCategorySelect" onchange="changeSelectedBoxCategory(this.value)" class="flex-1 bg-zinc-800 text-zinc-200 rounded px-2 py-1 text-xs border border-zinc-700 focus:outline-none font-semibold">
                      <option value="stairs">🪜 Cầu thang (Stair)</option>
                      <option value="tam_cap">🏛️ Tam cấp (Steps)</option>
                      <option value="ramps">📐 Ram dốc (Ramp)</option>
                      <option value="doors">🚪 Cửa đi (Door)</option>
                      <option value="windows">🪟 Cửa sổ (Window)</option>
                      <option value="columns">🏛️ Cột (Column)</option>
                      <option value="walls">🧱 Tường (Wall)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sample Door Crops Horizontal Slider -->



            <div class="space-y-2">



              <div class="flex items-center justify-between text-xs font-bold text-slate-800">



                <span class="flex items-center gap-1.5"><i data-lucide="crop" class="w-4 h-4 text-emerald-600"></i> Mẫu Cắt Cửa Đi & Kích Thước Nhận Diện</span>



                <span class="text-[10.5px] text-slate-500 font-normal">Click vào cửa để xem chi tiết</span>



              </div>



              <div id="cadDoorsGallery" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">



                <!-- Populated dynamically -->



              </div>



            </div>



          </div>







          <!-- SUBTAB 3: ORIGINAL DÁN TEXT CAD -->



          <div id="cad-subtab-text" class="hidden space-y-3.5 text-xs">



            <div>



              <label class="block font-bold text-slate-700 mb-1">Mặt bằng Revit đích:</label>



              <select id="cadTargetView" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600">



                <option value="2361036">04 - MẶT BẰNG TẦNG 4</option>



                <option value="312">01 - MẶT BẰNG TẦNG 1</option>



                <option value="695">02 - MẶT BẰNG TẦNG 2</option>



                <option value="1727585">03 - MẶT BẰNG TẦNG 3</option>



                <option value="active">View hiện hành đang mở</option>



              </select>



            </div>



            <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 space-y-1 leading-relaxed">



              <p>&bull; Yêu cầu: Bạn chỉ cần chọn (quét chọn) các Text trong AutoCAD trước khi bấm nút.</p>



              <p>&bull; Tự động xử lý bảng mã: Bảng mã VNI, TCVN3 &rarr; Unicode chuẩn tiếng Việt.</p>



            </div>



            <div class="pt-2">



              <button onclick="runPasteCadText()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group cursor-pointer" title="Dán Text AutoCAD sang Revit">



                <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



              </button>



            </div>



          </div>



        </div>







        <!-- TAB CONTENT 6: 3DS MAX SYNC -->



        <div id="tab-max" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="box" class="w-5 h-5 text-amber-600"></i> Đồng bộ mô hình từ 3ds Max sang Revit



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 font-bold border border-amber-200">ACIS SAT &rarr; FreeForm Solid</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Xuất vật thể 3ds Max qua định dạng trung gian <strong>ACIS SAT</strong>, tự động chuyển đổi thành <strong>FreeFormElement Solid</strong> chuẩn Revit – hỗ trợ cắt lát 2D và mặt cắt hoàn hảo, không chia nét tam giác.</p>



          </div>







          <div class="space-y-3 text-xs">



            <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 space-y-1.5 leading-relaxed">



              <div class="flex items-center gap-1.5 font-bold text-slate-900">



                <i data-lucide="mouse-pointer-click" class="w-4 h-4 text-amber-600"></i>



                <span>Tự động nhận diện đối tượng đang chọn trong Revit</span>



              </div>



              <p class="text-slate-600">&bull; <strong>Không cần nhập tên Family:</strong> Hệ thống tự động lấy chính đối tượng/Family bạn đang click chọn trên màn hình Revit để cập nhật hình học mới.</p>



              <p class="text-slate-600">&bull; <strong>Chuẩn B-Rep Solid (FreeFormElement):</strong> Tự động biến đổi Editable Poly &rarr; Body Object &rarr; ACIS SAT &rarr; FreeFormElement, giúp Revit cắt lát (Slice) và tô Hatch ruột đặc trên mọi tầng.</p>



              <p class="text-amber-800 text-[11px] font-medium pt-1">&bull; Hướng dẫn: Bạn chỉ cần click chọn 1 đối tượng/Family trong Revit (hoặc để trống để tạo mới), chọn các vật thể trong 3ds Max, rồi bấm nút Play.</p>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runSyncMaxToRevit()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Đồng bộ 3ds Max sang Revit">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 7: XUẤT REVIT SANG 3DS MAX POLY SẠCH -->



        <div id="tab-revit-to-max" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="share-2" class="w-5 h-5 text-orange-600"></i> Xuất Vật Thể Sang 3ds Max (Editable Poly Sạch)



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-orange-50 text-orange-700 font-bold border border-orange-200">No Triangulation</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Xuất hình học dạng khối 3D ACIS Solids và kịch bản tự động Quadrify biến đổi thành Editable Poly phẳng sạch, không bị chia đường chéo tam giác.</p>



          </div>







          <div class="space-y-3.5 text-xs">



            <div>



              <label class="block font-bold text-slate-700 mb-1">Tên file DWG Solids đầu ra:</label>



              <input type="text" id="revitToMaxFileName" value="Revit_To_Max_Solids" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-indigo-600">



            </div>



            <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 space-y-1.5 leading-relaxed">



              <p class="font-bold text-slate-800 flex items-center gap-1.5">



                <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600"></i> Cơ chế chống chia tam giác (Zero-Triangles):



              </p>



              <p>&bull; <strong>Bước 1 (Revit):</strong> Sử dụng bộ xuất ACIS B-Rep Solids nguyên bản, không dùng Polymesh nên giữ nguyên các mặt phẳng Quad toán học.</p>



              <p>&bull; <strong>Bước 2 (3ds Max):</strong> Tự động convert sang Editable Poly và thực thi thuật toán Quadrify loại bỏ 100% đường chéo tam giác nội suy.</p>



              <p class="text-amber-800 text-[11px] font-medium pt-1">&bull; Mẹo: Nếu bạn quét chọn các vật thể trên Revit, chỉ các vật thể đó được xuất. Nếu không chọn gì, toàn bộ view 3D sẽ được xuất.</p>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runExportRevitToMaxPoly()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Xuất sang 3ds Max dạng Editable Poly">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 8: CHUYỂN POLYLINE AUTOCAD SANG SÀN REVIT (SLAB) -->



        <div id="tab-cad-slab" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="layers" class="w-5 h-5 text-teal-600"></i> Chuyển Polyline AutoCAD ➔ Sàn Revit (Slab)



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-700 font-bold border border-teal-200">Auto CAD ➔ Revit</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Trích xuất đường bao Polyline khép kín đang chọn trong AutoCAD và tự động dựng thành Sàn (Slab) trong Revit, tự động thay thế nếu đang chọn Sàn trong Revit.</p>



          </div>







          <div class="space-y-3.5 text-xs">



            <!-- Loại Sàn -->



            <div>



              <label class="block font-bold text-slate-700 mb-1.5">Loại Sàn (Floor Category):</label>



              <div class="grid grid-cols-2 gap-2">



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="slabCategory" value="standard" checked onchange="updateSlabPresets()" class="text-teal-600 focus:ring-teal-500">



                  <div>



                    <div class="font-bold text-slate-900">🏢 Sàn thường</div>



                    <div class="text-[10px] text-slate-500">Bê tông cốt thép phẳng</div>



                  </div>



                </label>



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="slabCategory" value="toilet" onchange="updateSlabPresets()" class="text-teal-600 focus:ring-teal-500">



                  <div>



                    <div class="font-bold text-slate-900">🚽 Sàn vệ sinh / Hatch</div>



                    <div class="text-[10px] text-slate-500">Nền WC gạch chéo 45°</div>



                  </div>



                </label>



              </div>



            </div>







            <!-- Kích thước sàn & Cao độ offset -->



            <div class="grid grid-cols-2 gap-3">



              <div>



                <label class="block font-bold text-slate-700 mb-1">Độ dày sàn (Thickness mm):</label>



                <input type="number" id="slabThickness" value="100" step="10" min="20" max="1000" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-teal-600">



              </div>



              <div>



                <label class="block font-bold text-slate-700 mb-1">Cao độ lệch (Offset mm):</label>



                <input type="number" id="slabOffset" value="0" step="5" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-teal-600">



              </div>



            </div>







            <!-- Tầng / Cao độ (Level) -->



            <div>



              <label class="block font-bold text-slate-700 mb-1">Cao độ / Tầng đặt sàn:</label>



              <select id="slabTargetLevel" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-teal-600">



                <option value="-1">Tự động (Theo sàn đang chọn hoặc View đang mở)</option>



                <option value="311">01.MẶT BẰNG TẦNG 1 (±0.000m)</option>



                <option value="694">02.MẶT BẰNG TẦNG 2 (+4.200m)</option>



                <option value="1727584">03.MẶT BẰNG TẦNG 3 (+7.800m)</option>



                <option value="2360634">04.MẶT BẰNG TẦNG 4 (+11.400m)</option>



                <option value="2360635">06.MẶT BẰNG TẦNG TUM (+14.400m)</option>



                <option value="2360636">07.MẶT BẰNG MÁI (+17.400m)</option>



              </select>



            </div>







            <!-- Cơ chế thông minh: Tự động thay thế nếu đang chọn sàn trong Revit -->



            <div class="p-3.5 rounded-xl bg-teal-50/60 border border-teal-200 text-teal-900 space-y-1.5 leading-relaxed">



              <p class="font-bold flex items-center gap-1.5 text-teal-800">



                <i data-lucide="sparkles" class="w-4 h-4 text-teal-600"></i> Cơ chế Thay Thế Tự Động (Smart Replace):



              </p>



              <p class="text-teal-700">&bull; <strong>Nếu trong Revit đang click chọn 1 Sàn (Slab):</strong> Hệ thống sẽ tự động <strong>THAY THẾ</strong> sàn đó bằng đường bao Polyline mới từ CAD mà vẫn giữ đúng tầng và cao độ.</p>



              <p class="text-teal-700">&bull; <strong>Nếu không chọn sàn:</strong> Hệ thống sẽ tự động <strong>TẠO MỚI</strong> sàn tại Tầng/View bạn đang mở.</p>



              <p class="text-teal-800 font-medium pt-0.5">&bull; Cách dùng: Chọn Polyline khép kín bên AutoCAD ➔ Bấm nút Play bên dưới.</p>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runConvertCadPolylineToSlab()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Chuyển Polyline CAD sang Sàn Revit">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 9: ĐỒNG BỘ VỊ TRÍ CỬA CÁC TẦNG THEO TẦNG 1 -->



        <div id="tab-sync-openings" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">



                <i data-lucide="sliders-horizontal" class="w-5 h-5 text-blue-600"></i> Đồng bộ Vị trí Cửa theo Tầng 1



              </h2>



              <span class="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-bold border border-blue-200">Axis Sync</span>



            </div>



            <p class="text-xs text-slate-500 mt-1">Căn chỉnh tọa độ (X hoặc Y) của cửa sổ / cửa đi các tầng trên khớp chính xác với cửa cùng ô trục ở Tầng 1.</p>



          </div>







          <div class="space-y-4 text-xs">



            <!-- 1. Lựa chọn Loại cửa -->



            <div>



              <label class="block font-bold text-slate-700 mb-1.5">Loại đối tượng cần đồng bộ:</label>



              <div class="grid grid-cols-3 gap-2">



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="syncCategory" value="windows" checked class="text-blue-600 focus:ring-blue-500">



                  <div>



                    <div class="font-bold text-slate-900">🪟 Cửa sổ</div>



                    <div class="text-[10px] text-slate-500">OST_Windows</div>



                  </div>



                </label>



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="syncCategory" value="doors" class="text-blue-600 focus:ring-blue-500">



                  <div>



                    <div class="font-bold text-slate-900">🚪 Cửa đi</div>



                    <div class="text-[10px] text-slate-500">OST_Doors</div>



                  </div>



                </label>



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="syncCategory" value="all" class="text-blue-600 focus:ring-blue-500">



                  <div>



                    <div class="font-bold text-slate-900">✨ Cả hai</div>



                    <div class="text-[10px] text-slate-500">Cửa sổ & Cửa đi</div>



                  </div>



                </label>



              </div>



            </div>







            <!-- 2. Lựa chọn Phương trục đồng bộ (X hoặc Y) -->



            <div>



              <label class="block font-bold text-slate-700 mb-1.5">Chọn phương trục căn chỉnh:</label>



              <div class="grid grid-cols-2 gap-3">



                <label class="flex items-start gap-2.5 p-3 rounded-xl border-2 border-blue-500/60 bg-blue-50/40 hover:bg-blue-50 cursor-pointer transition select-none">



                  <input type="radio" name="syncAxisDirection" value="X" checked onchange="updateSyncAxesHelp()" class="mt-0.5 text-blue-600 focus:ring-blue-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1">



                      <span>📐 Phương Trục X</span>



                      <span class="text-[10px] px-1.5 py-0.2 rounded bg-blue-100 text-blue-800 font-semibold">Tường Ngang</span>



                    </div>



                    <div class="text-[11px] text-slate-600 mt-1 leading-snug">



                      Đồng bộ <strong>tọa độ X</strong> theo Tầng 1. Dành cho các tường chạy ngang dọc trục chữ (Trục A, E, C, D...). Cửa cùng ô trục số (2-3, 3-4...) sẽ có cùng X.



                    </div>



                  </div>



                </label>







                <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="syncAxisDirection" value="Y" onchange="updateSyncAxesHelp()" class="mt-0.5 text-blue-600 focus:ring-blue-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1">



                      <span>📏 Phương Trục Y</span>



                      <span class="text-[10px] px-1.5 py-0.2 rounded bg-indigo-100 text-indigo-800 font-semibold">Tường Dọc</span>



                    </div>



                    <div class="text-[11px] text-slate-600 mt-1 leading-snug">



                      Đồng bộ <strong>tọa độ Y</strong> theo Tầng 1. Dành cho các tường chạy dọc trục số (Trục 1, 11, 2...). Cửa cùng ô trục chữ (A-B, B-C...) sẽ có cùng Y.



                    </div>



                  </div>



                </label>



              </div>



            </div>







            <!-- 3. Bộ lọc Trục cụ thể & Chế độ thực thi -->



            <div class="grid grid-cols-3 gap-3">



              <div class="col-span-2">



                <label class="block font-bold text-slate-700 mb-1">



                  Bộ lọc trục tường áp dụng:



                  <span id="syncAxesHelpText" class="font-normal text-slate-500 ml-1">(VD: A, E hoặc để 'all' cho tất cả)</span>



                </label>



                <div class="flex gap-2">



                  <select id="syncAxesPreset" onchange="applySyncAxesPreset()" class="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-blue-600">



                    <option value="all">Tất cả trục (All)</option>



                    <option value="A, E">Trục A, E (Mặt tiền & Hậu)</option>



                    <option value="C">Trục C (Hành lang)</option>



                    <option value="D">Trục D (Phòng làm việc)</option>



                    <option value="custom">Tự nhập...</option>



                  </select>



                  <input type="text" id="syncTargetAxes" value="all" placeholder="VD: A, E hoặc all" class="flex-1 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-medium focus:bg-white focus:outline-none focus:border-blue-600">



                </div>



              </div>







              <div>



                <label class="block font-bold text-slate-700 mb-1">Chế độ thực thi:</label>



                <label class="flex items-center gap-2 p-2 bg-slate-50 border border-slate-300 rounded-lg cursor-pointer hover:bg-slate-100 transition select-none mt-0.5">



                  <input type="checkbox" id="syncApplyMove" checked class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500">



                  <span class="font-bold text-slate-800 text-[11px]">Thực thi dịch chuyển</span>



                </label>



              </div>



            </div>







            <!-- Explainer Card -->



            <div class="p-3.5 rounded-xl bg-blue-50/60 border border-blue-200 text-blue-900 space-y-1.5 leading-relaxed">



              <p class="font-bold flex items-center gap-1.5 text-blue-800">



                <i data-lucide="info" class="w-4 h-4 text-blue-600"></i> Nguyên lý ghép đôi & dịch chuyển:



              </p>



              <p class="text-blue-700">&bull; <strong>Phương X:</strong> Tìm các cửa ở Tầng 2, 3, 4 thuộc cùng ô trục X (vd: 2-3, 3-4...) và cùng trục tường Y. Tọa độ X của cửa tầng trên sẽ được gán bằng tọa độ X của cửa Tầng 1.</p>



              <p class="text-blue-700">&bull; <strong>Phương Y:</strong> Tương tự, đồng bộ tọa độ Y theo cửa Tầng 1 cho các bức tường chạy dọc (vd: Trục 1, 11...).</p>



              <p class="text-blue-800 font-medium pt-0.5">&bull; Bỏ tích "Thực thi dịch chuyển" nếu bạn chỉ muốn xem trước danh sách độ lệch (Preview) trong Console.</p>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runSyncOpeningsByFloor1()" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Đồng bộ vị trí cửa theo Tầng 1">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 10: ẨN / HIỆN TAG CỬA ĐI & CỬA SỔ -->



        <div id="tab-tags" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <div class="flex items-center gap-2">



                <span class="p-2 rounded-xl bg-pink-50 text-pink-600 border border-pink-100">



                  <i data-lucide="tags" class="w-5 h-5"></i>



                </span>



                <div>



                  <h2 class="text-base font-bold text-slate-900">10. Quản Lý Ẩn / Hiện Tag Cửa Đi & Cửa Sổ</h2>



                  <p class="text-xs text-slate-500">Bật/Tắt hiển thị Door Tags & Window Tags theo từng tầng hoặc toàn bộ công trình</p>



                </div>



              </div>



              <button onclick="loadTagsStatus()" class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 flex items-center gap-1.5 transition" title="Làm mới trạng thái">



                <i data-lucide="refresh-cw" class="w-3.5 h-3.5" id="tagsRefreshIcon"></i>



                <span>Làm mới</span>



              </button>



            </div>



          </div>







          <div class="space-y-4 text-xs">



            <!-- 1. Lựa chọn Loại Tag -->



            <div>



              <label class="block font-bold text-slate-700 mb-1.5">Chọn loại Tag đối tượng:</label>



              <div class="grid grid-cols-3 gap-2.5">



                <label class="flex items-center gap-2 p-2.5 rounded-xl border-2 border-pink-500/60 bg-pink-50/40 hover:bg-pink-50 cursor-pointer transition select-none">



                  <input type="radio" name="tagCategory" value="all" checked class="text-pink-600 focus:ring-pink-500">



                  <div>



                    <div class="font-bold text-slate-900">✨ Cả hai</div>



                    <div class="text-[10px] text-slate-500">Cửa đi & Cửa sổ</div>



                  </div>



                </label>



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="tagCategory" value="door" class="text-pink-600 focus:ring-pink-500">



                  <div>



                    <div class="font-bold text-slate-900">🚪 Tag Cửa Đi</div>



                    <div class="text-[10px] text-slate-500">Door Tags (D1, D2...)</div>



                  </div>



                </label>



                <label class="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                  <input type="radio" name="tagCategory" value="window" class="text-pink-600 focus:ring-pink-500">



                  <div>



                    <div class="font-bold text-slate-900">🪟 Tag Cửa Sổ</div>



                    <div class="text-[10px] text-slate-500">Window Tags (S1, K2...)</div>



                  </div>



                </label>



              </div>



            </div>







            <!-- 2. Lựa chọn Phạm vi Tầng & Hành động -->



            <div class="grid grid-cols-2 gap-3">



              <div>



                <label class="block font-bold text-slate-700 mb-1">Chọn phạm vi tầng áp dụng:</label>



                <select id="tagsLevelSelect" class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-semibold focus:bg-white focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent">



                  <option value="all">⭐ Tất cả các tầng (All Levels)</option>



                </select>



                <p class="text-[11px] text-slate-400 mt-1">Chọn 'Tất cả các tầng' để áp dụng đồng loạt cho toàn dự án.</p>



              </div>







              <div>



                <label class="block font-bold text-slate-700 mb-1">Hành động thực hiện:</label>



                <div class="grid grid-cols-2 gap-2">



                  <label class="flex items-center gap-2 p-2 rounded-xl border-2 border-rose-500/60 bg-rose-50/40 hover:bg-rose-50 cursor-pointer transition select-none">



                    <input type="radio" name="tagActionType" value="hide" checked class="text-rose-600 focus:ring-rose-500">



                    <div>



                      <div class="font-bold text-rose-900">🙈 ẨN TAG</div>



                      <div class="text-[10px] text-rose-600">Thoáng mặt bằng</div>



                    </div>



                  </label>



                  <label class="flex items-center gap-2 p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none">



                    <input type="radio" name="tagActionType" value="show" class="text-emerald-600 focus:ring-emerald-500">



                    <div>



                      <div class="font-bold text-emerald-900">👁 HIỆN TAG</div>



                      <div class="text-[10px] text-emerald-600">Kiểm tra ký hiệu</div>



                    </div>



                  </label>



                </div>



              </div>



            </div>







            <!-- 3. Bảng trạng thái trực quan các tầng (Live Tag Status Table) -->



            <div>



              <div class="flex items-center justify-between mb-1.5">



                <label class="font-bold text-slate-700">Trạng thái Tag theo từng Mặt bằng:</label>



                <span id="tagsSummaryBadge" class="text-[11px] text-slate-500 font-medium">Đang tải...</span>



              </div>



              <div class="border border-slate-200 rounded-xl overflow-hidden shadow-xs max-h-56 overflow-y-auto">



                <table class="w-full text-left text-xs">



                  <thead class="bg-slate-100/90 text-slate-600 font-bold sticky top-0 border-b border-slate-200 select-none">



                    <tr>



                      <th class="py-2 px-3">Mặt Bằng Tầng</th>



                      <th class="py-2 px-3 text-center">Tag Cửa Đi</th>



                      <th class="py-2 px-3 text-center">Tag Cửa Sổ</th>



                      <th class="py-2 px-3 text-right">Thao tác nhanh</th>



                    </tr>



                  </thead>



                  <tbody id="tagsStatusTableBody" class="divide-y divide-slate-100 bg-white">



                    <tr>



                      <td colspan="4" class="py-4 text-center text-slate-400">Đang quét danh sách tag...</td>



                    </tr>



                  </tbody>



                </table>



              </div>



            </div>







            <!-- Explainer Card -->



            <div class="p-3.5 rounded-xl bg-pink-50/60 border border-pink-200 text-pink-900 space-y-1 leading-relaxed">



              <p class="font-bold flex items-center gap-1.5 text-pink-800">



                <i data-lucide="info" class="w-4 h-4 text-pink-600"></i> Cơ chế kiểm soát Tag chuyên nghiệp:



              </p>



              <p class="text-pink-700">&bull; <strong>Ẩn Tag:</strong> Giúp bản vẽ mặt bằng sạch sẽ, thoáng mắt khi xuất CAD bố trí nội thất hoặc sơ đồ công năng.</p>



              <p class="text-pink-700">&bull; <strong>Hiện Tag:</strong> Khôi phục đầy đủ ký hiệu D1, D2, S1, K2... phục vụ xuất bản vẽ kỹ thuật và hồ sơ thi công.</p>



              <p class="text-pink-800 font-medium">&bull; Hệ thống tự động xử lý an toàn kể cả khi Mặt bằng có áp dụng View Template.</p>



            </div>



          </div>







          <div class="pt-3">



            <button onclick="runTagVisibilityAction()" id="btnRunTagVisibility" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-700 hover:via-sky-700 hover:to-cyan-700 text-white shadow-md shadow-blue-500/25 flex items-center justify-center transition active:scale-[0.98] group" title="Thực thi Ẩn / Hiện Tag Cửa">



              <i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>



            </button>



          </div>



        </div>







        <!-- TAB CONTENT 11: XÓA HATCH SOLID & KÉO LEADER CAO ĐỘ MEP -->



        <div id="tab-mep-cad" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <div class="flex items-center gap-2">



                <span class="p-2 rounded-xl bg-rose-50 text-rose-600 border border-rose-100">



                  <i data-lucide="sparkles" class="w-5 h-5"></i>



                </span>



                <div>



                  <h2 class="text-base font-bold text-slate-900">11. Xóa Hatch Solid & Kéo Leader Cao Độ MEP AutoCAD</h2>



                  <p class="text-xs text-slate-500">Xóa triệt để Solid/Hatch trong Block & Kéo đường Leader nghiêng từ Text cao độ (+) đến tâm tuyến ống gần nhất</p>



                </div>



              </div>



              <span class="text-[11px] px-2.5 py-1 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200">



                AutoCAD 2022



              </span>



            </div>



          </div>







          <div class="space-y-4 text-xs">



            <!-- 1. Phạm vi thực thi (Target Scope) -->



            <div>



              <label class="block font-bold text-slate-700 mb-1.5">1. Chọn đối tượng / phạm vi bản vẽ:</label>



              <div class="grid grid-cols-3 gap-2.5">



                <label class="flex items-start gap-2.5 p-3 rounded-xl border-2 border-rose-500 bg-rose-50/50 cursor-pointer transition select-none" id="scopeCardActive">



                  <input type="radio" name="mepCadScope" value="active" checked onchange="toggleMepCadScope(this.value)" class="mt-0.5 text-rose-600 focus:ring-rose-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1.5">



                      <i data-lucide="monitor" class="w-3.5 h-3.5 text-rose-600"></i> AutoCAD Đang Mở



                    </div>



                    <div class="text-[10px] text-slate-500 mt-0.5">Bản vẽ active trong AutoCAD hiện tại (COM Automation)</div>



                  </div>



                </label>



                <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none" id="scopeCardFolder">



                  <input type="radio" name="mepCadScope" value="folder" onchange="toggleMepCadScope(this.value)" class="mt-0.5 text-rose-600 focus:ring-rose-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1.5">



                      <i data-lucide="folder-kanban" class="w-3.5 h-3.5 text-indigo-600"></i> Cả Thư Mục DWG



                    </div>



                    <div class="text-[10px] text-slate-500 mt-0.5">Xử lý toàn bộ 48 file DWG Coolermaster Phase 2 (Headless)</div>



                  </div>



                </label>



                <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none" id="scopeCardFile">



                  <input type="radio" name="mepCadScope" value="file" onchange="toggleMepCadScope(this.value)" class="mt-0.5 text-rose-600 focus:ring-rose-500">



                  <div>



                    <div class="font-bold text-slate-900 flex items-center gap-1.5">



                      <i data-lucide="file-code" class="w-3.5 h-3.5 text-emerald-600"></i> File DWG Cụ Thể



                    </div>



                    <div class="text-[10px] text-slate-500 mt-0.5">Chỉ định 1 đường dẫn file .dwg bất kỳ trên máy</div>



                  </div>



                </label>



              </div>



            </div>







            <!-- Path Inputs (hiển thị khi chọn file hoặc folder) -->



            <div id="mepCadPathContainer" class="hidden space-y-2 p-3 bg-slate-50 rounded-xl border border-slate-200">



              <div id="mepCadFolderGroup">



                <label class="block font-bold text-slate-700 mb-1">Đường dẫn thư mục DWG hàng loạt:</label>



                <input type="text" id="mepCadFolderPath" value="D:/Dropbox/_Documents/_KIEN TRUC 2026/CM Fire Protect/Coolermaster 2 - BIM model/DWG_MEP_Coolermaster_Phase2" class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:outline-none focus:ring-2 focus:ring-rose-500">



              </div>



              <div id="mepCadFileGroup" class="hidden">



                <label class="block font-bold text-slate-700 mb-1">Đường dẫn file DWG:</label>



                <input type="text" id="mepCadFilePath" placeholder="D:/path/to/drawing.dwg" class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-mono text-[11px] focus:outline-none focus:ring-2 focus:ring-rose-500">



              </div>



            </div>







            <!-- 2. Cấu hình thông số lọc (Parameters) -->



            <div class="grid grid-cols-4 gap-3">



              <div>



                <label class="block font-bold text-slate-700 mb-1">Layer tuyến ống Line/Polyline:</label>



                <div class="relative">



                  <input type="text" id="mepCadLayer" value="P-PIPE" class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-bold focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500">



                  <span class="absolute right-2.5 top-2.5 w-3 h-3 rounded-full bg-red-600 border border-white shadow-xs" title="Màu Layer"></span>



                </div>



                <div class="flex gap-1.5 mt-1.5 flex-wrap">



                  <button type="button" onclick="document.getElementById('mepCadLayer').value='P-PIPE'" class="text-[10px] px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded font-semibold hover:bg-red-100">P-PIPE</button>



                  <button type="button" onclick="document.getElementById('mepCadLayer').value='P-PIPE-CNTR'" class="text-[10px] px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded font-semibold hover:bg-red-100">P-PIPE-CNTR</button>



                  <button type="button" onclick="document.getElementById('mepCadLayer').value='M-DUCT-CNTR'" class="text-[10px] px-1.5 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded font-semibold hover:bg-blue-100">M-DUCT-CNTR</button>



                  <button type="button" onclick="document.getElementById('mepCadLayer').value='E-CABL-CNTR'" class="text-[10px] px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded font-semibold hover:bg-amber-100">E-CABL-CNTR</button>



                </div>



              </div>







              <div>



                <label class="block font-bold text-slate-700 mb-1">Ký tự nhận diện Text cao độ:</label>



                <input type="text" id="mepCadSearchChar" value="+" class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-bold text-center focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500">



                <p class="text-[11px] text-slate-400 mt-1">Lọc Text/MText có chứa dấu <code>+</code> (e.g. <code>25ø • BOP +4.067</code>)</p>



              </div>







              <div>



                <label class="block font-bold text-slate-700 mb-1">Bán kính quét tối đa (mm):</label>



                <input type="number" id="mepCadMaxDist" value="5000" step="500" class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-semibold focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500">



                <p class="text-[11px] text-slate-400 mt-1">Khoảng cách xa nhất từ Text đến tim ống (Mặc định: 5000 mm)</p>



              </div>







              <div>



                <label class="block font-bold text-slate-700 mb-1">Hạ thấp leader trục Y (mm):</label>



                <input type="number" id="mepCadOffsetY" value="250" step="50" class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-semibold focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500">



                <p class="text-[11px] text-slate-400 mt-1">Dịch điểm xuất phát xuống dưới chân chữ (Mặc định: 250 mm)</p>



              </div>



            </div>







            <!-- Explainer Card -->



            <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 leading-relaxed">



              <div class="font-bold flex items-center gap-1.5 text-slate-800">



                <i data-lucide="info" class="w-4 h-4 text-rose-600"></i> Cơ chế xử lý 2 trong 1:



              </div>



              <div class="grid grid-cols-2 gap-3 text-[11px] text-slate-600">



                <div class="bg-white p-2.5 rounded-lg border border-slate-200">



                  <div class="font-bold text-rose-700 flex items-center gap-1">



                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i> 1. Xóa Hatch Solid & Solid



                  </div>



                  <p class="mt-1">Duyệt sạch mọi đối tượng Hatch SOLID và AcDbSolid trong ModelSpace, PaperSpace và <strong>bên trong tất cả Block</strong> mà không làm vỡ liên kết block.</p>



                </div>



                <div class="bg-white p-2.5 rounded-lg border border-slate-200">



                  <div class="font-bold text-indigo-700 flex items-center gap-1">



                    <i data-lucide="git-commit" class="w-3.5 h-3.5"></i> 2. Kéo Leader Nghiêng Cao Độ



                  </div>



                  <p class="mt-1">Tự động phân tích Bounding Box text: nếu ống nằm bên trái &rarr; kéo từ đáy góc trái; bên phải &rarr; kéo từ đáy góc phải, tạo đường xiên nghiêng chuẩn kỹ thuật.</p>



                </div>



              </div>



            </div>







            <!-- Action Buttons Grid -->



            <div class="pt-2 grid grid-cols-3 gap-3">



              <button onclick="runMepCadAction('delete_solids')" id="btnCadDeleteSolids" class="py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 border border-slate-200 text-slate-800 font-bold flex items-center justify-center gap-2 transition active:scale-[0.98]">



                <i data-lucide="trash-2" class="w-4 h-4 text-rose-600"></i>



                <span>Chỉ Xóa Solid / Hatch</span>



              </button>







              <button onclick="runMepCadAction('add_leaders')" id="btnCadAddLeaders" class="py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 border border-slate-200 text-slate-800 font-bold flex items-center justify-center gap-2 transition active:scale-[0.98]">



                <i data-lucide="git-branch" class="w-4 h-4 text-indigo-600"></i>



                <span>Chỉ Kéo Leader Nghiêng</span>



              </button>







              <button onclick="runMepCadAction('full')" id="btnCadFullPolish" class="py-2.5 px-4 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-indigo-600 hover:from-rose-700 hover:via-pink-700 hover:to-indigo-700 text-white font-bold shadow-md shadow-rose-500/25 flex items-center justify-center gap-2 transition active:scale-[0.98] group">



                <i data-lucide="sparkles" class="w-4 h-4 group-hover:scale-110 transition-transform"></i>



                <span>⚡ Chạy Toàn Bộ (2 Trong 1)</span>



              </button>



            </div>



          </div>



        </div>







        <!-- TAB CONTENT 12: LỌC KHUNG TÊN & IN HÀNG LOẠT (BATCH PLOT) -->



        <div id="tab-cad-plot" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">



          <div class="border-b border-slate-100 pb-3">



            <div class="flex items-center justify-between">



              <div class="flex items-center gap-2">



                <span class="p-2 rounded-xl bg-teal-50 text-teal-600 border border-teal-100">



                  <i data-lucide="printer" class="w-5 h-5"></i>



                </span>



                <div>



                  <h2 class="text-base font-bold text-slate-900">12. Lọc Khung Tên & In Hàng Loạt AutoCAD (Batch Plot)</h2>



                  <p class="text-xs text-slate-500">Tự động bóc tách mảng Associative Array, nhận diện khung có nội dung bản vẽ, sắp xếp X &rarr; Y và xuất Region in ấn</p>



                </div>



              </div>



              <div class="flex items-center gap-2">



                <span class="text-[11px] px-2.5 py-1 rounded-full bg-teal-100 text-teal-700 font-bold border border-teal-200">



                  Array Decomposition



                </span>



                <span class="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-bold border border-slate-200">



                  AutoCAD 2022



                </span>



              </div>



            </div>



          </div>







          <div class="space-y-4 text-xs">



            <!-- 1. Cấu hình quét & lọc -->



            <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-3">



              <div class="font-bold text-slate-800 flex items-center justify-between">



                <span class="flex items-center gap-1.5">



                  <i data-lucide="scan-search" class="w-4 h-4 text-teal-600"></i> 1. Cấu hình Quét & Lọc Khung Tên



                </span>



                <span class="text-[10px] text-slate-500">Hỗ trợ Block Mảng *U... & Block Khung Đơn Lẻ</span>



              </div>







              <div class="grid grid-cols-1 md:grid-cols-3 gap-3">



                <!-- Phạm vi quét -->



                <div>



                  <label class="block font-bold text-slate-700 mb-1">Phạm vi quét:</label>



                  <select id="cadPlotScope" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 font-medium focus:ring-1 focus:ring-teal-500">



                    <option value="selection" selected>Đối tượng đang chọn (Selection / Array)</option>



                    <option value="all">Toàn bộ ModelSpace bản vẽ</option>



                  </select>



                </div>







                <!-- Thứ tự sắp xếp -->



                <div>



                  <label class="block font-bold text-slate-700 mb-1">Thứ tự sắp xếp in:</label>



                  <select id="cadPlotSortMode" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 font-medium focus:ring-1 focus:ring-teal-500">



                    <option value="x_then_y" selected>Tăng dần theo X &rarr; Tăng dần theo Y</option>



                    <option value="y_then_x">Tăng dần theo Y &rarr; Tăng dần theo X</option>



                  </select>



                </div>







                <!-- Tùy chọn lọc khung trống -->



                <div class="flex items-center pt-5">



                  <label class="flex items-center gap-2 cursor-pointer font-bold text-slate-700">



                    <input type="checkbox" id="cadPlotSkipEmpty" checked class="rounded border-slate-300 text-teal-600 focus:ring-0">



                    <span>Chỉ lấy khung có nội dung (Bỏ khung trống)</span>



                  </label>



                </div>



              </div>







              <div class="pt-1">



                <button onclick="runScanCadTitleblocks()" id="btnScanCadPlot" class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-teal-600 via-emerald-600 to-cyan-600 hover:from-teal-700 hover:via-emerald-700 hover:to-cyan-700 text-white font-bold shadow-md shadow-teal-500/20 flex items-center justify-center gap-2 transition active:scale-[0.98]">



                  <i data-lucide="search" class="w-4 h-4"></i>



                  <span>Quét & Phân Tích Khung Tên AutoCAD Ngay</span>



                </button>



              </div>



            </div>







            <!-- 2. Thống kê kết quả & Bảng danh sách Region -->



            <div class="border border-slate-200 rounded-xl overflow-hidden bg-white">



              <!-- Summary Bar -->



              <div class="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">



                <div class="flex items-center gap-3">



                  <span class="font-bold text-slate-800 flex items-center gap-1.5">



                    <i data-lucide="layout-grid" class="w-4 h-4 text-teal-600"></i> Danh Sách Vùng In (Regions)



                  </span>



                  <div class="flex items-center gap-1.5 text-[11px]">



                    <span class="px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">Tổng: <strong id="statCadPlotTotal">0</strong></span>



                    <span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">Có nội dung: <strong id="statCadPlotContent">0</strong></span>



                    <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">Khung trống: <strong id="statCadPlotEmpty">0</strong></span>



                  </div>



                </div>



                <div class="flex items-center gap-2 text-xs">



                  <label class="flex items-center gap-1.5 cursor-pointer font-medium text-slate-600">



                    <input type="checkbox" id="cadPlotCheckAll" onchange="toggleSelectAllCadPlots(this)" checked class="rounded border-slate-300 text-teal-600 focus:ring-0">



                    <span>Chọn tất cả</span>



                  </label>



                </div>



              </div>







              <!-- Table Container -->



              <div class="max-h-[320px] overflow-y-auto">



                <table class="w-full text-left text-xs border-collapse">



                  <thead class="bg-slate-100/70 text-slate-600 text-[11px] font-bold uppercase sticky top-0 border-b border-slate-200">



                    <tr>



                      <th class="p-2.5 w-10 text-center">Chọn</th>



                      <th class="p-2.5 w-12 text-center">STT</th>



                      <th class="p-2.5 w-20">Vị trí</th>



                      <th class="p-2.5 min-w-[200px]">Tên Bản Vẽ (Sheet Title)</th>



                      <th class="p-2.5 w-28">Phân loại</th>



                      <th class="p-2.5 w-44">Tọa độ Region (Min &rarr; Max)</th>



                      <th class="p-2.5 w-28 text-center">Kích thước</th>



                      <th class="p-2.5 w-16 text-center">Đối tượng</th>



                      <th class="p-2.5 w-24 text-center">Thao tác</th>



                    </tr>



                  </thead>



                  <tbody id="cadPlotTableBody" class="divide-y divide-slate-100 font-mono text-[11px]">



                    <tr>



                      <td colspan="9" class="p-6 text-center text-slate-400 font-sans">



                        Chưa có dữ liệu. Bấm <strong>"Quét & Phân Tích Khung Tên AutoCAD Ngay"</strong> để tự động bóc tách các mảng titleblock.



                      </td>



                    </tr>



                  </tbody>



                </table>



              </div>



            </div>







            <!-- 3. Cấu hình in ấn & Xuất Batch Plot -->



            <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-3">



              <div class="font-bold text-slate-800 flex items-center justify-between">



                <span class="flex items-center gap-1.5">



                  <i data-lucide="settings" class="w-4 h-4 text-teal-600"></i> 2. Thiết Lập Máy In & Xuất Batch Plot PDF



                </span>



                <span class="text-[10px] text-slate-500">In trực tiếp qua lệnh -PLOT Window</span>



              </div>







              <div class="grid grid-cols-1 md:grid-cols-4 gap-2.5">



                <div>



                  <label class="block font-bold text-slate-700 mb-1">Máy in / Driver:</label>



                  <select id="cadPlotDevice" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 text-xs font-medium focus:ring-1 focus:ring-teal-500">



                    <option value="DWG To PDF.pc3" selected>DWG To PDF.pc3 (Mặc định)</option>



                    <option value="AutoCAD PDF (General Documentation).pc3">AutoCAD PDF (General Doc).pc3</option>



                    <option value="AutoCAD PDF (High Quality Print).pc3">AutoCAD PDF (High Quality).pc3</option>



                    <option value="Microsoft Print to PDF">Microsoft Print to PDF</option>



                  </select>



                </div>



                <div>



                  <label class="block font-bold text-slate-700 mb-1">Khổ giấy in:</label>



                  <select id="cadPlotPaperSize" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 text-xs font-medium focus:ring-1 focus:ring-teal-500">



                    <option value="ISO_full_bleed_A3_(420.00_x_297.00_MM)" selected>A3 Full Bleed (420 x 297 mm)</option>



                    <option value="ISO_A3_(420.00_x_297.00_MM)">A3 Standard (420 x 297 mm)</option>



                    <option value="ISO_full_bleed_A4_(297.00_x_210.00_MM)">A4 Full Bleed (297 x 210 mm)</option>



                    <option value="ISO_A4_(297.00_x_210.00_MM)">A4 Standard (297 x 210 mm)</option>



                  </select>



                </div>



                <div>



                  <label class="block font-bold text-slate-700 mb-1">Bảng nét in (CTB):</label>



                  <select id="cadPlotStyle" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 text-xs font-medium focus:ring-1 focus:ring-teal-500">



                    <option value="monochrome.ctb" selected>monochrome.ctb (Trắng đen)</option>



                    <option value="acad.ctb">acad.ctb (Màu theo Layer)</option>



                    <option value="Grayscale.ctb">Grayscale.ctb (Thang xám)</option>



                  </select>



                </div>



                <div>



                  <label class="block font-bold text-slate-700 mb-1">Thư mục xuất PDF:</label>



                  <input type="text" id="cadPlotOutputDir" value="~/Downloads/BatchPlot_PDF" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 font-mono text-[11px] focus:ring-1 focus:ring-teal-500">



                </div>



              </div>







              <!-- Action Buttons Row -->



              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">



                <button onclick="runBatchPlotAction('generate_only')" id="btnCadPlotGenScript" class="py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-800 font-bold flex items-center justify-center gap-2 transition active:scale-[0.98]">



                  <i data-lucide="file-code" class="w-4 h-4 text-slate-600"></i>



                  <span>1. Xuất Mã LISP In Hàng Loạt (.lsp)</span>



                </button>



                <button onclick="runBatchPlotAction('execute')" id="btnCadPlotExec" class="py-2.5 px-4 rounded-xl bg-gradient-to-r from-teal-600 via-emerald-600 to-green-600 hover:from-teal-700 hover:via-emerald-700 hover:to-green-700 text-white font-bold shadow-md shadow-emerald-500/20 flex items-center justify-center gap-2 transition active:scale-[0.98]">



                  <i data-lucide="printer" class="w-4 h-4"></i>



                  <span>2. Thực Thi In Hàng Loạt Trực Tiếp Vào AutoCAD</span>



                </button>



              </div>



            </div>



          </div>



        </div>







        <!-- ==================================================================== -->



        <!-- TAB CONTENT 13: SKETCHUP RUBY (.RB) -> 3D OBJ & PREVIEW WEBGL        -->



        <!-- ==================================================================== -->



        <div id="tab-rb-obj" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">



          <!-- Main Header with Live Status & Information -->



          <div class="border-b border-slate-100 pb-3 flex flex-wrap items-center justify-between gap-3">



            <div>



              <div class="flex items-center gap-2">



                <span class="p-1.5 rounded-xl bg-rose-50 text-rose-700 border border-rose-100">



                  <i data-lucide="box" class="w-5 h-5"></i>



                </span>



                <h2 class="text-base font-bold text-slate-900">Ruby .RB &rarr; 3D Wavefront OBJ Converter</h2>



                <span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-bold border border-rose-200 flex items-center gap-1">



                  <span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span> SketchUp Ruby 3D Parser



                </span>



                <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium border border-indigo-200">



                  Three.js WebGL Preview



                </span>



              </div>



              <p class="text-xs text-slate-500 mt-1">



                Tải lên hoặc dán mã SketchUp Ruby (.rb) &bull; Tự động mô phỏng API SketchUp &bull; Trích xuất 3D OBJ & MTL đầy đủ vật liệu &bull; Xem trước tương tác 3D WebGL trực tiếp.



              </p>



            </div>







            <!-- Header Quick Actions -->



            <div class="flex items-center gap-2">



              <button onclick="downloadRubyObj()" class="py-1.5 px-3 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300 cursor-pointer shadow-xs" title="Tải xuống tệp .OBJ của mô hình đang hiển thị">



                <i data-lucide="download" class="w-3.5 h-3.5 text-rose-600"></i> Tải OBJ



              </button>



              <button onclick="downloadRubyMtl()" class="py-1.5 px-3 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300 cursor-pointer shadow-xs" title="Tải xuống tệp vật liệu .MTL">



                <i data-lucide="palette" class="w-3.5 h-3.5 text-indigo-600"></i> Tải MTL



              </button>



              <button onclick="openRubyFolder()" class="p-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300 transition cursor-pointer" title="Mở thư mục ruby_exports trên Windows Explorer">



                <i data-lucide="folder-open" class="w-4 h-4 text-amber-600"></i>



              </button>



            </div>



          </div>







          <!-- Action & Source Toolbar Card -->



          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-3">



            <div class="flex flex-wrap items-center gap-2.5">



              <div class="flex items-center gap-1.5">



                <label class="text-xs font-bold text-slate-700 whitespace-nowrap flex items-center gap-1">



                  <i data-lucide="file-code" class="w-3.5 h-3.5 text-rose-600"></i> Mẫu Script .RB:



                </label>



                <select id="rubySampleSelect" onchange="loadRubySample()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-rose-500 shadow-xs">



                  <option value="house_bim_model.rb">house_bim_model.rb (Mô hình Nhà phố BIM)</option>



                  <option value="rebar.rb">rebar.rb (Bố trí Cốt thép Dầm Cột 3D)</option>



                  <option value="healthwave_sign.rb">healthwave_sign.rb (Bảng hiệu & Logo 3D)</option>



                  <option value="luxury_bedroom_render.rb">luxury_bedroom_render.rb (Nội thất Phòng ngủ)</option>



                </select>



              </div>







              <!-- Upload Custom File -->



              <div>



                <input type="file" id="rubyFileInput" accept=".rb,.txt" onchange="handleRubyFileUpload(event)" class="hidden">



                <button onclick="document.getElementById('rubyFileInput').click()" class="py-1.5 px-3 rounded-lg bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 font-medium text-xs flex items-center gap-1.5 shadow-xs transition cursor-pointer">



                  <i data-lucide="upload" class="w-3.5 h-3.5 text-indigo-600"></i> Chọn File .rb từ Máy...



                </button>



              </div>



            </div>







            <!-- Run Convert Button -->



            <div class="flex items-center gap-2">



              <button onclick="runRubyConvert()" id="btnRunRubyConvert" class="py-2 px-4 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-rose-700 hover:from-rose-700 hover:to-pink-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-rose-500/20 transition active:scale-95 cursor-pointer">



                <i data-lucide="play" class="w-4 h-4 fill-white"></i> Thực Thi & Chuyển Đổi sang 3D OBJ



              </button>



            </div>



          </div>







          <!-- Main Layout: 3D WebGL Canvas (Left) + Code & Settings (Right) -->



          <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5">



            <!-- Left/Center: WebGL Canvas (col-span-8 or 7) -->



            <div class="lg:col-span-7 xl:col-span-8 bg-zinc-900 border border-slate-800 rounded-2xl overflow-hidden relative shadow-inner flex flex-col" style="height: 560px;">



              <!-- Canvas Header Bar -->



              <div class="px-3.5 py-2.5 bg-zinc-900/95 border-b border-zinc-800 flex items-center justify-between text-xs text-zinc-300 z-10">



                <div class="flex items-center gap-2 min-w-0">



                  <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse shrink-0"></span>



                  <span class="font-bold text-white font-mono text-[12px] truncate" id="ruby3dCurrentTitle">house_bim_model.obj</span>



                  <span class="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 font-mono border border-zinc-700 shrink-0" id="ruby3dDimensions">--m x --m • Cao --m</span>



                </div>



                <!-- Camera Controls & View Presets -->



                <div class="flex items-center gap-1">



                  <button onclick="resetRuby3dCamera()" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[11px] px-2 transition cursor-pointer" title="Góc nhìn Isometric chuẩn">



                    Iso



                  </button>



                  <button onclick="setRuby3dViewTop()" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[11px] px-2 transition cursor-pointer" title="Góc nhìn Mặt Bằng (Top)">



                    Top



                  </button>



                  <button onclick="setRuby3dViewFront()" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[11px] px-2 transition cursor-pointer" title="Góc nhìn Mặt Đứng (Front)">



                    Front



                  </button>



                  <button onclick="toggleRuby3dWireframe()" id="btnRubyWireframe" class="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[11px] px-2 transition cursor-pointer flex items-center gap-1" title="Bật/tắt chế độ khung dây Wireframe">



                    <i data-lucide="grid" class="w-3 h-3"></i> Wireframe



                  </button>



                </div>



              </div>







              <!-- Three.js Canvas Element -->



              <div id="ruby3dCanvasContainer" class="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing">



                <!-- Overlay Spinner -->



                <div id="ruby3dLoadingOverlay" class="absolute inset-0 bg-zinc-900/85 backdrop-blur-xs flex flex-col items-center justify-center text-white z-20 hidden">



                  <div class="w-9 h-9 border-3 border-rose-500 border-t-transparent rounded-full animate-spin mb-2"></div>



                  <div class="text-xs font-semibold text-rose-200">Đang chuyển đổi và nạp 3D OBJ...</div>



                </div>



              </div>







              <!-- Bottom Stats Bar on Canvas -->



              <div class="px-3.5 py-2 bg-zinc-900/95 border-t border-zinc-800 flex flex-wrap items-center justify-between text-[11px] text-zinc-400 z-10 gap-2">



                <div class="flex flex-wrap items-center gap-3">



                  <div class="flex items-center gap-1.5">



                    <span class="text-zinc-500">Đỉnh (Vertices):</span>



                    <span class="font-bold text-white font-mono" id="ruby3dVertices">0</span>



                  </div>



                  <div class="flex items-center gap-1.5">



                    <span class="text-zinc-500">Mặt (Faces):</span>



                    <span class="font-bold text-white font-mono" id="ruby3dFaces">0</span>



                  </div>



                  <div class="flex items-center gap-1.5">



                    <span class="text-zinc-500">Dung lượng OBJ:</span>



                    <span class="font-bold text-emerald-400 font-mono" id="ruby3dFileSize">0 KB</span>



                  </div>



                  <div class="flex items-center gap-1.5">



                    <span class="text-zinc-500">Vật liệu:</span>



                    <span class="font-bold text-rose-400 font-mono" id="ruby3dMaterialsCount">0</span>



                  </div>



                </div>



                <div class="text-[10px] text-zinc-500">



                  Kéo chuột trái để xoay • Phải để Pan • Con lăn để Zoom



                </div>



              </div>



            </div>







            <!-- Right Sidebar: Ruby Code Editor & Output (col-span-4 or 5) -->



            <div class="lg:col-span-5 xl:col-span-4 space-y-3 flex flex-col" style="min-height: 560px;">



              <!-- Editor Container Card -->



              <div class="bg-slate-900 border border-slate-800 rounded-2xl p-3 flex flex-col flex-1 shadow-sm">



                <!-- Editor Toolbar -->



                <div class="flex items-center justify-between pb-2 border-b border-slate-800 mb-2">



                  <div class="flex items-center gap-1.5">



                    <span class="w-2 h-2 rounded-full bg-rose-500"></span>



                    <span class="text-xs font-bold text-white font-mono">Trình Biên Tập Ruby (.rb)</span>



                  </div>



                  <div class="flex items-center gap-1">



                    <button onclick="clearRubyCodeEditor()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10.5px] transition cursor-pointer" title="Xóa trắng mã nguồn">



                      Xóa



                    </button>



                    <button onclick="copyRubyCodeEditor()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10.5px] transition cursor-pointer" title="Sao chép toàn bộ mã nguồn">



                      Copy



                    </button>



                  </div>



                </div>







                <!-- Textarea Code Input -->



                <div class="flex-1 min-h-[260px] relative">



                  <textarea id="rubySourceCode" spellcheck="false" placeholder="# Dán code SketchUp Ruby vào đây...



# Ví dụ:



model = Sketchup.active_model



entities = model.active_entities



face = entities.add_face([0,0,0], [5.m,0,0], [5.m,3.m,0], [0,3.m,0])



face.pushpull(2.8.m)" class="w-full h-full min-h-[260px] bg-slate-950 text-slate-200 font-mono text-[11px] p-3 rounded-xl border border-slate-800 focus:outline-none focus:border-rose-500 resize-none leading-relaxed overflow-y-auto"></textarea>



                </div>







                <!-- Execution Console Box -->



                <div class="mt-2.5 pt-2 border-t border-slate-800">



                  <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">



                    <span>Nhật ký thông dịch (Console Output):</span>



                    <span class="text-emerald-400 font-mono text-[10px]">Headless Ready</span>



                  </div>



                  <div id="rubyConsoleLog" class="p-2 bg-slate-950 rounded-xl border border-slate-800/80 font-mono text-[10.5px] text-slate-300 h-24 overflow-y-auto whitespace-pre-wrap leading-tight">



Sẵn sàng thông dịch SketchUp Ruby sang Wavefront 3D OBJ.



                  </div>



                </div>







                <!-- Materials Breakdown List -->



                <div class="mt-2.5 pt-2 border-t border-slate-800">



                  <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">



                    Danh sách vật liệu (MTL Materials):



                  </div>



                  <div id="rubyMaterialsList" class="flex flex-wrap gap-1 max-h-20 overflow-y-auto pr-1">



                    <span class="text-[10.5px] text-slate-500 italic">Chưa có vật liệu nào được phân tích.</span>



                  </div>



                </div>



              </div>



            </div>



          </div>



        </div>











      
        <!-- ==================================================================== -->
        <!-- TAB 14: MEP AI STUDIO 3D • THIẾT KẾ & DỰNG 3D BIM TỰ ĐỘNG          -->
        <!-- ==================================================================== -->
        <div id="tab-mep-ai" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
          <!-- Main Header with Live Status & Information -->
          <div class="border-b border-slate-100 pb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="flex items-center gap-2">
                <span class="p-1.5 rounded-xl bg-cyan-50 text-cyan-700 border border-cyan-100">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </span>
                <h2 class="text-base font-bold text-slate-800">14. MEP AI Studio • Thiết Kế 3D Tự Động & BIM Toàn Diện</h2>
                <span class="text-[11px] px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800 font-semibold border border-cyan-200">BIM 4D Ready</span>
              </div>
              <p class="text-xs text-slate-500 mt-1">Tự động thiết kế Điện, Chiếu sáng, Cấp thoát nước, HVAC, Kiểm tra xung đột & Bóc tách khối lượng BOQ</p>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="openMepExportFolder()" class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 flex items-center gap-1.5 transition">
                <span>📂</span> Mở Thư Mục Xuất
              </button>
              <button onclick="runMepGeneratePipeline(true)" id="btnMepGenerate" class="px-3.5 py-1.5 text-xs font-bold rounded-xl bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-sm flex items-center gap-1.5 transition">
                <span>⚡</span> Thiết Kế MEP & Dựng 3D
              </button>
            </div>
          </div>

          <!-- Status Bar -->
          <div id="mepLiveStatus" class="p-2.5 rounded-xl bg-slate-900 text-slate-300 text-xs font-mono border border-slate-800 flex items-center justify-between">
            <span>💡 Sẵn sàng thiết kế hệ thống MEP tự động 3D. Bấm "Thiết Kế MEP & Dựng 3D" để bắt đầu.</span>
            <span class="text-slate-500 text-[11px]">TCVN 7114 • TCVN 4513 • ASHRAE</span>
          </div>

          <!-- 5 Stats Cards -->
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
              <span class="text-[11px] text-slate-500">Phần Tử BIM</span>
              <span id="mepStatTotalElements" class="text-lg font-bold text-slate-800">--</span>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
              <span class="text-[11px] text-slate-500">Phụ Tải Chiếu Sáng</span>
              <span id="mepStatTotalPower" class="text-lg font-bold text-amber-600">--</span>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
              <span class="text-[11px] text-slate-500">Công Suất Lạnh HVAC</span>
              <span id="mepStatTotalHvac" class="text-lg font-bold text-cyan-600">--</span>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
              <span class="text-[11px] text-slate-500">Đường Ống Nước</span>
              <span id="mepStatTotalPipes" class="text-lg font-bold text-blue-600">--</span>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
              <span class="text-[11px] text-slate-500">Điểm Xung Đột</span>
              <span id="mepStatClashesCount" class="text-lg font-bold text-rose-600">--</span>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
              <span class="text-[11px] text-slate-500">Dự Toán MEP (VND)</span>
              <span id="mepStatTotalCost" class="text-sm font-bold text-emerald-700 truncate mt-1">--</span>
            </div>
          </div>

          <!-- Main Layout: Controls (Left) + 3D Viewport (Right) -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <!-- Left Panel: Parameters & Quick Actions (4 cols) -->
            <div class="lg:col-span-4 space-y-3">
              <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div class="text-xs font-bold text-slate-700 flex items-center justify-between">
                  <span>📐 Thông Số Công Trình</span>
                  <span class="text-[10px] text-slate-400">Đơn vị: Mét</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <label class="block text-slate-500 mb-1">Rộng X (m)</label>
                    <input type="number" id="mepParamWidth" value="12" step="1" min="6" max="60" class="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white font-mono text-slate-800">
                  </div>
                  <div>
                    <label class="block text-slate-500 mb-1">Sâu Y (m)</label>
                    <input type="number" id="mepParamDepth" value="8" step="1" min="4" max="40" class="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white font-mono text-slate-800">
                  </div>
                  <div>
                    <label class="block text-slate-500 mb-1">Cao Tầng (m)</label>
                    <input type="number" id="mepParamHeight" value="3.6" step="0.2" min="2.8" max="6" class="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white font-mono text-slate-800">
                  </div>
                  <div>
                    <label class="block text-slate-500 mb-1">Số Tầng</label>
                    <input type="number" id="mepParamFloors" value="2" step="1" min="1" max="10" class="w-full px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white font-mono text-slate-800">
                  </div>
                </div>

                <div class="pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                  <label class="flex items-center gap-2 cursor-pointer text-slate-700">
                    <input type="checkbox" id="mepParamAutoResolve" checked class="w-4 h-4 text-cyan-600 rounded">
                    <span>Tự động nắn tuyến xử lý va chạm</span>
                  </label>
                </div>

                <button onclick="runMepAutoResolve()" class="w-full py-2 px-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm transition">
                  <span>🛠️</span> Nắn Tuyến Triệt Tiêu Xung Đột
                </button>
              </div>

              <!-- Quick Export / Download Panel -->
              <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div class="text-xs font-bold text-slate-700">📥 Xuất File Bản Vẽ & Mô Hình BIM</div>
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <button onclick="downloadMepFile('ifc')" class="p-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 font-medium flex items-center justify-center gap-1">
                    <span>📦</span> Tải IFC 4 BIM
                  </button>
                  <button onclick="downloadMepFile('dxf')" class="p-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 font-medium flex items-center justify-center gap-1">
                    <span>📐</span> Tải CAD DXF
                  </button>
                  <button onclick="downloadMepFile('obj')" class="p-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 font-medium flex items-center justify-center gap-1">
                    <span>🧊</span> Tải 3D OBJ
                  </button>
                  <button onclick="downloadMepFile('boq_json')" class="p-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 font-medium flex items-center justify-center gap-1">
                    <span>📊</span> Báo Cáo BOQ
                  </button>
                </div>
              </div>

              <!-- BIM Properties Inspector Box -->
              <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
                <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>Thuộc Tính BIM Đối Tượng</span>
                  <span class="text-[10px] text-cyan-400">Click 3D để xem</span>
                </div>
                <div id="mepSelectedElementProperties" class="min-h-[90px] flex items-center justify-center text-xs text-slate-500 italic">
                  Nhấp chuột vào bất kỳ cấu kiện hoặc điểm xung đột 3D để kiểm tra thông số chi tiết...
                </div>
              </div>
            </div>

            <!-- Right Panel: 3D WebGL Canvas (8 cols) -->
            <div class="lg:col-span-8 flex flex-col space-y-2">
              <!-- Viewer Controls & Layer Filters -->
              <div class="flex flex-wrap items-center justify-between gap-2 p-2 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <!-- Layer Filters -->
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="text-[11px] text-slate-400 mr-1">Lọc:</span>
                  <button id="btnFilter_arch" onclick="toggleMepFilter('arch')" class="px-2 py-1 rounded-lg bg-cyan-600 text-white font-medium text-[11px] transition">🏗️ Kiến Trúc</button>
                  <button id="btnFilter_elec" onclick="toggleMepFilter('elec')" class="px-2 py-1 rounded-lg bg-cyan-600 text-white font-medium text-[11px] transition">⚡ Điện & Đèn</button>
                  <button id="btnFilter_plumb" onclick="toggleMepFilter('plumb')" class="px-2 py-1 rounded-lg bg-cyan-600 text-white font-medium text-[11px] transition">🚰 Cấp Thoát Nước</button>
                  <button id="btnFilter_hvac" onclick="toggleMepFilter('hvac')" class="px-2 py-1 rounded-lg bg-cyan-600 text-white font-medium text-[11px] transition">❄️ HVAC</button>
                  <button id="btnFilter_clashes" onclick="toggleMepFilter('clashes')" class="px-2 py-1 rounded-lg bg-rose-600 text-white font-medium text-[11px] transition">💥 Xung Đột</button>
                </div>
                <!-- Camera Presets -->
                <div class="flex items-center gap-1">
                  <button onclick="setMepView('iso')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">3D</button>
                  <button onclick="setMepView('top')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">Mặt Bằng</button>
                  <button onclick="setMepView('front')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">Đứng</button>
                  <button onclick="setMepView('side')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">Cạnh</button>
                </div>
              </div>

              <!-- Canvas Container -->
              <div id="mep3dCanvasContainer" class="w-full h-[460px] sm:h-[500px] rounded-xl overflow-hidden bg-slate-950 relative border border-slate-800 flex items-center justify-center text-slate-600 text-xs font-mono">
                Đang khởi tạo WebGL 3D Canvas...
              </div>
            </div>
          </div>

          <!-- Bottom Tables: BOQ Schedule & Clash Matrix -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
            <!-- Clash Matrix Table -->
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div class="flex items-center justify-between">
                <div class="text-xs font-bold text-rose-400 flex items-center gap-1.5">
                  <span>💥 Báo Cáo Kiểm Tra Xung Đột MEP (Clash Report)</span>
                </div>
                <span class="text-[10px] text-slate-400">Dung sai: 20mm</span>
              </div>
              <div class="overflow-x-auto max-h-[260px] overflow-y-auto">
                <table class="w-full text-xs text-left">
                  <thead class="bg-slate-800/80 text-slate-400 text-[11px] sticky top-0">
                    <tr>
                      <th class="p-2 text-center">ID</th>
                      <th class="p-2 text-center">Mức Độ</th>
                      <th class="p-2">Mô Tả Va Chạm</th>
                      <th class="p-2 text-right">Độ Sâu</th>
                      <th class="p-2">Đề Xuất Nắn Tuyến</th>
                    </tr>
                  </thead>
                  <tbody id="mepClashesTableBody">
                    <tr><td colspan="5" class="p-4 text-center text-slate-500">Chưa có dữ liệu xung đột</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- BOQ Schedule Table -->
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div class="flex items-center justify-between">
                <div class="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <span>📊 Bảng Bóc Tách Khối Lượng (BOQ Schedule)</span>
                </div>
                <div class="text-xs font-bold text-slate-300">
                  Tổng: <span id="mepBoqGrandTotal" class="text-emerald-400">--</span>
                </div>
              </div>
              <div class="overflow-x-auto max-h-[260px] overflow-y-auto">
                <table class="w-full text-xs text-left">
                  <thead class="bg-slate-800/80 text-slate-400 text-[11px] sticky top-0">
                    <tr>
                      <th class="p-2 text-center">STT</th>
                      <th class="p-2">Vật Tư & Thiết Bị</th>
                      <th class="p-2 text-center">ĐVT</th>
                      <th class="p-2 text-right">Khối Lượng</th>
                      <th class="p-2 text-right">Đơn Giá</th>
                      <th class="p-2 text-right">Thành Tiền</th>
                    </tr>
                  </thead>
                  <tbody id="mepBoqTableBody">
                    <tr><td colspan="6" class="p-4 text-center text-slate-500">Chưa có dữ liệu bóc tách</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>


</section>







      <!-- ==================================================================== -->



      <!-- CỘT 3 (LỀ PHẢI): MÔI TRƯỜNG AEC ĐANG MỞ + CONSOLE NHẬT KÝ             -->



      <!-- ==================================================================== -->



      <aside id="colRightPanel" class="col-span-12 lg:col-span-3 xl:col-span-3 space-y-3.5 relative transition-all duration-200">







        <!-- ==================================================================== -->



        <!-- PANEL: ETABS STRUCTURAL AI HUB (HỒ SƠ DẦM & CỐT THÉP)                 -->



        <!-- ==================================================================== -->



        <div class="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-950 text-white border border-indigo-500/40 rounded-2xl p-3.5 shadow-lg shadow-indigo-950/30 space-y-2.5 relative overflow-hidden group">

          <!-- Nút Edge Toggle ép sát mép trong Right Panel (Border Seam Arrow Right) -->
          <button type="button" id="btnEdgeCollapseRight" onclick="toggleRightPanel(false)" class="hidden lg:flex absolute -left-3 top-5 z-20 w-6 h-6 rounded-full bg-white border border-slate-200 shadow-sm hover:shadow-md text-slate-500 hover:text-indigo-600 hover:border-indigo-400 items-center justify-center cursor-pointer transition-all hover:scale-110 group/btn" title="Thu gọn lề phải (Arrow Right)">
            <i data-lucide="chevron-right" class="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform text-slate-700"></i>
          </button>



          <div class="absolute -right-6 -bottom-6 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl pointer-events-none"></div>



          



          <div class="flex items-center justify-between">



            <span class="text-xs font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-1.5">



              <i data-lucide="layers" class="w-4 h-4 text-cyan-400"></i> ETABS AI Hub



            </span>



            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 103 Dầm
              </span>
              <!-- Nút Thu Gọn Header Arrow Right ép sát mép trong -->
              <button type="button" id="btnCollapseRightHeader" onclick="toggleRightPanel(false)" class="p-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-300 hover:text-white transition cursor-pointer shrink-0 border border-white/10 shadow-xs flex items-center justify-center w-6 h-6" title="Thu gọn lề phải (Arrow Right)">
                <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
              </button>
            </div>



          </div>



          



          <p class="text-[11px] text-slate-300 leading-snug">



            Mặt bằng dầm 2D đúng bề rộng, Model 3D khối đặc chuẩn tiết diện & bảng chọn thép TCVN 5574-2012.



          </p>







          <div class="grid grid-cols-3 gap-2 pt-1">



            <button onclick="openEtabsHub('middle')" class="py-2 px-1.5 rounded-xl bg-gradient-to-r from-blue-600 via-sky-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-bold text-[11px] flex items-center justify-center gap-1 shadow-md shadow-blue-500/25 transition active:scale-95 cursor-pointer" title="Mở trên tab giữa">



              <i data-lucide="layout-grid" class="w-3.5 h-3.5"></i> Trang giữa



            </button>



            <button onclick="openEtabsHub('modal')" class="py-2 px-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-[11px] flex items-center justify-center gap-1 border border-white/20 hover:border-white/40 transition active:scale-95 cursor-pointer" title="Phóng to Modal">



              <i data-lucide="maximize-2" class="w-3.5 h-3.5 text-amber-300"></i> Modal lớn



            </button>



            <button onclick="deployToVps()" id="btnCardDeployVps" class="py-2 px-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-[11px] flex items-center justify-center gap-1 shadow-md shadow-emerald-600/30 border border-emerald-400/30 transition active:scale-95 cursor-pointer" title="Deploy trực tiếp lên https://mr.pkld.online">



              <i data-lucide="send" class="w-3.5 h-3.5 text-emerald-200"></i> Deploy



            </button>



          </div>



          <button onclick="openGeneralNotesModal()" class="w-full mt-2.5 py-2 px-3 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-amber-500/25 transition active:scale-95 cursor-pointer" title="Xem Bảng Ghi Chú Chung Kết Cấu (Plot 1020)">



            <i data-lucide="file-text" class="w-4 h-4"></i> Bảng Ghi Chú Chung (Plot 1020)



          </button>



        </div>











        <!-- PANEL 1: THÔNG TIN MÔI TRƯỜNG CAD / MAX / REVIT ĐANG MỞ (COLLAPSIBLE) -->



        <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">



          <div onclick="togglePanel('bodyRevitDoc', 'arrowRevitDoc')" class="flex items-center justify-between p-3.5 bg-slate-50/70 border-b border-slate-100 cursor-pointer hover:bg-slate-100/70 transition select-none">



            <span class="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">



              <i data-lucide="monitor" class="w-4 h-4 text-indigo-600"></i> Môi Trường AEC Đang Mở



            </span>



            <div class="flex items-center gap-2">



              <span id="docModifiedBadge" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-200/80 text-slate-600 font-semibold">Live Hub</span>



              <button class="p-1 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition" title="Thu gọn / Mở rộng">



                <i data-lucide="chevron-up" id="arrowRevitDoc" class="w-4 h-4 transition-transform duration-200"></i>



              </button>



            </div>



          </div>







          <div id="bodyRevitDoc" class="p-3 space-y-2.5 transition-all">



            <!-- AutoCAD Card -->



            <div class="p-2 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">



              <div class="flex items-center gap-2 min-w-0">



                <span id="cadCardDot" class="w-2.5 h-2.5 rounded-full bg-slate-300 shrink-0"></span>



                <div class="min-w-0">



                  <div class="font-bold text-slate-800 flex items-center gap-1.5">



                    <i data-lucide="file-code-2" class="w-3.5 h-3.5 text-cyan-600 shrink-0"></i> AutoCAD (2D)



                  </div>



                  <div id="cadDocTitle" class="text-[11px] text-slate-500 truncate mt-0.5">Chưa mở</div>



                </div>



              </div>



              <span id="cadStateBadge" class="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-600 font-bold whitespace-nowrap shrink-0">Offline</span>



            </div>







            <!-- 3ds Max Card -->



            <div class="p-2 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">



              <div class="flex items-center gap-2 min-w-0">



                <span id="maxCardDot" class="w-2.5 h-2.5 rounded-full bg-slate-300 shrink-0"></span>



                <div class="min-w-0">



                  <div class="font-bold text-slate-800 flex items-center gap-1.5">



                    <i data-lucide="box" class="w-3.5 h-3.5 text-amber-600 shrink-0"></i> 3ds Max (3D)



                  </div>



                  <div id="maxSceneTitle" class="text-[11px] text-slate-500 truncate mt-0.5">Chưa mở</div>



                </div>



              </div>



              <span id="maxStateBadge" class="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-600 font-bold whitespace-nowrap shrink-0">Offline</span>



            </div>







            <!-- Revit Card -->



            <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">



              <div class="flex items-center justify-between">



                <div class="flex items-center gap-2 min-w-0">



                  <span id="revitCardDot" class="w-2.5 h-2.5 rounded-full bg-slate-300 shrink-0"></span>



                  <div class="font-bold text-slate-800 flex items-center gap-1.5">



                    <i data-lucide="building-2" class="w-3.5 h-3.5 text-indigo-600 shrink-0"></i> Revit (BIM)



                  </div>



                </div>



                <span id="revitStateBadge" class="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-600 font-bold whitespace-nowrap shrink-0">Offline</span>



              </div>



              <div class="pl-4">



                <div id="docTitle" class="text-xs font-semibold text-slate-700 truncate">Revit chưa bật (Tùy chọn)</div>



                <div id="activeViewName" class="text-[11px] text-slate-500 truncate">View: --</div>



              </div>



              <!-- Quick Numbers Grid (Tường, Cửa, Cột, Sheet) -->



              <div class="grid grid-cols-4 gap-1 text-center text-xs pt-1">



                <div class="bg-white p-1 rounded-lg border border-slate-200">



                  <div id="cntWalls" class="font-bold text-slate-900 text-xs">--</div>



                  <div class="text-[9px] text-slate-500 font-medium">Tường</div>



                </div>



                <div class="bg-white p-1 rounded-lg border border-slate-200">



                  <div id="cntDoors" class="font-bold text-emerald-700 text-xs">--</div>



                  <div class="text-[9px] text-slate-500 font-medium">Cửa</div>



                </div>



                <div class="bg-white p-1 rounded-lg border border-slate-200">



                  <div id="cntCols" class="font-bold text-cyan-700 text-xs">--</div>



                  <div class="text-[9px] text-slate-500 font-medium">Cột</div>



                </div>



                <div class="bg-white p-1 rounded-lg border border-slate-200">



                  <div id="cntSheets" class="font-bold text-amber-700 text-xs">--</div>



                  <div class="text-[9px] text-slate-500 font-medium">Sheet</div>



                </div>



              </div>



            </div>



          </div>



        </div>







        <!-- PANEL 2: CONSOLE KẾT QUẢ THỰC THI (COLLAPSIBLE) -->



        <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">



          <div onclick="togglePanel('bodyConsole', 'arrowConsole')" class="flex items-center justify-between p-3.5 bg-slate-50/70 border-b border-slate-100 cursor-pointer hover:bg-slate-100/70 transition select-none">



            <span class="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">



              <i data-lucide="terminal" class="w-4 h-4 text-blue-600"></i> Console Nhật Ký



            </span>



            <div class="flex items-center gap-2">



              <button onclick="event.stopPropagation(); clearConsole()" class="text-[10px] px-2 py-0.5 rounded bg-slate-200/80 hover:bg-slate-300 text-slate-700 font-medium transition cursor-pointer" title="Xóa nội dung console">Xóa log</button>



              <button class="p-1 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition" title="Thu gọn / Mở rộng">



                <i data-lucide="chevron-up" id="arrowConsole" class="w-4 h-4 transition-transform duration-200"></i>



              </button>



            </div>



          </div>







          <div id="bodyConsole" class="p-3 transition-all">



            <div id="consoleOutput" class="h-[280px] overflow-y-auto font-mono text-[11px] text-slate-700 bg-slate-50 p-2.5 rounded-xl border border-slate-200 space-y-1.5 leading-relaxed shadow-inner">



              <div class="text-slate-400">[System] Sẵn sàng nhận lệnh...</div>



            </div>



          </div>



        </div>







      </aside>







    </div>



  </main>







  <!-- JAVASCRIPT LOGIC -->



  <script>



    // Initialize Lucide icons



    lucide.createIcons();







    // Toggle Collapse / Expand for Column 3 Panels



    function togglePanel(bodyId, arrowId) {



      const body = document.getElementById(bodyId);



      const arrow = document.getElementById(arrowId);



      if (!body) return;



      body.classList.toggle('hidden');



      if (arrow) {



        arrow.classList.toggle('rotate-180');



      }



    }







    // Tab Switching for 2-Column Menu (Column 1)



    function switchTab(tabId) {



      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));



      document.querySelectorAll('.tab-btn').forEach(btn => {



        btn.classList.remove('bg-gradient-to-r', 'from-blue-600', 'via-sky-600', 'to-cyan-600', 'bg-indigo-600', 'text-white', 'shadow-sm', 'shadow-md', 'shadow-blue-500/20', 'border-transparent');



        btn.classList.add('bg-slate-50', 'text-slate-800', 'border', 'border-slate-200');



        const sub = btn.querySelector('.tab-subtitle');



        if (sub) {



          sub.classList.remove('opacity-80', 'text-white/80');



          sub.classList.add('text-slate-500');



        }



      });







      document.getElementById(tabId).classList.remove('hidden');



      if (tabId === 'tab-dwg' && !dwgLoadedOnce) {



        loadDwgTreeView();



      }



      if (tabId === 'tab-tags') {



        loadTagsStatus();



      }



      if (tabId === 'tab-cad') {



        initCad3dDashboard();



      }



      if (tabId === 'tab-rb-obj') {



        initRuby3dDashboard();



      }
      if (tabId === 'tab-mep-ai') {
        initMepDashboard();
      }



      if (tabId === 'tab-cad-plot' && currentCadPlotItems.length === 0) {



        runScanCadTitleblocks();



      }



      const activeBtn = document.getElementById('btn-' + tabId);



      if (activeBtn) {



        activeBtn.classList.remove('bg-slate-50', 'text-slate-800', 'border', 'border-slate-200');



        activeBtn.classList.add('bg-gradient-to-r', 'from-blue-600', 'via-sky-600', 'to-cyan-600', 'text-white', 'shadow-md', 'shadow-blue-500/20', 'border-transparent');



        const sub = activeBtn.querySelector('.tab-subtitle');



        if (sub) {



          sub.classList.remove('text-slate-500');



          sub.classList.add('opacity-80');



        }



      }



    }







    // Logger



    function log(msg, type = 'info') {



      const con = document.getElementById('consoleOutput');



      const time = new Date().toLocaleTimeString();



      let colorClass = 'text-slate-700';



      if (type === 'success') colorClass = 'text-emerald-800 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 inline-block';



      if (type === 'error') colorClass = 'text-rose-800 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200 inline-block';



      if (type === 'warning') colorClass = 'text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 inline-block';







      const entry = document.createElement('div');



      entry.className = 'py-0.5';



      entry.innerHTML = `<span class="text-slate-400 font-normal">[${time}]</span> <span class="${colorClass}">${msg}</span>`;



      con.appendChild(entry);



      con.scrollTop = con.scrollHeight;



    }







    function clearConsole() {



      document.getElementById('consoleOutput').innerHTML = '<div class="text-slate-400">[System] Đã xóa nhật ký.</div>';



    }







    // Fetch Multi-CAD & Revit Info



    async function refreshModelInfo() {



      const dot = document.getElementById('statusDot');



      const text = document.getElementById('statusText');



      const icon = document.getElementById('refreshIcon');



      if (icon) icon.classList.add('animate-spin');







      try {



        const res = await fetch('/api/hub-status');



        const hub = await res.json();







        // 1. Cập nhật AutoCAD (2D)



        const acad = hub.autocad || {};



        const cadDot = document.getElementById('cadStatusDot');



        const cadBadge = document.getElementById('cadStatusBadge');



        const cadPipe = document.getElementById('pipeAcad');



        const cadCardDot = document.getElementById('cadCardDot');



        const cadDocTitle = document.getElementById('cadDocTitle');



        const cadStateBadge = document.getElementById('cadStateBadge');







        if (acad.running) {



          if (cadDot) cadDot.className = 'w-2 h-2 rounded-full bg-emerald-500';



          if (cadCardDot) cadCardDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500';



          if (cadBadge) {



            cadBadge.className = 'text-[10px] px-1 py-0.2 rounded bg-cyan-100 text-cyan-800 font-bold';



            cadBadge.textContent = 'ONLINE';



          }



          if (cadStateBadge) {



            cadStateBadge.className = 'text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold';



            cadStateBadge.textContent = 'Online';



          }



          if (cadPipe) {



            cadPipe.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-50 border border-cyan-300 text-xs transition';



            cadPipe.title = 'AutoCAD: ' + (acad.activeFile || 'Đang mở');



          }



          if (cadDocTitle) {



            cadDocTitle.textContent = acad.activeFile || ('Đang hoạt động (PID ' + acad.pid + ')');



            cadDocTitle.className = 'text-[11px] text-cyan-800 font-semibold truncate mt-0.5';



          }



        } else {



          if (cadDot) cadDot.className = 'w-2 h-2 rounded-full bg-slate-300';



          if (cadCardDot) cadCardDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-300';



          if (cadBadge) {



            cadBadge.className = 'text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-500 font-bold';



            cadBadge.textContent = 'DWG';



          }



          if (cadStateBadge) {



            cadStateBadge.className = 'text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-500 font-bold';



            cadStateBadge.textContent = 'Offline';



          }



          if (cadPipe) cadPipe.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs opacity-60';



          if (cadDocTitle) {



            cadDocTitle.textContent = 'Chưa mở (Tùy chọn)';



            cadDocTitle.className = 'text-[11px] text-slate-400 truncate mt-0.5';



          }



        }







        // 2. Cập nhật 3ds Max (3D)



        const maxApp = hub.max || {};



        const maxDot = document.getElementById('maxStatusDot');



        const maxBadge = document.getElementById('maxStatusBadge');



        const maxPipe = document.getElementById('pipeMax');



        const maxCardDot = document.getElementById('maxCardDot');



        const maxSceneTitle = document.getElementById('maxSceneTitle');



        const maxStateBadge = document.getElementById('maxStateBadge');







        if (maxApp.running || maxApp.bridgeOnline) {



          const isBridge = maxApp.bridgeOnline;



          if (maxDot) maxDot.className = 'w-2 h-2 rounded-full ' + (isBridge ? 'bg-emerald-500' : 'bg-amber-400');



          if (maxCardDot) maxCardDot.className = 'w-2.5 h-2.5 rounded-full ' + (isBridge ? 'bg-emerald-500' : 'bg-amber-400');



          if (maxBadge) {



            maxBadge.className = 'text-[10px] px-1 py-0.2 rounded bg-amber-100 text-amber-800 font-bold';



            maxBadge.textContent = isBridge ? ':8096 ON' : 'RUNNING';



          }



          if (maxStateBadge) {



            maxStateBadge.className = 'text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold';



            maxStateBadge.textContent = isBridge ? 'Online' : 'Running';



          }



          if (maxPipe) {



            maxPipe.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-300 text-xs transition';



            maxPipe.title = '3ds Max: ' + (maxApp.activeFile || 'Đang mở');



          }



          if (maxSceneTitle) {



            maxSceneTitle.textContent = maxApp.activeFile || ('Đang mở (PID ' + maxApp.pid + ')');



            maxSceneTitle.className = 'text-[11px] text-amber-900 font-semibold truncate mt-0.5';



          }



        } else {



          if (maxDot) maxDot.className = 'w-2 h-2 rounded-full bg-slate-300';



          if (maxCardDot) maxCardDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-300';



          if (maxBadge) {



            maxBadge.className = 'text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-500 font-bold';



            maxBadge.textContent = ':8096';



          }



          if (maxStateBadge) {



            maxStateBadge.className = 'text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-500 font-bold';



            maxStateBadge.textContent = 'Offline';



          }



          if (maxPipe) maxPipe.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs opacity-60';



          if (maxSceneTitle) {



            maxSceneTitle.textContent = 'Chưa mở (Tùy chọn)';



            maxSceneTitle.className = 'text-[11px] text-slate-400 truncate mt-0.5';



          }



        }







        // 3. Cập nhật Revit (BIM)



        const revit = hub.revit || {};



        const revitDot = document.getElementById('revitStatusDot');



        const revitBadge = document.getElementById('revitStatusBadge');



        const revitPipe = document.getElementById('pipeRevit');



        const revitCardDot = document.getElementById('revitCardDot');



        const revitStateBadge = document.getElementById('revitStateBadge');







        if (revit.running || revit.bridgeOnline) {



          const isBridge = revit.bridgeOnline;



          if (revitDot) revitDot.className = 'w-2 h-2 rounded-full ' + (isBridge ? 'bg-emerald-500' : 'bg-indigo-400');



          if (revitCardDot) revitCardDot.className = 'w-2.5 h-2.5 rounded-full ' + (isBridge ? 'bg-emerald-500' : 'bg-indigo-400');



          if (revitBadge) {



            revitBadge.className = 'text-[10px] px-1 py-0.2 rounded bg-indigo-100 text-indigo-800 font-bold';



            revitBadge.textContent = isBridge ? ':8090 ON' : 'RUNNING';



          }



          if (revitStateBadge) {



            revitStateBadge.className = 'text-[10px] px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 font-bold';



            revitStateBadge.textContent = isBridge ? 'Online' : 'Running';



          }



          if (revitPipe) {



            revitPipe.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 border border-indigo-300 text-xs transition';



          }



          document.getElementById('docTitle').textContent = revit.activeFile || 'Dự án Revit';



          document.getElementById('docTitle').className = 'text-xs font-bold text-slate-900 truncate';



          document.getElementById('activeViewName').textContent = 'View: ' + (revit.activeView || 'Chưa mở view');







          if (revit.counts) {



            document.getElementById('cntWalls').textContent = revit.counts.walls ?? '--';



            document.getElementById('cntDoors').textContent = revit.counts.doors ?? '--';



            document.getElementById('cntCols').textContent = revit.counts.columns ?? '--';



            document.getElementById('cntSheets').textContent = revit.counts.sheets ?? '--';



          }



        } else {



          if (revitDot) revitDot.className = 'w-2 h-2 rounded-full bg-slate-300';



          if (revitCardDot) revitCardDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-300';



          if (revitBadge) {



            revitBadge.className = 'text-[10px] px-1 py-0.2 rounded bg-slate-200 text-slate-500 font-bold';



            revitBadge.textContent = ':8090';



          }



          if (revitStateBadge) {



            revitStateBadge.className = 'text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-500 font-bold';



            revitStateBadge.textContent = 'Offline';



          }



          if (revitPipe) revitPipe.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs opacity-60';



          document.getElementById('docTitle').textContent = 'Revit chưa bật (Tùy chọn)';



          document.getElementById('docTitle').className = 'text-xs font-medium text-slate-500 truncate';



          document.getElementById('activeViewName').textContent = 'View: --';



          document.getElementById('cntWalls').textContent = '--';



          document.getElementById('cntDoors').textContent = '--';



          document.getElementById('cntCols').textContent = '--';



          document.getElementById('cntSheets').textContent = '--';



        }







        // 4. Tổng kết Header Live Status Pill



        const activeCount = hub.activeCount || 0;



        if (activeCount > 0) {



          dot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500';



          text.textContent = 'AEC Hub: ' + hub.summary;



          text.className = 'text-emerald-700 font-bold text-xs truncate max-w-[280px]';



        } else {



          dot.className = 'w-2.5 h-2.5 rounded-full bg-slate-400';



          text.textContent = 'AEC Hub: Sẵn sàng';



          text.className = 'text-slate-600 font-medium text-xs';



        }







      } catch (e) {



        dot.className = 'w-2.5 h-2.5 rounded-full bg-amber-400';



        text.textContent = 'AEC Hub Offline';



      } finally {



        if (icon) icon.classList.remove('animate-spin');



      }



    }







    // Execute Select by Grid



    async function runSelectByGrid() {



      const gridX = document.getElementById('gridXInput').value.trim();



      const gridY = document.getElementById('gridYInput').value.trim();



      const tolY = parseFloat(document.getElementById('toleranceYInput').value) || 1500;



      const level = document.getElementById('gridLevelSelect').value;



      const cat = document.getElementById('gridCatSelect').value;



      const zoom = document.getElementById('gridZoomCheck').checked;



      const isolate = document.getElementById('gridIsolateCheck').checked;







      log(`Chọn: Trục X [${gridX}], Trục Y [${gridY}], Tầng [${level}], Cat [${cat}]...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'select_by_grid',



            gridX: gridX,



            gridY: gridY,



            toleranceY: tolY,



            level: level,



            category: cat,



            zoom: zoom,



            isolate: isolate



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



          log(`  Đã chọn ${data.count} đối tượng. IDs: [${data.elementIds.slice(0, 10).join(', ')}${data.count > 10 ? '...' : ''}]`, 'success');



        } else {



          log(`✗ LỖI: ${data.message}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // Execute Change Doors to D7



    async function runChangeDoorsD7() {



      const floor = document.getElementById('doorFloorSelect').value;



      log(`Đang đổi cửa trục C sang D7 mở 30° (Tầng: ${floor})...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ action: 'change_doors_d7', floor: floor })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



          if (data.doors) {



            data.doors.forEach(d => log(`  &bull; ID ${d.id}: Level ${d.level} &rarr; ${d.newType} (Mark: ${d.mark})`, 'info'));



          }



        } else {



          log(`✗ LỖI: ${data.message}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // Execute Create Dimensions



    async function runCreateDimensions() {



      const viewId = document.getElementById('dimViewSelect').value;



      const offB = parseFloat(document.getElementById('offsetBInput').value) || 1500;



      const offC = parseFloat(document.getElementById('offsetCInput').value) || 1500;



      const clean = document.getElementById('cleanDimCheck').checked;







      log(`Tạo Dim: View [${viewId}], Offset B [${offB}mm], C [${offC}mm]...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ action: 'create_dimensions', viewId: viewId, offsetB: offB, offsetC: offC, clean: clean })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: Đã tạo dim cho view ${viewId}`, 'success');



        } else {



          log(`✗ KẾT QUẢ: ${JSON.stringify(data)}`, 'warning');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // ==========================================



    // TAB 4: XUẤT BẢN VẼ DWG & TREEVIEW VIEW/SHEET



    // ==========================================



    let dwgTreeData = null;



    let dwgLoadedOnce = false;







    // Toggle Titleblock Settings Panel



    function toggleTitleblockPanel() {



      const mode = document.querySelector('input[name="dwgTitleblockMode"]:checked')?.value || 'none';



      const panel = document.getElementById('panelTitleblockSettings');



      if (panel) {



        if (mode === 'overlay') {



          panel.classList.remove('hidden');



          if (typeof lucide !== 'undefined') lucide.createIcons();



        } else {



          panel.classList.add('hidden');



        }



      }



    }







    // Apply Preset DWG File Path



    function applyTitleblockPreset() {



      const select = document.getElementById('dwgTitleblockPreset');



      const input = document.getElementById('dwgTitleblockFilePath');



      if (select && input && select.value !== 'custom') {



        input.value = select.value;



      }



    }







    // Reload Project Information from Revit



    async function reloadProjectInfoFromRevit() {



      log('Đang tải lại Thông tin dự án từ Revit...');



      await loadDwgTreeView(true);



    }







    // Update DWG Preview Filename



    function updateDwgPreviewName() {



      const tagInput = document.getElementById('dwgProjectTag');



      let tag = tagInput ? tagInput.value.trim() : 'Mau_40_CBS';



      if (!tag) tag = 'Mau_40_CBS';



      const cleanTag = tag.replace(/[^a-zA-Z0-9_-]/g, '_');



      const now = new Date();



      const ts = now.getFullYear() +



        String(now.getMonth() + 1).padStart(2, '0') +



        String(now.getDate()).padStart(2, '0') + '_' +



        String(now.getHours()).padStart(2, '0') +



        String(now.getMinutes()).padStart(2, '0') +



        String(now.getSeconds()).padStart(2, '0');



      const preview = document.getElementById('dwgFileNamePreview');



      if (preview) {



        preview.textContent = `${cleanTag}_${ts}_merge_cad.dwg`;



      }



    }







    // Open Downloads Folder in Windows Explorer



    async function openDownloadsFolder() {



      const folder = document.getElementById('dwgOutputFolder')?.value.trim() || '~/Downloads';



      log(`Đang mở thư mục: ${folder}...`, 'info');



      try {



        const res = await fetch('/api/open-downloads', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ folder: folder })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ Đã mở thư mục trong Explorer: ${data.folder}`, 'success');



        } else {



          log(`✗ Không thể mở thư mục: ${data.error}`, 'error');



        }



      } catch (e) {



        log(`✗ Lỗi kết nối: ${e}`, 'error');



      }



    }







    // Fetch Views & Project Info for TreeView



    async function loadDwgTreeView(force = false) {



      const container = document.getElementById('dwgTreeContainer');



      const summary = document.getElementById('dwgSelectedSummary');



      if (!container) return;







      if (!force && dwgLoadedOnce && dwgTreeData) {



        return;



      }







      if (summary) summary.textContent = 'Đang nạp từ Revit...';



      container.innerHTML = '<div class="text-slate-400 p-4 text-center flex items-center justify-center gap-2"><i data-lucide="rotate-cw" class="w-4 h-4 animate-spin text-cyan-600"></i> Đang tải danh sách view & bản vẽ từ Revit...</div>';



      if (typeof lucide !== 'undefined') lucide.createIcons();







      try {



        const res = await fetch('/api/dwg-treeview');



        const data = await res.json();







        if (data && data.success && Array.isArray(data.groups)) {



          dwgTreeData = data;



          dwgLoadedOnce = true;







          // Fill Project Information inputs



          if (data.projectInfo) {



            const pi = data.projectInfo;



            const setVal = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined) el.value = val; };



            setVal('piProjectName', pi.projectName || '');



            setVal('piBuildingName', pi.buildingName || '');



            setVal('piProjectAddress', pi.projectAddress || '');



            setVal('piClientName', pi.clientName || '');



            setVal('piIssueDate', pi.issueDate || '');



            setVal('piAuthor', pi.author || '');







            const tagInput = document.getElementById('dwgProjectTag');



            if (tagInput && (!tagInput.value || tagInput.value === 'Mau_40_CBS')) {



              let clean = (pi.projectName || '').replace(/^TÊN DỰ ÁN\\s*:\\s*/i, '').trim();



              if (clean.length > 25) clean = clean.split(',')[0].trim();



              if (clean) tagInput.value = clean.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30);



            }



            updateDwgPreviewName();



          }







          renderDwgTree(data.groups);



          log(`✓ Đã nạp ${data.totalViews || 0} view/bản vẽ qua ${data.groups.length} nhóm từ Revit.`, 'success');



        } else {



          container.innerHTML = `<div class="text-rose-500 p-4 text-center font-medium">Không thể nạp danh sách: ${data?.error || 'Revit chưa phản hồi'}<br><button type="button" onclick="loadDwgTreeView(true)" class="mt-2 px-3 py-1 bg-white border border-rose-200 text-rose-700 rounded-lg text-xs shadow-sm hover:bg-rose-50">Thử lại</button></div>`;



          if (summary) summary.textContent = 'Lỗi nạp';



        }



      } catch (err) {



        container.innerHTML = `<div class="text-rose-500 p-4 text-center font-medium">Lỗi kết nối: ${err}<br><button type="button" onclick="loadDwgTreeView(true)" class="mt-2 px-3 py-1 bg-white border border-rose-200 text-rose-700 rounded-lg text-xs shadow-sm hover:bg-rose-50">Thử lại</button></div>`;



        if (summary) summary.textContent = 'Lỗi kết nối';



      }



    }







    // Render TreeView DOM



    function renderDwgTree(groups) {



      const container = document.getElementById('dwgTreeContainer');



      if (!container) return;







      if (!groups || groups.length === 0) {



        container.innerHTML = '<div class="text-slate-400 p-4 text-center">Không có view nào trong dự án.</div>';



        return;



      }







      let html = '';



      groups.forEach(g => {



        const grpKey = g.groupKey || g.GroupKey || 'grp';



        const title = g.groupTitle || g.GroupTitle || 'Nhóm';



        const icon = g.icon || g.Icon || 'folder';



        const children = g.children || g.Children || [];







        html += `



          <div class="dwg-group-card border border-slate-200 rounded-xl bg-white overflow-hidden shadow-sm transition" data-group="${grpKey}">



            <!-- Group Header -->



            <div class="flex items-center justify-between px-3 py-2 bg-slate-100/80 hover:bg-slate-200/70 cursor-pointer select-none transition group-header" onclick="toggleTreeGroup('${grpKey}', event)">



              <div class="flex items-center gap-2.5 overflow-hidden">



                <span id="grp-chevron-${grpKey}" class="text-slate-400 text-[11px] w-3 transition-transform duration-150">▼</span>



                <input type="checkbox" id="grp-chk-${grpKey}" class="dwg-group-checkbox rounded text-cyan-600 focus:ring-cyan-500 w-4 h-4 cursor-pointer" onclick="event.stopPropagation(); toggleGroupChildren('${grpKey}', this.checked)">



                <span class="font-bold text-slate-800 flex items-center gap-1.5 truncate">



                  <i data-lucide="${icon}" class="w-3.5 h-3.5 text-cyan-600 flex-shrink-0"></i>



                  <span class="truncate">${title}</span>



                </span>



              </div>



              <span id="grp-count-${grpKey}" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 flex-shrink-0">0/${children.length}</span>



            </div>







            <!-- Group Children -->



            <div id="grp-children-${grpKey}" class="dwg-group-children divide-y divide-slate-100 pl-6 pr-2 py-1 bg-white">



        `;







        children.forEach(v => {



          const id = v.id ?? v.Id;



          const name = v.name ?? v.Name ?? `View_${id}`;



          const sheetNum = v.sheetNumber ?? v.SheetNumber ?? '';



          const scale = v.scale ?? v.Scale ?? '--';



          const safeNameAttr = name.replace(/"/g, '&quot;');



          const safeSheetAttr = sheetNum.replace(/"/g, '&quot;');







          html += `



            <label class="dwg-child-row flex items-center justify-between py-1.5 px-2 hover:bg-cyan-50/50 rounded-lg cursor-pointer transition select-none" data-group="${grpKey}" data-name="${safeNameAttr.toLowerCase()}" data-sheet="${safeSheetAttr.toLowerCase()}">



              <div class="flex items-center gap-2 overflow-hidden mr-2">



                <input type="checkbox" class="dwg-child-checkbox rounded text-cyan-600 focus:ring-cyan-500 w-3.5 h-3.5 cursor-pointer flex-shrink-0" data-group="${grpKey}" data-id="${id}" data-name="${safeNameAttr}" data-sheet="${safeSheetAttr}" onchange="onChildCheckboxChange('${grpKey}')">



                <span class="truncate text-slate-800 font-medium" title="${safeNameAttr}">



                  ${sheetNum ? `<span class="font-bold text-cyan-700 mr-1">[${sheetNum}]</span>` : ''}



                  ${name}



                </span>



              </div>



              <div class="flex items-center gap-2 flex-shrink-0 text-[10px]">



                <span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono font-medium">${scale}</span>



                <span class="text-slate-400 font-mono hidden sm:inline">#${id}</span>



              </div>



            </label>



          `;



        });







        html += `



            </div>



          </div>



        `;



      });







      container.innerHTML = html;



      if (typeof lucide !== 'undefined') lucide.createIcons();







      // Mặc định chọn nhóm Mặt bằng kiến trúc (Floor Plans)



      const floorGrpChk = document.getElementById('grp-chk-floor_plans');



      if (floorGrpChk) {



        toggleGroupChildren('floor_plans', true);



      } else {



        updateGlobalDwgSummary();



      }



    }







    // Toggle Group Collapse / Expand



    function toggleTreeGroup(grpKey, event) {



      if (event && event.target && (event.target.type === 'checkbox' || event.target.closest('input[type="checkbox"]'))) {



        return;



      }



      const childrenDiv = document.getElementById(`grp-children-${grpKey}`);



      const chevron = document.getElementById(`grp-chevron-${grpKey}`);



      if (!childrenDiv) return;







      const isHidden = childrenDiv.classList.contains('hidden');



      if (isHidden) {



        childrenDiv.classList.remove('hidden');



        if (chevron) chevron.textContent = '▼';



      } else {



        childrenDiv.classList.add('hidden');



        if (chevron) chevron.textContent = '▶';



      }



    }







    // Toggle All Children in a Specific Group



    function toggleGroupChildren(grpKey, isChecked) {



      const childBoxes = document.querySelectorAll(`.dwg-child-checkbox[data-group="${grpKey}"]`);



      childBoxes.forEach(cb => {



        const row = cb.closest('.dwg-child-row');



        if (!row || row.style.display !== 'none') {



          cb.checked = isChecked;



        }



      });



      updateParentGroupState(grpKey);



      updateGlobalDwgSummary();



    }







    // On Child Checkbox Changed



    function onChildCheckboxChange(grpKey) {



      updateParentGroupState(grpKey);



      updateGlobalDwgSummary();



    }







    // Update Group Checkbox and Badge Count



    function updateParentGroupState(grpKey) {



      const grpChk = document.getElementById(`grp-chk-${grpKey}`);



      const grpBadge = document.getElementById(`grp-count-${grpKey}`);



      const childBoxes = Array.from(document.querySelectorAll(`.dwg-child-checkbox[data-group="${grpKey}"]`));



      if (!grpChk || childBoxes.length === 0) return;







      const checkedCount = childBoxes.filter(cb => cb.checked).length;



      const totalCount = childBoxes.length;







      if (checkedCount === totalCount) {



        grpChk.checked = true;



        grpChk.indeterminate = false;



      } else if (checkedCount === 0) {



        grpChk.checked = false;



        grpChk.indeterminate = false;



      } else {



        grpChk.checked = false;



        grpChk.indeterminate = true;



      }







      if (grpBadge) {



        grpBadge.textContent = `${checkedCount}/${totalCount}`;



        if (checkedCount > 0) {



          grpBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800 flex-shrink-0';



        } else {



          grpBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 flex-shrink-0';



        }



      }



    }







    // Update Global Summary Badge



    function updateGlobalDwgSummary() {



      const summary = document.getElementById('dwgSelectedSummary');



      if (!summary) return;







      const allChildren = document.querySelectorAll('.dwg-child-checkbox');



      const checkedChildren = document.querySelectorAll('.dwg-child-checkbox:checked');



      summary.textContent = `Đã chọn: ${checkedChildren.length} / ${allChildren.length} view`;







      if (checkedChildren.length > 0) {



        summary.className = 'font-bold text-cyan-800 bg-cyan-100 px-2 py-0.5 rounded-full border border-cyan-300';



      } else {



        summary.className = 'font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200';



      }



    }







    // Set All Views Selected / Deselected



    function setAllDwgSelection(isSelected) {



      const visibleChildBoxes = Array.from(document.querySelectorAll('.dwg-child-checkbox')).filter(cb => {



        const row = cb.closest('.dwg-child-row');



        return !row || row.style.display !== 'none';



      });







      visibleChildBoxes.forEach(cb => {



        cb.checked = isSelected;



      });







      // Update all group states



      const groups = document.querySelectorAll('.dwg-group-card');



      groups.forEach(g => {



        const grpKey = g.dataset.group;



        if (grpKey) updateParentGroupState(grpKey);



      });







      updateGlobalDwgSummary();



    }







    // Expand / Collapse All Groups



    function setAllDwgExpansion(isExpanded) {



      const allChildrenDivs = document.querySelectorAll('.dwg-group-children');



      const allChevrons = document.querySelectorAll('[id^="grp-chevron-"]');







      allChildrenDivs.forEach(div => {



        if (isExpanded) div.classList.remove('hidden');



        else div.classList.add('hidden');



      });







      allChevrons.forEach(ch => {



        ch.textContent = isExpanded ? '▼' : '▶';



      });



    }







    // Realtime Search Filter



    function onDwgSearchInput(term) {



      const clearBtn = document.getElementById('dwgSearchClearBtn');



      const query = (term || '').trim().toLowerCase();







      if (clearBtn) {



        if (query) clearBtn.classList.remove('hidden');



        else clearBtn.classList.add('hidden');



      }







      const groups = document.querySelectorAll('.dwg-group-card');



      groups.forEach(g => {



        const grpKey = g.dataset.group;



        const rows = g.querySelectorAll('.dwg-child-row');



        let matchedCount = 0;







        rows.forEach(row => {



          const name = row.dataset.name || '';



          const sheet = row.dataset.sheet || '';



          const match = !query || name.includes(query) || sheet.includes(query);



          row.style.display = match ? '' : 'none';



          if (match) matchedCount++;



        });







        const childrenDiv = document.getElementById(`grp-children-${grpKey}`);



        const chevron = document.getElementById(`grp-chevron-${grpKey}`);







        if (matchedCount > 0) {



          g.style.display = '';



          if (query && childrenDiv) {



            childrenDiv.classList.remove('hidden');



            if (chevron) chevron.textContent = '▼';



          }



        } else {



          g.style.display = query ? 'none' : '';



        }



      });



    }







    function clearDwgSearch() {



      const input = document.getElementById('dwgSearchInput');



      if (input) {



        input.value = '';



        onDwgSearchInput('');



      }



    }







    // Update Overall Progress Bar & Status



    function updateDwgProgress(pct, statusText, detailText, countText, isDone = false) {



      const sec = document.getElementById('dwgProgressSection');



      const bar = document.getElementById('dwgProgressBar');



      const pctBadge = document.getElementById('dwgProgressPercent');



      const txt = document.getElementById('dwgProgressText');



      const det = document.getElementById('dwgProgressDetail');



      const cnt = document.getElementById('dwgProgressCount');



      const spinner = document.getElementById('dwgProgressSpinner');







      if (sec) sec.classList.remove('hidden');



      const clampedPct = Math.min(100, Math.max(0, Math.round(pct)));







      if (bar) {



        bar.style.width = `${clampedPct}%`;



        if (isDone) {



          bar.className = 'h-full bg-emerald-500 rounded-full transition-all duration-300 ease-out';



        } else {



          bar.className = 'h-full bg-gradient-to-r from-cyan-500 to-indigo-600 rounded-full transition-all duration-300 ease-out';



        }



      }







      if (pctBadge) {



        pctBadge.textContent = `${clampedPct}%`;



        if (isDone) {



          pctBadge.className = 'font-mono font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full text-xs';



        } else {



          pctBadge.className = 'font-mono font-bold text-cyan-800 bg-cyan-100 px-2.5 py-0.5 rounded-full text-xs';



        }



      }







      if (txt && statusText) txt.textContent = statusText;



      if (det && detailText) det.textContent = detailText;



      if (cnt && countText) cnt.textContent = countText;







      if (spinner) {



        if (isDone) {



          spinner.setAttribute('data-lucide', 'check-circle');



          spinner.className = 'w-4 h-4 text-emerald-600';



        } else {



          spinner.setAttribute('data-lucide', 'loader-2');



          spinner.className = 'w-4 h-4 animate-spin text-cyan-600';



        }



        if (typeof lucide !== 'undefined') lucide.createIcons();



      }



    }







    // Execute Custom DWG Export with Realtime Step-by-Step Progress



    async function runCustomDwgExport() {



      const checkedBoxes = Array.from(document.querySelectorAll('.dwg-child-checkbox:checked'));



      if (checkedBoxes.length === 0) {



        alert('Vui lòng chọn ít nhất 1 view hoặc bản vẽ trong danh sách trước khi xuất DWG!');



        log('⚠ Chưa chọn bản vẽ nào trong danh sách TreeView!', 'warning');



        return;



      }







      const totalViews = checkedBoxes.length;



      const viewList = checkedBoxes.map(cb => ({



        id: parseInt(cb.dataset.id),



        name: cb.dataset.name || `View_${cb.dataset.id}`,



        sheetNumber: cb.dataset.sheet || ''



      }));







      const mode = document.querySelector('input[name="dwgTitleblockMode"]:checked')?.value || 'none';



      const overlay = (mode === 'overlay');



      const tbFile = document.getElementById('dwgTitleblockFilePath')?.value.trim() || '';



      const layoutMode = document.querySelector('input[name="dwgLayoutMode"]:checked')?.value || 'vertical';



      const isMergeCad = (layoutMode === 'vertical');







      const projInfo = {



        projectName: document.getElementById('piProjectName')?.value.trim() || '',



        buildingName: document.getElementById('piBuildingName')?.value.trim() || '',



        projectAddress: document.getElementById('piProjectAddress')?.value.trim() || '',



        clientName: document.getElementById('piClientName')?.value.trim() || '',



        issueDate: document.getElementById('piIssueDate')?.value.trim() || '',



        author: document.getElementById('piAuthor')?.value.trim() || ''



      };







      const outputFolder = document.getElementById('dwgOutputFolder')?.value.trim() || '~/Downloads';



      const projectTag = document.getElementById('dwgProjectTag')?.value.trim() || 'Mau_40_CBS';







      const modeLabel = overlay ? `Có Khung tên (${tbFile})` : `Không Khung tên (Model Only)`;



      const layoutLabel = isMergeCad ? 'Gộp hàng dọc (Merge CAD)' : 'Từng file riêng';



      log(`Bắt đầu xuất ${totalViews} bản vẽ sang DWG [${modeLabel} | ${layoutLabel}]...`);







      const btn = document.getElementById('btnRunDwgExport');



      if (btn) {



        btn.disabled = true;



        btn.classList.add('opacity-60', 'cursor-not-allowed');



        btn.innerHTML = '<i data-lucide="loader-2" class="w-5 h-5 text-white animate-spin"></i>';



        if (typeof lucide !== 'undefined') lucide.createIcons();



      }







      updateDwgProgress(3, 'Đang khởi tạo tiến trình...', `Chuẩn bị xuất ${totalViews} bản vẽ...`, `0 / ${totalViews} bản vẽ`);







      try {



        // Bước 1: Khởi tạo phiên xuất (Chuẩn bị thư mục, nạp projectInfo)



        const initRes = await fetch('/api/export-dwg-init', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            outputFolder: outputFolder,



            projectTag: projectTag,



            layoutMode: layoutMode,



            projectInfo: projInfo



          })



        });



        const initData = await initRes.json();



        if (!initData.success) {



          throw new Error(initData.error || 'Lỗi khởi tạo phiên xuất');



        }







        const subExportFolder = initData.subExportFolder;



        const targetOutputFolder = initData.targetOutputFolder;



        const filePrefix = initData.filePrefix;



        const cleanProject = initData.cleanProject;



        const timestampStr = initData.timestamp;







        updateDwgProgress(8, 'Đã chuẩn bị xong môi trường', `Thư mục lưu: ${targetOutputFolder}`, `0 / ${totalViews} bản vẽ`);







        const exportedFiles = [];



        const perViewWeight = isMergeCad ? (75 / totalViews) : (90 / totalViews);







        // Bước 2: Xuất từng view và cập nhật tiến trình liên tục



        for (let i = 0; i < totalViews; i++) {



          const v = viewList[i];



          const currentOrder = i + 1;



          const currentPct = Math.round(8 + (i * perViewWeight));







          updateDwgProgress(



            currentPct,



            `Đang xuất view [${currentOrder}/${totalViews}]: ${v.name}...`,



            `Revit đang tạo hình học và kết xuất file DWG...`,



            `${i} / ${totalViews} bản vẽ`



          );







          const stepRes = await fetch('/api/export-dwg-step', {



            method: 'POST',



            headers: { 'Content-Type': 'application/json' },



            body: JSON.stringify({



              viewId: v.id,



              orderIndex: currentOrder,



              combineVertical: isMergeCad,



              subExportFolder: subExportFolder,



              filePrefix: filePrefix,



              overlayTitleblock: overlay,



              titleblockFile: tbFile



            })



          });







          const stepData = await stepRes.json();



          if (stepData.success && stepData.file) {



            exportedFiles.push(stepData.file);



            const donePct = Math.round(8 + (currentOrder * perViewWeight));



            updateDwgProgress(



              donePct,



              `Đã xuất xong [${currentOrder}/${totalViews}]: ${v.name}`,



              `Kích thước: ${stepData.file.fileSizeKb || 0} KB ➔ ${stepData.file.filePath}`,



              `${currentOrder} / ${totalViews} bản vẽ`



            );



            const sheetTag = stepData.file.sheetNumber ? ` [${stepData.file.sheetNumber}]` : '';



            log(`  &bull; [${currentOrder}/${totalViews}] ${stepData.file.viewName}${sheetTag} ➔ ${stepData.file.filePath} (${stepData.file.fileSizeKb} KB)`, 'info');



          } else {



            log(`  ✗ [${currentOrder}/${totalViews}] ${v.name}: ${stepData.error || 'Lỗi kết xuất view'}`, 'error');



          }



        }







        if (exportedFiles.length === 0) {



          throw new Error('Không có view nào được xuất thành công.');



        }







        // Bước 3: Nếu chọn Gộp hàng dọc (Merge CAD), chạy AutoCAD Core Console



        let finalPath = targetOutputFolder;



        if (isMergeCad) {



          updateDwgProgress(



            88,



            'Đang chạy AutoCAD Core Console gộp hàng dọc...',



            'AutoCAD đang sắp xếp các view theo hàng dọc và đồng bộ bảng màu Layer chuẩn...',



            `${totalViews} / ${totalViews} bản vẽ`



          );







          const asmRes = await fetch('/api/export-dwg-assemble', {



            method: 'POST',



            headers: { 'Content-Type': 'application/json' },



            body: JSON.stringify({



              cleanProject: cleanProject,



              timestamp: timestampStr,



              targetOutputFolder: targetOutputFolder,



              subExportFolder: subExportFolder,



              exportedFiles: exportedFiles



            })



          });







          const asmData = await asmRes.json();



          if (asmData.success && asmData.combinedDwgPath) {



            finalPath = asmData.combinedDwgPath;



            log(`✓ THÀNH CÔNG: Đã gộp toàn bộ ${exportedFiles.length} bản vẽ thành 1 file CAD!`, 'success');



            log(`  ★ File Merge CAD: ${finalPath}`, 'success');



          } else {



            log(`⚠ Gộp file AutoCAD gặp sự cố: ${asmData.message || 'Xem nhật ký assemble'}. Các file con đã lưu tại thư mục xuất.`, 'warning');



          }



        } else {



          log(`✓ THÀNH CÔNG: Đã xuất toàn bộ ${exportedFiles.length} file DWG riêng biệt vào Downloads!`, 'success');



        }







        // Bước 4: Hoàn thành 100%



        updateDwgProgress(



          100,



          '✓ Hoàn tất xuất bản vẽ 100%!',



          `Đã lưu file thành công tại: ${finalPath}`,



          `${totalViews} / ${totalViews} bản vẽ`,



          true



        );







      } catch (err) {



        log(`✗ LỖI XUẤT DWG: ${err.message || err}`, 'error');



        updateDwgProgress(



          0,



          `✗ Đã xảy ra lỗi khi xuất bản vẽ`,



          `${err.message || err}`,



          `0 / ${totalViews} bản vẽ`



        );



      } finally {



        if (btn) {



          btn.disabled = false;



          btn.classList.remove('opacity-60', 'cursor-not-allowed');



          btn.innerHTML = '<i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>';



          if (typeof lucide !== 'undefined') lucide.createIcons();



        }



      }



    }







    // Execute Paste CAD Text



    async function runPasteCadText() {



      const targetView = document.getElementById('cadTargetView').value;



      log(`Lấy text chọn trong AutoCAD và dán vào Revit View ${targetView}...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ action: 'paste_cad_text', targetView: targetView })



        });



        const data = await res.json();



        log(`✓ Kết quả Paste CAD: ${data.message || JSON.stringify(data)}`, 'success');



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // Execute Sync 3ds Max



    async function runSyncMaxToRevit() {



      log(`Đang kiểm tra đối tượng chọn trong Revit & 3ds Max...`);







      try {



        // Bước 1: Kiểm tra xem Revit có đang chọn 1 Family không



        const checkRes = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ action: 'check_revit_sync_target' })



        });



        const checkData = await checkRes.json();







        // Kiểm tra xem bên 3ds Max có chọn vật thể nào không



        if (checkData.maxHasSelection === false) {



          log(`⚠ Vui lòng chọn ít nhất 1 vật thể trong 3ds Max trước khi bấm đồng bộ!`, 'warn');



          alert('Vui lòng chọn ít nhất 1 vật thể trong 3ds Max trước khi bấm nút đồng bộ!');



          return;



        }







        // Nếu Revit ĐÃ CHỌN 1 Family có thể chỉnh sửa: đồng bộ đè trực tiếp



        if (checkData.isEditableFamily) {



          log(`Phát hiện Family đang chọn trong Revit: [${checkData.familyName}] (ID: ${checkData.instanceId}). Bắt đầu đồng bộ đè hình học...`);



          await doSyncMaxToRevit(false, null);



        } else {



          // Nếu KHÔNG chọn object nào hoặc object không phải là family:



          // Hỏi người dùng có muốn tạo Family mới không!



          let reasonMsg = checkData.hasSelection 



            ? `Đối tượng đang chọn trong Revit (ID: ${checkData.elementId} - ${checkData.category || 'Đối tượng'}) không phải là Family có thể chỉnh sửa (.rfa).`



            : `Hiện tại bạn chưa chọn đối tượng/Family nào trên màn hình Revit.`;



          



          openNewFamilyModal(checkData.maxObjectName || 'Family_3dsMax', reasonMsg);



        }



      } catch (err) {



        log(`✗ Lỗi kiểm tra đồng bộ: ${err}`, 'error');



      }



    }







    function openNewFamilyModal(defaultName, reasonMsg) {



      const modal = document.getElementById('modalNewFamily');



      const input = document.getElementById('inputNewFamilyName');



      const desc = document.getElementById('modalNewFamilyDesc');



      if (input) input.value = defaultName || 'Family_3dsMax';



      if (desc && reasonMsg) {



        desc.innerText = `${reasonMsg}\nBạn có muốn tạo một Family mới trong Revit từ các vật thể 3ds Max này không?`;



      }



      if (modal) {



        modal.classList.remove('hidden');



        if (typeof lucide !== 'undefined') lucide.createIcons();



        if (input) {



          setTimeout(() => { input.focus(); input.select(); }, 50);



        }



      }



    }







    function closeNewFamilyModal() {



      const modal = document.getElementById('modalNewFamily');



      if (modal) modal.classList.add('hidden');



      log(`Đã hủy thao tác tạo Family mới.`, 'info');



    }







    async function confirmCreateNewFamily() {



      const input = document.getElementById('inputNewFamilyName');



      const famName = (input ? input.value.trim() : '') || 'Family_3dsMax';



      const modal = document.getElementById('modalNewFamily');



      if (modal) modal.classList.add('hidden');



      log(`Bắt đầu tạo Family mới [${famName}] từ 3ds Max vào Revit...`);



      await doSyncMaxToRevit(true, famName);



    }







    async function doSyncMaxToRevit(createNewFamily, newFamilyName) {



      try {



        const payload = {



          action: 'sync_3dsmax',



          createNewFamily: !!createNewFamily,



          newFamilyName: newFamilyName || ''



        };



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify(payload)



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message || 'Đồng bộ hoàn tất.'}`, 'success');



        } else {



          log(`✗ LỖI đồng bộ: ${data.message || JSON.stringify(data)}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối đồng bộ: ${err}`, 'error');



      }



    }







    // Execute Export Revit to 3ds Max (Clean Poly, No Triangulation)



    async function runExportRevitToMaxPoly() {



      const fileName = document.getElementById('revitToMaxFileName').value.trim() || 'Revit_To_Max_Solids';



      log(`Đang xuất vật thể Revit sang 3ds Max dạng ACIS Solids (Không chia tam giác)...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ action: 'export_to_3dsmax_poly', fileName: fileName })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



          if (data.dwgPath) log(`  &bull; File Solids DWG: ${data.dwgPath} (${data.fileSizeKb ? data.fileSizeKb.toFixed(1) : 0} KB)`, 'info');



          if (data.maxScriptPath) log(`  &bull; Script MAXScript tự động: ${data.maxScriptPath}`, 'info');



          log(`  &bull; Lệnh vào 3ds Max: Kéo thả file .ms vào 3ds Max hoặc chạy: for o in selection do ( convertToPoly o; PolyToolsModeling.Quadrify false false )`, 'info');



        } else {



          log(`✗ LỖI: ${data.message || JSON.stringify(data)}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // Update slab default thickness & offset presets



    function updateSlabPresets() {



      const cat = document.querySelector('input[name="slabCategory"]:checked')?.value || 'standard';



      const thickInput = document.getElementById('slabThickness');



      const offsetInput = document.getElementById('slabOffset');



      if (cat === 'toilet') {



        if (thickInput && thickInput.value === '100') thickInput.value = '50';



        if (offsetInput && offsetInput.value === '0') offsetInput.value = '-50';



      } else {



        if (thickInput && thickInput.value === '50') thickInput.value = '100';



        if (offsetInput && offsetInput.value === '-50') offsetInput.value = '0';



      }



    }







    // Execute Convert CAD Polyline to Revit Slab (with Smart Replace)



    async function runConvertCadPolylineToSlab() {



      const cat = document.querySelector('input[name="slabCategory"]:checked')?.value || 'standard';



      const thickness = parseFloat(document.getElementById('slabThickness').value) || 100;



      const offset = parseFloat(document.getElementById('slabOffset').value) || 0;



      const levelId = parseInt(document.getElementById('slabTargetLevel').value) || -1;







      log(`Đang lấy Polyline từ AutoCAD và tạo/thay thế sàn Revit...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'convert_cad_polyline_to_slab',



            floorCategory: cat,



            thicknessMm: thickness,



            offsetMm: offset,



            levelId: levelId



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



          if (data.floorId) {



            log(`  &bull; Sàn: ID ${data.floorId} (${data.floorTypeName}) | Diện tích: ${data.areaSqm} m²`, 'info');



            log(`  &bull; Tầng: ${data.levelName} | Độ dày: ${data.thicknessMm}mm | Offset: ${data.offsetMm}mm`, 'info');



          }



          refreshModelInfo();



        } else {



          log(`✗ LỖI: ${data.message || data.error || JSON.stringify(data)}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // Update Target Axes Preset & Help Text based on Axis Direction (X vs Y)



    function updateSyncAxesHelp() {



      const dir = document.querySelector('input[name="syncAxisDirection"]:checked')?.value || 'X';



      const help = document.getElementById('syncAxesHelpText');



      const preset = document.getElementById('syncAxesPreset');



      const input = document.getElementById('syncTargetAxes');







      if (dir === 'X') {



        if (help) help.textContent = "(VD: A, E hoặc C, D hoặc để 'all' cho tất cả)";



        if (preset) {



          preset.innerHTML = `



            <option value="all">Tất cả trục (All)</option>



            <option value="A, E">Trục A, E (Mặt tiền & Hậu)</option>



            <option value="C">Trục C (Hành lang)</option>



            <option value="D">Trục D (Phòng làm việc)</option>



            <option value="custom">Tự nhập...</option>



          `;



        }



      } else {



        if (help) help.textContent = "(VD: 1, 11 hoặc để 'all' cho tất cả)";



        if (preset) {



          preset.innerHTML = `



            <option value="all">Tất cả trục (All)</option>



            <option value="1, 11">Trục 1, 11 (Tường hồi biên)</option>



            <option value="2, 10">Trục 2, 10</option>



            <option value="custom">Tự nhập...</option>



          `;



        }



      }



      if (input && preset && preset.value !== 'custom') {



        input.value = preset.value;



      }



    }







    function applySyncAxesPreset() {



      const preset = document.getElementById('syncAxesPreset')?.value;



      const input = document.getElementById('syncTargetAxes');



      if (preset && input && preset !== 'custom') {



        input.value = preset;



      }



    }







    // Execute Synchronize Openings (Doors/Windows) with Floor 1



    async function runSyncOpeningsByFloor1() {



      const cat = document.querySelector('input[name="syncCategory"]:checked')?.value || 'windows';



      const dir = document.querySelector('input[name="syncAxisDirection"]:checked')?.value || 'X';



      const axes = document.getElementById('syncTargetAxes')?.value.trim() || 'all';



      const applyMove = document.getElementById('syncApplyMove')?.checked ?? true;







      const catLabel = cat === 'windows' ? 'Cửa sổ' : (cat === 'doors' ? 'Cửa đi' : 'Cửa sổ & Cửa đi');



      log(`Đang phân tích và đồng bộ vị trí ${catLabel} theo Tầng 1 (Phương ${dir}, Trục: ${axes}, Thực thi: ${applyMove ? 'CÓ' : 'XEM TRƯỚC'})...`);







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'sync_openings_by_floor1',



            category: cat,



            axisDirection: dir,



            targetAxes: axes,



            apply: applyMove



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ ${data.message}`, 'success');



          log(`  &bull; Tổng quét: ${data.totalFound} cửa (Tầng 1: ${data.floor1Count}, Tầng trên: ${data.upperCount})`, 'info');



          log(`  &bull; Cần dịch chuyển: ${data.needsMoveCount} | Đã dịch chuyển: ${data.movedCount}`, data.movedCount > 0 ? 'success' : 'info');







          if (data.details && data.details.length > 0) {



            const needMoves = data.details.filter(d => d.needsMove);



            if (needMoves.length > 0) {



              log(`  --- Chi tiết các cửa cần chỉnh vị trí (${needMoves.length}) ---`, 'info');



              needMoves.slice(0, 10).forEach(d => {



                const markStr = d.mark ? ` [Mark: ${d.mark}]` : '';



                log(`    &bull; ID ${d.id} (${d.name})${markStr} | ${d.axis}_${d.bay} | ${d.level}: Hiện tại=${d.current} ➔ Đích Tầng 1=${d.target} (Lệch: ${d.delta}mm) ${d.moved ? '✓ Đã dời' : ''}`, 'info');



              });



              if (needMoves.length > 10) {



                log(`    ... và còn ${needMoves.length - 10} cửa khác.`, 'info');



              }



            } else {



              log(`  &bull; Tất cả các cửa tầng trên đã thẳng hàng chính xác với Tầng 1!`, 'success');



            }



          }



          refreshModelInfo();



        } else {



          log(`✗ LỖI: ${data.message || data.error || JSON.stringify(data)}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // =========================================================================



    // TAB 10: MANAGE DOOR & WINDOW TAGS (HIDE / SHOW BY LEVEL OR ALL LEVELS)



    // =========================================================================



    let tagsDataCache = [];







    async function loadTagsStatus() {



      const icon = document.getElementById('tagsRefreshIcon');



      const badge = document.getElementById('tagsSummaryBadge');



      const tbody = document.getElementById('tagsStatusTableBody');



      const levelSelect = document.getElementById('tagsLevelSelect');



      if (icon) icon.classList.add('animate-spin');



      if (badge) badge.textContent = 'Đang quét trạng thái...';







      try {



        const res = await fetch('/api/tags-status');



        const data = await res.json();



        if (data.success && data.views) {



          tagsDataCache = data.views;



          



          // 1. Populate level select dropdown



          const currentSelected = levelSelect ? levelSelect.value : 'all';



          let selectHtml = '<option value="all">⭐ Tất cả các tầng (All Levels)</option>';



          data.views.forEach(v => {



            const vname = v.viewName || `View_${v.viewId}`;



            selectHtml += `<option value="${v.viewId}">${vname} [${v.doorTagCount} Door, ${v.windowTagCount} Win]</option>`;



          });



          if (levelSelect) {



            levelSelect.innerHTML = selectHtml;



            levelSelect.value = currentSelected;



          }







          // 2. Populate status table



          let totalDoors = 0;



          let totalWins = 0;



          let tableHtml = '';







          data.views.forEach(v => {



            totalDoors += v.doorTagCount || 0;



            totalWins += v.windowTagCount || 0;







            const doorBadge = v.doorTagCount === 0 



              ? '<span class="px-2 py-0.5 rounded bg-slate-100 text-slate-400 font-medium">0 tag</span>'



              : (v.doorTagsHidden



                ? `<span class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-bold">${v.doorTagCount} [Đang Ẩn]</span>`



                : `<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">${v.doorTagCount} [Đang Hiện]</span>`);







            const winBadge = v.windowTagCount === 0



              ? '<span class="px-2 py-0.5 rounded bg-slate-100 text-slate-400 font-medium">0 tag</span>'



              : (v.windowTagsHidden



                ? `<span class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-bold">${v.windowTagCount} [Đang Ẩn]</span>`



                : `<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">${v.windowTagCount} [Đang Hiện]</span>`);







            tableHtml += `



              <tr class="hover:bg-pink-50/30 transition">



                <td class="py-2.5 px-3">



                  <div class="font-bold text-slate-900 truncate">${v.viewName}</div>



                  <div class="text-[10px] text-slate-400 font-mono">ID #${v.viewId} ${v.hasTemplate ? '&bull; Có View Template' : ''}</div>



                </td>



                <td class="py-2.5 px-3 text-center">${doorBadge}</td>



                <td class="py-2.5 px-3 text-center">${winBadge}</td>



                <td class="py-2.5 px-3 text-right">



                  <div class="flex items-center justify-end gap-1.5">



                    <button onclick="quickToggleTag('${v.viewId}', 'all', true)" class="px-2 py-1 rounded bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 font-medium transition" title="Ẩn tất cả tag view này">Ẩn</button>



                    <button onclick="quickToggleTag('${v.viewId}', 'all', false)" class="px-2 py-1 rounded bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-600 font-medium transition" title="Hiện tất cả tag view này">Hiện</button>



                  </div>



                </td>



              </tr>



            `;



          });







          if (tbody) tbody.innerHTML = tableHtml || '<tr><td colspan="4" class="py-4 text-center text-slate-400">Không tìm thấy mặt bằng nào.</td></tr>';



          if (badge) badge.textContent = `${data.views.length} Mặt bằng &bull; ${totalDoors} Tag cửa đi &bull; ${totalWins} Tag cửa sổ`;







        } else {



          if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-rose-500 font-semibold">${data.error || 'Lỗi nạp trạng thái tag'}</td></tr>`;



          if (badge) badge.textContent = 'Lỗi nạp';



        }



      } catch (err) {



        if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-rose-500 font-semibold">Lỗi kết nối: ${err}</td></tr>`;



        if (badge) badge.textContent = 'Lỗi kết nối';



      } finally {



        if (icon) icon.classList.remove('animate-spin');



      }



    }







    async function runTagVisibilityAction() {



      const cat = document.querySelector('input[name="tagCategory"]:checked')?.value || 'all';



      const level = document.getElementById('tagsLevelSelect')?.value || 'all';



      const actionType = document.querySelector('input[name="tagActionType"]:checked')?.value || 'hide';



      const isHide = (actionType === 'hide');







      const catLabel = (cat === 'door') ? 'Tag Cửa đi' : (cat === 'window') ? 'Tag Cửa sổ' : 'Tag Cửa đi & Cửa sổ';



      const lvlLabel = (level === 'all') ? 'TẤT CẢ CÁC TẦNG' : `Tầng ID #${level}`;



      const stateLabel = isHide ? 'ẨN' : 'HIỆN';







      log(`Bắt đầu thực thi: ${stateLabel} [${catLabel}] tại [${lvlLabel}]...`);







      const btn = document.getElementById('btnRunTagVisibility');



      if (btn) {



        btn.disabled = true;



        btn.classList.add('opacity-60', 'cursor-not-allowed');



        btn.innerHTML = '<i data-lucide="loader-2" class="w-5 h-5 text-white animate-spin"></i>';



        if (typeof lucide !== 'undefined') lucide.createIcons();



      }







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'manage_tags',



            subAction: 'set_visibility',



            target: cat,



            viewTarget: level,



            hide: isHide



          })



        });







        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



          if (data.updatedViews && data.updatedViews.length > 0) {



            data.updatedViews.forEach(uv => {



              log(`  &bull; ${uv.viewName}: ${uv.affectedCount > 0 ? (isHide ? 'Đã ẩn ' : 'Đã hiện ') + uv.affectedCount + ' tag' : 'Không có tag thay đổi'}`, 'info');



            });



          }



          await loadTagsStatus();



          refreshModelInfo();



        } else {



          log(`✗ LỖI: ${data.message || data.error || JSON.stringify(data)}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      } finally {



        if (btn) {



          btn.disabled = false;



          btn.classList.remove('opacity-60', 'cursor-not-allowed');



          btn.innerHTML = '<i data-lucide="play" class="w-5 h-5 fill-white group-hover:scale-110 transition-transform"></i>';



          if (typeof lucide !== 'undefined') lucide.createIcons();



        }



      }



    }







    async function quickToggleTag(viewId, target, hide) {



      const stateLabel = hide ? 'Ẩn' : 'Hiện';



      log(`Thao tác nhanh: ${stateLabel} tag cho View #${viewId}...`);



      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'manage_tags',



            subAction: 'set_visibility',



            target: target,



            viewTarget: String(viewId),



            hide: hide



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ ${data.message}`, 'success');



          await loadTagsStatus();



        } else {



          log(`✗ Lỗi: ${data.message || data.error}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    function toggleMepCadScope(scope) {



      const container = document.getElementById('mepCadPathContainer');



      const groupFolder = document.getElementById('mepCadFolderGroup');



      const groupFile = document.getElementById('mepCadFileGroup');



      



      const cards = [



        { id: 'scopeCardActive', val: 'active' },



        { id: 'scopeCardFolder', val: 'folder' },



        { id: 'scopeCardFile', val: 'file' }



      ];







      cards.forEach(c => {



        const el = document.getElementById(c.id);



        if (!el) return;



        if (c.val === scope) {



          el.className = 'flex items-start gap-2.5 p-3 rounded-xl border-2 border-rose-500 bg-rose-50/50 cursor-pointer transition select-none';



        } else {



          el.className = 'flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer transition select-none';



        }



      });







      if (scope === 'active') {



        container.classList.add('hidden');



      } else if (scope === 'folder') {



        container.classList.remove('hidden');



        groupFolder.classList.remove('hidden');



        groupFile.classList.add('hidden');



      } else if (scope === 'file') {



        container.classList.remove('hidden');



        groupFolder.classList.add('hidden');



        groupFile.classList.remove('hidden');



      }



    }







    async function runMepCadAction(subAction) {



      const scope = document.querySelector('input[name="mepCadScope"]:checked')?.value || 'active';



      const layer = document.getElementById('mepCadLayer')?.value.trim() || 'P-PIPE-CNTR';



      const searchChar = document.getElementById('mepCadSearchChar')?.value.trim() || '+';



      const maxDist = parseFloat(document.getElementById('mepCadMaxDist')?.value) || 5000.0;



      const offsetY = parseFloat(document.getElementById('mepCadOffsetY')?.value) || 250.0;



      const filePath = document.getElementById('mepCadFilePath')?.value.trim() || '';



      const folderPath = document.getElementById('mepCadFolderPath')?.value.trim() || '';







      const actionTitle = (subAction === 'delete_solids') 



        ? 'Xóa Hatch Solid & Solid' 



        : ((subAction === 'add_leaders') ? 'Kéo Leader Cao Độ' : 'Toàn Bộ MEP Polish (Xóa Solid + Kéo Leader)');



      



      const scopeLabel = (scope === 'active') ? 'AutoCAD đang mở' : ((scope === 'folder') ? 'Thư mục DWG hàng loạt' : `File: ${filePath}`);



      log(`Bắt đầu: ${actionTitle} [Mục tiêu: ${scopeLabel}, Layer: ${layer}, Dịch Y: -${offsetY}mm]...`, 'info');







      const btnMap = {



        'delete_solids': document.getElementById('btnCadDeleteSolids'),



        'add_leaders': document.getElementById('btnCadAddLeaders'),



        'full': document.getElementById('btnCadFullPolish')



      };



      const activeBtn = btnMap[subAction];



      const origHtml = activeBtn ? activeBtn.innerHTML : '';



      if (activeBtn) {



        activeBtn.disabled = true;



        activeBtn.classList.add('opacity-60', 'cursor-not-allowed');



        activeBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Đang xử lý AutoCAD...</span>';



        if (typeof lucide !== 'undefined') lucide.createIcons();



      }







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'cad_mep_polish',



            subAction: subAction,



            scope: scope,



            layer: layer,



            searchChar: searchChar,



            maxDist: maxDist,



            offsetY: offsetY,



            filePath: filePath,



            folderPath: folderPath



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message || 'Đã hoàn tất xử lý CAD'}`, 'success');



          if (data.results && Array.isArray(data.results)) {



            data.results.forEach(r => {



              log(`  &bull; [${r.index}/${data.total}] ${r.file}: ${r.message}`, r.success ? 'info' : 'warning');



            });



          }



        } else {



          log(`✗ LỖI: ${data.message || JSON.stringify(data)}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      } finally {



        if (activeBtn) {



          activeBtn.disabled = false;



          activeBtn.classList.remove('opacity-60', 'cursor-not-allowed');



          activeBtn.innerHTML = origHtml;



          if (typeof lucide !== 'undefined') lucide.createIcons();



        }



      }



    }







    // =========================================================================



    // TAB 12: LỌC KHUNG TÊN & IN HÀNG LOẠT (BATCH PLOT)



    // =========================================================================



    let currentCadPlotItems = [];







    async function runScanCadTitleblocks() {



      const btn = document.getElementById('btnScanCadPlot');



      const origHtml = btn.innerHTML;



      btn.disabled = true;



      btn.classList.add('opacity-60', 'cursor-not-allowed');



      btn.innerHTML = `<span class="inline-block animate-spin mr-2">🔄</span> Đang bóc tách mảng & phân tích khung tên trong AutoCAD...`;







      const scope = document.getElementById('cadPlotScope').value;



      const sortMode = document.getElementById('cadPlotSortMode').value;



      const skipEmpty = document.getElementById('cadPlotSkipEmpty').checked;







      log(`[CAD Plot] Bắt đầu quét khung tên (Phạm vi: ${scope}, Sắp xếp: ${sortMode}, Lọc trống: ${skipEmpty})...`, 'info');







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'scan_cad_titleblocks',



            scope: scope,



            sortMode: sortMode,



            skipEmpty: skipEmpty



          })



        });



        const data = await res.json();



        if (data.success) {



          currentCadPlotItems = data.items || [];



          document.getElementById('statCadPlotTotal').textContent = data.totalScanned || 0;



          document.getElementById('statCadPlotContent').textContent = data.totalWithContent || 0;



          document.getElementById('statCadPlotEmpty').textContent = data.totalEmpty || 0;







          renderCadPlotTable(currentCadPlotItems);



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



        } else {



          log(`✗ LỖI: ${data.message || 'Không thể quét khung tên'}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      } finally {



        btn.disabled = false;



        btn.classList.remove('opacity-60', 'cursor-not-allowed');



        btn.innerHTML = origHtml;



        if (typeof lucide !== 'undefined') lucide.createIcons();



      }



    }







    function renderCadPlotTable(items) {



      const tbody = document.getElementById('cadPlotTableBody');



      if (!items || items.length === 0) {



        tbody.innerHTML = `<tr><td colspan="9" class="p-6 text-center text-slate-400 font-sans">Không tìm thấy khung tên nào phù hợp với bộ lọc.</td></tr>`;



        return;



      }







      let html = '';



      items.forEach((it, idx) => {



        const badgeColor = it.sheetType.includes('Mặt bằng') ? 'bg-blue-50 text-blue-700 border-blue-200' :



                           it.sheetType.includes('Mặt đứng') ? 'bg-amber-50 text-amber-700 border-amber-200' :



                           it.sheetType.includes('Mặt cắt') ? 'bg-purple-50 text-purple-700 border-purple-200' :



                           it.sheetType.includes('Bìa') ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :



                           'bg-slate-100 text-slate-700 border-slate-200';







        html += `



          <tr class="hover:bg-teal-50/40 transition group">



            <td class="p-2.5 text-center">



              <input type="checkbox" class="cad-plot-item-chk rounded border-slate-300 text-teal-600 focus:ring-0" data-idx="${idx}" checked>



            </td>



            <td class="p-2.5 text-center font-bold text-slate-700">${String(it.stt).padStart(2, '0')}</td>



            <td class="p-2.5 font-semibold text-slate-800">${it.columnName || ('Ô ' + it.cellIndex)}</td>



            <td class="p-2.5 font-sans font-bold text-slate-900 group-hover:text-teal-700 transition">



              ${it.title}



              <div class="text-[10px] text-slate-400 font-mono font-normal">Block: ${it.tbName || it.arrayBlock} (Ô: ${it.cellIndex})</div>



            </td>



            <td class="p-2.5">



              <span class="text-[10px] px-2 py-0.5 rounded-full border font-sans font-semibold ${badgeColor}">



                ${it.sheetType}



              </span>



            </td>



            <td class="p-2.5 text-slate-600 font-mono text-[10px]">



              (${it.xmin.toFixed(1)}, ${it.ymin.toFixed(1)})<br>&rarr; (${it.xmax.toFixed(1)}, ${it.ymax.toFixed(1)})



            </td>



            <td class="p-2.5 text-center font-mono text-slate-700">



              ${it.width.toFixed(0)} &times; ${it.height.toFixed(0)}



            </td>



            <td class="p-2.5 text-center">



              <span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 font-bold" title="Texts: ${it.textCount}, Dims: ${it.dimCount}, Lines: ${it.lineCount}, Hatches: ${it.hatchCount}">



                ${it.totalEntities}



              </span>



            </td>



            <td class="p-2.5 text-center">



              <button onclick="zoomToCadPlotItem(${it.xmin}, ${it.ymin}, ${it.xmax}, ${it.ymax})" class="p-1 px-2 rounded-lg bg-slate-100 hover:bg-teal-100 hover:text-teal-700 text-slate-700 font-sans text-[11px] font-semibold border border-slate-200 transition flex items-center gap-1 mx-auto" title="Zoom AutoCAD đến khung này">



                <i data-lucide="zoom-in" class="w-3.5 h-3.5"></i>



                <span>Zoom</span>



              </button>



            </td>



          </tr>



        `;



      });







      tbody.innerHTML = html;



      if (typeof lucide !== 'undefined') lucide.createIcons();



    }







    async function zoomToCadPlotItem(xmin, ymin, xmax, ymax) {



      log(`[CAD Plot] Đang zoom AutoCAD tới vùng (${xmin.toFixed(1)}, ${ymin.toFixed(1)}) -> (${xmax.toFixed(1)}, ${ymax.toFixed(1)})...`, 'info');



      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'zoom_cad_region',



            xmin: xmin,



            ymin: ymin,



            xmax: xmax,



            ymax: ymax



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ Đã zoom màn hình AutoCAD đến khung tên chỉ định!`, 'success');



        } else {



          log(`✗ Không thể zoom AutoCAD: ${data.message}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối zoom: ${err}`, 'error');



      }



    }







    function toggleSelectAllCadPlots(master) {



      const chks = document.querySelectorAll('.cad-plot-item-chk');



      chks.forEach(c => c.checked = master.checked);



    }







    async function runBatchPlotAction(subAction) {



      let chks = document.querySelectorAll('.cad-plot-item-chk:checked');



      if (chks.length === 0) {



        if (currentCadPlotItems.length === 0) {



          log('[CAD Plot] Danh sách trống, đang tự động quét khung tên từ AutoCAD...', 'info');



          await runScanCadTitleblocks();



          chks = document.querySelectorAll('.cad-plot-item-chk:checked');



        }



        if (chks.length === 0) {



          alert('Không tìm thấy khung tên nào có nội dung trong AutoCAD để in. Vui lòng chọn mảng khung tên trong AutoCAD và bấm nút "Quét & Phân Tích Khung Tên"!');



          return;



        }



      }







      const selectedIndices = Array.from(chks).map(c => parseInt(c.getAttribute('data-idx')));



      const selectedItems = selectedIndices.map(i => currentCadPlotItems[i]).filter(Boolean);







      const device = document.getElementById('cadPlotDevice').value;



      const paperSize = document.getElementById('cadPlotPaperSize').value;



      const plotStyle = document.getElementById('cadPlotStyle').value;



      const outputDir = document.getElementById('cadPlotOutputDir').value.trim();







      const btnId = subAction === 'generate_only' ? 'btnCadPlotGenScript' : 'btnCadPlotExec';



      const btn = document.getElementById(btnId);



      const origHtml = btn.innerHTML;



      btn.disabled = true;



      btn.classList.add('opacity-60', 'cursor-not-allowed');







      const actionName = subAction === 'generate_only' ? 'Tạo script LISP' : 'In hàng loạt vào AutoCAD';



      log(`[CAD Plot] Bắt đầu ${actionName} cho ${selectedItems.length} bản vẽ...`, 'info');







      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'batch_plot_cad',



            subAction: subAction,



            items: selectedItems,



            plotDevice: device,



            paperSize: paperSize,



            plotStyle: plotStyle,



            outputDir: outputDir



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: ${data.message}`, 'success');



          if (data.scriptPath) {



            log(`  &bull; File Script: ${data.scriptPath}`, 'info');



          }



          if (data.outputDir) {



            log(`  &bull; Thư mục xuất PDF: ${data.outputDir}`, 'info');



          }



        } else {



          log(`✗ LỖI: ${data.message || 'Không thể thực thi lệnh in'}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối in ấn: ${err}`, 'error');



      } finally {



        btn.disabled = false;



        btn.classList.remove('opacity-60', 'cursor-not-allowed');



        btn.innerHTML = origHtml;



        if (typeof lucide !== 'undefined') lucide.createIcons();



      }



    }







    // =========================================================================



    // 3 TABS: CÔNG CỤ AEC, CADLIB LISP EXPLORER, MAXSCRIPT & PYTHON EXPLORER



    // =========================================================================



    let cadlibLispItems = [];



    let cadlibLispCategories = [];



    let cadlibLispCategoryCounts = {};



    let activeLispCategory = 'all';



    let activeCadlibSource = 'all';



    let currentFilteredCadlib = [];







    let maxscriptItems = [];



    let maxscriptCategories = [];



    let maxscriptCategoryCounts = {};



    let activeMaxscriptCategory = 'all';



    let activeMaxscriptSource = 'all';







    function switchNavTab(tabName) {



      const btnTools = document.getElementById('navTabBtn-tools');



      const btnCadlib = document.getElementById('navTabBtn-cadlib');



      const btnMaxscript = document.getElementById('navTabBtn-maxscript');



      const paneTools = document.getElementById('navPane-tools');



      const paneCadlib = document.getElementById('navPane-cadlib');



      const paneMaxscript = document.getElementById('navPane-maxscript');







      const activeClass = 'flex-1 py-1.5 px-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1 bg-white text-indigo-700 shadow-xs cursor-pointer truncate';



      const inactiveClass = 'flex-1 py-1.5 px-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1 text-slate-600 hover:text-slate-900 cursor-pointer truncate';







      if (tabName === 'tools') {



        if (btnTools) btnTools.className = activeClass;



        if (btnCadlib) btnCadlib.className = inactiveClass;



        if (btnMaxscript) btnMaxscript.className = inactiveClass;



        if (paneTools) paneTools.classList.remove('hidden');



        if (paneCadlib) paneCadlib.classList.add('hidden');



        if (paneMaxscript) paneMaxscript.classList.add('hidden');



      } else if (tabName === 'cadlib') {



        if (btnTools) btnTools.className = inactiveClass;



        if (btnCadlib) btnCadlib.className = activeClass;



        if (btnMaxscript) btnMaxscript.className = inactiveClass;



        if (paneTools) paneTools.classList.add('hidden');



        if (paneCadlib) paneCadlib.classList.remove('hidden');



        if (paneMaxscript) paneMaxscript.classList.add('hidden');







        if (cadlibLispItems.length === 0) {



          loadCadlibLisps();



        } else {



          filterLispCards();



        }



        setTimeout(() => {



          const inp = document.getElementById('lispSearchInput');



          if (inp) inp.focus();



        }, 80);



      } else if (tabName === 'maxscript') {



        if (btnTools) btnTools.className = inactiveClass;



        if (btnCadlib) btnCadlib.className = inactiveClass;



        if (btnMaxscript) btnMaxscript.className = activeClass;



        if (paneTools) paneTools.classList.add('hidden');



        if (paneCadlib) paneCadlib.classList.add('hidden');



        if (paneMaxscript) paneMaxscript.classList.remove('hidden');







        if (maxscriptItems.length === 0) {



          loadMaxscripts();



        } else {



          filterMaxscriptCards();



        }



        setTimeout(() => {



          const inp = document.getElementById('maxscriptSearchInput');



          if (inp) inp.focus();



        }, 80);



      }



    }







    async function openLispHelpModal() {



      switchNavTab('cadlib');



    }







    function closeLispHelpModal() {



      switchNavTab('tools');



    }







    // Lắng nghe phím ESC để chuyển về tab công cụ chính



    document.addEventListener('keydown', function(e) {



      if (e.key === 'Escape') {



        const paneCadlib = document.getElementById('navPane-cadlib');



        const paneMaxscript = document.getElementById('navPane-maxscript');



        if ((paneCadlib && !paneCadlib.classList.contains('hidden')) ||



            (paneMaxscript && !paneMaxscript.classList.contains('hidden'))) {



          switchNavTab('tools');



        }



      }



    });







    async function loadCadlibLisps() {



      const container = document.getElementById('lispGridContainer');



      if (container) {



        container.innerHTML = `



          <div class="p-8 text-center text-slate-500 space-y-2">



            <span class="inline-block animate-spin text-xl">🔄</span>



            <div class="font-bold text-xs">Đang quét CADLib LISP & ACadScript...</div>



          </div>



        `;



      }







      try {



        const res = await fetch('/api/cadlib-lisps');



        const data = await res.json();



        if (data.success) {



          cadlibLispItems = data.items || [];



          cadlibLispCategories = data.categories || [];



          cadlibLispCategoryCounts = data.categoryCounts || {};







          // Cập nhật badges



          const totalFiles = data.totalFiles || cadlibLispItems.length;



          const totalCmds = data.totalCommands || 0;



          const badgeHeader = document.getElementById('headerLispCountBadge');



          if (badgeHeader) badgeHeader.textContent = totalFiles;



          const badgeNav = document.getElementById('cadlibNavBadge');



          if (badgeNav) badgeNav.textContent = totalFiles;



          const badgeModal = document.getElementById('modalLispBadgeTotal');



          if (badgeModal) badgeModal.textContent = `${totalFiles.toLocaleString()} Scripts • ${totalCmds} Lệnh`;







          // Cập nhật số lượng trên các nút nguồn



          const btnAll = document.getElementById('btnCadSrc-all');



          if (btnAll) btnAll.textContent = `Tất cả (${totalFiles})`;



          const btnCad = document.getElementById('btnCadSrc-cadlib');



          if (btnCad && data.sources && data.sources['CADLib LISP']) {



            btnCad.textContent = `CADLib (${data.sources['CADLib LISP']})`;



          }



          const btnAcad = document.getElementById('btnCadSrc-acadscript');



          if (btnAcad && data.sources && data.sources['ACadScript']) {



            btnAcad.textContent = `ACadScript (${data.sources['ACadScript']})`;



          }







          const badgeCat = document.getElementById('cadlibActiveCatBadge');



          if (badgeCat) badgeCat.textContent = `Tất cả (${totalFiles})`;







          renderLispCategories();



          filterLispCards();



        } else {



          if (container) {



            container.innerHTML = `<div class="p-6 text-center text-rose-500 font-bold text-xs">${data.message || 'Lỗi khi quét LISP'}</div>`;



          }



        }



      } catch (err) {



        if (container) {



          container.innerHTML = `<div class="p-6 text-center text-rose-500 font-bold text-xs">Lỗi kết nối API: ${err}</div>`;



        }



      }



    }







    function renderLispCategories() {



      const tabs = document.getElementById('lispCategoryTabs');



      if (!tabs) return;







      let html = `



        <button onclick="setLispCategory('all')" id="btnLispCat-all" class="px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap cursor-pointer transition ${activeLispCategory === 'all' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'}">



          Tất cả (${cadlibLispItems.length})



        </button>



      `;







      cadlibLispCategories.forEach(cat => {



        const count = cadlibLispCategoryCounts[cat] || cadlibLispItems.filter(it => it.category === cat).length;



        const isActive = (activeLispCategory === cat);



        html += `



          <button onclick="setLispCategory('${cat}')" id="btnLispCat-${encodeURIComponent(cat)}" class="px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap cursor-pointer transition ${isActive ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'}">



            ${cat} (${count})



          </button>



        `;



      });







      tabs.innerHTML = html;



    }







    function setLispCategory(cat) {



      activeLispCategory = cat;



      const badge = document.getElementById('cadlibActiveCatBadge');



      if (badge) {



        if (cat === 'all') {



          badge.textContent = `Tất cả (${cadlibLispItems.length})`;



        } else {



          const count = cadlibLispCategoryCounts[cat] || cadlibLispItems.filter(it => it.category === cat).length;



          badge.textContent = `${cat} (${count})`;



        }



      }



      renderLispCategories();



      filterLispCards();



    }







    let isCadlibCatCollapsed = false;



    function toggleCadlibCategories() {



      isCadlibCatCollapsed = !isCadlibCatCollapsed;



      const container = document.getElementById('lispCategoryTabs');



      const arrow = document.getElementById('cadlibCatArrow');



      const toggleText = document.getElementById('cadlibCatToggleText');







      if (container) {



        if (isCadlibCatCollapsed) {



          container.classList.add('hidden');



        } else {



          container.classList.remove('hidden');



        }



      }







      if (arrow) {



        arrow.style.transform = isCadlibCatCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';



      }







      if (toggleText) {



        toggleText.textContent = isCadlibCatCollapsed ? 'Mở rộng' : 'Thu gọn';



      }



    }







    function setCadlibSource(src) {



      activeCadlibSource = src;



      const btnAll = document.getElementById('btnCadSrc-all');



      const btnCad = document.getElementById('btnCadSrc-cadlib');



      const btnAcad = document.getElementById('btnCadSrc-acadscript');







      const activeStyle = 'px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-indigo-600 text-white shadow-xs';



      const inactiveStyle = 'px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-slate-100 hover:bg-slate-200 text-slate-700';







      if (btnAll) btnAll.className = (src === 'all') ? activeStyle : inactiveStyle;



      if (btnCad) btnCad.className = (src === 'CADLib LISP') ? activeStyle : inactiveStyle;



      if (btnAcad) btnAcad.className = (src === 'ACadScript') ? activeStyle : inactiveStyle;







      filterLispCards();



    }







    function clearLispSearch() {



      const inp = document.getElementById('lispSearchInput');



      if (inp) {



        inp.value = '';



        inp.focus();



      }



      filterLispCards();



    }







    function filterLispCards() {



      const searchVal = (document.getElementById('lispSearchInput')?.value || '').trim().toLowerCase();



      const btnClear = document.getElementById('btnClearLispSearch');



      if (btnClear) {



        if (searchVal) btnClear.classList.remove('hidden');



        else btnClear.classList.add('hidden');



      }







      let filtered = cadlibLispItems.filter(it => {



        // Lọc theo Nguồn (Source)



        if (activeCadlibSource !== 'all' && it.source !== activeCadlibSource) {



          return false;



        }



        // Lọc theo Category



        if (activeLispCategory !== 'all' && it.category !== activeLispCategory) {



          return false;



        }



        // Lọc theo Search keyword



        if (!searchVal) return true;







        const inFeat = (it.featureName || '').toLowerCase().includes(searchVal);



        const inName = (it.file || '').toLowerCase().includes(searchVal);



        const inSub = (it.subfolder || '').toLowerCase().includes(searchVal);



        const inDesc = (it.description || '').toLowerCase().includes(searchVal);



        const inCmds = (it.commands || []).some(c => c.toLowerCase().includes(searchVal));



        return inFeat || inName || inSub || inDesc || inCmds;



      });







      const countEl = document.getElementById('lispFilterCount');



      if (countEl) {



        countEl.textContent = `Hiển thị ${filtered.length.toLocaleString()} / ${cadlibLispItems.length.toLocaleString()} scripts`;



      }







      renderLispGrid(filtered, searchVal);



    }







    function renderLispGrid(items, searchVal) {



      const container = document.getElementById('lispGridContainer');



      if (!container) return;







      if (items.length === 0) {



        container.innerHTML = `



          <div class="p-10 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">



            <i data-lucide="search-x" class="w-10 h-10 mx-auto text-slate-300 mb-2"></i>



            <div class="font-bold text-sm text-slate-700">Không tìm thấy script hoặc lệnh nào phù hợp</div>



            <div class="text-xs text-slate-400 mt-1">Thử tìm bằng từ khóa khác: dim, text, wall, block, alx, beam, curve...</div>



          </div>



        `;



        if (typeof lucide !== 'undefined') lucide.createIcons();



        return;



      }







      // Lưu danh sách đang lọc để các hàm index truy xuất an toàn (không bị lỗi escape regex / backslash)



      currentFilteredCadlib = items;







      const displayItems = items.slice(0, 150);



      let html = '';







      displayItems.forEach((it, idx) => {



        const ext = (it.ext || '').toLowerCase();



        const extBadgeColor = ext === '.lsp' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' :



                              ext === '.cs' ? 'bg-sky-50 text-sky-700 border-sky-200' :



                              ext === '.py' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :



                              ext === '.scr' ? 'bg-amber-50 text-amber-700 border-amber-200' :



                              'bg-slate-100 text-slate-700 border-slate-200';







        const srcBadgeColor = it.source === 'ACadScript' ? 'bg-sky-50 text-sky-700 border-sky-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';



        const displayName = it.featureName || it.file;



        const iconName = ext === '.py' ? 'terminal' : ext === '.cs' ? 'code-2' : ext === '.scr' ? 'play-circle' : 'file-code';



        const canLoadDirect = (ext === '.lsp' || ext === '.scr');



        const extClean = ext.replace('.', '').toUpperCase();







        html += `



          <div class="p-3 bg-white border border-slate-200 rounded-xl shadow-xs hover:shadow-md hover:border-indigo-300 transition flex flex-col justify-between space-y-2 group">



            <div>



              <!-- Header Card: TÊN TÍNH NĂNG NỔI BẬT LÀM TIÊU ĐỀ CHÍNH -->



              <div class="flex items-start justify-between gap-1.5">



                <div class="min-w-0 flex-1">



                  <div class="font-bold text-xs text-indigo-950 flex items-center gap-1.5" title="${displayName}">



                    <i data-lucide="${iconName}" class="w-3.5 h-3.5 text-indigo-600 shrink-0"></i>



                    <span class="truncate">${displayName}</span>



                  </div>



                  <!-- Tên file gốc kỹ thuật & thư mục -->



                  <div class="flex items-center gap-1.5 text-[9.5px] text-slate-400 font-mono mt-0.5 truncate">



                    <span class="text-slate-600 font-medium truncate">📄 ${it.file}</span>



                    ${it.subfolder ? `<span class="text-slate-400 truncate">📁 ${it.subfolder}</span>` : ''}



                  </div>



                </div>



                <div class="flex items-center gap-1 shrink-0">



                  <span class="text-[9px] px-1.5 py-0.2 rounded font-mono font-bold border ${extBadgeColor}">



                    ${extClean}



                  </span>



                  <span class="text-[9px] px-1.5 py-0.2 rounded font-sans font-semibold border ${srcBadgeColor}">



                    ${it.source === 'CADLib LISP' ? 'CADLib' : 'ACadScript'}



                  </span>



                </div>



              </div>







              <!-- Danh mục & Lệnh tắt -->



              <div class="mt-1.5 flex items-center gap-1.5 flex-wrap">



                <span class="text-[9.5px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">



                  🏷️ ${it.category}



                </span>



                ${it.commands && it.commands.length > 0 ? it.commands.map(cmd => `



                  <span onclick="copyLispCommand('${cmd}')" class="px-2 py-0.5 rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-mono text-[10px] font-bold cursor-pointer transition select-all active:scale-95 shadow-2xs" title="Click để copy lệnh ${cmd}">



                    ${cmd}



                  </span>



                `).join('') : ''}



              </div>







              <!-- Mô tả tính năng -->



              ${it.description ? `



                <p class="text-[10.5px] text-slate-600 mt-1.5 leading-relaxed line-clamp-2" title="${it.description}">



                  ${it.description}



                </p>



              ` : ''}



            </div>







            <!-- Footer Card: Action Buttons -->



            <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">



              <span class="text-[10px] text-slate-400 font-mono">${(it.sizeBytes / 1024).toFixed(1)} KB</span>



              <div class="flex items-center gap-1">



                ${canLoadDirect ? `



                  <button onclick="loadLispByIndex(${idx})" class="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 border border-indigo-200 text-[10px] font-bold transition flex items-center gap-1 cursor-pointer active:scale-95" title="Nạp trực tiếp file này vào AutoCAD đang mở">



                    <i data-lucide="play" class="w-3 h-3"></i>



                    <span>Nạp CAD</span>



                  </button>



                ` : ''}



                ${it.commands && it.commands.length > 0 ? `



                  <button onclick="copyLispCmdByIndex(${idx})" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-semibold transition flex items-center gap-1 cursor-pointer" title="Copy lệnh chính: ${it.commands[0]}">



                    <i data-lucide="copy" class="w-3 h-3"></i>



                    <span>Copy</span>



                  </button>



                ` : ''}



                <button onclick="openCadEditorByIndex(${idx})" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-semibold transition flex items-center gap-1 cursor-pointer" title="Mở file trong Code Editor (VS Code / Default)">



                  <i data-lucide="code" class="w-3 h-3"></i>



                  <span>Mở</span>



                </button>



                <button onclick="openCadFolderByIndex(${idx})" class="p-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Mở thư mục trong Windows Explorer">



                  <i data-lucide="folder" class="w-3.5 h-3.5"></i>



                </button>



              </div>



            </div>



          </div>



        `;



      });







      if (items.length > 150) {



        html += `



          <div class="p-3 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">



            Đang hiển thị 150 / ${items.length.toLocaleString()} scripts. Sử dụng ô tìm kiếm để lọc nhanh script bạn cần.



          </div>



        `;



      }







      container.innerHTML = html;



      if (typeof lucide !== 'undefined') lucide.createIcons();



    }







    function copyLispCmdByIndex(idx) {



      const it = currentFilteredCadlib[idx];



      if (!it || !it.commands || it.commands.length === 0) return;



      copyLispCommand(it.commands[0]);



    }







    function loadLispByIndex(idx) {



      const it = currentFilteredCadlib[idx];



      if (!it || !it.fullPath) return;



      loadLispToAcad(it.fullPath, it.file);



    }







    function openCadEditorByIndex(idx) {



      const it = currentFilteredCadlib[idx];



      if (!it || !it.fullPath) return;



      openScriptEditor(it.fullPath);



    }







    function openCadFolderByIndex(idx) {



      const it = currentFilteredCadlib[idx];



      if (!it || !it.fullPath) return;



      openScriptFolder(it.fullPath);



    }







    function copyLispCommand(cmd) {



      if (!cmd) return;



      navigator.clipboard.writeText(cmd).then(() => {



        log(`✓ Đã sao chép lệnh AutoCAD: [${cmd}]`, 'success');



      });



    }







    async function loadLispToAcad(fullPath, fname) {



      log(`[CADLib] Đang nạp script: ${fname} vào AutoCAD (${fullPath})...`, 'info');



      try {



        const res = await fetch('/api/execute-action', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({



            action: 'load_cad_lisp',



            filePath: fullPath



          })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ THÀNH CÔNG: Đã nạp ${fname} vào AutoCAD! ${data.message || ''}`, 'success');



        } else {



          log(`✗ LỖI nạp script: ${data.message || 'Thất bại'}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối nạp script: ${err}`, 'error');



      }



    }







    function copyToClipboard(text, label = 'Nội dung') {



      if (!text) return;



      navigator.clipboard.writeText(text).then(() => {



        log(`✓ Đã sao chép ${label} vào Clipboard!`, 'success');



      });



    }







    // =========================================================================



    // MAXSCRIPT & PYTHON EXPLORER (SKMSTOOL & 3DS MAX 2022)



    // =========================================================================



    async function loadMaxscripts() {



      const container = document.getElementById('maxscriptGridContainer');



      if (container) {



        container.innerHTML = `



          <div class="p-8 text-center text-slate-500 space-y-2">



            <span class="inline-block animate-spin text-xl">🔄</span>



            <div class="font-bold text-xs">Đang tổng hợp 1,205 scripts từ skMSTool & 3ds Max 2022...</div>



          </div>



        `;



      }







      try {



        const res = await fetch('/api/maxscripts');



        const data = await res.json();



        if (data.success) {



          maxscriptItems = data.items || [];



          maxscriptCategories = data.categories || [];



          maxscriptCategoryCounts = data.categoryCounts || {};







          // Cập nhật badges



          const totalFiles = data.totalFiles || maxscriptItems.length;



          const badgeNav = document.getElementById('maxscriptNavBadge');



          if (badgeNav) badgeNav.textContent = totalFiles;



          const badgeTotal = document.getElementById('maxscriptBadgeTotal');



          if (badgeTotal) badgeTotal.textContent = `${totalFiles.toLocaleString()} Scripts`;







          // Cập nhật số lượng trên các nút nguồn



          const btnSrcMstool = document.getElementById('btnMsSrc-skMSTool');



          if (btnSrcMstool && data.sources && data.sources['skMSTool']) {



            btnSrcMstool.textContent = `skMSTool (${data.sources['skMSTool']})`;



          }



          const btnSrcUser = document.getElementById('btnMsSrc-user3dsmax');



          if (btnSrcUser && data.sources && data.sources['3ds Max 2022']) {



            btnSrcUser.textContent = `3ds Max 2022 (${data.sources['3ds Max 2022']})`;



          }







          const badgeCat = document.getElementById('maxscriptActiveCatBadge');



          if (badgeCat) badgeCat.textContent = `Tất cả (${totalFiles.toLocaleString()})`;







          renderMaxscriptCategories();



          filterMaxscriptCards();



        } else {



          if (container) {



            container.innerHTML = `<div class="p-6 text-center text-rose-500 font-bold text-xs">${data.message || 'Lỗi khi quét scripts'}</div>`;



          }



        }



      } catch (err) {



        if (container) {



          container.innerHTML = `<div class="p-6 text-center text-rose-500 font-bold text-xs">Lỗi kết nối API Maxscript: ${err}</div>`;



        }



      }



    }







    function renderMaxscriptCategories() {



      const tabs = document.getElementById('maxscriptCategoryTabs');



      if (!tabs) return;







      let html = `



        <button onclick="setMaxscriptCategory('all')" id="btnMsCat-all" class="px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap cursor-pointer transition ${activeMaxscriptCategory === 'all' ? 'bg-amber-600 text-white shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'}">



          Tất cả (${maxscriptItems.length})



        </button>



      `;







      maxscriptCategories.forEach(cat => {



        const count = maxscriptCategoryCounts[cat] || maxscriptItems.filter(it => it.category === cat).length;



        const isActive = (activeMaxscriptCategory === cat);



        html += `



          <button onclick="setMaxscriptCategory('${cat}')" id="btnMsCat-${encodeURIComponent(cat)}" class="px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap cursor-pointer transition ${isActive ? 'bg-amber-600 text-white shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'}">



            ${cat} (${count})



          </button>



        `;



      });







      tabs.innerHTML = html;



    }







    function setMaxscriptCategory(cat) {



      activeMaxscriptCategory = cat;



      const badge = document.getElementById('maxscriptActiveCatBadge');



      if (badge) {



        if (cat === 'all') {



          badge.textContent = `Tất cả (${maxscriptItems.length.toLocaleString()})`;



        } else {



          const count = maxscriptCategoryCounts[cat] || maxscriptItems.filter(it => it.category === cat).length;



          badge.textContent = `${cat} (${count})`;



        }



      }



      renderMaxscriptCategories();



      filterMaxscriptCards();



    }







    let isMaxscriptCatCollapsed = false;



    function toggleMaxscriptCategories() {



      isMaxscriptCatCollapsed = !isMaxscriptCatCollapsed;



      const container = document.getElementById('maxscriptCategoryTabs');



      const arrow = document.getElementById('maxscriptCatArrow');



      const toggleText = document.getElementById('maxscriptCatToggleText');







      if (container) {



        if (isMaxscriptCatCollapsed) {



          container.classList.add('hidden');



        } else {



          container.classList.remove('hidden');



        }



      }







      if (arrow) {



        arrow.style.transform = isMaxscriptCatCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';



      }







      if (toggleText) {



        toggleText.textContent = isMaxscriptCatCollapsed ? 'Mở rộng' : 'Thu gọn';



      }



    }







    function setMaxscriptSource(src) {



      activeMaxscriptSource = src;



      const btnAll = document.getElementById('btnMsSrc-all');



      const btnMstool = document.getElementById('btnMsSrc-skMSTool');



      const btnUser = document.getElementById('btnMsSrc-user3dsmax');







      const activeStyle = 'px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-amber-600 text-white shadow-xs';



      const inactiveStyle = 'px-2 py-0.8 rounded-lg text-[11px] font-bold whitespace-nowrap cursor-pointer transition bg-slate-100 hover:bg-slate-200 text-slate-700';







      if (btnAll) btnAll.className = (src === 'all') ? activeStyle : inactiveStyle;



      if (btnMstool) btnMstool.className = (src === 'skMSTool') ? activeStyle : inactiveStyle;



      if (btnUser) btnUser.className = (src === '3ds Max 2022') ? activeStyle : inactiveStyle;







      filterMaxscriptCards();



    }







    function clearMaxscriptSearch() {



      const inp = document.getElementById('maxscriptSearchInput');



      if (inp) {



        inp.value = '';



        inp.focus();



      }



      filterMaxscriptCards();



    }







    function filterMaxscriptCards() {



      const searchVal = (document.getElementById('maxscriptSearchInput')?.value || '').trim().toLowerCase();



      const btnClear = document.getElementById('btnClearMaxscriptSearch');



      if (btnClear) {



        if (searchVal) btnClear.classList.remove('hidden');



        else btnClear.classList.add('hidden');



      }







      let filtered = maxscriptItems.filter(it => {



        // Lọc theo Nguồn (Source)



        if (activeMaxscriptSource !== 'all' && it.source !== activeMaxscriptSource) {



          return false;



        }



        // Lọc theo Category



        if (activeMaxscriptCategory !== 'all' && it.category !== activeMaxscriptCategory) {



          return false;



        }



        // Lọc theo Search keyword



        if (!searchVal) return true;







        const inFeat = (it.featureName || '').toLowerCase().includes(searchVal);



        const inName = it.file.toLowerCase().includes(searchVal);



        const inSub = (it.subfolder || '').toLowerCase().includes(searchVal);



        const inTitle = (it.title || '').toLowerCase().includes(searchVal);



        const inTip = (it.tooltip || '').toLowerCase().includes(searchVal);



        const inDesc = (it.description || '').toLowerCase().includes(searchVal);



        const inMacro = (it.macro || '').toLowerCase().includes(searchVal);



        const inCmd = (it.runCommand || '').toLowerCase().includes(searchVal);



        return inFeat || inName || inSub || inTitle || inTip || inDesc || inMacro || inCmd;



      });







      const countEl = document.getElementById('maxscriptFilterCount');



      if (countEl) {



        countEl.textContent = `Hiển thị ${filtered.length.toLocaleString()} / ${maxscriptItems.length.toLocaleString()} scripts`;



      }







      renderMaxscriptGrid(filtered, searchVal);



    }







    function renderMaxscriptGrid(items, searchVal) {



      const container = document.getElementById('maxscriptGridContainer');



      if (!container) return;







      if (items.length === 0) {



        container.innerHTML = `



          <div class="p-10 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">



            <i data-lucide="search-x" class="w-10 h-10 mx-auto text-slate-300 mb-2"></i>



            <div class="font-bold text-sm text-slate-700">Không tìm thấy script nào phù hợp</div>



            <div class="text-xs text-slate-400 mt-1">Thử từ khóa khác: tách, remesh, vật liệu, vray, thép, spline, dầm...</div>



          </div>



        `;



        if (typeof lucide !== 'undefined') lucide.createIcons();



        return;



      }







      // Lưu danh sách đang lọc để các hàm index truy xuất an toàn (không bị lỗi escape regex / quote)



      currentFilteredMaxscripts = items;







      // Giới hạn hiển thị 150 thẻ đầu tiên để DOM luôn mượt mà tức thì



      const displayItems = items.slice(0, 150);



      let html = '';







      displayItems.forEach((it, idx) => {



        const extBadgeColor = it.ext === '.mcr' ? 'bg-amber-50 text-amber-700 border-amber-200' :



                              it.ext === '.py' ? 'bg-sky-50 text-sky-700 border-sky-200' :



                              it.ext === '.mse' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :



                              'bg-purple-50 text-purple-700 border-purple-200';







        const srcBadgeColor = it.source === 'skMSTool' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200';



        const displayName = it.featureName || it.title || it.file;







        html += `



          <div class="p-3 bg-white border border-slate-200 rounded-xl shadow-xs hover:shadow-md hover:border-amber-300 transition flex flex-col justify-between space-y-2 group">



            <div>



              <!-- Header Card: TÊN TÍNH NĂNG NỔI BẬT LÀM TIÊU ĐỀ CHÍNH -->



              <div class="flex items-start justify-between gap-1.5">



                <div class="min-w-0 flex-1">



                  <div class="font-bold text-xs text-indigo-950 flex items-center gap-1.5" title="${displayName}">



                    <i data-lucide="${it.ext === '.py' ? 'terminal' : 'sparkles'}" class="w-3.5 h-3.5 text-amber-600 shrink-0"></i>



                    <span class="truncate">${displayName}</span>



                  </div>



                  <!-- Tên file gốc kỹ thuật & thư mục -->



                  <div class="flex items-center gap-1.5 text-[9.5px] text-slate-400 font-mono mt-0.5 truncate">



                    <span class="text-slate-600 font-medium truncate">📄 ${it.file}</span>



                    ${it.subfolder ? `<span class="text-slate-400 truncate">📁 ${it.subfolder}</span>` : ''}



                  </div>



                </div>



                <div class="flex items-center gap-1 shrink-0">



                  <span class="text-[9px] px-1.5 py-0.2 rounded font-mono font-bold border ${extBadgeColor}">



                    ${it.ext.toUpperCase()}



                  </span>



                  <span class="text-[9px] px-1.5 py-0.2 rounded font-sans font-semibold border ${srcBadgeColor}">



                    ${it.source}



                  </span>



                </div>



              </div>







              <!-- Danh mục -->



              <div class="mt-1.5 flex items-center gap-1.5 flex-wrap">



                <span class="text-[9.5px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">



                  🏷️ ${it.category}



                </span>



                ${it.macro ? `<span class="text-[9.5px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-mono font-bold border border-amber-200">macro: ${it.macro}</span>` : ''}



              </div>







              <!-- Snippet Command -->



              <div class="mt-2 font-mono text-[10px] bg-slate-900 text-amber-300 px-2 py-1 rounded truncate select-all" title="${it.runCommand}">



                ${it.runCommand}



              </div>



            </div>







            <!-- Footer Card: Action Buttons -->



            <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">



              <span class="text-[10px] text-slate-400 font-mono">${(it.sizeBytes / 1024).toFixed(1)} KB</span>



              <div class="flex items-center gap-1">



                <button onclick="copyMaxscriptCmd(${idx})" class="px-2 py-1 rounded-lg bg-amber-50 hover:bg-amber-600 hover:text-white text-amber-700 border border-amber-200 text-[10px] font-bold transition flex items-center gap-1 cursor-pointer active:scale-95" title="Copy lệnh fileIn / python để paste vào MAXScript Listener (F11)">



                  <i data-lucide="copy" class="w-3 h-3"></i>



                  <span>fileIn</span>



                </button>



                <button onclick="openScriptEditorByIndex(${idx})" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-semibold transition flex items-center gap-1 cursor-pointer" title="Mở file trong Code Editor (VS Code / Default)">



                  <i data-lucide="code" class="w-3 h-3"></i>



                  <span>Mở</span>



                </button>



                <button onclick="openScriptFolderByIndex(${idx})" class="p-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Mở thư mục trong Windows Explorer">



                  <i data-lucide="folder" class="w-3.5 h-3.5"></i>



                </button>



              </div>



            </div>



          </div>



        `;



      });







      if (items.length > 150) {



        html += `



          <div class="p-3 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">



            Đang hiển thị 150 / ${items.length.toLocaleString()} scripts. Sử dụng ô tìm kiếm để lọc nhanh script bạn cần.



          </div>



        `;



      }







      container.innerHTML = html;



      if (typeof lucide !== 'undefined') lucide.createIcons();



    }







    let currentFilteredMaxscripts = [];







    function copyMaxscriptCmd(idx) {



      const it = currentFilteredMaxscripts[idx];



      if (!it || !it.runCommand) return;



      copyToClipboard(it.runCommand, 'Lệnh nạp MaxScript');



    }







    function openScriptEditorByIndex(idx) {



      const it = currentFilteredMaxscripts[idx];



      if (!it || !it.fullPath) return;



      openScriptEditor(it.fullPath);



    }







    function openScriptFolderByIndex(idx) {



      const it = currentFilteredMaxscripts[idx];



      if (!it || !it.fullPath) return;



      openScriptFolder(it.fullPath);



    }







    async function openScriptEditor(fullPath) {



      log(`[Maxscript] Đang mở file: ${fullPath}...`, 'info');



      try {



        const res = await fetch('/api/open-script-editor', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ path: fullPath })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ ${data.message}`, 'success');



        } else {



          log(`✗ ${data.message || 'Lỗi mở file'}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    async function openScriptFolder(fullPath) {



      try {



        const res = await fetch('/api/open-script-folder', {



          method: 'POST',



          headers: { 'Content-Type': 'application/json' },



          body: JSON.stringify({ path: fullPath })



        });



        const data = await res.json();



        if (data.success) {



          log(`✓ Đã mở thư mục chứa file trong Explorer.`, 'success');



        } else {



          log(`✗ ${data.message || 'Lỗi mở thư mục'}`, 'error');



        }



      } catch (err) {



        log(`✗ Lỗi kết nối: ${err}`, 'error');



      }



    }







    // Initial check



    refreshModelInfo();



    setInterval(refreshModelInfo, 10000); // Tự động làm mới mỗi 10s



  

    // ====================================================================
    // UNIFIED LEFT & RIGHT PANEL COLLAPSE / EXPAND LAYOUT MANAGER
    // ====================================================================
    function updateLayoutGrid() {
      const colLeft = document.getElementById('colLeftPanel');
      const colCenter = document.getElementById('colCenterWorkspace');
      const colRight = document.getElementById('colRightPanel');
      
      const bar = document.getElementById('panelExpandBar');
      const btnBarLeft = document.getElementById('btnBarExpandLeft');
      const btnBarRight = document.getElementById('btnBarExpandRight');
      const spanBadge = document.getElementById('workspaceSpanBadge');
      
      const edgeExpandLeft = document.getElementById('btnEdgeExpandLeft');
      const edgeExpandRight = document.getElementById('btnEdgeExpandRight');
      const stickyExpandLeft = document.getElementById('btnStickyExpandLeft');
      const stickyExpandRight = document.getElementById('btnStickyExpandRight');
      
      if (!colCenter) return;
      
      const isLeftHidden = !colLeft || colLeft.classList.contains('hidden');
      const isRightHidden = !colRight || colRight.classList.contains('hidden');
      
      // Update colCenter Tailwind grid span classes
      colCenter.classList.remove(
        'lg:col-span-5', 'lg:col-span-8', 'lg:col-span-9', 'lg:col-span-12',
        'xl:col-span-6', 'xl:col-span-9', 'xl:col-span-12'
      );
      
      if (isLeftHidden && isRightHidden) {
        colCenter.classList.add('lg:col-span-12', 'xl:col-span-12');
      } else if (isLeftHidden && !isRightHidden) {
        colCenter.classList.add('lg:col-span-9', 'xl:col-span-9');
      } else if (!isLeftHidden && isRightHidden) {
        colCenter.classList.add('lg:col-span-8', 'xl:col-span-9');
      } else {
        colCenter.classList.add('lg:col-span-5', 'xl:col-span-6');
      }
      
      // Left Panel expand controls
      if (isLeftHidden) {
        if (btnBarLeft) { btnBarLeft.classList.remove('hidden'); btnBarLeft.classList.add('inline-flex'); }
        if (edgeExpandLeft) { edgeExpandLeft.classList.remove('hidden'); edgeExpandLeft.classList.add('flex'); }
        if (stickyExpandLeft) { stickyExpandLeft.classList.remove('hidden'); stickyExpandLeft.classList.add('flex'); }
      } else {
        if (btnBarLeft) { btnBarLeft.classList.add('hidden'); btnBarLeft.classList.remove('inline-flex'); }
        if (edgeExpandLeft) { edgeExpandLeft.classList.add('hidden'); edgeExpandLeft.classList.remove('flex'); }
        if (stickyExpandLeft) { stickyExpandLeft.classList.add('hidden'); stickyExpandLeft.classList.remove('flex'); }
      }
      
      // Right Panel expand controls
      if (isRightHidden) {
        if (btnBarRight) { btnBarRight.classList.remove('hidden'); btnBarRight.classList.add('inline-flex'); }
        if (edgeExpandRight) { edgeExpandRight.classList.remove('hidden'); edgeExpandRight.classList.add('flex'); }
        if (stickyExpandRight) { stickyExpandRight.classList.remove('hidden'); stickyExpandRight.classList.add('flex'); }
      } else {
        if (btnBarRight) { btnBarRight.classList.add('hidden'); btnBarRight.classList.remove('inline-flex'); }
        if (edgeExpandRight) { edgeExpandRight.classList.add('hidden'); edgeExpandRight.classList.remove('flex'); }
        if (stickyExpandRight) { stickyExpandRight.classList.add('hidden'); stickyExpandRight.classList.remove('flex'); }
      }
      
      // Top bar visibility & status badge
      if (bar) {
        if (isLeftHidden || isRightHidden) {
          bar.classList.remove('hidden');
          bar.classList.add('flex');
          if (spanBadge) {
            if (isLeftHidden && isRightHidden) {
              spanBadge.textContent = 'Toàn màn hình tối đa (12 Cột)';
            } else if (isLeftHidden) {
              spanBadge.textContent = 'Mở rộng lề trái (9 Cột)';
            } else {
              spanBadge.textContent = 'Mở rộng lề phải (8-9 Cột)';
            }
          }
        } else {
          bar.classList.add('hidden');
          bar.classList.remove('flex');
        }
      }
      
      if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
      }
      
      // Dispatch resize so Three.js viewports & 2D canvas adapt immediately
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        if (typeof resizeThreeRenderer === 'function') {
          if (window.threeRenderer && window.threeCamera) {
            resizeThreeRenderer('etabs3DContainer', window.threeRenderer, window.threeCamera);
          }
          if (window.modalThreeRenderer && window.modalThreeCamera) {
            resizeThreeRenderer('modal3DContainer', window.modalThreeRenderer, window.modalThreeCamera);
          }
        }
      }, 50);
    }

    function toggleLeftPanel(forceOpen) {
      const colLeft = document.getElementById('colLeftPanel');
      if (!colLeft) return;
      const isHidden = colLeft.classList.contains('hidden');
      const shouldOpen = (typeof forceOpen === 'boolean') ? forceOpen : isHidden;
      
      if (shouldOpen) {
        colLeft.classList.remove('hidden');
        try { localStorage.setItem('revitai_left_panel_collapsed', '0'); } catch(e){}
      } else {
        colLeft.classList.add('hidden');
        try { localStorage.setItem('revitai_left_panel_collapsed', '1'); } catch(e){}
      }
      updateLayoutGrid();
    }

    function toggleRightPanel(forceOpen) {
      const colRight = document.getElementById('colRightPanel');
      if (!colRight) return;
      const isHidden = colRight.classList.contains('hidden');
      const shouldOpen = (typeof forceOpen === 'boolean') ? forceOpen : isHidden;
      
      if (shouldOpen) {
        colRight.classList.remove('hidden');
        try { localStorage.setItem('revitai_right_panel_collapsed', '0'); } catch(e){}
      } else {
        colRight.classList.add('hidden');
        try { localStorage.setItem('revitai_right_panel_collapsed', '1'); } catch(e){}
      }
      updateLayoutGrid();
    }

    // Restore Left & Right Panel state on initial load
    try {
      const is3DRoute = ['/3d', '/modal-3d', '/etabs-3d', '/structure-3d'].some(r => window.location.pathname.startsWith(r)) || window.location.search.includes('3d');

      if (is3DRoute) {
        // REQUIREMENT 3: Mặc định left và right panel MINIMIN (collapsed) trên route riêng 3D!
        const colLeft = document.getElementById('colLeftPanel');
        if (colLeft) colLeft.classList.add('hidden');
        const colRight = document.getElementById('colRightPanel');
        if (colRight) colRight.classList.add('hidden');
        
        updateLayoutGrid();
        
        // Auto open ETABS Hub and switch to 3D Model
        setTimeout(() => {
          if (typeof openEtabsHub === 'function') {
            openEtabsHub('workspace');
          }
          if (typeof switchEtabsSubTab === 'function') {
            switchEtabsSubTab('etabs-3d');
          }
          if (window.location.pathname === '/modal-3d' || window.location.search.includes('modal=1')) {
            if (typeof openEtabsHub === 'function') {
              openEtabsHub('modal');
            }
          }
        }, 120);
      } else {
        // Normal route: restore from localStorage
        if (localStorage.getItem('revitai_left_panel_collapsed') === '1') {
          const colLeft = document.getElementById('colLeftPanel');
          if (colLeft) colLeft.classList.add('hidden');
        }
        if (localStorage.getItem('revitai_right_panel_collapsed') === '1') {
          const colRight = document.getElementById('colRightPanel');
          if (colRight) colRight.classList.add('hidden');
        }
        updateLayoutGrid();
      }
    } catch(e) {}

    // Keyboard shortcuts:
    // Ctrl+B -> Toggle Left Panel
    // Ctrl+J -> Toggle Right Panel
    window.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && !['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target || {}).tagName)) {
        if (e.key.toLowerCase() === 'b') {
          e.preventDefault();
          toggleLeftPanel();
        } else if (e.key.toLowerCase() === 'j') {
          e.preventDefault();
          toggleRightPanel();
        }
      }
    });

</script>



  <!-- MODAL: HỎI TẠO FAMILY MỚI CHO TAB 6 -->



  <div id="modalNewFamily" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">



    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in duration-200">



      <div class="flex items-start gap-3">



        <div class="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-600 flex-shrink-0">



          <i data-lucide="help-circle" class="w-6 h-6"></i>



        </div>



        <div class="space-y-1">



          <h3 class="text-sm font-bold text-slate-900">Tạo Family Mới trong Revit?</h3>



          <p id="modalNewFamilyDesc" class="text-xs text-slate-500 leading-relaxed whitespace-pre-line">



            Bạn chưa chọn Family nào trong Revit (hoặc đối tượng đang chọn không phải là Family).



            Bạn có muốn tạo một Family mới từ các vật thể 3ds Max này không?



          </p>



        </div>



      </div>







      <div class="space-y-1.5 text-xs">



        <label class="block font-bold text-slate-700">Tên Family mới:</label>



        <input type="text" id="inputNewFamilyName" value="Family_3dsMax" onkeydown="if(event.key==='Enter') confirmCreateNewFamily()" class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 font-semibold focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent">



        <p class="text-[11px] text-slate-400">Family sẽ được tạo tự động từ mẫu Generic Model, nạp hình học phẳng sạch (ẩn tam giác) và đặt vào Revit.</p>



      </div>







      <div class="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100">



        <button type="button" onclick="closeNewFamilyModal()" class="px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold text-xs transition">



          Hủy bỏ



        </button>



        <button type="button" onclick="confirmCreateNewFamily()" id="btnConfirmNewFamily" class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs shadow-md shadow-amber-600/20 flex items-center gap-1.5 transition active:scale-[0.98]">



          <i data-lucide="plus-circle" class="w-4 h-4"></i>



          <span>Tạo Family Mới</span>



        </button>



      </div>



    </div>



  </div>















  <!-- ==================================================================== -->



  <!-- FULLSCREEN MODAL: ETABS STRUCTURAL AI HUB                             -->



  <!-- ==================================================================== -->



  <div id="etabsModal" class="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-sm hidden flex items-center justify-center p-3 sm:p-5">



    <div class="bg-white w-full max-w-[1600px] h-[92vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300">



      



      <!-- Modal Header -->



      <div class="p-4 bg-slate-50 text-slate-800 flex items-center justify-between border-b border-slate-200">



        <div class="flex items-center gap-2.5">



          <span class="p-2 rounded-xl bg-indigo-600 text-white shadow-sm">



            <i data-lucide="layers" class="w-5 h-5"></i>



          </span>



          <div>



            <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">



              Hồ Sơ Dầm & Cốt Thép ETABS • Fullscreen View



              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">Live 3D & 2D</span>



            </h3>



            <p class="text-[11px] text-slate-500">Model: CAI_TAO_PHUONG_AN_B.EDB (103 Dầm • TCVN 5574-2012)</p>



          </div>



        </div>







        <div class="flex items-center gap-3">



          <div class="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200">



            <button onclick="switchEtabsModalTab('modal-2d')" id="modal-tabbtn-2d" class="py-1 px-3 rounded-lg text-xs font-bold bg-indigo-600 text-white transition shadow-sm">2D Mặt Bằng</button>



            <button onclick="switchEtabsModalTab('modal-3d')" id="modal-tabbtn-3d" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition">3D Khối Đặc</button>



            <button onclick="switchEtabsModalTab('modal-rebar')" id="modal-tabbtn-rebar" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition">Bảng Thép Dầm</button>



            <button onclick="switchEtabsModalTab('modal-column')" id="modal-tabbtn-column" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center gap-1.5">



              <span>🏛️ Bản Vẽ Cột (15×4)</span>



            </button>



            <button onclick="switchEtabsModalTab('modal-notes')" id="modal-tabbtn-notes" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center gap-1.5">



              <span>📋 Ghi Chú Chung</span>



            </button>



          </div>



          <button onclick="closeEtabsModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng modal">



            <i data-lucide="x" class="w-5 h-5"></i>



          </button>



        </div>



      </div>







      <!-- Modal Body -->



      <div class="flex-1 overflow-hidden p-4 bg-slate-50">



        <div id="modal-pane-2d" class="w-full h-full flex flex-col space-y-2">



          <div class="flex items-center justify-between">



            <div class="flex items-center gap-2 text-xs font-bold text-slate-700 flex-wrap">



              <span>Chọn Tầng:</span>



              <div id="modal2DStoryButtons" class="flex items-center gap-1.5 flex-wrap"></div>



              <input type="hidden" id="modal2DStorySelect" value="T3">



            </div>



            <div class="flex items-center gap-2">



              <button onclick="zoomModal2D(1.2)" class="p-1 rounded bg-white border text-xs font-bold px-2">Zoom +</button>



              <button onclick="zoomModal2D(0.8)" class="p-1 rounded bg-white border text-xs font-bold px-2">Zoom -</button>



              <button onclick="resetModal2DView()" class="p-1 rounded bg-white border text-xs font-bold px-2">Vừa khung</button>



            </div>



          </div>



          <div class="flex-1 bg-[#aaaaaa] rounded-2xl overflow-hidden relative border border-slate-400">



            <canvas id="modal2DCanvas" class="w-full h-full cursor-grab active:cursor-grabbing"></canvas>



          </div>



        </div>







        <div id="modal-pane-3d" class="w-full h-full hidden flex flex-col space-y-2">



          <div class="flex items-center justify-between text-xs text-slate-700 font-bold">



            <span>Model 3D Khối Đặc Đúng Tiết Diện:</span>



            <button onclick="resetModal3DCamera()" class="p-1 px-3 bg-white border rounded-lg text-xs">Reset góc nhìn</button>



          </div>



          <div class="flex-1 bg-[#aaaaaa] rounded-2xl overflow-hidden relative border border-slate-400">



            <div id="modal3DContainer" class="w-full h-full"></div>



          </div>



        </div>







        <div id="modal-pane-rebar" class="w-full h-full hidden overflow-y-auto">



          <div class="rounded-xl border border-slate-200 overflow-hidden shadow-sm bg-white">



            <table class="w-full text-left text-xs border-collapse">



              <thead class="bg-slate-100 text-slate-700 font-bold text-[10px] uppercase sticky top-0">



                <tr class="divide-x divide-slate-200">



                  <th class="p-2.5">Tầng</th>



                  <th class="p-2.5">Dầm Dài (DX/DY)</th>



                  <th class="p-2.5">Tiết Diện</th>



                  <th class="p-2.5 text-right">Nhịp L (m)</th>



                  <th class="p-2.5 text-right bg-amber-50">As Gối T</th>



                  <th class="p-2.5 text-right bg-amber-50">As Bụng</th>



                  <th class="p-2.5 text-right bg-amber-50">As Gối P</th>



                  <th class="p-2.5 text-right bg-sky-50">As Đai</th>



                  <th class="p-2.5 bg-indigo-50">Cốt Thép Dọc Chọn (TCVN)</th>



                  <th class="p-2.5 bg-indigo-50 text-center">Đai Chọn</th>



                  <th class="p-2.5 text-center">Đánh Giá</th>



                </tr>



              </thead>



              <tbody id="modalRebarTableBody" class="divide-y divide-slate-200 font-mono text-[11px]"></tbody>



            </table>



        </div>







        <div id="modal-pane-column" class="w-full h-full hidden flex flex-col space-y-2">



          <div class="flex items-center justify-between text-xs text-slate-700 font-bold shrink-0">



            <div class="flex items-center gap-2">



              <span class="text-amber-800 font-extrabold flex items-center gap-1.5">



                <i data-lucide="columns" class="w-4 h-4 text-amber-600"></i> Bảng Chi Tiết Tiết Diện Cột Toàn Nhà (15 Cột × 4 Tầng)



              </span>



              <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-mono font-bold">TCVN 5574:2018</span>



            </div>



            <div class="flex items-center gap-2">



              <button type="button" onclick="exportColumnSheetPdf()" class="py-1 px-3 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition active:scale-95 cursor-pointer">



                <span>Xuất PDF</span>



              </button>



              <button type="button" onclick="exportColumnSheetDxf()" class="py-1 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition active:scale-95 cursor-pointer">



                <span>Xuất DXF</span>



              </button>



              <button type="button" onclick="zoomModalColumnCad(1.2)" class="p-1 px-2.5 rounded bg-white border text-xs font-bold hover:bg-slate-50 cursor-pointer">Zoom +</button>



              <button type="button" onclick="zoomModalColumnCad(0.833)" class="p-1 px-2.5 rounded bg-white border text-xs font-bold hover:bg-slate-50 cursor-pointer">Zoom -</button>



              <button type="button" onclick="fitModalColumnCadView()" class="p-1 px-2.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-xs font-bold hover:bg-amber-100 cursor-pointer">Vừa khung</button>



            </div>



          </div>



          <div class="flex-1 bg-slate-200/60 rounded-2xl overflow-hidden relative border border-slate-300">



            <canvas id="modalColumnCadCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>



            <div id="modalColumnCadHoverBadge" class="absolute top-2.5 right-2.5 flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-300 shadow-md text-xs font-semibold text-slate-700 pointer-events-none transition-all duration-150">



              <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>



              <span id="modalColumnCadHoverText">Rê chuột vào tiết diện cột để xem thông số</span>



            </div>



          </div>



        </div>







        <!-- MODAL PANE 5: BẢNG GHI CHÚ CHUNG KẾT CẤU -->



        <div id="modal-pane-notes" class="w-full h-full hidden flex flex-col space-y-2">



          <div class="flex items-center justify-between text-xs text-slate-700 font-bold shrink-0">



            <div class="flex items-center gap-2">



              <span class="text-amber-800 font-extrabold flex items-center gap-1.5">



                <i data-lucide="file-text" class="w-4 h-4 text-amber-600"></i> Bảng Ghi Chú Chung Kết Cấu (Plot 1020)



              </span>



              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-mono font-bold">TCVN 5574-2012</span>



            </div>



            <div class="flex items-center gap-2">



              <div class="inline-flex p-0.5 bg-white rounded-lg border border-slate-300 gap-1 text-xs shadow-2xs">



                <button type="button" id="gnEtabsModalBtn_hd" onclick="setNotesViewMode('hd', 'etabsModal')" class="py-1 px-2.5 rounded text-xs font-bold bg-amber-500 text-white transition cursor-pointer">HD CAD</button>



                <button type="button" id="gnEtabsModalBtn_pdf" onclick="setNotesViewMode('pdf', 'etabsModal')" class="py-1 px-2.5 rounded text-xs font-semibold text-slate-600 hover:text-slate-900 transition cursor-pointer">PDF</button>



                <button type="button" id="gnEtabsModalBtn_text" onclick="setNotesViewMode('text', 'etabsModal')" class="py-1 px-2.5 rounded text-xs font-semibold text-slate-600 hover:text-slate-900 transition cursor-pointer">Điều khoản</button>



              </div>



              <button type="button" onclick="openGeneralNotesModal('hd')" class="py-1 px-3 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition active:scale-95 cursor-pointer" title="Mở modal phóng to độc lập">



                <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i>



                <span>Fullscreen riêng</span>



              </button>



              <button type="button" onclick="downloadGeneralNotesPdf()" class="py-1 px-2.5 rounded bg-white border border-slate-300 text-slate-700 font-bold hover:bg-slate-50 cursor-pointer">Tải PDF</button>



              <button type="button" onclick="zoomNotesCanvas(1.2, 'modalGnInteractiveCanvas')" class="p-1 px-2.5 rounded bg-white border text-xs font-bold hover:bg-slate-50 cursor-pointer">Zoom +</button>



              <button type="button" onclick="zoomNotesCanvas(0.833, 'modalGnInteractiveCanvas')" class="p-1 px-2.5 rounded bg-white border text-xs font-bold hover:bg-slate-50 cursor-pointer">Zoom -</button>



              <button type="button" onclick="fitNotesCanvas('modalGnInteractiveCanvas')" class="p-1 px-2.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-xs font-bold hover:bg-amber-100 cursor-pointer">Vừa khung</button>



            </div>



          </div>



          <div class="flex-1 bg-slate-900 rounded-2xl overflow-hidden relative border border-slate-800">



            <div id="gnEtabsModalPane_hd" class="w-full h-full relative">



              <canvas id="modalGnInteractiveCanvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>



            </div>



            <div id="gnEtabsModalPane_pdf" class="w-full h-full hidden">



              <iframe id="gnEtabsModalPdfIframe" src="about:blank" data-src="/static/general_notes_drawing.pdf#view=FitH" class="w-full h-full border-0"></iframe>



            </div>



            <div id="gnEtabsModalPane_text" class="w-full h-full hidden bg-white p-4 overflow-y-auto space-y-4">



              <div class="text-xs text-slate-700 space-y-2">



                <div class="font-bold text-slate-900 border-b pb-1 text-sm">🛡️ BẢNG CHIỀU DÀY BÊ TÔNG BẢO VỆ (Cmin mm)</div>



                <div class="grid grid-cols-4 gap-2 text-[11px]">



                  <div class="p-2 rounded bg-amber-50 border border-amber-200 font-bold">Móng: 70/40mm</div>



                  <div class="p-2 rounded bg-indigo-50 border border-indigo-200 font-bold">Cột: 25mm</div>



                  <div class="p-2 rounded bg-blue-50 border border-blue-200 font-bold">Dầm: 25-30mm</div>



                  <div class="p-2 rounded bg-emerald-50 border border-emerald-200 font-bold">Sàn: 15mm</div>



                </div>



                <div class="font-bold text-slate-900 border-b pb-1 pt-2 text-sm">📋 24 ĐIỀU QUY ĐỊNH KẾT CẤU CHÍNH (TCVN 5574-2012)</div>



                <div id="modalGnClausesList" class="space-y-1.5 text-[11px] leading-relaxed">



                  <p><strong>01.</strong> Thiết kế dựa trên TCVN hiện hành.</p>



                  <p><strong>07.</strong> Áp lực gió tiêu chuẩn Wo = 95 kg/m² (vùng II-B).</p>



                  <p><strong>16.</strong> Thép phi &le; 10: Ra = 2300 kg/cm²; phi &ge; 12: Ra = 3650 kg/cm²; Bê tông Mác #300.</p>



                  <p><strong>18.</strong> Có thể nối thép cột tại bất kỳ vị trí nào nhưng không nối quá 50% tiết diện.</p>



                  <p><strong>22.</strong> Đoạn neo dầm vào cột tối thiểu 35d; dầm phụ vào dầm chính neo 30d.</p>



                  <p><strong>23.</strong> Tường dài > 4m bố trí bổ trụ 200x200; tường cao > 3.6m bố trí giằng 200x100.</p>



                  <p class="text-indigo-600 font-semibold cursor-pointer" onclick="openGeneralNotesModal('text')">&rarr; Nhấn "Fullscreen riêng" để xem đầy đủ 24 điều khoản & sao chép văn bản.</p>



                </div>



              </div>



            </div>



          </div>



        </div>



      </div>







    </div>



  </div>







  <!-- ETABS Hub Controller Script -->



  <script src="/static/etabs_hub.js?v=20261024_gpu_v1"></script>



  <!-- AutoCAD 3D OBJ & Vision Hub Controller Script -->



  <script src="/static/cad_3d_hub.js?v=20261024_gpu_v1"></script>



  <script src="/static/ruby_3d_hub.js?v=20261024_gpu_v1"></script>
  <script src="/static/mep_3d_hub.js?v=20261024_gpu_v1"></script>



  <script src="/static/general_notes_hub.js?v=20261020_v1"></script>



  <script>



    // Live Browser Reload: Tự động tải lại trang khi server Flask hot-reload



    (function() {



      if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {



        let lastStamp = null;



        setInterval(async () => {



          try {



            const res = await fetch('/api/heartbeat', { cache: 'no-store' });



            if (res.ok) {



              const data = await res.json();



              if (lastStamp && data.server_stamp && data.server_stamp !== lastStamp) {



                console.log('[RevitAI Hot-Reload] Code thay đổi, tự động tải lại trang...');



                window.location.reload();



              }



              lastStamp = data.server_stamp;



            }



          } catch (e) {}



        }, 1500);



      }



    })();



  </script>



  

</body>



</html>



"""







# ==============================================================================



# API ROUTES



# ==============================================================================







@app.route('/api/heartbeat')



def api_heartbeat():



    return jsonify({



        "status": "ok",



        "server_stamp": _SERVER_START_TIME



    })







@app.route('/')
@app.route('/3d')
@app.route('/modal-3d')
@app.route('/etabs-3d')
@app.route('/structure-3d')
def index():



    return render_template_string(HTML_TEMPLATE)











@app.route('/favicon.ico')



def favicon():



    return send_from_directory(CURRENT_DIR, 'revit_ai.ico', mimetype='image/vnd.microsoft.icon')











@app.route('/api/etabs-data')



def api_etabs_data():



    import etabs_service



    return jsonify(etabs_service.get_etabs_data())











@app.route('/api/etabs-refresh', methods=['POST'])



def api_etabs_refresh():



    import etabs_service



    return jsonify(etabs_service.refresh_etabs_data())











@app.route('/api/export-svg-to-pdf', methods=['POST'])



def api_export_svg_to_pdf():



    import io



    import svg_cad_exporter



    data = request.get_json(silent=True) or {}



    svg_pages = data.get('svg_pages') or []



    if not svg_pages and 'svg' in data:



        svg_pages = [data['svg']]



    if not svg_pages:



        return jsonify({"success": False, "message": "Không có dữ liệu SVG để xuất PDF"}), 400



    try:



        pdf_bytes = svg_cad_exporter.convert_svg_pages_to_pdf(svg_pages)



        filename = data.get('filename') or "BanVe_Dam_ETABS.pdf"



        return send_file(



            io.BytesIO(pdf_bytes),



            mimetype='application/pdf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất PDF từ SVG: {str(e)}"}), 500











@app.route('/api/export-svg-to-dxf', methods=['POST'])



def api_export_svg_to_dxf():



    import io



    import svg_cad_exporter



    data = request.get_json(silent=True) or {}



    svg_pages = data.get('svg_pages') or []



    if not svg_pages and 'svg' in data:



        svg_pages = [data['svg']]



    if not svg_pages:



        return jsonify({"success": False, "message": "Không có dữ liệu SVG để xuất DXF"}), 400



    try:



        custom_layers = data.get('custom_layers') or None



        dxf_bytes = svg_cad_exporter.convert_svg_to_dxf(svg_pages, custom_layers=custom_layers)



        filename = data.get('filename') or "BanVe_Dam_ETABS.dxf"



        return send_file(



            io.BytesIO(dxf_bytes),



            mimetype='application/dxf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất DXF từ SVG: {str(e)}"}), 500











@app.route('/api/export-beam-pdf', methods=['GET', 'POST'])



def api_export_beam_pdf():



    import io



    import beam_cad_exporter



    



    combine_short = True



    layout_settings = None



    beam_groups = []



    page_scope = 'all'



    page_range = None



    current_page_index = 1



    



    if request.method == 'POST':



        data = request.get_json(silent=True) or {}



        if 'svg' in data or 'svg_pages' in data:



            import svg_cad_exporter



            svg_pages = data.get('svg_pages') or [data['svg']]



            pdf_bytes = svg_cad_exporter.convert_svg_pages_to_pdf(svg_pages)



            filename = data.get('filename') or "BanVe_Dam_ETABS.pdf"



            return send_file(



                io.BytesIO(pdf_bytes),



                mimetype='application/pdf',



                as_attachment=True,



                download_name=filename



            )



        combine_short = bool(data.get('combine_short', True))



        layout_settings = data.get('layout_settings', None)



        page_scope = data.get('scope') or data.get('page_scope') or 'all'



        page_range = data.get('page_range') or data.get('pages') or None



        current_page_index = data.get('current_page_index') or 1







        if 'beam_groups' in data and data['beam_groups']:



            beam_groups = data['beam_groups']



        elif 'beam_group' in data and data['beam_group']:



            beam_groups = [data['beam_group']]



            page_scope = 'current'



        else:



            st = data.get('story')



            b_id = data.get('long_beam_id') or data.get('beam_id')



            beam_groups = beam_cad_exporter.get_beam_groups_from_data(story_filter=st, beam_id_filter=b_id)



    else:



        st = request.args.get('story')



        b_id = request.args.get('long_beam_id') or request.args.get('beam_id')



        comb_arg = request.args.get('combine_short')



        page_scope = request.args.get('scope') or request.args.get('page_scope') or 'all'



        page_range = request.args.get('page_range') or request.args.get('pages') or None



        current_page_index = request.args.get('current_page_index') or 1



        if comb_arg is not None:



            combine_short = comb_arg in ('1', 'true', 'True')



        beam_groups = beam_cad_exporter.get_beam_groups_from_data(story_filter=st, beam_id_filter=b_id)







    if not beam_groups:



        return jsonify({"success": False, "message": "Không tìm thấy dữ liệu dầm để xuất PDF"}), 404







    try:



        pdf_bytes = beam_cad_exporter.generate_beam_pdf(



            beam_groups, 



            combine_short=combine_short, 



            layout_settings=layout_settings,



            page_scope=page_scope,



            page_range=page_range,



            current_page_index=current_page_index



        )



        filename = "ToanBo_BanVe_Dam_ETABS.pdf"



        if page_scope == 'current' and len(beam_groups) == 1:



            bg0 = beam_groups[0]



            filename = f"Dam_{bg0.get('story','T1')}_{bg0.get('long_beam_id','BEAM')}.pdf"



        elif page_scope == 'range' and page_range:



            safe_range = str(page_range).replace(' ', '').replace(',', '_')



            filename = f"BanVe_Dam_ETABS_Trang_{safe_range}.pdf"







        return send_file(



            io.BytesIO(pdf_bytes),



            mimetype='application/pdf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất PDF: {str(e)}"}), 500











@app.route('/api/export-beam-dxf', methods=['GET', 'POST'])



def api_export_beam_dxf():



    import io



    import beam_cad_exporter



    



    combine_short = True



    layout_settings = None



    beam_groups = []



    page_scope = 'all'



    page_range = None



    current_page_index = 1



    



    if request.method == 'POST':



        data = request.get_json(silent=True) or {}



        if 'svg' in data or 'svg_pages' in data:



            import svg_cad_exporter



            svg_pages = data.get('svg_pages') or [data['svg']]



            custom_layers = data.get('custom_layers') or None



            dxf_bytes = svg_cad_exporter.convert_svg_to_dxf(svg_pages, custom_layers=custom_layers)



            filename = data.get('filename') or "BanVe_Dam_ETABS.dxf"



            return send_file(



                io.BytesIO(dxf_bytes),



                mimetype='application/dxf',



                as_attachment=True,



                download_name=filename



            )



        combine_short = bool(data.get('combine_short', True))



        layout_settings = data.get('layout_settings', None)



        page_scope = data.get('scope') or data.get('page_scope') or 'all'



        page_range = data.get('page_range') or data.get('pages') or None



        current_page_index = data.get('current_page_index') or 1







        if 'beam_groups' in data and data['beam_groups']:



            beam_groups = data['beam_groups']



        elif 'beam_group' in data and data['beam_group']:



            beam_groups = [data['beam_group']]



            page_scope = 'current'



        else:



            st = data.get('story')



            b_id = data.get('long_beam_id') or data.get('beam_id')



            beam_groups = beam_cad_exporter.get_beam_groups_from_data(story_filter=st, beam_id_filter=b_id)



    else:



        st = request.args.get('story')



        b_id = request.args.get('long_beam_id') or request.args.get('beam_id')



        comb_arg = request.args.get('combine_short')



        page_scope = request.args.get('scope') or request.args.get('page_scope') or 'all'



        page_range = request.args.get('page_range') or request.args.get('pages') or None



        current_page_index = request.args.get('current_page_index') or 1



        if comb_arg is not None:



            combine_short = comb_arg in ('1', 'true', 'True')



        beam_groups = beam_cad_exporter.get_beam_groups_from_data(story_filter=st, beam_id_filter=b_id)







    if not beam_groups:



        return jsonify({"success": False, "message": "Không tìm thấy dữ liệu dầm để xuất DXF"}), 404







    try:



        dxf_bytes = beam_cad_exporter.generate_beam_dxf(



            beam_groups, 



            combine_short=combine_short, 



            layout_settings=layout_settings,



            page_scope=page_scope,



            page_range=page_range,



            current_page_index=current_page_index



        )



        filename = "ToanBo_BanVe_Dam_ETABS.dxf"



        if page_scope == 'current' and len(beam_groups) == 1:



            bg0 = beam_groups[0]



            filename = f"Dam_{bg0.get('story','T1')}_{bg0.get('long_beam_id','BEAM')}.dxf"



        elif page_scope == 'range' and page_range:



            safe_range = str(page_range).replace(' ', '').replace(',', '_')



            filename = f"BanVe_Dam_ETABS_Trang_{safe_range}.dxf"







        return send_file(



            io.BytesIO(dxf_bytes),



            mimetype='application/dxf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất DXF: {str(e)}"}), 500











@app.route('/api/column-matrix', methods=['GET'])



def api_column_matrix():



    import column_cad_exporter



    try:



        data = column_cad_exporter.get_column_matrix_data()



        return jsonify({"success": True, "data": data})



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": str(e)}), 500











@app.route('/api/export-column-pdf', methods=['GET', 'POST'])



def api_export_column_pdf():



    import io



    import column_cad_exporter



    try:



        mat = column_cad_exporter.get_column_matrix_data()



        pdf_bytes = column_cad_exporter.generate_column_pdf(mat)



        filename = "Bang_Chi_Tiet_Tiet_Dien_Cot_15x4.pdf"



        return send_file(



            io.BytesIO(pdf_bytes),



            mimetype='application/pdf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất PDF Cột: {str(e)}"}), 500











@app.route('/api/export-column-dxf', methods=['GET', 'POST'])



def api_export_column_dxf():



    import io



    import column_cad_exporter



    try:



        mat = column_cad_exporter.get_column_matrix_data()



        dxf_bytes = column_cad_exporter.generate_column_dxf(mat)



        filename = "Bang_Chi_Tiet_Tiet_Dien_Cot_15x4.dxf"



        return send_file(



            io.BytesIO(dxf_bytes),



            mimetype='application/dxf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất DXF Cột: {str(e)}"}), 500











@app.route('/api/tie-beam-data', methods=['GET'])



def api_tie_beam_data():



    import tie_beam_cad_exporter



    try:



        data = tie_beam_cad_exporter.get_tie_beam_data()



        return jsonify({"success": True, "data": data})



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": str(e)}), 500











@app.route('/api/export-tie-beam-pdf', methods=['GET', 'POST'])



def api_export_tie_beam_pdf():



    import io



    import tie_beam_cad_exporter



    try:



        pdf_bytes = tie_beam_cad_exporter.generate_tie_beam_pdf()



        filename = "Bang_Chi_Tiet_Da_Kieng_Truc_ABC.pdf"



        return send_file(



            io.BytesIO(pdf_bytes),



            mimetype='application/pdf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất PDF Đà Kiềng: {str(e)}"}), 500











@app.route('/api/export-tie-beam-dxf', methods=['GET', 'POST'])



def api_export_tie_beam_dxf():



    import io



    import tie_beam_cad_exporter



    try:



        dxf_bytes = tie_beam_cad_exporter.generate_tie_beam_dxf()



        filename = "Bang_Chi_Tiet_Da_Kieng_Truc_ABC.dxf"



        return send_file(



            io.BytesIO(dxf_bytes),



            mimetype='application/dxf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất DXF Đà Kiềng: {str(e)}"}), 500











@app.route('/api/export-beam-plan-pdf', methods=['GET', 'POST'])



def api_export_beam_plan_pdf():



    import io



    import beam_plan_cad_exporter



    story = request.args.get('story') or (request.json.get('story') if (request.is_json and request.json) else None) or 'T3'



    try:



        pdf_bytes = beam_plan_cad_exporter.generate_beam_plan_pdf(story=story)



        filename = f"Mat_Bang_Ket_Cau_Dam_{story}.pdf"



        return send_file(



            io.BytesIO(pdf_bytes),



            mimetype='application/pdf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất PDF Mặt Bằng Dầm: {str(e)}"}), 500











@app.route('/api/export-beam-plan-dxf', methods=['GET', 'POST'])



def api_export_beam_plan_dxf():



    import io



    import beam_plan_cad_exporter



    story = request.args.get('story') or (request.json.get('story') if (request.is_json and request.json) else None) or 'T3'



    try:



        dxf_bytes = beam_plan_cad_exporter.generate_beam_plan_dxf(story=story)



        filename = f"Mat_Bang_Ket_Cau_Dam_{story}.dxf"



        return send_file(



            io.BytesIO(dxf_bytes),



            mimetype='application/dxf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất DXF Mặt Bằng Dầm: {str(e)}"}), 500











@app.route('/api/export-column-plan-pdf', methods=['GET', 'POST'])



def api_export_column_plan_pdf():



    import io



    import column_plan_cad_exporter



    try:



        pdf_bytes = column_plan_cad_exporter.generate_column_plan_pdf()



        filename = "Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.pdf"



        return send_file(



            io.BytesIO(pdf_bytes),



            mimetype='application/pdf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất PDF Mặt Bằng Cột: {str(e)}"}), 500











@app.route('/api/export-column-plan-dxf', methods=['GET', 'POST'])



def api_export_column_plan_dxf():



    import io



    import column_plan_cad_exporter



    try:



        dxf_bytes = column_plan_cad_exporter.generate_column_plan_dxf()



        filename = "Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.dxf"



        return send_file(



            io.BytesIO(dxf_bytes),



            mimetype='application/dxf',



            as_attachment=True,



            download_name=filename



        )



    except Exception as e:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "message": f"Lỗi xuất DXF Mặt Bằng Cột: {str(e)}"}), 500











@app.route('/api/rebar/db/status', methods=['GET'])



def api_rebar_db_status():



    import db_postgres



    return jsonify(db_postgres.db_manager.get_db_status())











@app.route('/api/rebar/db/save', methods=['POST'])



def api_rebar_db_save():



    import db_postgres



    data = request.get_json(silent=True) or {}



    if 'designs' in data:



        res = db_postgres.db_manager.save_all_designs(data['designs'])



    elif 'beam_design' in data:



        res = db_postgres.db_manager.save_beam_design(data['beam_design'])



    else:



        res = db_postgres.db_manager.save_beam_design(data)



    return jsonify(res)











@app.route('/api/rebar/db/load', methods=['GET'])



def api_rebar_db_load():



    import db_postgres



    proj = request.args.get('project_name', 'CAI_TAO_PHUONG_AN_B')



    return jsonify(db_postgres.db_manager.load_all_designs(project_name=proj))











@app.route('/static/etabs_hub.js')



def static_etabs_hub():



    resp = make_response(send_from_directory(CURRENT_DIR, 'etabs_hub.js', mimetype='application/javascript'))



    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'



    return resp











@app.route('/etabs_hub.js')



def root_etabs_hub():



    resp = make_response(send_from_directory(CURRENT_DIR, 'etabs_hub.js', mimetype='application/javascript'))



    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'



    return resp











@app.route('/etabs_beam_data.json')



def root_etabs_json():



    return send_from_directory(CURRENT_DIR, 'etabs_beam_data.json', mimetype='application/json')











@app.route('/OBJLoader.js')



@app.route('/static/OBJLoader.js')



def root_obj_loader():



    return send_from_directory(CURRENT_DIR, 'OBJLoader.js', mimetype='application/javascript')











@app.route('/MTLLoader.js')



@app.route('/static/MTLLoader.js')



def root_mtl_loader():



    return send_from_directory(CURRENT_DIR, 'MTLLoader.js', mimetype='application/javascript')











@app.route('/rebar.obj')



@app.route('/static/rebar.obj')



def root_rebar_obj():



    return send_from_directory(CURRENT_DIR, 'rebar.obj', mimetype='text/plain')











@app.route('/rebar.mtl')



@app.route('/static/rebar.mtl')



def root_rebar_mtl():



    return send_from_directory(CURRENT_DIR, 'rebar.mtl', mimetype='text/plain')











# ==============================================================================



# AUTOCAD 3D OBJ & VISION PIPELINE ROUTES



# ==============================================================================







@app.route('/static/cad_3d_hub.js')



@app.route('/cad_3d_hub.js')



def static_cad_3d_hub():



    resp = make_response(send_from_directory(CURRENT_DIR, 'cad_3d_hub.js', mimetype='application/javascript'))



    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'



    return resp











@app.route('/api/cad/status')



def api_cad_status():



    import cad_3d_service



    return jsonify(cad_3d_service.get_available_cad_assets())











@app.route('/api/cad/run-clipboard-pipeline', methods=['POST'])



def api_cad_run_clipboard_pipeline():



    import cad_3d_service



    data = request.json or {}



    source = data.get("source", "clipboard")



    custom_path = data.get("customPath", "")







    try:



        if source == "sample":



            dxf_path = os.path.join(cad_3d_service.AUTOCAD_3D_OBJ_DIR, "clipboard_converted.dxf")



            if not os.path.exists(dxf_path):



                return jsonify({"success": False, "message": "Không tìm thấy file mẫu clipboard_converted.dxf"})



        elif source == "custom" and custom_path:



            dxf_path = custom_path



            if not os.path.exists(dxf_path):



                return jsonify({"success": False, "message": f"Không tìm thấy file: {custom_path}"})



            if dxf_path.lower().endswith(".dwg"):



                out_dxf = dxf_path[:-4] + ".dxf"



                cad_3d_service.convert_dwg_to_dxf(dxf_path, out_dxf)



                dxf_path = out_dxf



        else:



            scratch = os.path.join(cad_3d_service.AUTOCAD_3D_OBJ_DIR, "_scratch")



            os.makedirs(scratch, exist_ok=True)



            ole_f = os.path.join(scratch, "clipboard_raw.bin")



            dwg_f = os.path.join(scratch, "clipboard_model.dwg")



            dxf_f = os.path.join(scratch, "clipboard_model.dxf")







            cad_3d_service.extract_clipboard_ole(ole_f)



            cad_3d_service.extract_dwg_from_ole(ole_f, dwg_f)



            cad_3d_service.convert_dwg_to_dxf(dwg_f, dxf_f)



            dxf_path = dxf_f







        expected_stairs = data.get("expected_stairs")
        vision_res = cad_3d_service.run_vision_detection(dxf_path, expected_stairs=expected_stairs)



        return jsonify({



            "success": True,



            "message": f"Đã trích xuất và nhận diện thành công: {vision_res['counts']['doors']} cửa, {vision_res['counts']['windows']} cửa sổ, {vision_res['counts']['columns']} cột, {vision_res['counts']['major_walls']} mảng tường.",



            "dxf_path": dxf_path,



            "vision": vision_res



        })



    except Exception as ex:



        return jsonify({"success": False, "message": str(ex)})











@app.route('/api/cad/generate-3d', methods=['POST'])



def api_cad_generate_3d():



    import cad_3d_service



    data = request.json or {}



    dxf_path = data.get("dxfPath", "")



    if not dxf_path or not os.path.exists(dxf_path):



        scratch_dxf = os.path.join(cad_3d_service.AUTOCAD_3D_OBJ_DIR, "_scratch", "clipboard_model.dxf")



        sample_dxf = os.path.join(cad_3d_service.AUTOCAD_3D_OBJ_DIR, "clipboard_converted.dxf")



        if os.path.exists(scratch_dxf):



            dxf_path = scratch_dxf



        elif os.path.exists(sample_dxf):



            dxf_path = sample_dxf



        else:



            return jsonify({"success": False, "message": "Không tìm thấy file DXF để tạo 3D OBJ."})







    try:



        expected_stairs = data.get("expected_stairs")
        models_summary = cad_3d_service.generate_3d_obj_models(dxf_path, expected_stairs=expected_stairs)



        return jsonify({



            "success": True,



            "message": "Đã sinh thành công mô hình 3D OBJ (Tường, Cửa, Cửa sổ, Cầu thang, Ram dốc, Full Building).",



            "models": models_summary["models"]



        })



    except Exception as ex:



        return jsonify({"success": False, "message": str(ex)})











@app.route('/api/cad/3d-models/<path:filename>')



def api_cad_serve_model(filename):



    import cad_3d_service



    m_dir = os.path.join(cad_3d_service.AUTOCAD_3D_OBJ_DIR, "models_export", "meters")



    if not os.path.exists(os.path.join(m_dir, filename)):



        m_dir = cad_3d_service.AUTOCAD_3D_OBJ_DIR



    return send_from_directory(m_dir, filename, as_attachment=(request.args.get('download') == '1'))











@app.route('/api/cad/vision-image/<path:filename>')



def api_cad_serve_vision_image(filename):



    import cad_3d_service



    v_dir = cad_3d_service.DEFAULT_VISION_DIR



    return send_from_directory(v_dir, filename)











@app.route('/api/cad/vision-crop/<path:filename>')



def api_cad_serve_vision_crop(filename):



    import cad_3d_service



    crop_dir = os.path.join(cad_3d_service.DEFAULT_VISION_DIR, "crops")



    return send_from_directory(crop_dir, filename)











@app.route('/api/cad/update-annotations', methods=['POST'])
def api_cad_update_annotations():
    try:
        import cad_3d_service
        data = request.get_json(force=True)
        res = cad_3d_service.update_vision_annotations(data)
        return jsonify(res)
    except Exception as ex:
        return jsonify({"status": "error", "message": str(ex)}), 500


@app.route('/api/cad/open-folder', methods=['POST'])



def api_cad_open_folder():



    import cad_3d_service



    target = cad_3d_service.AUTOCAD_3D_OBJ_DIR



    os.makedirs(target, exist_ok=True)



    try:



        import subprocess



        subprocess.Popen(f'explorer "{target}"')



        return jsonify({"success": True, "folder": target})



    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)})











# =========================================================================



# ROUTE: SKETCHUP RUBY (.RB) -> 3D OBJ CONVERTER & VIEWER (TAB 13)



# =========================================================================



@app.route('/api/rb/samples', methods=['GET'])



def api_rb_samples():



    """Trả về danh sách các tệp mẫu Ruby .rb có sẵn trong thư mục dự án."""



    import importlib
    import sketchup_ruby_engine
    importlib.reload(sketchup_ruby_engine)



    samples = sketchup_ruby_engine.list_sample_rb_files()



    return jsonify({"success": True, "samples": samples})











@app.route('/api/rb/sample-code', methods=['GET'])



def api_rb_sample_code():



    """Đọc nội dung mã nguồn của một tệp .rb mẫu."""



    import sketchup_ruby_engine



    filename = request.args.get('file', 'house_bim_model.rb')



    clean_name = os.path.basename(filename)



    target = os.path.join(sketchup_ruby_engine.RUBY_DIR, clean_name)



    if not os.path.exists(target):



        return jsonify({"success": False, "error": f"Tệp không tồn tại: {clean_name}"}), 404



    try:



        with open(target, 'r', encoding='utf-8', errors='replace') as f:



            code = f.read()



        return jsonify({"success": True, "code": code, "fileName": clean_name})



    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)}), 500











@app.route('/api/rb/convert', methods=['POST'])



def api_rb_convert():



    """Thông dịch mã Ruby SketchUp sang mô hình 3D Wavefront OBJ & MTL."""



    import sketchup_ruby_engine



    data = request.get_json(silent=True) or {}



    code = data.get('code', '')



    file_name = data.get('fileName', 'ruby_model')



    if not code.strip():



        return jsonify({"success": False, "error": "Mã nguồn Ruby trống!"}), 400



    try:



        stats = sketchup_ruby_engine.convert_rb_code_to_obj(code=code, file_name=file_name)



        return jsonify({"success": True, "stats": stats})



    except Exception as ex:



        import traceback



        traceback.print_exc()



        return jsonify({"success": False, "error": str(ex)}), 500











@app.route('/api/rb/3d-models/<path:filename>')



def api_rb_serve_model(filename):



    """Phục vụ file .obj, .mtl được xuất từ engine Ruby."""



    import sketchup_ruby_engine



    m_dir = sketchup_ruby_engine.RUBY_EXPORTS_DIR



    return send_from_directory(m_dir, filename, as_attachment=(request.args.get('download') == '1'))











@app.route('/api/rb/open-folder', methods=['POST'])



def api_rb_open_folder():



    """Mở thư mục chứa file OBJ xuất ra trên Windows Explorer."""



    import sketchup_ruby_engine



    target = sketchup_ruby_engine.RUBY_EXPORTS_DIR



    os.makedirs(target, exist_ok=True)



    try:



        import subprocess



        subprocess.Popen(f'explorer "{target}"')



        return jsonify({"success": True, "folder": target})





    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)})

# ==============================================================================
# MEP AI STUDIO 3D AUTOMATION API ROUTES
# ==============================================================================

@app.route('/static/mep_3d_hub.js')
@app.route('/mep_3d_hub.js')
def serve_mep_3d_hub_js():
    static_dir = os.path.join(CURRENT_DIR, 'static')
    resp = make_response(send_from_directory(static_dir, 'mep_3d_hub.js', mimetype='application/javascript'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/api/mep/status', methods=['GET'])
def api_mep_status():
    import mep_bim_engine
    return jsonify({
        "status": "ready",
        "exports_dir": mep_bim_engine.EXPORTS_DIR,
        "ifc_available": bool(mep_bim_engine.ifcopenshell),
        "ezdxf_available": bool(mep_bim_engine.ezdxf)
    })

@app.route('/api/mep/generate', methods=['POST'])
def api_mep_generate():
    try:
        import mep_bim_engine
        data = request.get_json() or {}
        w = float(data.get('width_m', 12.0)) * 1000.0
        d = float(data.get('depth_m', 8.0)) * 1000.0
        h = float(data.get('height_m', 3.6)) * 1000.0
        floors = int(data.get('floors', 2))
        auto_resolve = bool(data.get('auto_resolve', True))

        res = mep_bim_engine.run_complete_mep_pipeline(
            building_width=w,
            building_depth=d,
            floor_height=h,
            num_floors=floors,
            auto_resolve_clashes=auto_resolve
        )

        obj_name = os.path.basename(res["exported_files"]["obj"])
        mtl_name = os.path.basename(res["exported_files"]["mtl"])

        return jsonify({
            "success": True,
            "elapsed_seconds": res["elapsed_seconds"],
            "model_name": res["model_name"],
            "summary": res["summary"],
            "clash_detection": res["clash_detection"],
            "boq_schedule": res["boq_schedule"],
            "exported_files": res["exported_files"],
            "obj_url": f"/api/mep/models/{obj_name}",
            "mtl_url": f"/api/mep/models/{mtl_name}"
        })
    except Exception as ex:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(ex)})

@app.route('/api/mep/auto-resolve', methods=['POST'])
def api_mep_auto_resolve():
    try:
        import mep_bim_engine
        res = mep_bim_engine.run_complete_mep_pipeline(auto_resolve_clashes=True)
        return jsonify({
            "success": True,
            "resolved_count": res["clash_detection"]["auto_resolve"]["resolved_count"] if res["clash_detection"]["auto_resolve"] else 0,
            "clash_detection": res["clash_detection"]
        })
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)})

@app.route('/api/mep/models/<path:filename>')
def api_mep_serve_model(filename):
    import mep_bim_engine
    target_dir = mep_bim_engine.EXPORTS_DIR
    file_path = os.path.join(target_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    mimetype = 'text/plain'
    if filename.endswith('.obj'):
        mimetype = 'text/plain'
    elif filename.endswith('.mtl'):
        mimetype = 'text/plain'
    elif filename.endswith('.dxf'):
        mimetype = 'application/dxf'
    elif filename.endswith('.ifc'):
        mimetype = 'application/x-step'
    elif filename.endswith('.json'):
        mimetype = 'application/json'

    resp = make_response(send_from_directory(target_dir, filename, mimetype=mimetype))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/api/mep/open-folder', methods=['POST'])
def api_mep_open_folder():
    import mep_bim_engine
    target = mep_bim_engine.EXPORTS_DIR
    os.makedirs(target, exist_ok=True)
    try:
        import subprocess
        subprocess.Popen(f'explorer "{target}"')
        return jsonify({"success": True, "folder": target})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)})














# ==============================================================================



# GENERAL STRUCTURAL NOTES (BẢNG GHI CHÚ CHUNG KẾT CẤU) ROUTES



# ==============================================================================







GENERAL_NOTES_SOURCE_DIR = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Documents\\plot\\1020"



GENERAL_NOTES_PDF_NAME = "Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf"







@app.route('/static/general_notes_hub.js')



@app.route('/general_notes_hub.js')



def static_general_notes_hub():



    resp = make_response(send_from_directory(os.path.join(CURRENT_DIR, 'static'), 'general_notes_hub.js', mimetype='application/javascript'))



    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'



    return resp







@app.route('/api/general-notes/pdf')



def api_general_notes_pdf():



    src = os.path.join(GENERAL_NOTES_SOURCE_DIR, GENERAL_NOTES_PDF_NAME)



    if os.path.exists(src):



        return send_file(src, mimetype='application/pdf')



    static_pdf = os.path.join(CURRENT_DIR, 'static', 'general_notes_drawing.pdf')



    if os.path.exists(static_pdf):



        return send_file(static_pdf, mimetype='application/pdf')



    return jsonify({"error": "PDF not found"}), 404







@app.route('/api/general-notes/image')



def api_general_notes_image():



    static_png = os.path.join(CURRENT_DIR, 'static', 'general_notes_page1.png')



    if os.path.exists(static_png):



        return send_file(static_png, mimetype='image/png')



    return jsonify({"error": "Image not found"}), 404







@app.route('/api/general-notes/open-folder', methods=['POST'])



def api_general_notes_open_folder():



    target = GENERAL_NOTES_SOURCE_DIR if os.path.exists(GENERAL_NOTES_SOURCE_DIR) else os.path.join(CURRENT_DIR, 'static')



    try:



        import subprocess



        subprocess.Popen(f'explorer "{target}"')



        return jsonify({"success": True, "folder": target})



    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)})







@app.route('/api/general-notes/info')



def api_general_notes_info():



    src = os.path.join(GENERAL_NOTES_SOURCE_DIR, GENERAL_NOTES_PDF_NAME)



    actual_path = src if os.path.exists(src) else os.path.join(CURRENT_DIR, 'static', 'general_notes_drawing.pdf')



    size_kb = round(os.path.getsize(actual_path) / 1024, 1) if os.path.exists(actual_path) else 143.3



    return jsonify({



        "success": True,



        "title": "BẢN VẼ GHI CHÚ CHUNG KẾT CẤU (TCVN 5574-2012)",



        "filename": GENERAL_NOTES_PDF_NAME,



        "source_dir": GENERAL_NOTES_SOURCE_DIR,



        "size_kb": size_kb,



        "date_modified": "20/10/2026 08:24:43 AM",



        "sheet_format": "A3 Landscape (1191 × 842 pt)",



        "dpi": 250,



        "image_resolution": "4136 × 2924 px",



        "pdf_url": "/api/general-notes/pdf",



        "image_url": "/api/general-notes/image"



    })



















@app.route('/api/deploy-to-vps', methods=['POST'])



def api_deploy_to_vps():



    """Deploy toàn bộ giao diện và dữ liệu ETABS Hub lên https://mr.pkld.online."""



    try:



        import deploy_etabs



        res = deploy_etabs.deploy_hub_to_vps()



        return jsonify(res)



    except Exception as e:



        return jsonify({'success': False, 'message': f'Ngoại lệ khi deploy: {str(e)}'})















@app.route('/api/hub-status')



def api_hub_status():



    """Lấy thông tin trạng thái toàn bộ hệ sinh thái AEC (AutoCAD, 3ds Max, Revit, Dashboard)."""



    import aec_hub



    return jsonify(aec_hub.get_hub_status())











@app.route('/api/model-info')



def api_model_info():



    """Lấy thông tin tài liệu và đối tượng từ Revit Bridge kèm theo Multi-CAD status."""



    import aec_hub



    hub_stat = aec_hub.get_hub_status()



    base_url = revit_cli.get_base_url()



    try:



        if not hub_stat.get("revit", {}).get("running") and not hub_stat.get("revit", {}).get("bridgeOnline"):



            return jsonify({



                "online": False,



                "hub": hub_stat,



                "message": "Revit chưa bật (Tùy chọn - không bắt buộc)"



            })







        status_res = revit_cli.request_json(f"{base_url}/api/status", timeout=1.0)



        if "error" in status_res:



            return jsonify({"online": False, "hub": hub_stat, "message": "Revit Bridge chưa nạp"})







        model_res = revit_cli.request_json(f"{base_url}/api/model", timeout=1.0)



        return jsonify({



            "online": True,



            "hub": hub_stat,



            "title": status_res.get("title", ""),



            "activeView": status_res.get("activeView"),



            "counts": model_res.get("counts", {}),



            "levels": model_res.get("levels", []),



            "grids": model_res.get("grids", [])



        })



    except Exception as ex:



        return jsonify({"online": False, "hub": hub_stat, "error": str(ex)})











@app.route('/api/dwg-treeview')



def api_dwg_treeview():



    """Lấy danh sách View/Sheet phân nhóm dạng TreeView và Thông tin dự án."""



    base_url = revit_cli.get_base_url()



    dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



    payload = {



        "action": "execute_dynamic",



        "dllPath": dll_path,



        "typeName": "RevitScript.GetViewsAndProjectInfoForExport",



        "methodName": "Run",



        "args": {}



    }



    try:



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)



        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})



    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)})











@app.route('/api/tags-status')



def api_tags_status():



    """Lấy danh sách và trạng thái ẩn/hiện Door & Window Tags theo từng tầng."""



    base_url = revit_cli.get_base_url()



    dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



    payload = {



        "action": "execute_dynamic",



        "dllPath": dll_path,



        "typeName": "RevitScript.ManageDoorWindowTags",



        "methodName": "Run",



        "args": {



            "subAction": "get_status"



        }



    }



    try:



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)



        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})



    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)})











@app.route('/api/cadlib-lisps')



def api_cadlib_lisps():



    """Lấy danh sách thông tin, tính năng và lệnh tắt của toàn bộ LISP trong CADLib."""



    import cadlib_lisp_manager



    reload = (request.args.get('reload', '0') == '1')



    return jsonify(cadlib_lisp_manager.get_cadlib_lisp_list(force_reload=reload))











@app.route('/api/maxscripts')



def api_maxscripts():



    """Lấy danh sách tổng hợp Maxscript & Python từ skMSTool và 3ds Max 2022."""



    import maxscript_manager



    reload = (request.args.get('reload', '0') == '1')



    return jsonify(maxscript_manager.get_maxscript_list(force_reload=reload))











@app.route('/api/open-script-editor', methods=['POST'])



def api_open_script_editor():



    """Mở file script trong code editor (VS Code hoặc mặc định)."""



    import maxscript_manager



    data = request.json or {}



    path = data.get("path", "")



    ok, msg = maxscript_manager.open_script_in_editor(path)



    return jsonify({"success": ok, "message": msg})











@app.route('/api/open-script-folder', methods=['POST'])



def api_open_script_folder():



    """Mở thư mục chứa file script trong Explorer."""



    import maxscript_manager



    data = request.json or {}



    path = data.get("path", "")



    ok, msg = maxscript_manager.open_containing_folder(path)



    return jsonify({"success": ok, "message": msg})











@app.route('/api/open-downloads', methods=['POST'])



def api_open_downloads():



    """Mở thư mục Downloads hoặc thư mục xuất DWG trong Windows Explorer."""



    data = request.json or {}



    folder = data.get("folder") or os.path.join(os.path.expanduser("~"), "Downloads")



    if folder in ["~/Downloads", "~\\Downloads", "Downloads"]:



        expanded = os.path.join(os.path.expanduser("~"), "Downloads")



    else:



        expanded = os.path.abspath(os.path.expanduser(folder))







    os.makedirs(expanded, exist_ok=True)



    try:



        import subprocess



        subprocess.Popen(f'explorer "{expanded}"')



        return jsonify({"success": True, "folder": expanded})



    except Exception as ex:



        return jsonify({"success": False, "error": str(ex)})











@app.route('/api/export-dwg-init', methods=['POST'])



def api_export_dwg_init():



    """Khởi tạo phiên xuất bản vẽ, chuẩn bị thư mục Downloads và thông tin dự án."""



    data = request.json or {}



    raw_folder = str(data.get("outputFolder", "")).strip()



    downloads_default = os.path.join(os.path.expanduser("~"), "Downloads")



    if not raw_folder or raw_folder in ["~/Downloads", "~\\Downloads", "Downloads"]:



        target_output_folder = downloads_default



    else:



        target_output_folder = os.path.abspath(os.path.expanduser(raw_folder))



    os.makedirs(target_output_folder, exist_ok=True)







    import datetime, re



    now = datetime.datetime.now()



    timestamp_str = now.strftime("%Y%m%d_%H%M%S")







    raw_tag = str(data.get("projectTag", "")).strip()



    if not raw_tag:



        raw_tag = data.get("projectInfo", {}).get("projectName", "").strip()



        if not raw_tag or "TÊN DỰ ÁN" in raw_tag.upper() or len(raw_tag) > 30:



            raw_tag = "Mau_40_CBS"







    clean_project = re.sub(r'[^\w\-]+', '_', raw_tag).strip('_')



    if not clean_project:



        clean_project = "Mau_40_CBS"







    file_prefix = f"{clean_project}_{timestamp_str}"



    combine_vert = (data.get("layoutMode") == "vertical")







    # Thư mục tạm luôn là pure ASCII để AutoCAD script không bị lỗi font/dấu cách



    if combine_vert:



        sub_export_folder = os.path.join(target_output_folder, f"_temp_merge_{timestamp_str}")



    else:



        sub_export_folder = target_output_folder



    os.makedirs(sub_export_folder, exist_ok=True)







    # Cập nhật thông tin dự án nếu có



    proj_info = data.get("projectInfo", {})



    if proj_info:



        base_url = revit_cli.get_base_url()



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        try:



            revit_cli.request_json(f"{base_url}/api/execute", {



                "action": "execute_dynamic",



                "dllPath": dll_path,



                "typeName": "RevitScript.ExportCustomViewsToDwg",



                "methodName": "Run",



                "args": {



                    "viewIds": [],



                    "projectInfo": proj_info



                }



            }, timeout=15)



        except:



            pass







    return jsonify({



        "success": True,



        "cleanProject": clean_project,



        "timestamp": timestamp_str,



        "filePrefix": file_prefix,



        "targetOutputFolder": target_output_folder,



        "subExportFolder": sub_export_folder,



        "combinedFileName": f"{clean_project}_{timestamp_str}_merge_cad.dwg"



    })











@app.route('/api/export-dwg-step', methods=['POST'])



def api_export_dwg_step():



    """Xuất một view/bản vẽ đơn lẻ và cập nhật ngay tiến trình cho Frontend."""



    data = request.json or {}



    view_id = data.get("viewId")



    order_index = int(data.get("orderIndex", 1))



    combine_vert = bool(data.get("combineVertical", False))



    sub_export_folder = data.get("subExportFolder") or os.path.join(os.path.expanduser("~"), "Downloads")



    file_prefix = data.get("filePrefix", "")



    overlay = bool(data.get("overlayTitleblock", False))



    tb_file = str(data.get("titleblockFile", ""))







    base_url = revit_cli.get_base_url()



    dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



    payload = {



        "action": "execute_dynamic",



        "dllPath": dll_path,



        "typeName": "RevitScript.ExportCustomViewsToDwg",



        "methodName": "Run",



        "args": {



            "viewIds": [view_id],



            "orderIndex": order_index,



            "filePrefix": file_prefix if not combine_vert else "",



            "overlayTitleblock": overlay,



            "titleblockFile": tb_file,



            "combineVertical": combine_vert,



            "outputFolder": sub_export_folder



        }



    }



    res = revit_cli.request_json(f"{base_url}/api/execute", payload, timeout=120)



    file_info = None



    if isinstance(res, dict) and res.get("exportedFiles") and len(res["exportedFiles"]) > 0:



        file_info = res["exportedFiles"][0]







    return jsonify({



        "success": bool(res.get("success", False)) if isinstance(res, dict) else False,



        "orderIndex": order_index,



        "viewId": view_id,



        "file": file_info,



        "error": res.get("error") if isinstance(res, dict) else str(res)



    })











@app.route('/api/export-dwg-assemble', methods=['POST'])



def api_export_dwg_assemble():



    """Chạy AutoCAD Core Console gộp các view con thành 1 file Merge CAD và áp màu layer chuẩn."""



    data = request.json or {}



    clean_project = data.get("cleanProject", "Mau_40_CBS")



    timestamp_str = data.get("timestamp", "")



    target_output_folder = data.get("targetOutputFolder") or os.path.join(os.path.expanduser("~"), "Downloads")



    sub_export_folder = data.get("subExportFolder")



    exported_files = data.get("exportedFiles", [])







    from export_views_vertical_dwg import assemble_vertical_dwg



    combined_name = f"{clean_project}_{timestamp_str}_merge_cad.dwg"



    asm_data = {



        "success": True,



        "exportFolder": target_output_folder,



        "views": [



            {



                "index": f.get("order", idx + 1),



                "id": f.get("viewId", 0),



                "name": f.get("viewName", f"View_{idx+1}"),



                "filePath": f.get("filePath"),



                "width": 38000.0,



                "height": 20000.0,



                "yOffset": 0.0



            }



            for idx, f in enumerate(exported_files)



            if f and f.get("filePath") and os.path.exists(f.get("filePath"))



        ]



    }



    ok = assemble_vertical_dwg(asm_data, output_name=combined_name)



    comb_path = os.path.join(target_output_folder, combined_name)







    # Dọn dẹp thư mục tạm _temp_merge_...



    try:



        import shutil



        if sub_export_folder and os.path.exists(sub_export_folder) and sub_export_folder != target_output_folder:



            shutil.rmtree(sub_export_folder, ignore_errors=True)



    except:



        pass







    return jsonify({



        "success": ok,



        "combinedDwgPath": comb_path if ok else None,



        "outputFolder": target_output_folder,



        "message": f"Đã gộp thành công file Merge CAD tại: {comb_path}" if ok else "Lỗi gộp file AutoCAD"



    })











@app.route('/api/execute-action', methods=['POST'])



def api_execute_action():



    """Điều phối và thực thi các script hỗ trợ."""



    data = request.json or {}



    action = data.get("action")



    base_url = revit_cli.get_base_url()







    # 1. Hành động: Chọn theo Trục



    if action == "select_by_grid":



        grid_x_raw = data.get("gridX", "").strip()



        grid_y_raw = data.get("gridY", "").strip()



        



        grid_x = grid_x_raw.split() if " " in grid_x_raw else (grid_x_raw if grid_x_raw else None)



        grid_y = grid_y_raw.split() if " " in grid_y_raw else (grid_y_raw if grid_y_raw else None)







        res = select_elements_by_grid(



            grid_x=grid_x,



            grid_y=grid_y,



            tolerance_y_mm=float(data.get("toleranceY", 1500)),



            level=data.get("level", "all"),



            category=data.get("category", "doors"),



            zoom_to=bool(data.get("zoom", False)),



            isolate=bool(data.get("isolate", False)),



            verbose=False



        )



        return jsonify(res)







    # 2. Hành động: Đổi cửa D7 mở 30 độ



    elif action == "change_doors_d7":



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.ChangeAxisCDoorsToD7",



            "methodName": "Run"



        }



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)



        return jsonify(res)







    # 3. Hành động: Đánh Dim tự động 3 lớp & nội thất



    elif action == "create_dimensions":



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        view_id = data.get("viewId")



        clean = bool(data.get("clean", True))



        off_b = float(data.get("offsetB", 1500.0))



        off_c = float(data.get("offsetC", 1500.0))







        args_dict = {



            "offsetB": off_b,



            "offsetC": off_c,



            "cleanExisting": clean



        }



        if view_id and view_id != "all":



            args_dict["viewId"] = int(view_id)







        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.CreateCompleteFloorDimensions",



            "methodName": "Run",



            "args": args_dict



        }



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)



        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})







    # 4. Hành động: Xuất DWG Custom (Hỗ trợ TreeView, Khung tên & Bố cục)



    elif action in ["export_dwg_custom", "export_dwg"]:



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        view_ids = data.get("viewIds", [])



        overlay = bool(data.get("overlayTitleblock", False))



        tb_file = str(data.get("titleblockFile", ""))



        proj_info = data.get("projectInfo", {})



        combine_vert = (data.get("layoutMode") == "vertical")







        # 1. Thư mục đích: Mặc định là ~/Downloads của người dùng



        import datetime, re, shutil



        downloads_default = os.path.join(os.path.expanduser("~"), "Downloads")



        raw_folder = str(data.get("outputFolder", "")).strip()



        if not raw_folder or raw_folder in ["~/Downloads", "~\\Downloads", "Downloads"]:



            target_output_folder = downloads_default



        else:



            target_output_folder = os.path.abspath(os.path.expanduser(raw_folder))



        os.makedirs(target_output_folder, exist_ok=True)







        # 2. Quy tắc đặt tên file: {project} + {timestamp} + merge_cad



        now = datetime.datetime.now()



        timestamp_str = now.strftime("%Y%m%d_%H%M%S")







        raw_tag = str(data.get("projectTag", "")).strip()



        if not raw_tag:



            raw_tag = proj_info.get("projectName", "").strip()



            if not raw_tag or "TÊN DỰ ÁN" in raw_tag.upper() or len(raw_tag) > 30:



                raw_tag = "Mau_40_CBS"







        clean_project = re.sub(r'[^\w\-]+', '_', raw_tag).strip('_')



        if not clean_project:



            clean_project = "Mau_40_CBS"







        file_prefix = f"{clean_project}_{timestamp_str}"







        # 3. Phân chia thư mục tạm cho các view con khi gộp



        sub_export_folder = target_output_folder



        if combine_vert:



            sub_export_folder = os.path.join(target_output_folder, f"_temp_merge_{timestamp_str}")



            os.makedirs(sub_export_folder, exist_ok=True)







        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.ExportCustomViewsToDwg",



            "methodName": "Run",



            "args": {



                "viewIds": view_ids,



                "filePrefix": file_prefix if not combine_vert else "",



                "overlayTitleblock": overlay,



                "titleblockFile": tb_file,



                "projectInfo": proj_info,



                "combineVertical": combine_vert,



                "outputFolder": sub_export_folder



            }



        }



        # Timeout 300s (5 phút) để tránh lỗi timed out khi xuất nhiều view



        res = revit_cli.request_json(f"{base_url}/api/execute", payload, timeout=300)







        if isinstance(res, dict) and res.get("success") and combine_vert:



            try:



                from export_views_vertical_dwg import assemble_vertical_dwg



                # Tên file gộp chuẩn theo đúng yêu cầu người dùng: {project}_{timestamp}_merge_cad.dwg



                combined_name = f"{clean_project}_{timestamp_str}_merge_cad.dwg"



                asm_data = {



                    "success": True,



                    "exportFolder": target_output_folder,



                    "views": [



                        {



                            "index": f.get("order", idx + 1),



                            "id": f.get("viewId", 0),



                            "name": f.get("viewName", f"View_{idx+1}"),



                            "filePath": f.get("filePath"),



                            "width": 38000.0,



                            "height": 20000.0,



                            "yOffset": 0.0



                        }



                        for idx, f in enumerate(res.get("exportedFiles", []))



                        if f.get("filePath") and os.path.exists(f.get("filePath"))



                    ]



                }



                ok = assemble_vertical_dwg(asm_data, output_name=combined_name)



                if ok:



                    comb_path = os.path.join(target_output_folder, combined_name)



                    res["combinedDwgPath"] = comb_path



                    res["outputFolder"] = target_output_folder



                    res["message"] = f"Đã gộp thành công file Merge CAD tại: {comb_path}"







                    # Dọn dẹp thư mục tạm _temp_... sau khi gộp xong



                    try:



                        if os.path.exists(sub_export_folder) and sub_export_folder != target_output_folder:



                            shutil.rmtree(sub_export_folder, ignore_errors=True)



                    except:



                        pass



                else:



                    res["message"] += " (Lưu ý: Không thể hoàn tất lệnh gộp AutoCAD, các file view riêng đã được tạo)"



            except Exception as asm_ex:



                res["message"] += f" (Chú ý gộp DWG: {asm_ex})"



        elif isinstance(res, dict) and res.get("success"):



            res["outputFolder"] = target_output_folder







        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})







    # 5. Hành động: Paste Text từ AutoCAD



    elif action == "paste_cad_text":



        import subprocess



        try:



            cmd = [sys.executable, os.path.join(CURRENT_DIR, "paste_cad_text_to_revit.py")]



            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=CURRENT_DIR)



            return jsonify({



                "success": proc.returncode == 0,



                "message": proc.stdout[-500:] if proc.stdout else proc.stderr[-500:]



            })



        except Exception as ex:



            return jsonify({"success": False, "message": str(ex)})







    # 5.5 Kiểm tra mục tiêu đồng bộ Revit & 3ds Max



    elif action == "check_revit_sync_target":



        max_has_sel = False



        max_obj_name = "Family_3dsMax"



        try:



            req_max = urllib.request.Request(



                "http://127.0.0.1:8096/api/execute",



                data=json.dumps({"code": "(if selection.count > 0 then (if selection.count == 1 then selection[1].name else (selection[1].name + \"_group\")) else \"NONE\")"}).encode("utf-8"),



                headers={"Content-Type": "application/json; charset=utf-8"}



            )



            with urllib.request.urlopen(req_max, timeout=3) as res_max:



                d_max = json.loads(res_max.read().decode("utf-8"))



                res_str = str(d_max.get("result", "")).strip().strip('"')



                if res_str and res_str != "NONE":



                    max_has_sel = True



                    max_obj_name = res_str



        except:



            pass







        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        revit_payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.Sync3dsMaxToRevitFamily",



            "methodName": "Run",



            "args": {



                "checkOnly": True



            }



        }



        res_revit = revit_cli.request_json(f"{base_url}/api/execute", revit_payload)







        has_sel = False



        is_fam = False



        fam_name = ""



        elem_cat = ""



        elem_id = 0



        inst_id = 0



        if isinstance(res_revit, dict) and res_revit.get("success"):



            has_sel = bool(res_revit.get("hasSelection"))



            is_fam = bool(res_revit.get("isEditableFamily"))



            fam_name = res_revit.get("familyName", "")



            elem_cat = res_revit.get("category", "")



            elem_id = res_revit.get("elementId", 0)



            inst_id = res_revit.get("instanceId", 0)







        return jsonify({



            "success": True,



            "hasSelection": has_sel,



            "isEditableFamily": is_fam,



            "familyName": fam_name,



            "category": elem_cat,



            "elementId": elem_id,



            "instanceId": inst_id,



            "maxHasSelection": max_has_sel,



            "maxObjectName": max_obj_name



        })







    # 6. Hành động: Đồng bộ 3ds Max



    elif action == "sync_3dsmax":



        import subprocess



        try:



            cmd = [sys.executable, os.path.join(CURRENT_DIR, "sync_max_to_revit.py"), "--no-gui"]



            if data.get("createNewFamily"):



                cmd.append("--create-new")



                if data.get("newFamilyName"):



                    cmd.extend(["--family-name", str(data.get("newFamilyName")).strip()])



            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=CURRENT_DIR)



            return jsonify({



                "success": proc.returncode == 0,



                "message": proc.stdout[-500:] if proc.stdout else proc.stderr[-500:]



            })



        except Exception as ex:



            return jsonify({"success": False, "message": str(ex)})







    # 7. Hành động: Xuất Revit sang 3ds Max dạng Poly sạch (Không chia tam giác)



    elif action == "export_to_3dsmax_poly":



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        file_name = data.get("fileName", "Revit_To_Max_Solids")



        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.ExportRevitToMaxPoly",



            "methodName": "Run",



            "args": {



                "fileName": file_name



            }



        }



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)







        # Nếu Revit xuất thành công, tự động gọi Bridge 3ds Max (Port 8096) nạp và xử lý Editable Poly



        if isinstance(res, dict) and res.get("success"):



            dwg_path = res.get("dwgPath", "")



            escaped_dwg = dwg_path.replace("\\", "\\\\")



            max_code = f"""(



    local dwgFile = "{escaped_dwg}"



    if doesFileExist dwgFile then (



        local oldObjs = for o in objects collect o



        importFile dwgFile #noPrompt



        local newObjs = for o in objects where (findItem oldObjs o == 0) collect o



        for o in newObjs do (



            if isValidNode o and canConvertTo o Editable_Poly do (



                convertToPoly o



                try ( PolyToolsModeling.Quadrify false false ) catch ()



                try ( o.EditablePoly.RemoveInvisibleEdges() ) catch ()



            )



        )



        select newObjs



        max zoomext sel



        "SUCCESS|" + (newObjs.count as string)



    ) else (



        "ERROR|File not found: " + dwgFile



    )



)"""



            max_url = "http://127.0.0.1:8096/api/execute"



            try:



                import urllib.request



                max_req = urllib.request.Request(



                    max_url,



                    data=json.dumps({"language": "maxscript", "code": max_code}).encode("utf-8"),



                    headers={"Content-Type": "application/json"}



                )



                with urllib.request.urlopen(max_req, timeout=15) as max_res:



                    max_data = json.loads(max_res.read().decode("utf-8"))



                    res["maxBridgeResponse"] = max_data



                    res["message"] += " &bull; 3ds Max Bridge đã tự động nạp và làm sạch sang Editable Poly!"



            except Exception as max_ex:



                res["maxBridgeNotice"] = f"Revit đã xuất xong. 3ds Max Bridge chưa kết nối ({max_ex}). Bạn có thể kéo thả file .ms vào 3ds Max."







        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})







    # 8. Hành động: Chuyển Polyline AutoCAD sang Sàn Revit (Smart Replace)



    elif action == "convert_cad_polyline_to_slab":



        import subprocess



        try:



            cmd = [



                sys.executable,



                os.path.join(CURRENT_DIR, "sync_cad_slab_to_revit.py"),



                "--category", str(data.get("floorCategory", "standard")),



                "--thickness", str(data.get("thicknessMm", 100)),



                "--offset", str(data.get("offsetMm", 0)),



                "--level-id", str(data.get("levelId", -1))



            ]



            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45, cwd=CURRENT_DIR)



            out_str = proc.stdout.strip() if proc.stdout else ""



            try:



                fb = out_str.find("{")



                lb = out_str.rfind("}")



                if fb != -1 and lb != -1 and lb > fb:



                    return jsonify(json.loads(out_str[fb:lb+1]))



            except:



                pass



            return jsonify({



                "success": proc.returncode == 0,



                "message": out_str if out_str else proc.stderr.strip()



            })



        except Exception as ex:



            return jsonify({"success": False, "message": str(ex)})







    # 9. Hành động: Đồng bộ Vị trí Cửa các tầng theo Tầng 1 (Trục X hoặc Y)



    elif action == "sync_openings_by_floor1":



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.SyncOpeningsByFloor1",



            "methodName": "Run",



            "args": {



                "category": str(data.get("category", "windows")),



                "axisDirection": str(data.get("axisDirection", "X")),



                "targetAxes": str(data.get("targetAxes", "all")),



                "apply": bool(data.get("apply", True)),



                "toleranceMm": float(data.get("toleranceMm", 1200.0))



            }



        }



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)



        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})







    elif action == "manage_tags":



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.ManageDoorWindowTags",



            "methodName": "Run",



            "args": {



                "subAction": str(data.get("subAction", "set_visibility")),



                "target": str(data.get("target", "all")),



                "viewTarget": str(data.get("viewTarget", "all")),



                "hide": bool(data.get("hide", True))



            }



        }



        res = revit_cli.request_json(f"{base_url}/api/execute", payload)



        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})







    # 11. Hành động: Xuất DWG MEP Coolermaster Phase 2 kèm Tag Cos Cao Độ



    elif action == "export_coolermaster_mep_dwg":



        dll_path = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")



        payload = {



            "action": "execute_dynamic",



            "dllPath": dll_path,



            "typeName": "RevitScript.ExportCoolermasterMepDwg",



            "methodName": "Run",



            "args": {



                "outputDir": data.get("outputDir", r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model\DWG_MEP_Coolermaster_Phase2"),



                "tagElevation": bool(data.get("tagElevation", True)),



                "minSegmentLengthMm": float(data.get("minSegmentLengthMm", 800.0)),



                "trades": data.get("trades", ["chua_chay", "hut_khoi", "thong_gio", "dien_mang_cap", "busway", "bao_khoi"])



            }



        }



        res = revit_cli.request_json(f"{base_url}/api/execute", payload, timeout=7200)



        return jsonify(res if isinstance(res, dict) else {"success": True, "result": res})







    # 12. Hành động: Xử lý CAD - Xóa Hatch Solid & Kéo Leader Cao Độ MEP



    elif action == "cad_mep_polish":



        import mep_cad_operator



        sub_act = data.get("subAction", "full")



        scope = data.get("scope", "active")



        layer = str(data.get("layer", "P-PIPE-CNTR")).strip()



        search_char = str(data.get("searchChar", "+")).strip()



        max_dist = float(data.get("maxDist", 5000.0))



        offset_y = float(data.get("offsetY", 250.0))







        if scope == "active":



            msg = mep_cad_operator.run_on_active_autocad(



                action=sub_act,



                layer=layer,



                search_char=search_char,



                max_dist=max_dist,



                offset_y=offset_y



            )



            success = "SUCCESS" in msg or "Đã gửi lệnh" in msg



            return jsonify({"success": success, "message": msg})







        elif scope == "file":



            file_path = str(data.get("filePath", "")).strip()



            ok, msg = mep_cad_operator.run_on_dwg_file(



                dwg_path=file_path,



                action=sub_act,



                layer=layer,



                search_char=search_char,



                max_dist=max_dist,



                offset_y=offset_y



            )



            return jsonify({"success": ok, "message": msg})







        elif scope == "folder":



            folder_path = str(data.get("folderPath", "")).strip()



            res = mep_cad_operator.run_batch_dwg(



                folder_path=folder_path,



                action=sub_act,



                layer=layer,



                search_char=search_char,



                max_dist=max_dist,



                offset_y=offset_y



            )



            return jsonify(res)







        return jsonify({"success": False, "message": f"Phạm vi scope không hợp lệ: {scope}"})







    # 13. Hành động: Quét / Bóc tách khung tên trong mảng AutoCAD



    elif action == "scan_cad_titleblocks":



        import cad_titleblock_plotter



        scope = data.get("scope", "selection")



        skip_empty = bool(data.get("skipEmpty", True))



        sort_mode = data.get("sortMode", "x_then_y")



        min_ents = int(data.get("minEntities", 1))



        res = cad_titleblock_plotter.scan_titleblocks_in_acad(



            scope=scope,



            skip_empty=skip_empty,



            sort_mode=sort_mode,



            min_entities=min_ents



        )



        return jsonify(res)







    # 14. Hành động: Zoom CAD vào vùng khung tên chỉ định



    elif action == "zoom_cad_region":



        import cad_titleblock_plotter



        xmin = float(data.get("xmin", 0.0))



        ymin = float(data.get("ymin", 0.0))



        xmax = float(data.get("xmax", 0.0))



        ymax = float(data.get("ymax", 0.0))



        ok, msg = cad_titleblock_plotter.zoom_to_region_in_acad(xmin, ymin, xmax, ymax)



        return jsonify({"success": ok, "message": msg})







    # 15. Hành động: Tạo script / In hàng loạt (Batch Plot)



    elif action == "batch_plot_cad":



        import cad_titleblock_plotter



        items = data.get("items", [])



        sub_act = data.get("subAction", "execute") # 'execute' hoặc 'generate_only'



        device = data.get("plotDevice", "DWG To PDF.pc3")



        paper = data.get("paperSize", "ISO_full_bleed_A3_(420.00_x_297.00_MM)")



        style = data.get("plotStyle", "monochrome.ctb")



        out_dir = data.get("outputDir", None)



        



        if sub_act == "generate_only":



            script_path, out_dir = cad_titleblock_plotter.generate_batch_plot_script(



                items=items,



                plot_device=device,



                paper_size=paper,



                plot_style=style,



                output_dir=out_dir



            )



            return jsonify({



                "success": True,



                "message": f"Đã tạo mã LISP in hàng loạt {len(items)} bản vẽ tại: {script_path}",



                "scriptPath": script_path,



                "outputDir": out_dir



            })



        else:



            res = cad_titleblock_plotter.execute_batch_plot_in_acad(



                items=items,



                plot_device=device,



                paper_size=paper,



                plot_style=style,



                output_dir=out_dir



            )



            return jsonify(res)







    # 16. Hành động: Nạp LISP vào AutoCAD



    elif action == "load_cad_lisp":



        import cadlib_lisp_manager



        file_path = str(data.get("filePath", "")).strip()



        ok, msg = cadlib_lisp_manager.load_lisp_into_acad(file_path)



        return jsonify({"success": ok, "message": msg})







    return jsonify({"success": False, "message": f"Hành động không xác định: {action}"})











if __name__ == '__main__':



    default_port = int(os.environ.get("DASHBOARD_PORT", 5000))



    port = default_port



    



    import socket



    def is_port_in_use(p):



        try:



            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:



                s.settimeout(0.5)



                return s.connect_ex(('127.0.0.1', p)) == 0



        except Exception:



            return False







    if "WERKZEUG_RUN_MAIN" not in os.environ and is_port_in_use(port) and "DASHBOARD_PORT" not in os.environ:



        for candidate in [5000, 5005, 5050, 8080]:



            if not is_port_in_use(candidate):



                port = candidate



                break







    print(f"==================================================")



    print(f" RevitAI Automation Hub Dashboard khởi chạy tại:")



    print(f" -> http://127.0.0.1:{port}")



    print(f" -> Chế độ Hot-Reload (debug=True, use_reloader=True): BẬT")



    print(f"==================================================")







    app.config['TEMPLATES_AUTO_RELOAD'] = True



    watch_files = [



        os.path.join(CURRENT_DIR, 'etabs_hub.js'),



        os.path.join(CURRENT_DIR, 'etabs_beam_data.json'),



        os.path.join(CURRENT_DIR, 'etabs_service.py'),



        os.path.join(CURRENT_DIR, 'cad_3d_hub.js'),



        os.path.join(CURRENT_DIR, 'cad_3d_service.py'),



        os.path.join(CURRENT_DIR, 'sketchup_ruby_engine.py'),



        os.path.join(CURRENT_DIR, 'static', 'ruby_3d_hub.js'),



    ]



    extra_files = [f for f in watch_files if os.path.exists(f)]







    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False, threaded=True)



