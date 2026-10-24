import sys, os, time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

out_f = "d:/Dropbox/_Documents/RevitAI/scratch_cell_detail.txt"
if os.path.exists(out_f):
    os.remove(out_f)

lsp_file = "d:/Dropbox/_Documents/RevitAI/scratch_inspect_cells.lsp"
lsp_code = f"""(vl-load-com)
(defun c:InspectCells ( / f btr subEnt cnt subEd eType subName )
  (setq f (open "{out_f}" "w"))
  
  (foreach name '("*U151" "*U307")
    (write-line (strcat "\\n================== CELL BLOCK: " name " ==================") f)
    (setq btr (tblobjname "BLOCK" name))
    (if btr
      (progn
        (setq subEnt (entnext btr) cnt 0)
        (while subEnt
          (setq subEd (entget subEnt))
          (setq eType (cdr (assoc 0 subEd)))
          (setq subName (cdr (assoc 2 subEd)))
          (setq pt10 (cdr (assoc 10 subEd)))
          (write-line (strcat "  [" (itoa cnt) "] " eType 
                              (if subName (strcat " Name=" subName) "")
                              " Layer=" (cdr (assoc 8 subEd))
                              (if pt10 (strcat " Pt=" (vl-prin1-to-string pt10)) "")) f)
          (setq cnt (1+ cnt))
          (setq subEnt (entnext subEnt))
        )
        (write-line (strcat "Total sub-entities: " (itoa cnt)) f)
      )
      (write-line "Block table record NOT found!" f)
    )
  )

  (close f)
  (princ "\nDone Cells\n")
  (princ)
)
(c:InspectCells)
"""

with open(lsp_file, "w", encoding="utf-8") as f:
    f.write(lsp_code)

send_to_acad.send_acad_command(f'(load "{lsp_file.replace(chr(92), "/")}")\n', skip_esc=False)

for i in range(10):
    time.sleep(0.5)
    if os.path.exists(out_f):
        print("Cell detail written!")
        break
