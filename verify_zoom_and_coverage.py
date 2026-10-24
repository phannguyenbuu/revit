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
        await page.wait_for_function("() => window.etabsData && window.etabsData.beams && window.etabsData.beams.length > 0", timeout=15000)

        # Open beam B2 (Story T1: Top Req = 9.03 cm2, Bot Req = 4.10 cm2)
        print("Opening modal for beam B2 (Story T1)...")
        await page.evaluate("""() => {
            const beam = window.etabsData.beams.find(b => b.label === 'B2' && b.story === 'T1') || window.etabsData.beams[0];
            openBeamRebarModal(beam);
        }""")
        await page.wait_for_timeout(1500)

        # Zoom into the CAD drawing on canvas
        await page.evaluate("""() => {
            if (typeof brmCadView !== 'undefined') {
                brmCadView.scale = 1.3;
                brmCadView.offsetX = 30;
                brmCadView.offsetY = 10;
                renderBeamDrawings();
            }
        }""")
        await page.wait_for_timeout(500)

        # Test Case A: Under-capacity -> Top Main = 2D16 (4.02 cm2 < 9.03 cm2), Bot Main = 2D14 (3.08 cm2 < 4.10 cm2)
        print("Testing under-capacity: Top Main = 2D16, Bot Main = 2D14...")
        await page.evaluate("""() => {
            const selTop = document.getElementById('brmSelMainTop');
            for (let i = 0; i < selTop.options.length; i++) {
                if (selTop.options[i].value.includes('2D16')) {
                    selTop.selectedIndex = i;
                    break;
                }
            }
            const selBot = document.getElementById('brmSelMainBot');
            for (let i = 0; i < selBot.options.length; i++) {
                if (selBot.options[i].value.includes('2D14')) {
                    selBot.selectedIndex = i;
                    break;
                }
            }
            onRebarSelectChange();
        }""")
        await page.wait_for_timeout(800)

        top_status_under = await page.evaluate("() => document.getElementById('brmStatusMainTop')?.textContent")
        top_title_under = await page.evaluate("() => document.getElementById('brmStatusMainTop')?.title")
        bot_status_under = await page.evaluate("() => document.getElementById('brmStatusMainBot')?.textContent")
        bot_title_under = await page.evaluate("() => document.getElementById('brmStatusMainBot')?.title")
        print(f"[Under-Capacity] Top Status: {repr(top_status_under)}, Title: {repr(top_title_under)}")
        print(f"[Under-Capacity] Bot Status: {repr(bot_status_under)}, Title: {repr(bot_title_under)}")

        # Screenshot under-capacity state
        out_under_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verified_b2_under_capacity.png")
        await page.screenshot(path=out_under_png)
        print(f"Under-capacity screenshot saved to {out_under_png}")

        # Test Case B: Full capacity -> Top Main = 3D20 (9.42 cm2 >= 9.03 cm2), Bot Main = 3D20 (9.42 cm2 >= 4.10 cm2)
        print("Testing full capacity: Top Main = 3D20, Bot Main = 3D20...")
        await page.evaluate("""() => {
            const selTop = document.getElementById('brmSelMainTop');
            for (let i = 0; i < selTop.options.length; i++) {
                if (selTop.options[i].value.includes('3D20')) {
                    selTop.selectedIndex = i;
                    break;
                }
            }
            const selBot = document.getElementById('brmSelMainBot');
            for (let i = 0; i < selBot.options.length; i++) {
                if (selBot.options[i].value.includes('3D20')) {
                    selBot.selectedIndex = i;
                    break;
                }
            }
            onRebarSelectChange();
        }""")
        await page.wait_for_timeout(800)

        top_status_full = await page.evaluate("() => document.getElementById('brmStatusMainTop')?.textContent")
        top_title_full = await page.evaluate("() => document.getElementById('brmStatusMainTop')?.title")
        bot_status_full = await page.evaluate("() => document.getElementById('brmStatusMainBot')?.textContent")
        bot_title_full = await page.evaluate("() => document.getElementById('brmStatusMainBot')?.title")
        print(f"[Full-Capacity] Top Status: {repr(top_status_full)}, Title: {repr(top_title_full)}")
        print(f"[Full-Capacity] Bot Status: {repr(bot_status_full)}, Title: {repr(bot_title_full)}")

        # Screenshot full capacity modal
        out_full_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verified_b2_full_capacity.png")
        await page.screenshot(path=out_full_png)
        print(f"Full-capacity screenshot saved to {out_full_png}")

        # Screenshot canvas only
        canvas = await page.wait_for_selector("#brmDrawingCanvas")
        out_canvas_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verified_b2_canvas_zoomed.png")
        await canvas.screenshot(path=out_canvas_png)
        print(f"Zoomed CAD canvas screenshot saved to {out_canvas_png}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
