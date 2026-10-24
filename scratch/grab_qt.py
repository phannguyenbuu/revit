import urllib.request
import json

code = r'''
import sys
from PySide2 import QtWidgets

app = QtWidgets.QApplication.instance()
main_wnd = None
for w in app.topLevelWidgets():
    if "autodesk 3ds max" in w.windowTitle().lower():
        main_wnd = w
        break

if main_wnd:
    docks = main_wnd.findChildren(QtWidgets.QDockWidget, "MaxAICopilotDock")
    if docks:
        pm = docks[-1].grab()
        pm.save(r'D:\Dropbox\_Documents\RevitAI\scratch\chatbot_dock.png')
        print("Saved chatbot_dock.png from dock")

    toolbars = main_wnd.findChildren(QtWidgets.QToolBar, "MaxAIToolBar")
    if toolbars:
        pm2 = toolbars[-1].grab()
        pm2.save(r'D:\Dropbox\_Documents\RevitAI\scratch\ai_toolbar.png')
        print("Saved ai_toolbar.png from toolbar")
'''

data = json.dumps({"language": "python", "code": code}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8096/api/execute", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode("utf-8"))
