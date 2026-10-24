from playwright.sync_api import sync_playwright
import time

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        # -------------------------------------------------------------
        # TEST 1 & 2: Main page, ETABS Hub layout, 3D on top, 2 cols below, NO panelExpandBar
        # -------------------------------------------------------------
        print("Navigating to http://127.0.0.1:5000 ...", flush=True)
        page.goto('http://127.0.0.1:5000', wait_until='domcontentloaded')
        time.sleep(2)

        # Requirement 1: Verify panelExpandBar does NOT exist
        bar_count = page.locator('#panelExpandBar').count()
        print(f"panelExpandBar count in DOM: {bar_count}", flush=True)
        assert bar_count == 0, "panelExpandBar should be completely removed (Hình 1 đã bỏ)"

        # Open ETABS Hub in workspace
        print("Opening ETABS Hub in workspace...", flush=True)
        page.evaluate("openEtabsHub('workspace')")
        time.sleep(1)

        # Requirement 2: Verify subpane-etabs-3d is visible by default at the top
        subpane_3d = page.locator('#subpane-etabs-3d')
        print(f"subpane-etabs-3d visible: {subpane_3d.is_visible()}", flush=True)
        assert subpane_3d.is_visible(), "subpane-etabs-3d should be visible at the top by default"

        # Verify 3D container is present
        container_3d = page.locator('#etabs3DContainer')
        print(f"etabs3DContainer visible: {container_3d.is_visible()}", flush=True)
        assert container_3d.is_visible(), "etabs3DContainer should be visible"

        # Verify 2-column control deck below the canvas
        btn_sub_3d = page.locator('#subtab-btn-3d')
        btn_sub_2d = page.locator('#subtab-btn-2d')
        btn_modal = page.locator("button:has-text('Phóng to Modal')")
        btn_refresh = page.locator('#btnRefreshEtabs')

        assert btn_sub_3d.is_visible(), "subtab-btn-3d should be visible in column 1"
        assert btn_sub_2d.is_visible(), "subtab-btn-2d should be visible in column 1"
        assert btn_modal.is_visible(), "Phóng to Modal should be visible in column 2"
        assert btn_refresh.is_visible(), "btnRefreshEtabs should be visible in column 2"

        # Verify vertical position: 3D container must be ABOVE the control deck
        box_3d = container_3d.bounding_box()
        box_deck = btn_sub_3d.bounding_box()
        print(f"3D container Y: {box_3d['y']}, Control deck Y: {box_deck['y']}", flush=True)
        assert box_3d['y'] < box_deck['y'], "3D canvas MUST be positioned ABOVE the 2-column control deck!"

        page.screenshot(path='scratch/verified_canvas_3d_on_top.png')
        print("Captured scratch/verified_canvas_3d_on_top.png", flush=True)

        # -------------------------------------------------------------
        # TEST 3: Route riêng /3d (Mặc định Left & Right Panel MINIMIN)
        # -------------------------------------------------------------
        print("\nNavigating to dedicated route http://127.0.0.1:5000/3d ...", flush=True)
        page.goto('http://127.0.0.1:5000/3d', wait_until='domcontentloaded')
        time.sleep(2)

        col_left = page.locator('#colLeftPanel')
        col_right = page.locator('#colRightPanel')
        col_center = page.locator('#colCenterWorkspace')

        print(f"/3d route - colLeftPanel visible: {col_left.is_visible()}", flush=True)
        print(f"/3d route - colRightPanel visible: {col_right.is_visible()}", flush=True)
        assert not col_left.is_visible(), "On /3d route, Left Panel MUST be minimin (hidden) by default!"
        assert not col_right.is_visible(), "On /3d route, Right Panel MUST be minimin (hidden) by default!"

        center_classes = col_center.evaluate('e => e.className')
        print(f"/3d route - Center workspace classes: {center_classes}", flush=True)
        assert 'lg:col-span-12' in center_classes, "Center workspace must expand to full 12 columns!"
        assert 'xl:col-span-12' in center_classes, "Center workspace must expand to full 12 columns!"

        # Verify 3D canvas is active
        container_3d_route = page.locator('#etabs3DContainer')
        print(f"/3d route - etabs3DContainer visible: {container_3d_route.is_visible()}", flush=True)
        assert container_3d_route.is_visible(), "On /3d route, 3D canvas must be immediately visible!"

        page.screenshot(path='scratch/verified_route_3d_fullscreen.png')
        print("Captured scratch/verified_route_3d_fullscreen.png", flush=True)

        # Test subtab switching to 2D and back to 3D
        print("\nTesting switching to 2D and back to 3D on 2-column deck...", flush=True)
        btn_sub_2d = page.locator('#subtab-btn-2d')
        btn_sub_2d.click()
        time.sleep(0.5)
        subpane_2d = page.locator('#subpane-etabs-2d')
        assert subpane_2d.is_visible(), "2D subpane should be visible after clicking (1) 2D"

        btn_sub_3d = page.locator('#subtab-btn-3d')
        btn_sub_3d.click()
        time.sleep(0.5)
        assert subpane_3d.is_visible(), "3D subpane should be visible again after clicking (2) 3D"

        # -------------------------------------------------------------
        # TEST 4: Route riêng /modal-3d
        # -------------------------------------------------------------
        print("\nNavigating to dedicated route http://127.0.0.1:5000/modal-3d ...", flush=True)
        page.goto('http://127.0.0.1:5000/modal-3d', wait_until='domcontentloaded')
        time.sleep(2)

        modal = page.locator('#etabsModal')
        print(f"/modal-3d route - etabsModal visible: {modal.is_visible()}", flush=True)
        assert modal.is_visible(), "On /modal-3d route, full-screen 3D modal should be opened!"

        page.screenshot(path='scratch/verified_route_modal_3d.png')
        print("Captured scratch/verified_route_modal_3d.png", flush=True)

        browser.close()
        print("\n>>> ALL 3 USER REQUIREMENTS VERIFIED & PASSED 100%! <<<", flush=True)

if __name__ == '__main__':
    verify()
