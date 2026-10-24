import sys, os, time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

out_f = "d:/Dropbox/_Documents/RevitAI/scratch_tb_exact.txt"
if os.path.exists(out_f):
    os.remove(out_f)

lsp_file = "d:/Dropbox/_Documents/RevitAI/scratch_inspect_tb_exact.lsp"
lsp_code = f"""(vl-load-com)
(defun c:InspectTBExact ( / f )
  (setq f (open "{out_f}" "w"))
  
  ;; Look at *U152 array BBox: (116956.1, 232484.9) -> (159914.0, 932018.6)
  ;; It has 17 rows, spacing = 42000.
  ;; Row 0: Y from 232484.9.
  ;; Row 16: Y = 232484.9 + 16 * 42000 = 904484.9.
  ;; 932018.6 - 904484.9 = 27533.7.
  ;; Width = 159914.0 - 116956.1 = 42957.9.
  ;; Height of single titleblock = 27533.7!
  
  (write-line (strcat "Col 1 Width: " (rtos (- 159914.0 116956.1) 2 2)) f)
  (write-line (strcat "Col 1 Single TB Height: " (rtos (- 932018.6 (+ 232484.9 (* 16 42000.0))) 2 2)) f)
  
  ;; Let's inspect what's inside each of the 17 cells for Col 1 (*U152) and Col 2 (*U308)!
  ;; In AutoCAD ModelSpace, what entities fall within each bounding box?
  ;; Cell k of Col 1:
  ;; X: [116956.1, 159914.0]
  ;; Y: [232484.9 + k * 42000, 232484.9 + k * 42000 + 27534.0]
  
  (write-line "\\n--- COL 1 (*U152) CELLS ---" f)
  (setq k 0)
  (while (< k 17)
    (setq ymin (+ 232484.9 (* k 42000.0)))
    (setq ymax (+ ymin 27534.0))
    (setq xmin 116956.1)
    (setq xmax 159914.0)
    
    ;; Test ssget "C" (crossing) excluding the array block itself
    ;; We query entities inside (margin 100mm inside)
    (setq p1 (list (+ xmin 100.0) (+ ymin 100.0) 0.0))
    (setq p2 (list (- xmax 100.0) (- ymax 100.0) 0.0))
    (setq ssInside (ssget "C" p1 p2))
    
    ;; Count entities and check types
    (setq totalEnts 0 textCnt 0 dimCnt 0 lineCnt 0 wallCnt 0)
    (setq textSample "")
    (if ssInside
      (repeat (setq n (sslength ssInside))
        (setq e (ssname ssInside (setq n (1- n))))
        (setq ed (entget e))
        (setq et (cdr (assoc 0 ed)))
        (setq bn (cdr (assoc 2 ed)))
        ;; Ignore the array block itself (*U152 and *U308)
        (if (not (or (equal bn "*U152") (equal bn "*U308")))
          (progn
            (setq totalEnts (1+ totalEnts))
            (if (or (equal et "TEXT") (equal et "MTEXT"))
              (progn
                (setq textCnt (1+ textCnt))
                (if (equal textSample "")
                  (setq textSample (cdr (assoc 1 ed)))
                )
              )
            )
            (if (equal et "DIMENSION") (setq dimCnt (1+ dimCnt)))
            (if (or (equal et "LINE") (equal et "LWPOLYLINE")) (setq lineCnt (1+ lineCnt)))
          )
        )
      )
    )
    (write-line (strcat "Row " (itoa k) " (Y=" (rtos ymin 2 0) ".." (rtos ymax 2 0) 
                        "): totalEnts=" (itoa totalEnts) 
                        " (texts=" (itoa textCnt) ", dims=" (itoa dimCnt) ", lines=" (itoa lineCnt) ")"
                        " SampleText: " textSample) f)
    (setq k (1+ k))
  )

  (write-line "\\n--- COL 2 (*U308) CELLS ---" f)
  (setq k 0)
  (while (< k 17)
    (setq ymin (+ 232484.9 (* k 42000.0)))
    (setq ymax (+ ymin 27534.0))
    (setq xmin 179523.0)
    (setq xmax 222480.9)
    
    (setq p1 (list (+ xmin 100.0) (+ ymin 100.0) 0.0))
    (setq p2 (list (- xmax 100.0) (- ymax 100.0) 0.0))
    (setq ssInside (ssget "C" p1 p2))
    
    (setq totalEnts 0 textCnt 0 dimCnt 0 lineCnt 0)
    (setq textSample "")
    (if ssInside
      (repeat (setq n (sslength ssInside))
        (setq e (ssname ssInside (setq n (1- n))))
        (setq ed (entget e))
        (setq et (cdr (assoc 0 ed)))
        (setq bn (cdr (assoc 2 ed)))
        (if (not (or (equal bn "*U152") (equal bn "*U308")))
          (progn
            (setq totalEnts (1+ totalEnts))
            (if (or (equal et "TEXT") (equal et "MTEXT"))
              (progn
                (setq textCnt (1+ textCnt))
                (if (equal textSample "")
                  (setq textSample (cdr (assoc 1 ed)))
                )
              )
            )
            (if (equal et "DIMENSION") (setq dimCnt (1+ dimCnt)))
            (if (or (equal et "LINE") (equal et "LWPOLYLINE")) (setq lineCnt (1+ lineCnt)))
          )
        )
      )
    )
    (write-line (strcat "Row " (itoa k) " (Y=" (rtos ymin 2 0) ".." (rtos ymax 2 0) 
                        "): totalEnts=" (itoa totalEnts) 
                        " (texts=" (itoa textCnt) ", dims=" (itoa dimCnt) ", lines=" (itoa lineCnt) ")"
                        " SampleText: " textSample) f)
    (setq k (1+ k))
  )

  (close f)
  (princ "\nDone Exact\n")
  (princ)
)
(c:InspectTBExact)
"""

with open(lsp_file, "w", encoding="utf-8") as f:
    f.write(lsp_code)

send_to_acad.send_acad_command(f'(load "{lsp_file.replace(chr(92), "/")}")\n', skip_esc=False)

for i in range(10):
    time.sleep(0.5)
    if os.path.exists(out_f):
        print("Exact detail written!")
        break
