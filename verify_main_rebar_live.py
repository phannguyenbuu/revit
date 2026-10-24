import asyncio
import os
import sys
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = await context.new_page()

        print("Navigating to https://mr.pkld.online ...")
        await page.goto("https://mr.pkld.online", wait_until="networkidle", timeout=60000)

        # Switch to tab 3 (Rebar Table)
        print("Switching to rebar tab...")
        await page.click("#subtab-btn-rebar")
        await page.wait_for_timeout(1000)

        # Click the first 'Chọn thép' button or trigger openBeamRebarModal
        print("Opening Beam Rebar Modal...")
        await page.evaluate("""() => {
            if (window.etabsData && window.etabsData.beams && window.etabsData.beams.length > 0) {
                openBeamRebarModal(window.etabsData.beams[0]);
            }
        }""")
        await page.wait_for_timeout(1500)

        # Read initial values
        init_top_status = await page.evaluate("() => document.getElementById('brmStatusMainTop')?.textContent")
        init_bot_status = await page.evaluate("() => document.getElementById('brmStatusMainBot')?.textContent")
        print(f"Initial Top Status: {repr(init_top_status)}")
        print(f"Initial Bot Status: {repr(init_bot_status)}")

        # Select 3D20 for Thép Chủ Trên
        print("Selecting 3D20 for Top Main...")
        await page.evaluate("""() => {
            const sel = document.getElementById('brmSelMainTop');
            for (let i = 0; i < sel.options.length; i++) {
                if (sel.options[i].value.includes('3D20')) {
                    sel.selectedIndex = i;
                    break;
                }
            }
            onRebarSelectChange();
        }""")
        await page.wait_for_timeout(1000)

        # Select 3D20 for Thép Chủ Dưới
        print("Selecting 3D20 for Bot Main...")
        await page.evaluate("""() => {
            const sel = document.getElementById('brmSelMainBot');
            for (let i = 0; i < sel.options.length; i++) {
                if (sel.options[i].value.includes('3D20')) {
                    sel.selectedIndex = i;
                    break;
                }
            }
            onRebarSelectChange();
        }""")
        await page.wait_for_timeout(1000)

        # Read updated statuses
        updated_top_status = await page.evaluate("() => document.getElementById('brmStatusMainTop')?.textContent")
        updated_bot_status = await page.evaluate("() => document.getElementById('brmStatusMainBot')?.textContent")
        print(f"Updated Top Status: {repr(updated_top_status)}")
        print(f"Updated Bot Status: {repr(updated_bot_status)}")

        # Screenshot the modal
        out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verified_main_rebar_modal.png")
        await page.screenshot(path=out_png)
        print(f"Screenshot saved to {out_png}")

        # Check canvas drawing elements or text
        # Let's inspect activeBeam and canvas drawing
        active_beam_info = await page.evaluate("""() => {
            const b = window.selectedBeamForRebar;
            return {
                label: b ? b.label : null,
                rebar_main_top: b ? b.rebar_main_top : null,
                rebar_main_bot: b ? b.rebar_main_bot : null
            };
        }""")
        print(f"Active Beam Info: {active_beam_info}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
