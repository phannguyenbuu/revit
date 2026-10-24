import sys, os, time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

out_f = "d:/Dropbox/_Documents/RevitAI/scratch_tb_geometry.txt"
if os.path.exists(out_f):
    os.remove(out_f)

lsp_file = "d:/Dropbox/_Documents/RevitAI/scratch_inspect_tb.lsp"
lsp_code = f"""(vl-load-com)
(defun c:InspectTB ( / f )
  (setq f (open "{out_f}" "w"))
  
  (foreach name '("TitleBlock.XPXD" "TitleBlock.XPXD.165")
    (write-line (strcat "\\n================== TITLEBLOCK: " name " ==================") f)
    (setq btr (tblobjname "BLOCK" name))
    (if btr
      (progn
        ;; Let's find min/max coords of all entities in block
        (setq subEnt (entnext btr))
        (setq minX 1e99 minY 1e99 maxX -1e99 maxY -1e99 cnt 0)
        (while subEnt
          (setq subEd (entget subEnt))
          (setq eType (cdr (assoc 0 subEd)))
          (setq pt10 (cdr (assoc 10 subEd)))
          (setq pt11 (cdr (assoc 11 subEd)))
          (if (and pt10 (or (equal eType "LINE") (equal eType "LWPOLYLINE") (equal eType "TEXT") (equal eType "MTEXT") (equal eType "ATTDEF")))
            (progn
              (if (< (car pt10) minX) (setq minX (car pt10)))
              (if (< (cadr pt10) minY) (setq minY (cadr pt10)))
              (if (> (car pt10) maxX) (setq maxX (car pt10)))
              (if (> (cadr pt10) maxY) (setq maxY (cadr pt10)))
            )
          )
          (if (and pt11 (equal eType "LINE"))
            (progn
              (if (< (car pt11) minX) (setq minX (car pt11)))
              (if (< (cadr pt11) minY) (setq minY (cadr pt11)))
              (if (> (car pt11) maxX) (setq maxX (car pt11)))
              (if (> (cadr pt11) maxY) (setq maxY (cadr pt11)))
            )
          )
          (setq cnt (1+ cnt))
          (setq subEnt (entnext subEnt))
        )
        (write-line (strcat "Entity count: " (itoa cnt)) f)
        (write-line (strcat "Min: (" (rtos minX 2 2) ", " (rtos minY 2 2) ")") f)
        (write-line (strcat "Max: (" (rtos maxX 2 2) ", " (rtos maxY 2 2) ")") f)
        (write-line (strcat "Width: " (rtos (- maxX minX) 2 2) " Height: " (rtos (- maxY minY) 2 2)) f)
      )
    )
  )

  (close f)
  (princ "\nDone TB\n")
  (princ)
)
(c:InspectTB)
"""

with open(lsp_file, "w", encoding="utf-8") as f:
    f.write(lsp_code)

send_to_acad.send_acad_command(f'(load "{lsp_file.replace(chr(92), "/")}")\n', skip_esc=False)

for i in range(10):
    time.sleep(0.5)
    if os.path.exists(out_f):
        print("TB detail written!")
        break
