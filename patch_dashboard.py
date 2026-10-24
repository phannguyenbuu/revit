import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def patch():
    dash_file = r"d:\Dropbox\_Documents\RevitAI\web_dashboard.py"
    with open(dash_file, 'r', encoding='utf-8') as f:
        code = f.read()

    import etabs_ui

    # 1. Add Three.js to head
    three_js_tags = """  <!-- Three.js & OrbitControls for ETABS 3D Solid Cross-Section Model -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>"""
    if 'three.min.js' not in code:
        assert '</head>' in code
        code = code.replace('</head>', three_js_tags, 1)
        print("1. Added Three.js to head")

    # 2. Add ETABS_WORKSPACE_TAB to Cột 2
    workspace_target = '<section class="col-span-12 lg:col-span-5 xl:col-span-6 space-y-4">'
    if 'id="tab-etabs-hub"' not in code:
        assert workspace_target in code
        code = code.replace(workspace_target, workspace_target + "\n" + etabs_ui.ETABS_WORKSPACE_TAB, 1)
        print("2. Added ETABS Workspace Tab to Cột 2")

    # 3. Add ETABS_RIGHT_PANEL_CARD to Cột 3
    col3_target = '<aside class="col-span-12 lg:col-span-3 xl:col-span-3 space-y-3.5">'
    if 'ETABS AI Hub' not in code:
        assert col3_target in code
        code = code.replace(col3_target, col3_target + "\n" + etabs_ui.ETABS_RIGHT_PANEL_CARD, 1)
        print("3. Added ETABS Card to Cột 3")

    # 4. Add Modal and JS script before </body>
    modal_addition = etabs_ui.ETABS_FULLSCREEN_MODAL + '\n  <!-- ETABS Hub Controller Script -->\n  <script src="/static/etabs_hub.js"></script>\n</body>'
    if 'id="etabsModal"' not in code:
        assert '</body>' in code
        code = code.replace('</body>', modal_addition, 1)
        print("4. Added ETABS Modal and JS before </body>")

    # 5. Add API Routes
    api_addition = """@app.route('/api/etabs-data')
def api_etabs_data():
    import etabs_service
    return jsonify(etabs_service.get_etabs_data())


@app.route('/api/etabs-refresh', methods=['POST'])
def api_etabs_refresh():
    import etabs_service
    return jsonify(etabs_service.refresh_etabs_data())


@app.route('/static/etabs_hub.js')
def static_etabs_hub():
    return send_from_directory(CURRENT_DIR, 'etabs_hub.js', mimetype='application/javascript')
"""

    if '/api/etabs-data' not in code:
        assert "@app.route('/api/hub-status')" in code
        code = code.replace("@app.route('/api/hub-status')", api_addition + "\n\n@app.route('/api/hub-status')", 1)
        print("5. Added ETABS API Routes")

    with open(dash_file, 'w', encoding='utf-8') as f:
        f.write(code)

    print("SUCCESS: web_dashboard.py updated!")

if __name__ == '__main__':
    patch()
