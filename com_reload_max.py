import win32com.client

try:
    max_app = win32com.client.GetActiveObject("MAX.Application")
    res = max_app.ExecuteMAXScriptScript(r'python.ExecuteFile @"d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge.py"')
    print(f"Executed via MAX.Application COM: {res}")
except Exception as e:
    print(f"COM Error: {e}")
