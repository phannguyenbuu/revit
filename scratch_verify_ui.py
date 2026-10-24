import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1600, 'height': 950})
        await page.goto('http://127.0.0.1:5000', wait_until='networkidle')
        await page.wait_for_timeout(2000)

        # Look for buttons to open modal
        btn = page.locator("button:has-text('Chi Tiết Bố Trí Thép Dầm')").first
        if await btn.count() > 0:
            await btn.click()
            await page.wait_for_timeout(1500)
        else:
            # Try to open via JS
            await page.evaluate("() => { if (typeof openBeamRebarModal === 'function') { const b = etabsData.beams.find(x => x.longBeamId === 'DX3' && x.story === 'T1') || etabsData.beams[0]; openBeamRebarModal(b); } }")
            await page.wait_for_timeout(1500)

        # Screenshot modal
        await page.screenshot(path='scratch_modal_verified.png')
        print("Captured scratch_modal_verified.png")

        # Click TC Lưng badge
        tc_lung = page.locator('#brmHeaderTcLungBadge')
        if await tc_lung.count() > 0:
            await tc_lung.click()
            await page.wait_for_timeout(500)
            await page.screenshot(path='scratch_tc_lung_dropdown.png')
            print("Captured scratch_tc_lung_dropdown.png")

        # Click TC Bụng badge
        tc_bung = page.locator('#brmHeaderTcBungBadge')
        if await tc_bung.count() > 0:
            await tc_bung.click()
            await page.wait_for_timeout(500)
            await page.screenshot(path='scratch_tc_bung_dropdown.png')
            print("Captured scratch_tc_bung_dropdown.png")

        await browser.close()

asyncio.run(main())
