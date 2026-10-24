# -*- coding: utf-8 -*-
"""
etabs_ui.py
UI Components for ETABS Structural AI Hub in RevitAI Dashboard:
1. Right-panel trigger card
2. Active Workspace tab (Middle page)
3. Fullscreen Modal
4. 2D True-Width Framing Plan Viewer (Canvas)
5. 3D Solid Cross-Section Model (Three.js)
6. TCVN 5574-2012 Rebar Table & Selection
"""

ETABS_RIGHT_PANEL_CARD = """
        <!-- ==================================================================== -->
        <!-- PANEL: ETABS STRUCTURAL AI HUB (HỒ SƠ DẦM & CỐT THÉP)                 -->
        <!-- ==================================================================== -->
        <div class="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-950 text-white border border-indigo-500/40 rounded-2xl p-3.5 shadow-lg shadow-indigo-950/30 space-y-2.5 relative overflow-hidden group">
          <div class="absolute -right-6 -bottom-6 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl pointer-events-none"></div>
          
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-1.5">
              <i data-lucide="layers" class="w-4 h-4 text-cyan-400"></i> ETABS AI Hub
            </span>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 103 Dầm
            </span>
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
        </div>
"""

ETABS_WORKSPACE_TAB = """
        <!-- ==================================================================== -->
        <!-- TAB CONTENT: ETABS STRUCTURAL AI HUB (ACTIVE WORKSPACE - TRANG GIỮA) -->
        <!-- ==================================================================== -->
        <div id="tab-etabs-hub" class="tab-content hidden bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-5">
          
          <!-- Header Bar -->
          <div class="border-b border-slate-100 pb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="flex items-center gap-2">
                <span class="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
                  <i data-lucide="layers" class="w-5 h-5"></i>
                </span>
                <div>
                  <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">
                    Hồ Sơ Kết Cấu Dầm & Cốt Thép ETABS
                    <span class="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">TCVN 5574-2012</span>
                  </h2>
                  <p class="text-xs text-slate-500 mt-0.5">Model: <span class="font-mono font-semibold text-slate-700">CAI_TAO_PHUONG_AN_B.EDB</span> (103 Dầm • 56 Cột • 5 Tầng)</p>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-2">
              <button onclick="refreshEtabsDataLive()" id="btnRefreshEtabs" class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs flex items-center gap-1.5 transition cursor-pointer" title="Làm mới lại dữ liệu trực tiếp từ ETABS">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-indigo-600"></i> Làm mới EDB
              </button>
              <button onclick="openEtabsHub('modal')" class="py-1.5 px-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center gap-1.5 border border-indigo-200 transition cursor-pointer" title="Phóng to Modal toàn màn hình">
                <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Phóng to Modal
              </button>
            </div>
          </div>

          <!-- 3-Way Segmented Switch Tab Bar -->
          <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
            <div class="inline-flex p-1.5 bg-slate-200/80 rounded-2xl border border-slate-300/80 shadow-inner gap-1">
              <button onclick="switchEtabsSubTab('etabs-2d')" id="subtab-btn-2d" class="etabs-subtab-btn py-2 px-4 rounded-xl font-bold text-xs flex items-center gap-2 bg-indigo-600 text-white shadow-md shadow-indigo-600/25 transition-all duration-150 cursor-pointer">
                <i data-lucide="map" class="w-4 h-4"></i> (1) Mặt Bằng Dầm 2D Đúng Bề Rộng
              </button>
              <button onclick="switchEtabsSubTab('etabs-3d')" id="subtab-btn-3d" class="etabs-subtab-btn py-2 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer">
                <i data-lucide="box" class="w-4 h-4"></i> (2) Model 3D Đúng Tiết Diện
              </button>
              <button onclick="switchEtabsSubTab('etabs-rebar')" id="subtab-btn-rebar" class="etabs-subtab-btn py-2 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 text-slate-600 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer">
                <i data-lucide="table-2" class="w-4 h-4"></i> (3) Bảng Cốt Thép & Chọn Thép
              </button>
            </div>

            <div class="hidden sm:flex items-center gap-2 text-xs text-slate-500 font-medium">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span class="font-mono">CAI_TAO_PHUONG_AN_B.EDB (103 Dầm • 56 Cột)</span>
            </div>
          </div>

          <!-- SUB-PANE 1: MẶT BẰNG DẦM 2D (ĐÚNG BỀ RỘNG DẦM + TEXT TIẾT DIỆN) -->
          <div id="subpane-etabs-2d" class="etabs-subpane space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
              <div class="flex items-center gap-3">
                <label class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <i data-lucide="layers" class="w-3.5 h-3.5 text-indigo-600"></i> Chọn tầng xem mặt bằng:
                </label>
                <select id="etabs2DStorySelect" onchange="renderEtabs2DPlan()" class="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-bold text-indigo-900 focus:outline-none focus:ring-1 focus:ring-indigo-600 cursor-pointer shadow-sm">
                  <option value="T4">04. Tầng 4 / Sân Thượng (Z = 15.6m)</option>
                  <option value="T3">03. Tầng 3 (Z = 11.8m)</option>
                  <option value="T2">02. Tầng 2 (Z = 7.6m)</option>
                  <option value="T1">01. Tầng 1 (Z = 1.8m)</option>
                  <option value="TM">05. Tầng Mái Tum (Z = 19.4m)</option>
                </select>
              </div>

              <!-- Controls -->
              <div class="flex items-center gap-2">
                <button onclick="zoomEtabs2D(1.2)" class="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold" title="Phóng to">
                  <i data-lucide="zoom-in" class="w-4 h-4"></i>
                </button>
                <button onclick="zoomEtabs2D(0.8)" class="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold" title="Thu nhỏ">
                  <i data-lucide="zoom-out" class="w-4 h-4"></i>
                </button>
                <button onclick="resetEtabs2DView()" class="py-1.5 px-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold flex items-center gap-1" title="Vừa màn hình">
                  <i data-lucide="maximize" class="w-3.5 h-3.5"></i> Vừa khung
                </button>
                <label class="flex items-center gap-1.5 text-xs font-medium text-slate-700 ml-2 cursor-pointer">
                  <input type="checkbox" id="chkShow2DLabels" checked onchange="renderEtabs2DPlan()" class="rounded border-slate-300 text-indigo-600 focus:ring-0"> Hiện nhãn tiết diện
                </label>
              </div>
            </div>

            <!-- 2D Canvas Container -->
            <div class="relative w-full h-[540px] bg-[#aaaaaa] rounded-2xl overflow-hidden border border-slate-400 shadow-inner">
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
                  <div class="flex items-center gap-2"><span class="w-4 h-2 bg-sky-500 rounded-sm shrink-0"></span> Dầm BTCT (Vẽ đúng bề rộng 200/250/300mm)</div>
                  <div class="flex items-center gap-2"><span class="w-3 h-3 bg-slate-700 rounded-sm shrink-0"></span> Cột BTCT (Đúng kích thước thực)</div>
                  <div class="flex items-center gap-2"><span class="w-4 h-0.5 border-t border-dashed border-emerald-600 shrink-0"></span> Lưới trục kiến trúc (1-7, A-C)</div>
                </div>
              </div>

              <!-- Beam hover tooltip -->
              <div id="etabs2DTooltip" class="absolute hidden bg-slate-900/95 text-white border border-indigo-400 text-xs rounded-xl p-2.5 shadow-xl pointer-events-none z-10 space-y-1"></div>
            </div>
          </div>

          <!-- SUB-PANE 2: MODEL 3D ĐÚNG TIẾT DIỆN (THREE.JS SOLID BOXES) -->
          <div id="subpane-etabs-3d" class="etabs-subpane hidden space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
              <div class="flex items-center gap-3">
                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <i data-lucide="box" class="w-3.5 h-3.5 text-indigo-600"></i> Điều khiển 3D:
                </span>
                <span class="text-[11px] text-slate-500">Chuột trái: Xoay 360° • Lăn chuột: Phóng to/nhỏ • Chuột phải: Dời hình • Bấm vào dầm: Chọn cốt thép</span>
              </div>
            </div>

            <!-- 3D Three.js Container -->
            <div class="relative w-full h-[580px] bg-[#aaaaaa] rounded-2xl overflow-hidden border border-slate-400 shadow-inner group">
              <div id="etabs3DContainer" class="w-full h-full"></div>
              
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
                  <i data-lucide="send" class="w-3.5 h-3.5 text-amber-200"></i> Deploy
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
              </div>

              <!-- Export Buttons -->
              <div class="flex items-center gap-2">
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

        </div>

        <!-- ==================================================================== -->
        <!-- ==================================================================== -->
        <!-- MODAL: CHI TIẾT BẢN VẼ DẦM, MẶT CẮT NGANG/DỌC & DẦM LIÊN TỤC         -->
        <!-- ==================================================================== -->
        <div id="beamRebarModal" class="fixed inset-0 z-50 bg-slate-900/75 backdrop-blur-sm hidden flex items-center justify-center p-2 sm:p-4">
          <div class="bg-white text-slate-800 w-full max-w-5xl rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-300 animate-in fade-in zoom-in-95 duration-150 max-h-[94vh]">
            
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

              <div class="flex items-center gap-2.5">
                <!-- Segmented View Switcher -->
                <div class="inline-flex p-1 bg-slate-200/90 rounded-2xl border border-slate-300 gap-1 text-xs shadow-inner">
                  <button id="btnBrmModeSpan" onclick="setBeamDrawingMode('span')" class="px-3 py-1 rounded-xl font-bold bg-white text-indigo-700 shadow-sm transition">
                    Mặt Cắt Nhịp Đang Chọn
                  </button>
                  <button id="btnBrmModeChain" onclick="setBeamDrawingMode('chain')" class="px-3 py-1 rounded-xl font-semibold text-slate-600 hover:text-slate-900 transition flex items-center gap-1">
                    Dầm Dài Liên Tục <span id="brmChainCountBadge" class="px-1.5 py-0.2 bg-indigo-100 text-indigo-800 rounded-full text-[10px] font-bold">4 nhịp</span>
                  </button>
                </div>

                <button onclick="closeBeamRebarModal()" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition cursor-pointer" title="Đóng">
                  <i data-lucide="x" class="w-5 h-5"></i>
                </button>
              </div>
            </div>

            <!-- Modal Body (Scrollable) -->
            <div class="p-3.5 sm:p-4 space-y-3 overflow-y-auto flex-1 bg-slate-50/50">

              <!-- Continuous Chain Breadcrumbs Bar -->
              <div class="p-2 bg-white rounded-2xl border border-slate-200 flex items-center justify-between gap-2 shadow-xs text-xs">
                <div class="flex items-center gap-1.5 overflow-x-auto py-0.5 flex-1" id="brmChainBreadcrumbs">
                  <!-- Rendered by JS -->
                </div>
                <span class="text-[10px] text-slate-400 font-medium whitespace-nowrap hidden sm:inline">Click để chuyển nhịp</span>
              </div>

              <!-- Canvas CAD Drawing Container -->
              <div class="relative bg-white rounded-2xl border border-slate-300 shadow-xs overflow-hidden">
                <canvas id="brmDrawingCanvas" class="w-full h-[370px] block cursor-pointer"></canvas>
                <div class="absolute top-2 right-2 flex items-center gap-1.5 bg-white/95 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-slate-200 text-[10px] text-slate-600 font-medium shadow-xs pointer-events-none">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span id="brmCanvasLegend">Mặt cắt dọc nhịp & 3 mặt cắt ngang (1-1, 2-2, 3-3)</span>
                </div>
              </div>

              <!-- Moments & Req As Cards -->
              <div class="grid grid-cols-3 gap-2.5">
                <div class="bg-rose-50/80 border border-rose-200 rounded-2xl p-2.5 text-center shadow-xs">
                  <div class="text-[10px] font-bold uppercase text-rose-700 tracking-wider">Gối Trái (Môn. Âm)</div>
                  <div id="brmMLeft" class="text-sm font-bold text-rose-900 font-mono mt-0.5">-28.5 kNm</div>
                  <div class="text-[11px] text-slate-600 mt-0.5">As yc: <strong id="brmAsLeftReq" class="text-rose-700 font-mono">2.55 cm²</strong></div>
                </div>
                <div class="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-2.5 text-center shadow-xs">
                  <div class="text-[10px] font-bold uppercase text-emerald-700 tracking-wider">Nhịp Giữa (Môn. Dương)</div>
                  <div id="brmMMid" class="text-sm font-bold text-emerald-900 font-mono mt-0.5">+24.4 kNm</div>
                  <div class="text-[11px] text-slate-600 mt-0.5">As yc: <strong id="brmAsMidReq" class="text-emerald-700 font-mono">2.18 cm²</strong></div>
                </div>
                <div class="bg-rose-50/80 border border-rose-200 rounded-2xl p-2.5 text-center shadow-xs">
                  <div class="text-[10px] font-bold uppercase text-rose-700 tracking-wider">Gối Phải (Môn. Âm)</div>
                  <div id="brmMRight" class="text-sm font-bold text-rose-900 font-mono mt-0.5">-30.2 kNm</div>
                  <div class="text-[11px] text-slate-600 mt-0.5">As yc: <strong id="brmAsRightReq" class="text-rose-700 font-mono">2.70 cm²</strong></div>
                </div>
              </div>

              <!-- Rebar Selection Inputs -->
              <div class="bg-white border border-slate-200 rounded-2xl p-3.5 space-y-2.5 shadow-xs">
                <div class="flex items-center justify-between pb-1.5 border-b border-slate-100">
                  <h4 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <i data-lucide="layers" class="w-4 h-4 text-indigo-600"></i> Bố Trí Thép Dầm & Kiểm Tra TCVN:
                  </h4>
                  <span class="text-[10px] text-slate-400">Thay đổi dropdown sẽ cập nhật bản vẽ tức thì</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  <!-- Gối Trái -->
                  <div class="flex items-center justify-between gap-2 bg-slate-50 p-2 rounded-xl border border-slate-200/80">
                    <label class="text-xs font-semibold text-slate-700 w-24">Thép Gối Trái:</label>
                    <select id="brmSelLeft" onchange="onRebarSelectChange()" class="flex-1 bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-mono font-bold text-indigo-950 focus:outline-none focus:ring-2 focus:ring-indigo-600 cursor-pointer shadow-xs"></select>
                    <span id="brmStatusLeft" class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 whitespace-nowrap">Đạt</span>
                  </div>

                  <!-- Gối Phải -->
                  <div class="flex items-center justify-between gap-2 bg-slate-50 p-2 rounded-xl border border-slate-200/80">
                    <label class="text-xs font-semibold text-slate-700 w-24">Thép Gối Phải:</label>
                    <select id="brmSelRight" onchange="onRebarSelectChange()" class="flex-1 bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-mono font-bold text-indigo-950 focus:outline-none focus:ring-2 focus:ring-indigo-600 cursor-pointer shadow-xs"></select>
                    <span id="brmStatusRight" class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 whitespace-nowrap">Đạt</span>
                  </div>

                  <!-- Nhịp Giữa -->
                  <div class="flex items-center justify-between gap-2 bg-slate-50 p-2 rounded-xl border border-slate-200/80">
                    <label class="text-xs font-semibold text-slate-700 w-24">Thép Bụng Nhịp:</label>
                    <select id="brmSelMid" onchange="onRebarSelectChange()" class="flex-1 bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-mono font-bold text-indigo-950 focus:outline-none focus:ring-2 focus:ring-indigo-600 cursor-pointer shadow-xs"></select>
                    <span id="brmStatusMid" class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 whitespace-nowrap">Đạt</span>
                  </div>

                  <!-- Cốt Đai -->
                  <div class="flex items-center justify-between gap-2 bg-slate-50 p-2 rounded-xl border border-slate-200/80">
                    <label class="text-xs font-semibold text-slate-700 w-24">
                      Cốt Đai:
                      <span class="block text-[9px] text-slate-400 font-normal">Y/c: <span id="brmShearReq">5.75 cm²/m</span></span>
                    </label>
                    <select id="brmSelStirrup" onchange="onRebarSelectChange()" class="flex-1 bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-mono font-bold text-indigo-950 focus:outline-none focus:ring-2 focus:ring-indigo-600 cursor-pointer shadow-xs"></select>
                    <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-sky-100 text-sky-800 border border-sky-300 whitespace-nowrap">TCVN Đạt</span>
                  </div>
                </div>
              </div>

            </div>

            <!-- Modal Footer -->
            <div class="p-3.5 bg-slate-100 border-t border-slate-200 flex items-center justify-between">
              <button onclick="closeBeamRebarModal()" class="py-2 px-4 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs transition cursor-pointer">
                Đóng
              </button>
              <button onclick="saveBeamRebarSelection()" class="py-2 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-md shadow-indigo-600/30 transition active:scale-95 cursor-pointer">
                <i data-lucide="check" class="w-4 h-4"></i> Lưu Cốt Thép Dầm
              </button>
            </div>

          </div>
        </div>
"""


ETABS_FULLSCREEN_MODAL = """
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
            <button onclick="switchEtabsModalTab('modal-rebar')" id="modal-tabbtn-rebar" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition">Bảng Thép TCVN</button>
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
            <div class="flex items-center gap-2 text-xs font-bold text-slate-700">
              <span>Chọn Tầng:</span>
              <select id="modal2DStorySelect" onchange="renderModal2DPlan()" class="bg-white border border-slate-300 rounded-lg px-3 py-1 font-bold text-indigo-900 cursor-pointer">
                <option value="T4">04. Tầng 4 / Sân Thượng (Z = 15.6m)</option>
                <option value="T3">03. Tầng 3 (Z = 11.8m)</option>
                <option value="T2">02. Tầng 2 (Z = 7.6m)</option>
                <option value="T1">01. Tầng 1 (Z = 1.8m)</option>
                <option value="TM">05. Tầng Mái Tum (Z = 19.4m)</option>
              </select>
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
        </div>
      </div>

    </div>
  </div>
"""
