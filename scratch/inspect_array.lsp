(vl-load-com)

(defun c:InspectArray ( / ss ent ed blkName obj blkDef curEnt count curEd eType subName minPt maxPt f i )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_array_inspect.txt" "w"))
  (setq ss (ssget "_I"))
  (if (not ss) (setq ss (ssget "_P")))
  (if (not ss)
    (setq ss (ssget "X" '((0 . "INSERT") (2 . "`*U152,`*U308"))))
  )
  (write-line (strcat "Found entities in SS: " (itoa (if ss (sslength ss) 0))) f)
  (if ss
    (repeat (setq i (sslength ss))
      (setq ent (ssname ss (setq i (1- i))))
      (setq ed (entget ent))
      (setq blkName (cdr (assoc 2 ed)))
      (setq obj (vlax-ename->vla-object ent))
      (write-line (strcat "\n--- ENTITY: " blkName " ---") f)
      (setq minPt nil maxPt nil)
      (vl-catch-all-apply 'vla-getboundingbox (list obj 'minPt 'maxPt))
      (if (and minPt maxPt)
        (write-line (strcat "BoundingBox: (" (rtos (car (vlax-safearray->list minPt)) 2 2) ","
                            (rtos (cadr (vlax-safearray->list minPt)) 2 2) ") -> ("
                            (rtos (car (vlax-safearray->list maxPt)) 2 2) ","
                            (rtos (cadr (vlax-safearray->list maxPt)) 2 2) ")") f)
      )

      ;; Check XData and Dictionary
      (write-line (strcat "Has Extension Dictionary: " (if (assoc 360 ed) "YES" "NO")) f)
      
      ;; Inspect block definition
      (setq blkDef (tblobjname "BLOCK" blkName))
      (write-line (strcat "Block Table Record: " (vl-prin1-to-string blkDef)) f)
      (setq curEnt (entnext blkDef))
      (setq count 0)
      (while curEnt
        (setq curEd (entget curEnt))
        (setq eType (cdr (assoc 0 curEd)))
        (setq subName (cdr (assoc 2 curEd)))
        (if (< count 35)
          (write-line (strcat "  Sub-ent [" (itoa count) "]: " eType " " (if subName (strcat "Name=" subName) "")
                              " Layer=" (cdr (assoc 8 curEd))
                              " Pt=" (vl-prin1-to-string (cdr (assoc 10 curEd)))) f)
        )
        (setq count (1+ count))
        (setq curEnt (entnext curEnt))
      )
      (write-line (strcat "Total sub-entities in block def: " (itoa count)) f)
    )
  )
  (close f)
  (princ "\nDone InspectArray\n")
  (princ)
)
(c:InspectArray)
