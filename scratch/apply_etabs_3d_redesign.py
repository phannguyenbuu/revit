import re
import sys

def run():
    with open('web_dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # ---------------------------------------------------------
    # 1. REMOVE panelExpandBar (Image 1 BỎ)
    # ---------------------------------------------------------
    bar_match = re.search(r'<!-- Top Expand Bar khi Left hoặc Right Panel bị thu gọn -->\s*<div id="panelExpandBar".*?</div>\s*<div id="leftPanelExpandBar" class="hidden"></div>', content, re.DOTALL)
    if bar_match:
        content = content[:bar_match.start()] + '<div id="leftPanelExpandBar" class="hidden"></div>' + content[bar_match.end():]
        print("1. Removed panelExpandBar successfully (Hình 1 đã bỏ).")
    else:
        # Fallback if different formatting
        bar_match2 = re.search(r'<div id="panelExpandBar".*?</div>\s*<div id="leftPanelExpandBar" class="hidden"></div>', content, re.DOTALL)
        if bar_match2:
            content = content[:bar_match2.start()] + '<div id="leftPanelExpandBar" class="hidden"></div>' + content[bar_match2.end():]
            print("1. Removed panelExpandBar (fallback).")
        else:
            print("WARNING: panelExpandBar not found for removal")

    # ---------------------------------------------------------
    # 2. RESTRUCTURE tab-etabs-hub:
    #    - Move canvas 3D to the top (subpane-etabs-3d active by default)
    #    - Move header + tabs below into a clean 2-column deck
    # ---------------------------------------------------------
    # Find start of tab-etabs-hub
    hub_start_marker = '<div id="tab-etabs-hub"'
    hub_idx = content.find(hub_start_marker)
    if hub_idx == -1:
        print("ERROR: tab-etabs-hub not found")
        return False

    # Find the start of the old header bar: <!-- Header Bar -->
    header_bar_marker = '<!-- Header Bar -->'
    header_idx = content.find(header_bar_marker, hub_idx)
    if header_idx == -1:
        print("ERROR: <!-- Header Bar --> not found")
        return False

    # Find the start of the subpanes: <!-- SUB-PANE 1: MẶT BẰNG DẦM 2D
    subpane1_marker = '<!-- SUB-PANE 1: MẶT BẰNG DẦM 2D'
    subpane1_idx = content.find(subpane1_marker, header_idx)
    if subpane1_idx == -1:
        print("ERROR: <!-- SUB-PANE 1: MẶT BẰNG DẦM 2D not found")
        return False

    # The block to be moved down is content[header_idx:subpane1_idx]
    # We will remove this block from the top and replace with nothing
    content = content[:header_idx] + content[subpane1_idx:]

    # Now make subpane-etabs-3d visible by default, and subpane-etabs-2d hidden by default
    subpane2d_old = '<div id="subpane-etabs-2d" class="etabs-subpane space-y-3">'
    subpane2d_new = '<div id="subpane-etabs-2d" class="etabs-subpane hidden space-y-3">'
    content = content.replace(subpane2d_old, subpane2d_new, 1)

    subpane3d_old = '<div id="subpane-etabs-3d" class="etabs-subpane hidden space-y-3">'
    subpane3d_new = '<div id="subpane-etabs-3d" class="etabs-subpane space-y-3">'
    content = content.replace(subpane3d_old, subpane3d_new, 1)

    # Now define the new 2-Column Control Deck to place at the bottom of tab-etabs-hub
    two_col_deck = '''
          <!-- ==================================================================== -->
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
'''
    # Find the end of tab-etabs-hub before TAB CONTENT 1: CHỌN THEO TRỤC
    tab_grid_marker = '<!-- TAB CONTENT 1: CHỌN THEO TRỤC -->'
    tab_grid_idx = content.find(tab_grid_marker)
    if tab_grid_idx == -1:
        print("ERROR: TAB CONTENT 1: CHỌN THEO TRỤC not found")
        return False

    # Find the last </div> before tab_grid_marker
    close_hub_div = content.rfind('</div>', 0, tab_grid_idx)
    if close_hub_div == -1:
        print("ERROR: close_hub_div not found")
        return False

    # Insert two_col_deck before close_hub_div
    content = content[:close_hub_div] + two_col_deck + '\n\n        ' + content[close_hub_div:]
    print("2. Moved 3D canvas to top and placed 2-column control deck at the bottom.")

    # ---------------------------------------------------------
    # 3. ADD FLASK ROUTES FOR /3d, /modal-3d, /etabs-3d
    # ---------------------------------------------------------
    route_target = "@app.route('/')\n\n\n\ndef index():"
    route_target_crlf = "@app.route('/')\r\n\r\n\r\n\r\ndef index():"
    
    new_routes = """@app.route('/')
@app.route('/3d')
@app.route('/modal-3d')
@app.route('/etabs-3d')
@app.route('/structure-3d')
def index():"""

    if route_target_crlf in content:
        content = content.replace(route_target_crlf, new_routes, 1)
        print("3. Added Flask routes for /3d, /modal-3d, /etabs-3d (CRLF).")
    elif route_target in content:
        content = content.replace(route_target, new_routes, 1)
        print("3. Added Flask routes for /3d, /modal-3d, /etabs-3d (LF).")
    else:
        # Regex replacement
        m = re.search(r"@app\.route\('/'\)\s*def index\(\):", content)
        if m:
            content = content[:m.start()] + new_routes + content[m.end():]
            print("3. Added Flask routes via regex.")
        else:
            print("ERROR: @app.route('/') not found")
            return False

    # ---------------------------------------------------------
    # 4. UPDATE CLIENT-SIDE JAVASCRIPT:
    #    - Detect /3d route and default Left & Right panel to MINIMIN (hidden)
    #    - Auto-activate ETABS Hub & 3D view
    # ---------------------------------------------------------
    js_init_target = re.search(
        r'// Restore Left & Right Panel state on initial load.*?updateLayoutGrid\(\);\s*}\s*catch\(e\)\s*\{\}',
        content,
        re.DOTALL
    )
    if not js_init_target:
        print("ERROR: js_init_target not found")
        return False

    new_js_init = '''// Restore Left & Right Panel state on initial load
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
    } catch(e) {}'''

    content = content[:js_init_target.start()] + new_js_init + content[js_init_target.end():]
    print("4. Updated client-side JS for 3D route detection and minimin panel defaults.")

    with open('web_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("ALL 3 REQUIREMENTS APPLIED TO web_dashboard.py SUCCESSFULLY!")
    return True

if __name__ == '__main__':
    run()
