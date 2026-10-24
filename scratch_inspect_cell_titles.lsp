(vl-load-com)
(defun c:InspectCellTitles ( / f )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_cell_titles.txt" "w"))

  (defun scanCol (colName xmin xmax arrName / k ymin ymax p1 p2 ssInside n e ed et bn txtList sheetTitle)
    (write-line (strcat "\n================ " colName " (" arrName ") ================") f)
    (setq k 0)
    (while (< k 17)
      (setq ymin (+ 232484.9 (* k 42000.0)))
      (setq ymax (+ ymin 27534.0))
      
      (setq p1 (list (+ xmin 50.0) (+ ymin 50.0) 0.0))
      (setq p2 (list (- xmax 50.0) (- ymax 50.0) 0.0))
      (setq ssInside (ssget "C" p1 p2))
      
      (setq txtList nil)
      (setq objCounts nil)
      (if ssInside
        (repeat (setq n (sslength ssInside))
          (setq e (ssname ssInside (setq n (1- n))))
          (setq ed (entget e))
          (setq et (cdr (assoc 0 ed)))
          (setq bn (cdr (assoc 2 ed)))
          (if (not (or (equal bn "*U152") (equal bn "*U308")))
            (progn
              ;; Count types
              (setq item (assoc et objCounts))
              (if item
                (setq objCounts (subst (cons et (1+ (cdr item))) item objCounts))
                (setq objCounts (cons (cons et 1) objCounts))
              )
              ;; Collect texts
              (if (or (equal et "TEXT") (equal et "MTEXT"))
                (setq txtList (cons (cdr (assoc 1 ed)) txtList))
              )
            )
          )
        )
      )
      
      (if objCounts
        (progn
          (write-line (strcat "ROW " (itoa k) " | Region: (" 
                              (rtos xmin 2 1) "," (rtos ymin 2 1) ") -> ("
                              (rtos xmax 2 1) "," (rtos ymax 2 1) ")") f)
          (setq strTypes "")
          (foreach pair objCounts
            (setq strTypes (strcat strTypes (car pair) "=" (itoa (cdr pair)) " "))
          )
          (write-line (strcat "  Objects: " strTypes) f)
          (write-line "  Texts:" f)
          (foreach tVal (reverse txtList)
            (write-line (strcat "    - " tVal) f)
          )
        )
      )
      (setq k (1+ k))
    )
  )

  (scanCol "COLUMN 1" 116956.1 159914.0 "*U152")
  (scanCol "COLUMN 2" 179523.0 222480.9 "*U308")

  (close f)
  (princ "
Done Titles
")
  (princ)
)
(c:InspectCellTitles)
