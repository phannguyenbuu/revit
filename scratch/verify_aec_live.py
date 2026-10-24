import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("http://127.0.0.1:5000", wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Switch tab to ETABS Hub and subtab to 3D Structure
    page.evaluate("switchTab('tab-etabs-hub');")
    page.wait_for_timeout(500)
    page.evaluate("switchEtabsSubTab('etabs-3d');")
    page.wait_for_timeout(1500)

    # Click Wall mode button
    page.evaluate("setAecToolMode('wall');")
    page.wait_for_timeout(500)

    # Take screenshot of subpane-etabs-3d
    subpane = page.query_selector("#subpane-etabs-3d")
    if subpane:
        subpane.screenshot(path="scratch/verified_aec_3d_structure.png")
        print("Screenshot saved to scratch/verified_aec_3d_structure.png")
    else:
        page.screenshot(path="scratch/verified_page.png")
        print("Page screenshot saved to scratch/verified_page.png")

    browser.close()
