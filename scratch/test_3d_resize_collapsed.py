from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1600, 'height': 950})
    page = context.new_page()

    page.goto('http://127.0.0.1:5000', wait_until='domcontentloaded')
    time.sleep(2)

    # Open ETABS Hub in workspace
    page.evaluate("openEtabsHub('workspace')")
    time.sleep(1)

    # Switch to 3D Structure sub-tab: switchEtabsSubTab('3d')
    page.evaluate("switchEtabsSubTab('3d')")
    time.sleep(1)

    page.screenshot(path='scratch/3d_structure_normal.png')
    print("Normal 3D captured")

    # Collapse Left Panel using btnEdgeCollapseLeft
    page.locator('#btnEdgeCollapseLeft').click()
    time.sleep(1)

    page.screenshot(path='scratch/3d_structure_collapsed_wide.png')
    print("Wide collapsed 3D captured")

    # Expand back using btnEdgeExpandLeft
    page.locator('#btnEdgeExpandLeft').click()
    time.sleep(0.5)

    browser.close()
    print("DONE 3D test successfully!")
