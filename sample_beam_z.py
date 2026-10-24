import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# We can inspect beam bounding boxes using a small script or C# helper
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectTestBeamParams',
    'methodName': 'Run'
}
