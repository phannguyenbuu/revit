(vl-load-com)
(defun c:InspectDetail ( / f ss ent ed blkName obj minPt maxPt btr subEnt cnt )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_array_detail.txt" "w"))
  
  ;; 1. Check Previous Selection
  (setq ss (ssget "_P"))
  (write-line (strcat "SS_P count: " (itoa (if ss (sslength ss) 0))) f)
  (if ss
    (repeat (setq i (sslength ss))
      (setq ent (ssname ss (setq i (1- i))))
      (setq ed (entget ent))
      (write-line (strcat "  P Ent: " (cdr (assoc 0 ed)) " Name=" (vl-prin1-to-string (cdr (assoc 2 ed)))) f)
    )
  )

  ;; 2. Find *U152 and *U308 specifically
  (foreach name '("*U152" "*U308")
    (write-line (strcat "\n================== ARRAY BLOCK: " name " ==================") f)
    (setq ssArr (ssget "X" (list '(0 . "INSERT") (cons 2 (strcat "`" name)))))
    (write-line (strcat "Found instances in DWG: " (itoa (if ssArr (sslength ssArr) 0))) f)
    (if ssArr
      (repeat (setq j (sslength ssArr))
        (setq ent (ssname ssArr (setq j (1- j))))
        (setq ed (entget ent))
        (setq obj (vlax-ename->vla-object ent))
        (setq minPt nil maxPt nil)
        (vl-catch-all-apply 'vla-getboundingbox (list obj 'minPt 'maxPt))
        (if (and minPt maxPt)
          (setq minPt (vlax-safearray->list minPt)
                maxPt (vlax-safearray->list maxPt))
        )
        (write-line (strcat "Instance handle: " (cdr (assoc 5 ed))
                            " Pos: " (vl-prin1-to-string (cdr (assoc 10 ed)))
                            " BBox: (" (rtos (car minPt) 2 1) "," (rtos (cadr minPt) 2 1) ")->("
                                       (rtos (car maxPt) 2 1) "," (rtos (cadr maxPt) 2 1) ")") f)
      )
    )
    
    ;; Inspect Block Definition Sub-entities
    (setq btr (tblobjname "BLOCK" name))
    (if btr
      (progn
        (write-line "Sub-entities inside block table record:" f)
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
Done Detail
")
  (princ)
)
(c:InspectDetail)
