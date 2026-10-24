import sys
import urllib.request
sys.stdout.reconfigure(encoding='utf-8')

res = urllib.request.urlopen('http://127.0.0.1:5000')
html = res.read().decode('utf-8')

checks = [
    'aecBtnModeWall',
    'aecBtnModeDoor',
    'aecBtnSnap50',
    'aecBtnSnap100',
    'aec3DHintHUD',
    'Vẽ Tường (Line)',
    'Đặt Cửa (Block)'
]

for c in checks:
    print(f'HTML check "{c}":', c in html)

js_res = urllib.request.urlopen('http://127.0.0.1:5000/static/etabs_hub.js')
js = js_res.read().decode('utf-8')
js_checks = [
    'setAecToolMode',
    'setAecSnapRound',
    'setupAec3DInteraction',
    'buildAecMeshes',
    'aecElements'
]

for c in js_checks:
    print(f'JS check "{c}":', c in js)
