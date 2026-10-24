from playwright.sync_api import sync_playwright
import time

def test_toggle():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        print("Navigating to http://127.0.0.1:5000 ...", flush=True)
        page.goto('http://127.0.0.1:5000', wait_until='domcontentloaded')
        time.sleep(2)

        # 1. Verify initial expanded state
        col_left = page.locator('#colLeftPanel')
        btn_collapse_edge = page.locator('#btnEdgeCollapseLeft')
        btn_collapse_hdr = page.locator('#btnCollapseLeftHeader')

        print(f"colLeftPanel visible: {col_left.is_visible()}", flush=True)
        print(f"btnEdgeCollapseLeft visible: {btn_collapse_edge.is_visible()}", flush=True)
        print(f"btnCollapseLeftHeader visible: {btn_collapse_hdr.is_visible()}", flush=True)

        assert col_left.is_visible(), "colLeftPanel should be visible initially"
        assert btn_collapse_edge.is_visible(), "btnEdgeCollapseLeft should be visible"
        assert btn_collapse_hdr.is_visible(), "btnCollapseLeftHeader should be visible"

        page.screenshot(path='scratch/left_panel_expanded.png')
        print("Captured scratch/left_panel_expanded.png", flush=True)

        # 2. Click collapse button (edge seam button with left arrow)
        print("Clicking btnEdgeCollapseLeft to collapse panel...", flush=True)
        btn_collapse_edge.click()
        time.sleep(0.5)

        print(f"colLeftPanel visible after collapse: {col_left.is_visible()}", flush=True)
        assert not col_left.is_visible(), "colLeftPanel should be hidden after collapse"
        
        expand_bar = page.locator('#leftPanelExpandBar')
        btn_expand_edge = page.locator('#btnEdgeExpandLeft')
        btn_sticky = page.locator('#btnStickyExpandLeft')

        print(f"leftPanelExpandBar visible: {expand_bar.is_visible()}", flush=True)
        print(f"btnEdgeExpandLeft visible: {btn_expand_edge.is_visible()}", flush=True)
        print(f"btnStickyExpandLeft visible: {btn_sticky.is_visible()}", flush=True)

        assert expand_bar.is_visible(), "leftPanelExpandBar should be visible when collapsed"
        assert btn_expand_edge.is_visible(), "btnEdgeExpandLeft should be visible when collapsed"
        assert btn_sticky.is_visible(), "btnStickyExpandLeft should be visible when collapsed"

        page.screenshot(path='scratch/left_panel_collapsed.png')
        print("Captured scratch/left_panel_collapsed.png", flush=True)

        # 3. Click expand button to restore
        print("Clicking btnEdgeExpandLeft to restore panel...", flush=True)
        btn_expand_edge.click()
        time.sleep(0.5)

        print(f"colLeftPanel visible after restore: {col_left.is_visible()}", flush=True)
        assert col_left.is_visible(), "colLeftPanel should be visible again after restore"
        assert not expand_bar.is_visible(), "leftPanelExpandBar should be hidden after restore"

        # 4. Now test header collapse button
        print("Testing header collapse button btnCollapseLeftHeader...", flush=True)
        btn_collapse_hdr.click()
        time.sleep(0.5)
        print(f"colLeftPanel visible after header collapse: {col_left.is_visible()}", flush=True)
        assert not col_left.is_visible(), "colLeftPanel should be hidden via header collapse button"

        # Restore via expand bar button
        print("Restoring via leftPanelExpandBar button...", flush=True)
        page.locator('#leftPanelExpandBar button').click()
        time.sleep(0.5)
        print(f"colLeftPanel visible after expand bar click: {col_left.is_visible()}", flush=True)
        assert col_left.is_visible(), "colLeftPanel should be restored via expand bar"

        page.screenshot(path='scratch/left_panel_restored.png')
        print("Captured scratch/left_panel_restored.png", flush=True)

        browser.close()
        print(">>> ALL TESTS PASSED SUCCESSFULLY! <<<", flush=True)

if __name__ == '__main__':
    test_toggle()
