(vl-load-com)
(defun c:InspectCells ( / f btr subEnt cnt subEd eType subName )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_cell_detail.txt" "w"))
  
  (foreach name '("*U151" "*U307")
    (write-line (strcat "\n================== CELL BLOCK: " name " ==================") f)
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
  (princ "
Done Cells
")
  (princ)
)
(c:InspectCells)
