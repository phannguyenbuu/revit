(vl-load-com)

(setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_diag.txt" "w"))
(write-line "STEP 1: Testing AecWallAdd" f)

;; Call AecWallAdd with ESC to see prompt
(command "_.AecWallAdd")
(write-line (strcat "PROMPT_1=" (getvar "LASTPROMPT")) f)
(command) ;; cancel

(write-line "STEP 2: Testing AecDoorAdd" f)
(command "_.AecDoorAdd")
(write-line (strcat "PROMPT_2=" (getvar "LASTPROMPT")) f)
(command) ;; cancel

(write-line "STEP 3: Testing AecWindowAdd" f)
(command "_.AecWindowAdd")
(write-line (strcat "PROMPT_3=" (getvar "LASTPROMPT")) f)
(command) ;; cancel

(close f)
(princ)
