import subprocess
import os
import sys
import ezdxf
import shutil

sys.stdout.reconfigure(encoding='utf-8')

title = "01. MẶT BẰNG TẦNG 1"

lsp = f'''
(vl-load-com)
(defun c:AddTitle ()
  (setq acad (vlax-get-acad-object))
  (setq doc (vla-get-ActiveDocument acad))
  (setq ms (vla-get-ModelSpace doc))
  
  ;; Create text
  (setq pt (vlax-3d-point 0.0 -5000.0 0.0))
  (setq mtxt (vla-AddMText ms pt 0.0 "{title}"))
  (vla-put-Height mtxt 800.0)
  (vla-put-AttachmentPoint mtxt 5) ;; 5 = Middle Center
  (vla-put-InsertionPoint mtxt pt)
  
  (command "_ZOOM" "_E")
  (command "_QSAVE")
  (command "_QUIT")
)
(c:AddTitle)
'''

with open('test_vla_title.lsp', 'w', encoding='utf-8') as f:
    f.write(lsp)

dwg = r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\view_01.dwg'
test_dwg = r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\test_vla_out.dwg'
shutil.copyfile(dwg, test_dwg)

accore = r'C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe'
cmd = [accore, '/i', test_dwg, '/s', os.path.abspath('test_vla_title.lsp')]
proc = subprocess.run(cmd, capture_output=True, timeout=20)
print('VLA returncode:', proc.returncode)

# Export DXF and check with ezdxf
scr = 'FILEDIA\n0\n_DXFOUT\ncheck_vla.dxf\n16\n_QUIT\n'
with open('dxfout_vla.scr', 'w') as f:
    f.write(scr)

cmd2 = [accore, '/i', test_dwg, '/s', os.path.abspath('dxfout_vla.scr')]
subprocess.run(cmd2, capture_output=True, timeout=15)

if os.path.exists('check_vla.dxf'):
    doc = ezdxf.readfile('check_vla.dxf')
    msp = doc.modelspace()
    for e in msp.query('MTEXT'):
        if 'BẰNG' in e.text or 'TẦNG' in e.text or '01' in e.text:
            print('SUCCESSFUL MTEXT:', repr(e.text))
