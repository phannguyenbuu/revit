
(defun c:AddMyTitle ()
  (vl-load-com)
  (setvar "CMDECHO" 0)
  ;; Create Arial text style
  (if (not (tblsearch "STYLE" "UNICODE_TITLE"))
    (command "-STYLE" "UNICODE_TITLE" "arial.ttf" 0 1.0 0 "_N" "_N")
  )
  ;; Make text entity
  (entmake
    (list
      (cons 0 "TEXT")
      (cons 100 "AcDbEntity")
      (cons 100 "AcDbText")
      (cons 10 (list 0.0 0.0 0.0))
      (cons 11 (list 0.0 0.0 0.0))
      (cons 40 800.0)
      (cons 1 "01. MẶT BẰNG TẦNG 1")
      (cons 7 "UNICODE_TITLE")
      (cons 72 1) ;; Center
      (cons 73 2) ;; Middle
    )
  )
  (command "_ZOOM" "_E")
  (command "_QSAVE")
  (command "_QUIT")
)
(c:AddMyTitle)
