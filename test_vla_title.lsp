
(vl-load-com)
(defun c:AddTitle ()
  (setq acad (vlax-get-acad-object))
  (setq doc (vla-get-ActiveDocument acad))
  (setq ms (vla-get-ModelSpace doc))
  
  ;; Create text
  (setq pt (vlax-3d-point 0.0 -5000.0 0.0))
  (setq mtxt (vla-AddMText ms pt 0.0 "01. MẶT BẰNG TẦNG 1"))
  (vla-put-Height mtxt 800.0)
  (vla-put-AttachmentPoint mtxt 5) ;; 5 = Middle Center
  (vla-put-InsertionPoint mtxt pt)
  
  (command "_ZOOM" "_E")
  (command "_QSAVE")
  (command "_QUIT")
)
(c:AddTitle)
