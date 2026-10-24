from playwright.sync_api import sync_playwright
import time

def test_right_panel_toggle():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        print("Navigating to http://127.0.0.1:5000 ...", flush=True)
        page.goto('http://127.0.0.1:5000', wait_until='domcontentloaded')
        time.sleep(2)

        col_left = page.locator('#colLeftPanel')
        col_center = page.locator('#colCenterWorkspace')
        col_right = page.locator('#colRightPanel')

        btn_collapse_edge_r = page.locator('#btnEdgeCollapseRight')
        btn_collapse_hdr_r = page.locator('#btnCollapseRightHeader')

        print(f"colRightPanel visible: {col_right.is_visible()}", flush=True)
        print(f"btnEdgeCollapseRight visible: {btn_collapse_edge_r.is_visible()}", flush=True)
        print(f"btnCollapseRightHeader visible: {btn_collapse_hdr_r.is_visible()}", flush=True)

        assert col_right.is_visible(), "colRightPanel should be visible initially"
        assert btn_collapse_edge_r.is_visible(), "btnEdgeCollapseRight should be visible"
        assert btn_collapse_hdr_r.is_visible(), "btnCollapseRightHeader should be visible"

        # 1. Collapse Right Panel via edge seam button
        print("Clicking btnEdgeCollapseRight to collapse Right Panel...", flush=True)
        btn_collapse_edge_r.click()
        time.sleep(0.5)

        assert not col_right.is_visible(), "colRightPanel should be hidden after collapse"
        btn_expand_edge_r = page.locator('#btnEdgeExpandRight')
        btn_bar_expand_r = page.locator('#btnBarExpandRight')
        btn_sticky_r = page.locator('#btnStickyExpandRight')

        print(f"btnEdgeExpandRight visible: {btn_expand_edge_r.is_visible()}", flush=True)
        print(f"btnBarExpandRight visible: {btn_bar_expand_r.is_visible()}", flush=True)
        print(f"btnStickyExpandRight visible: {btn_sticky_r.is_visible()}", flush=True)

        assert btn_expand_edge_r.is_visible(), "btnEdgeExpandRight should be visible"
        assert btn_bar_expand_r.is_visible(), "btnBarExpandRight should be visible"
        assert btn_sticky_r.is_visible(), "btnStickyExpandRight should be visible"

        page.screenshot(path='scratch/right_panel_collapsed.png')
        print("Captured scratch/right_panel_collapsed.png", flush=True)

        # 2. Also collapse Left Panel to test Both Collapsed (Full Screen 12 Columns)
        print("Now collapsing Left Panel to test Both Panels Collapsed (12 Cols Fullscreen)...", flush=True)
        page.locator('#btnEdgeCollapseLeft').click()
        time.sleep(0.5)

        assert not col_left.is_visible(), "colLeftPanel should be hidden"
        assert not col_right.is_visible(), "colRightPanel should be hidden"

        center_classes = col_center.evaluate('e => e.className')
        print(f"Center workspace classes when both collapsed: {center_classes}", flush=True)
        assert 'lg:col-span-12' in center_classes, "colCenterWorkspace should have lg:col-span-12"
        assert 'xl:col-span-12' in center_classes, "colCenterWorkspace should have xl:col-span-12"

        page.screenshot(path='scratch/both_panels_collapsed_fullscreen.png')
        print("Captured scratch/both_panels_collapsed_fullscreen.png", flush=True)

        # 3. Restore Left Panel via bar button
        print("Restoring Left Panel via top bar button...", flush=True)
        page.locator('#btnBarExpandLeft').click()
        time.sleep(0.5)
        assert col_left.is_visible(), "colLeftPanel should be restored"

        # 4. Restore Right Panel via edge expand button
        print("Restoring Right Panel via edge expand button...", flush=True)
        btn_expand_edge_r.click()
        time.sleep(0.5)
        assert col_right.is_visible(), "colRightPanel should be restored"

        # 5. Test Right Panel Header Collapse button
        print("Testing Right Panel Header collapse button...", flush=True)
        btn_collapse_hdr_r.click()
        time.sleep(0.5)
        assert not col_right.is_visible(), "colRightPanel should be hidden via header collapse button"

        # Restore Right Panel via top bar button
        page.locator('#btnBarExpandRight').click()
        time.sleep(0.5)
        assert col_right.is_visible(), "colRightPanel should be restored via top bar button"

        page.screenshot(path='scratch/all_panels_restored.png')
        print("Captured scratch/all_panels_restored.png", flush=True)

        browser.close()
        print(">>> ALL RIGHT PANEL & FULLSCREEN TESTS PASSED SUCCESSFULLY! <<<", flush=True)

if __name__ == '__main__':
    test_right_panel_toggle()
