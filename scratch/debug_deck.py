from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto('http://127.0.0.1:5000')
    page.evaluate("openEtabsHub('workspace')")
    
    btn = page.locator('#subtab-btn-3d')
    print("btn count:", btn.count())
    if btn.count() > 0:
        info = btn.first.evaluate('''e => {
            let cur = e;
            const chain = [];
            while (cur && cur.tagName !== 'BODY') {
                chain.push({
                    tag: cur.tagName,
                    id: cur.id,
                    className: cur.className,
                    display: window.getComputedStyle(cur).display
                });
                cur = cur.parentElement;
            }
            return chain;
        }''')
        print("DOM CHAIN:")
        for item in info:
            print(" ->", item)
    b.close()
