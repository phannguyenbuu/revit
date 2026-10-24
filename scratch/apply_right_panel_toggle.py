import re
import sys

def apply():
    with open('web_dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update Right Panel <aside>
    aside_target = '<aside class="col-span-12 lg:col-span-3 xl:col-span-3 space-y-3.5">'
    if aside_target not in content:
        print("ERROR: aside_target for colRightPanel not found")
        return False
    aside_replacement = '<aside id="colRightPanel" class="col-span-12 lg:col-span-3 xl:col-span-3 space-y-3.5 relative transition-all duration-200">'
    content = content.replace(aside_target, aside_replacement, 1)

    # 2. Add btnEdgeCollapseRight to the first card in Right Panel
    card_target = '<div class="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-950 text-white border border-indigo-500/40 rounded-2xl p-3.5 shadow-lg shadow-indigo-950/30 space-y-2.5 relative overflow-hidden group">'
    if card_target not in content:
        print("ERROR: card_target for Right Panel not found")
        return False
    card_replacement = '''<div class="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-950 text-white border border-indigo-500/40 rounded-2xl p-3.5 shadow-lg shadow-indigo-950/30 space-y-2.5 relative overflow-hidden group">

          <!-- Nút Edge Toggle ép sát mép trong Right Panel (Border Seam Arrow Right) -->
          <button type="button" id="btnEdgeCollapseRight" onclick="toggleRightPanel(false)" class="hidden lg:flex absolute -left-3 top-5 z-20 w-6 h-6 rounded-full bg-white border border-slate-200 shadow-sm hover:shadow-md text-slate-500 hover:text-indigo-600 hover:border-indigo-400 items-center justify-center cursor-pointer transition-all hover:scale-110 group/btn" title="Thu gọn lề phải (Arrow Right)">
            <i data-lucide="chevron-right" class="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform text-slate-700"></i>
          </button>'''
    content = content.replace(card_target, card_replacement, 1)

    # 3. Add btnCollapseRightHeader in the header of the top card in Right Panel
    header_right_target = '<span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30 flex items-center gap-1">\n\n\n\n              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 103 Dầm\n\n\n\n            </span>'
    header_right_target_crlf = '<span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30 flex items-center gap-1">\r\n\r\n\r\n\r\n              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 103 Dầm\r\n\r\n\r\n\r\n            </span>'

    badge_replacement = '''<div class="flex items-center gap-1.5 shrink-0">
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 103 Dầm
              </span>
              <!-- Nút Thu Gọn Header Arrow Right ép sát mép trong -->
              <button type="button" id="btnCollapseRightHeader" onclick="toggleRightPanel(false)" class="p-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-300 hover:text-white transition cursor-pointer shrink-0 border border-white/10 shadow-xs flex items-center justify-center w-6 h-6" title="Thu gọn lề phải (Arrow Right)">
                <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
              </button>
            </div>'''

    if header_right_target_crlf in content:
        content = content.replace(header_right_target_crlf, badge_replacement, 1)
    elif header_right_target in content:
        content = content.replace(header_right_target, badge_replacement, 1)
    else:
        # Regex replacement
        m = re.search(r'<span class="text-\[10px\] px-2 py-0\.5 rounded-full bg-emerald-500/20.*?103 Dầm\s*</span>', content, re.DOTALL)
        if not m:
            print("ERROR: 103 Dầm badge target not found")
            return False
        content = content[:m.start()] + badge_replacement + content[m.end():]

    # 4. Update sticky buttons after </header> to add btnStickyExpandRight
    sticky_left_target = 'id="btnStickyExpandLeft"'
    idx_sticky = content.find(sticky_left_target)
    if idx_sticky == -1:
        print("ERROR: btnStickyExpandLeft not found")
        return False
    end_sticky = content.find('</button>', idx_sticky) + 9

    sticky_right_btn = '''\n\n  <!-- Floating Sticky Expand Button cho Right Panel (Arrow Left) -->
  <button type="button" id="btnStickyExpandRight" onclick="toggleRightPanel(true)" class="hidden fixed right-0 top-36 z-50 bg-white/95 backdrop-blur-xs hover:bg-indigo-50 border border-r-0 border-slate-300 hover:border-indigo-400 rounded-l-xl px-1.5 py-3 shadow-lg cursor-pointer flex flex-col items-center gap-1 text-slate-600 hover:text-indigo-600 group transition-all" title="Mở lề phải AEC Hub & Console (Arrow Left)">
    <i data-lucide="chevron-left" class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform"></i>
    <span class="text-[9px] font-bold text-slate-500 group-hover:text-indigo-600 [writing-mode:vertical-lr] tracking-wider uppercase">Hub</span>
  </button>'''

    content = content[:end_sticky] + sticky_right_btn + content[end_sticky:]

    # 5. Update Center Workspace header buttons (btnEdgeExpandRight and unified panelExpandBar)
    sec_old_block = re.search(
        r'<button type="button" id="btnEdgeExpandLeft".*?<!-- Top Expand Bar khi Left Panel bị thu gọn -->\s*<div id="leftPanelExpandBar".*?</div>',
        content,
        re.DOTALL
    )
    if not sec_old_block:
        print("ERROR: sec_old_block in colCenterWorkspace not found")
        return False

    sec_new_block = '''<!-- Nút Edge Toggle Mở Rộng Left Panel (Border Seam Arrow Right khi Left Panel bị thu gọn) -->
        <button type="button" id="btnEdgeExpandLeft" onclick="toggleLeftPanel(true)" class="hidden absolute -left-3 top-5 z-20 w-6 h-6 rounded-full bg-indigo-600 border border-indigo-700 shadow-md hover:bg-indigo-700 text-white items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Mở rộng danh mục (Arrow Right)">
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform"></i>
        </button>

        <!-- Nút Edge Toggle Mở Rộng Right Panel (Border Seam Arrow Left khi Right Panel bị thu gọn) -->
        <button type="button" id="btnEdgeExpandRight" onclick="toggleRightPanel(true)" class="hidden absolute -right-3 top-5 z-20 w-6 h-6 rounded-full bg-indigo-600 border border-indigo-700 shadow-md hover:bg-indigo-700 text-white items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Mở rộng lề phải (Arrow Left)">
          <i data-lucide="chevron-left" class="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform"></i>
        </button>

        <!-- Top Expand Bar khi Left hoặc Right Panel bị thu gọn -->
        <div id="panelExpandBar" class="hidden items-center justify-between bg-white border border-slate-200/80 rounded-2xl px-3.5 py-2 shadow-xs transition-all gap-2 flex-wrap mb-1">
          <div class="flex items-center gap-2">
            <!-- Nút Mở Left Panel -->
            <button type="button" id="btnBarExpandLeft" onclick="toggleLeftPanel(true)" class="hidden items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs cursor-pointer transition-all hover:shadow group">
              <i data-lucide="chevron-right" class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"></i>
              <span>Mở Danh Mục Công Cụ</span>
            </button>
            <span id="panelExpandBarSubtitle" class="text-xs text-slate-500 hidden sm:inline">12 AEC Tools • 433 CAD Files • 1,205 Maxscripts</span>
          </div>

          <div class="flex items-center gap-2 ml-auto">
            <span id="workspaceSpanBadge" class="text-[11px] text-indigo-700 font-semibold bg-indigo-50 border border-indigo-100 rounded-lg px-2 py-0.5 hidden md:inline">Không gian mở rộng (9 Cột)</span>
            <!-- Nút Mở Right Panel -->
            <button type="button" id="btnBarExpandRight" onclick="toggleRightPanel(true)" class="hidden items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-xs cursor-pointer transition-all hover:shadow group">
              <span>Mở Lề Phải (Hub & Console)</span>
              <i data-lucide="chevron-left" class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform"></i>
            </button>
          </div>
        </div>
        <div id="leftPanelExpandBar" class="hidden"></div>'''

    content = content[:sec_old_block.start()] + sec_new_block + content[sec_old_block.end():]

    # 6. Update JavaScript code for Left and Right Panel toggle & layout management
    js_old_block = re.search(
        r'// ====================================================================\s*// LEFT PANEL COLLAPSE / EXPAND TOGGLE.*?(?=</script>)',
        content,
        re.DOTALL
    )
    if not js_old_block:
        print("ERROR: js_old_block not found")
        return False

    js_new_block = '''// ====================================================================
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
      if (localStorage.getItem('revitai_left_panel_collapsed') === '1') {
        const colLeft = document.getElementById('colLeftPanel');
        if (colLeft) colLeft.classList.add('hidden');
      }
      if (localStorage.getItem('revitai_right_panel_collapsed') === '1') {
        const colRight = document.getElementById('colRightPanel');
        if (colRight) colRight.classList.add('hidden');
      }
      updateLayoutGrid();
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

'''

    content = content[:js_old_block.start()] + js_new_block + content[js_old_block.end():]

    with open('web_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: web_dashboard.py updated with Right Panel collapse/expand!")
    return True

if __name__ == '__main__':
    apply()
