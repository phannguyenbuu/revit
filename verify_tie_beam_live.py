import sys
import os
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\a055c581-4895-42d8-96b3-162c30934b62"
TARGET_URL = "https://mr.pkld.online"

async def test_live():
    print(f"=== TESTING LIVE VPS: {TARGET_URL} ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1600, 'height': 1050})
        page = await context.new_page()

        # 1. Goto page
        print("Navigating to", TARGET_URL)
        await page.goto(TARGET_URL, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(2000)

        # 2. Check tab 5 button
        tab5_btn = page.locator('#subtab-btn-tie-beam-cad')
        assert await tab5_btn.count() > 0, "Không tìm thấy nút tab (5) Bản Vẽ Đà Kiềng"
        print("Found Tab 5 button. Clicking Tab 5...")
        await tab5_btn.click()
        await page.wait_for_timeout(1500)

        # Check subpane visibility
        subpane = page.locator('#subpane-etabs-tie-beam-cad')
        assert await subpane.is_visible(), "Subpane tie beam cad không hiển thị"
        print("Subpane 5 is visible.")

        # Check canvas
        canvas = page.locator('#tabTieBeamCadCanvas')
        assert await canvas.count() > 0, "Canvas tabTieBeamCadCanvas không tồn tại"
        box = await canvas.bounding_box()
        print(f"Canvas size: {box['width']}x{box['height']}")

        # Hover over canvas to trigger tooltip
        # Let's move mouse to roughly middle of canvas where tie beam DK-B is drawn
        hover_x = box['x'] + box['width'] * 0.45
        hover_y = box['y'] + box['height'] * 0.45
        await page.mouse.move(hover_x, hover_y)
        await page.wait_for_timeout(800)

        badge_text = await page.locator('#tabTieBeamCadHoverText').inner_text()
        print(f"Hover badge text: {badge_text}")

        tab_screenshot = os.path.join(ARTIFACT_DIR, "verified_vps_tab_tie_beam_cad.png")
        await page.screenshot(path=tab_screenshot)
        print("Saved Tab 5 screenshot:", tab_screenshot)

        # 3. Test Fullscreen Modal
        print("Testing Tie Beam Drawing Modal...")
        open_modal_btn = page.locator('button:has-text("Phóng To Toàn Màn Hình")').nth(1) # second one (first is column cad)
        if await open_modal_btn.count() == 0:
            open_modal_btn = page.locator('#subpane-etabs-tie-beam-cad button:has-text("Phóng To Toàn Màn Hình")')
        await open_modal_btn.click()
        await page.wait_for_timeout(1500)

        modal = page.locator('#tieBeamDrawingModal')
        assert await modal.is_visible(), "Modal tie beam không mở"
        print("Modal tie beam is visible!")

        # Modal canvas hover
        modal_canvas = page.locator('#tieBeamCadCanvas')
        mbox = await modal_canvas.bounding_box()
        await page.mouse.move(mbox['x'] + mbox['width'] * 0.45, mbox['y'] + mbox['height'] * 0.45)
        await page.wait_for_timeout(600)

        modal_badge_text = await page.locator('#tieBeamCadHoverText').inner_text()
        print(f"Modal Hover badge text: {modal_badge_text}")

        modal_screenshot = os.path.join(ARTIFACT_DIR, "verified_vps_modal_tie_beam_cad.png")
        await page.screenshot(path=modal_screenshot)
        print("Saved Modal screenshot:", modal_screenshot)

        # Close modal
        close_btn = page.locator('#tieBeamDrawingModal button[title="Đóng"]')
        await close_btn.click()
        await page.wait_for_timeout(600)
        assert not await modal.is_visible(), "Modal chưa đóng"

        # 4. Verify API downloads
        print("Testing PDF API /api/export-tie-beam-pdf...")
        pdf_res = await page.request.get(f"{TARGET_URL}/api/export-tie-beam-pdf")
        assert pdf_res.status == 200, f"PDF export failed with status {pdf_res.status}"
        pdf_body = await pdf_res.body()
        assert len(pdf_body) > 10000, f"PDF too small: {len(pdf_body)} bytes"
        assert pdf_body[:4] == b'%PDF', "Không phải file PDF hợp lệ"
        print(f"PDF verified: {len(pdf_body)} bytes, header: {pdf_body[:5]}")

        print("Testing DXF API /api/export-tie-beam-dxf...")
        dxf_res = await page.request.get(f"{TARGET_URL}/api/export-tie-beam-dxf")
        assert dxf_res.status == 200, f"DXF export failed with status {dxf_res.status}"
        dxf_body = await dxf_res.body()
        assert len(dxf_body) > 10000, f"DXF too small: {len(dxf_body)} bytes"
        assert b'SECTION' in dxf_body[:200], "Không phải file DXF hợp lệ"
        print(f"DXF verified: {len(dxf_body)} bytes")

        # 5. Check beamRebarModal quick button
        print("Testing Beam Rebar Modal header button...")
        # Switch to 3D or rebar tab to select a beam
        await page.locator('#subtab-btn-rebar').click()
        await page.wait_for_timeout(1000)

        # Click first row in table to open beam modal
        first_row = page.locator('#rebarTableBody tr').first
        if await first_row.count() > 0:
            await first_row.click()
            await page.wait_for_timeout(1000)
            beam_modal = page.locator('#beamRebarModal')
            if await beam_modal.is_visible():
                print("Beam modal opened. Checking quick button [Đà Kiềng (Trục A,B,C)]...")
                quick_btn = page.locator('button[title*="Xem Bản Vẽ Chi Tiết Đà Kiềng"]')
                assert await quick_btn.count() > 0, "Không tìm thấy nút Đà Kiềng trong header dầm"
                await quick_btn.click()
                await page.wait_for_timeout(1000)
                assert await modal.is_visible(), "Bấm nút nhanh không mở modal đà kiềng"
                print("Quick button successfully opened tie beam modal!")
                quick_screenshot = os.path.join(ARTIFACT_DIR, "verified_vps_quick_button_tie_beam.png")
                await page.screenshot(path=quick_screenshot)

        await browser.close()
        print("=== ALL LIVE VPS TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    asyncio.run(test_live())
