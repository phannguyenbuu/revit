import re
import sys

def apply():
    with open('web_dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update <aside class="col-span-12 lg:col-span-4 xl:col-span-3 space-y-3.5">
    aside_target = '<aside class="col-span-12 lg:col-span-4 xl:col-span-3 space-y-3.5">'
    if aside_target not in content:
        print("ERROR: aside_target not found")
        return False
    
    aside_replacement = '<aside id="colLeftPanel" class="col-span-12 lg:col-span-4 xl:col-span-3 space-y-3.5 relative transition-all duration-200">'
    content = content.replace(aside_target, aside_replacement, 1)

    # 2. Add relative to the first div inside aside and add btnEdgeCollapseLeft
    div_target = '<div class="bg-white border border-slate-200 rounded-2xl p-3.5 shadow-sm">'
    if div_target not in content:
        print("ERROR: div_target not found")
        return False

    div_replacement = '''<div class="bg-white border border-slate-200 rounded-2xl p-3.5 shadow-sm relative">

          <!-- Nút Edge Toggle ép sát mép trong (Border Seam Arrow Left) -->
          <button type="button" id="btnEdgeCollapseLeft" onclick="toggleLeftPanel(false)" class="hidden lg:flex absolute -right-3 top-5 z-20 w-6 h-6 rounded-full bg-white border border-slate-200 shadow-sm hover:shadow-md text-slate-500 hover:text-indigo-600 hover:border-indigo-400 items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Thu gọn danh mục (Arrow Left)">
            <i data-lucide="chevron-left" class="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform"></i>
          </button>'''
    content = content.replace(div_target, div_replacement, 1)

    # 3. Update tabs header to include flex items-center justify-between and btnCollapseLeftHeader
    tabs_target = '<div class="border-b border-slate-100 pb-2.5 mb-3">\n\n\n\n            <div class="flex items-center bg-slate-100 p-1 rounded-xl gap-1">'
    crlf_tabs_target = '<div class="border-b border-slate-100 pb-2.5 mb-3">\r\n\r\n\r\n\r\n            <div class="flex items-center bg-slate-100 p-1 rounded-xl gap-1">'
    
    if crlf_tabs_target in content:
        tabs_found = crlf_tabs_target
        newline = '\r\n'
    elif tabs_target in content:
        tabs_found = tabs_target
        newline = '\n'
    else:
        # Try regex
        m = re.search(r'<div class="border-b border-slate-100 pb-2\.5 mb-3">\s*<div class="flex items-center bg-slate-100 p-1 rounded-xl gap-1">', content)
        if not m:
            print("ERROR: tabs_target not found")
            return False
        tabs_found = m.group(0)
        newline = '\r\n' if '\r\n' in tabs_found else '\n'

    tabs_replacement = f'<div class="border-b border-slate-100 pb-2.5 mb-3 flex items-center justify-between gap-1.5">{newline}{newline}            <div class="flex-1 min-w-0 flex items-center bg-slate-100 p-1 rounded-xl gap-1">'
    content = content.replace(tabs_found, tabs_replacement, 1)

    # 4. Add btnCollapseLeftHeader after maxscript tab button closing
    btn_max_target = 'id="maxscriptNavBadge">1205</span>'
    if btn_max_target not in content:
        print("ERROR: btn_max_target not found")
        return False

    # Find the next closing </div> of the tabs container
    idx = content.find(btn_max_target)
    close_div_idx = content.find('</div>', idx)
    if close_div_idx == -1:
        print("ERROR: close_div_idx not found")
        return False
    
    collapse_btn_html = f'''</div>

            <!-- Nút Thu Gọn Left Panel (Arrow Left ép sát mép trong) -->
            <button type="button" id="btnCollapseLeftHeader" onclick="toggleLeftPanel(false)" class="p-1.5 rounded-xl bg-slate-100 hover:bg-indigo-100 text-slate-500 hover:text-indigo-700 transition cursor-pointer shrink-0 border border-slate-200/60 hover:border-indigo-300 shadow-xs flex items-center justify-center w-8 h-8" title="Thu gọn danh mục (Arrow Left)">
              <i data-lucide="chevron-left" class="w-4 h-4"></i>
            </button>'''
    content = content[:close_div_idx] + collapse_btn_html + content[close_div_idx + 6:]

    # 5. Update Cột 2 (<section class="col-span-12 lg:col-span-5 xl:col-span-6 space-y-4">)
    sec_target = '<section class="col-span-12 lg:col-span-5 xl:col-span-6 space-y-4">'
    if sec_target not in content:
        print("ERROR: sec_target not found")
        return False
    
    sec_replacement = '''<section id="colCenterWorkspace" class="col-span-12 lg:col-span-5 xl:col-span-6 space-y-4 relative transition-all duration-200">

        <!-- Nút Edge Toggle Mở Rộng (Border Seam Arrow Right khi Left Panel bị thu gọn) -->
        <button type="button" id="btnEdgeExpandLeft" onclick="toggleLeftPanel(true)" class="hidden absolute -left-3 top-5 z-20 w-6 h-6 rounded-full bg-indigo-600 border border-indigo-700 shadow-md hover:bg-indigo-700 text-white items-center justify-center cursor-pointer transition-all hover:scale-110 group" title="Mở rộng danh mục (Arrow Right)">
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform"></i>
        </button>

        <!-- Top Expand Bar khi Left Panel bị thu gọn -->
        <div id="leftPanelExpandBar" class="hidden items-center justify-between bg-white border border-indigo-100 rounded-2xl px-3.5 py-2 shadow-xs transition-all">
          <div class="flex items-center gap-2">
            <button type="button" onclick="toggleLeftPanel(true)" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs cursor-pointer transition-all hover:shadow group">
              <i data-lucide="chevron-right" class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"></i>
              <span>Mở Danh Mục Công Cụ</span>
            </button>
            <span class="text-xs text-slate-500 hidden sm:inline">12 AEC Tools • 433 CAD Files • 1,205 Maxscripts</span>
          </div>
          <span class="text-[11px] text-slate-400 hidden md:inline">Không gian làm việc mở rộng tối đa (9 Cột)</span>
        </div>'''
    content = content.replace(sec_target, sec_replacement, 1)

    # 6. Add Sticky Expand button before </body>
    body_target = '</body>'
    if body_target not in content:
        print("ERROR: body_target not found")
        return False
    
    sticky_btn = '''  <!-- Floating Sticky Expand Button (khi cuộn trang hoặc ở bất kỳ đâu) -->
  <button type="button" id="btnStickyExpandLeft" onclick="toggleLeftPanel(true)" class="hidden fixed left-0 top-36 z-50 bg-white/95 backdrop-blur-xs hover:bg-indigo-50 border border-l-0 border-slate-300 hover:border-indigo-400 rounded-r-xl px-1.5 py-3 shadow-lg cursor-pointer flex flex-col items-center gap-1 text-slate-600 hover:text-indigo-600 group transition-all" title="Mở danh mục công cụ (Arrow Right)">
    <i data-lucide="chevron-right" class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"></i>
    <span class="text-[9px] font-bold text-slate-500 group-hover:text-indigo-600 [writing-mode:vertical-lr] tracking-wider uppercase">Menu</span>
  </button>

</body>'''
    content = content.replace(body_target, sticky_btn, 1)

    # 7. Add toggleLeftPanel JS function before the closing </script> around line 25098
    # Search for refreshModelInfo();\n\n\n\n    setInterval(refreshModelInfo, 10000);
    ref_target = 'setInterval(refreshModelInfo, 10000);'
    if ref_target not in content:
        print("ERROR: ref_target not found")
        return False
    
    idx_ref = content.find(ref_target)
    script_end_idx = content.find('</script>', idx_ref)
    if script_end_idx == -1:
        print("ERROR: script_end_idx not found")
        return False
    
    js_code = '''

    // ====================================================================
    // LEFT PANEL COLLAPSE / EXPAND TOGGLE (ARROW LEFT/RIGHT)
    // ====================================================================
    function toggleLeftPanel(forceOpen) {
      const colLeft = document.getElementById('colLeftPanel');
      const colCenter = document.getElementById('colCenterWorkspace');
      const expandBar = document.getElementById('leftPanelExpandBar');
      const edgeExpand = document.getElementById('btnEdgeExpandLeft');
      const stickyExpand = document.getElementById('btnStickyExpandLeft');
      
      if (!colLeft || !colCenter) return;
      
      const isCurrentlyHidden = colLeft.classList.contains('hidden');
      const shouldOpen = (typeof forceOpen === 'boolean') ? forceOpen : isCurrentlyHidden;
      
      if (shouldOpen) {
        // Expand Left Panel
        colLeft.classList.remove('hidden');
        colCenter.classList.remove('lg:col-span-9', 'xl:col-span-9');
        colCenter.classList.add('lg:col-span-5', 'xl:col-span-6');
        
        if (expandBar) {
          expandBar.classList.add('hidden');
          expandBar.classList.remove('flex');
        }
        if (edgeExpand) {
          edgeExpand.classList.add('hidden');
          edgeExpand.classList.remove('flex');
        }
        if (stickyExpand) {
          stickyExpand.classList.add('hidden');
          stickyExpand.classList.remove('flex');
        }
        
        try { localStorage.setItem('revitai_left_panel_collapsed', '0'); } catch(e){}
      } else {
        // Collapse Left Panel
        colLeft.classList.add('hidden');
        colCenter.classList.remove('lg:col-span-5', 'xl:col-span-6');
        colCenter.classList.add('lg:col-span-9', 'xl:col-span-9');
        
        if (expandBar) {
          expandBar.classList.remove('hidden');
          expandBar.classList.add('flex');
        }
        if (edgeExpand) {
          edgeExpand.classList.remove('hidden');
          edgeExpand.classList.add('flex');
        }
        if (stickyExpand) {
          stickyExpand.classList.remove('hidden');
          stickyExpand.classList.add('flex');
        }
        
        try { localStorage.setItem('revitai_left_panel_collapsed', '1'); } catch(e){}
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

    // Restore Left Panel state on initial load
    try {
      if (localStorage.getItem('revitai_left_panel_collapsed') === '1') {
        toggleLeftPanel(false);
      }
    } catch(e) {}

    // Keyboard shortcut Ctrl+B or Alt+[ to toggle left panel
    window.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b' && !['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target || {}).tagName)) {
        e.preventDefault();
        toggleLeftPanel();
      }
    });

'''
    content = content[:script_end_idx] + js_code + content[script_end_idx:]

    with open('web_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: web_dashboard.py updated successfully!")
    return True

if __name__ == '__main__':
    apply()
