(vl-load-com)

(setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aec_com.txt" "w"))
(setq acadApp (vlax-get-acad-object))

;; Try different ProgIDs for ACA COM
(setq progids '(
  "AecX.AecArchBaseApplication"
  "AecX.AecArchBaseApplication.8.4"
  "AecX.AecArchBaseApplication.8.3"
  "AecX.AecArchBaseApplication.8.2"
  "AecX.AecBaseApplication"
  "AecX.AecBaseApplication.8.4"
))

(foreach prog progids
  (setq obj (vl-catch-all-apply 'vla-getinterfaceobject (list acadApp prog)))
  (if (and obj (not (vl-catch-all-error-p obj)))
    (write-line (strcat "SUCCESS: " prog " -> " (vl-prin1-to-string obj)) f)
    (write-line (strcat "FAILED: " prog) f)
  )
)

(close f)
(princ)
