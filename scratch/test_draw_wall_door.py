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

    # Add a sample wall and door in T3 to verify 3D rendering
    page.evaluate("""
      aecElements.push({
        id: 'wall_demo_1',
        type: 'wall',
        p1: { x: 3000, y: 11800, z: -2000 },
        p2: { x: 15000, y: 11800, z: -2000 },
        thickness: 200,
        height: 3000,
        story: 'T3'
      });
      aecElements.push({
        id: 'door_demo_1',
        type: 'door',
        pos: { x: 9000, y: 11800, z: -2000 },
        width: 1000,
        height: 2200,
        thickness: 200,
        angle: 0,
        story: 'T3'
      });
      saveAecElementsToStorage();
      refreshAecScene();
      setAecToolMode('door');
    """)
    page.wait_for_timeout(1000)

    subpane = page.query_selector("#subpane-etabs-3d")
    if subpane:
        subpane.screenshot(path="scratch/verified_rendered_wall_door.png")
        print("Screenshot saved to scratch/verified_rendered_wall_door.png")

    browser.close()
