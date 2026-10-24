import asyncio
import os
from playwright.async_api import async_playwright

async def verify_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = await context.new_page()

        print("Navigating to https://mr.pkld.online ...")
        await page.goto("https://mr.pkld.online", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # 1. Click Tab 4: Column CAD
        print("Clicking Tab 4: Column CAD...")
        await page.click("#subtab-btn-column-cad")
        await page.wait_for_timeout(1500)
        await page.screenshot(path="verified_vps_tab4_column_15x4.png")

        # 2. Check Tab 1: 2D Plan with Story 'C'
        print("Clicking Tab 1: 2D Plan...")
        await page.click("#subtab-btn-2d")
        await page.wait_for_timeout(1000)

        print("Clicking Story C button...")
        btn_c = page.locator("#etabs2DStoryButtons button:has-text('C')")
        if await btn_c.count() > 0:
            await btn_c.first.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path="verified_vps_story_c_columns.png")

        # 3. Open Column Drawing Modal
        print("Opening Column Drawing Modal...")
        btn_modal = page.locator("button:has-text('Bản Vẽ Cột (15×4)')")
        if await btn_modal.count() > 0:
            await btn_modal.first.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="verified_vps_column_modal_15x4.png")

        print("Finished Playwright verification.")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(verify_ui())
