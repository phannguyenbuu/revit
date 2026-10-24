(vl-load-com)

(defun c:ScanTitleblocksEx ( / ss f btrEnt btrNext subEd cellOffsets cellNames 
                               firstCellName tbBlockName tbRelOffset btrCell subSub ssEd
                               arrPos arrBaseX arrBaseY tbW tbH k cOff cellBaseX cellBaseY
                               xmin ymin xmax ymax p1 p2 ssInside n entInside edInside etInside bnInside
                               totalEnts textCnt dimCnt lineCnt hatchCnt txtList bestTitle i ent ed bn
                               outFile scopeMode )
  
  (setq outFile (getstring nil "\nEnter output file path: "))
  (if (or (equal outFile "") (not outFile))
    (setq outFile "d:/Dropbox/_Documents/RevitAI/scratch_tb_scan_res.txt")
  )
  
  (setq f (open outFile "w"))

  ;; Check Selection first, fallback to All Arrays
  (setq ss (ssget "_I"))
  (if (not ss) (setq ss (ssget "_P")))
  (if (not ss)
    (setq ss (ssget "X" '((0 . "INSERT") (2 . "`*U*"))))
  )

  (if ss
    (repeat (setq i (sslength ss))
      (setq ent (ssname ss (setq i (1- i))))
      (setq ed (entget ent))
      (setq bn (cdr (assoc 2 ed)))
      
      ;; Đối tượng Mảng Khối Nặc Danh (Associative Array *U...)
      (if (and bn (wcmatch (strcase bn) "`*U*"))
        (progn
          (setq btrEnt (tblobjname "BLOCK" bn))
          (if btrEnt
            (progn
              ;; Đọc các cell con trong định nghĩa Block mảng
              (setq btrNext (entnext btrEnt))
              (setq cellOffsets nil cellNames nil)
              (while btrNext
                (setq subEd (entget btrNext))
                (if (equal (cdr (assoc 0 subEd)) "INSERT")
                  (progn
                    (setq cellOffsets (cons (cdr (assoc 10 subEd)) cellOffsets))
                    (setq cellNames (cons (cdr (assoc 2 subEd)) cellNames))
                  )
                )
                (setq btrNext (entnext btrNext))
              )

              ;; Nếu có nhiều sub-inserts, đây là mảng (Array)
              (if (> (length cellOffsets) 1)
                (progn
                  (setq cellOffsets (reverse cellOffsets))
                  (setq cellNames (reverse cellNames))
                  
                  ;; Lấy thông số khung con đầu tiên (VD: *U151 -> TitleBlock...)
                  (setq firstCellName (car cellNames))
                  (setq tbBlockName "")
                  (setq tbRelOffset '(0.0 0.0 0.0))
                  (setq btrCell (tblobjname "BLOCK" firstCellName))
                  (if btrCell
                    (progn
                      (setq subSub (entnext btrCell))
                      (while subSub
                        (setq ssEd (entget subSub))
                        (if (equal (cdr (assoc 0 ssEd)) "INSERT")
                          (progn
                            (setq tbBlockName (cdr (assoc 2 ssEd)))
                            (setq tbRelOffset (cdr (assoc 10 ssEd)))
                          )
                        )
                        (setq subSub (entnext subSub))
                      )
                    )
                  )

                  ;; Vị trí của cả Block mảng trong ModelSpace
                  (setq arrPos (cdr (assoc 10 ed)))
                  (setq arrBaseX (car arrPos))
                  (setq arrBaseY (cadr arrPos))

                  ;; Kích thước 1 ô khung tên chuẩn
                  (setq tbW 42957.9)
                  (setq tbH 27533.7)

                  ;; Duyệt qua từng cell trong mảng
                  (setq k 0)
                  (foreach cOff cellOffsets
                    (setq cellBaseX (+ arrBaseX (car cOff) (car tbRelOffset)))
                    (setq cellBaseY (+ arrBaseY (cadr cOff) (cadr tbRelOffset)))
                    (setq xmin cellBaseX)
                    (setq ymin cellBaseY)
                    (setq xmax (+ xmin tbW))
                    (setq ymax (+ ymin tbH))

                    ;; Quét kiểm tra thực thể bên trong ô
                    (setq p1 (list (+ xmin 100.0) (+ ymin 100.0) 0.0))
                    (setq p2 (list (- xmax 100.0) (- ymax 100.0) 0.0))
                    (setq ssInside (ssget "C" p1 p2))

                    (setq totalEnts 0 textCnt 0 dimCnt 0 lineCnt 0 hatchCnt 0)
                    (setq txtList nil)
                    (if ssInside
                      (repeat (setq n (sslength ssInside))
                        (setq entInside (ssname ssInside (setq n (1- n))))
                        (setq edInside (entget entInside))
                        (setq etInside (cdr (assoc 0 edInside)))
                        (setq bnInside (cdr (assoc 2 edInside)))
                        ;; Loại trừ chính block mảng
                        (if (not (equal bnInside bn))
                          (progn
                            (setq totalEnts (1+ totalEnts))
                            (if (or (equal etInside "TEXT") (equal etInside "MTEXT"))
                              (progn
                                (setq textCnt (1+ textCnt))
                                (setq txtList (cons (cdr (assoc 1 edInside)) txtList))
                              )
                            )
                            (if (equal etInside "DIMENSION") (setq dimCnt (1+ dimCnt)))
                            (if (or (equal etInside "LINE") (equal etInside "LWPOLYLINE")) (setq lineCnt (1+ lineCnt)))
                            (if (equal etInside "HATCH") (setq hatchCnt (1+ hatchCnt)))
                          )
                        )
                      )
                    )

                    ;; Xác định tiêu đề bản vẽ tốt nhất từ txtList
                    (setq bestTitle "")
                    (foreach tStr (reverse txtList)
                      (if (or (wcmatch (strcase tStr) "*M*T B*NG*")
                              (wcmatch (strcase tStr) "*MB*")
                              (wcmatch (strcase tStr) "*M*T *NG*")
                              (wcmatch (strcase tStr) "*M*T C*T*")
                              (wcmatch (strcase tStr) "*B*N V*")
                              (wcmatch (strcase tStr) "*KH*I NH*")
                              (wcmatch (strcase tStr) "*CHI TI*T*")
                              (wcmatch (strcase tStr) "*S* *"))
                        (if (equal bestTitle "")
                          (setq bestTitle tStr)
                        )
                      )
                    )
                    (if (and (equal bestTitle "") (> (length txtList) 0))
                      (setq bestTitle (car (reverse txtList)))
                    )

                    ;; Ghi dòng dữ liệu dạng TAB-delimited
                    (write-line (strcat "ROW\t" bn "\t" (itoa k) "\t" (if tbBlockName tbBlockName "") "\t"
                                        (rtos xmin 2 2) "\t" (rtos ymin 2 2) "\t"
                                        (rtos xmax 2 2) "\t" (rtos ymax 2 2) "\t"
                                        (rtos tbW 2 2) "\t" (rtos tbH 2 2) "\t"
                                        (itoa totalEnts) "\t" (itoa textCnt) "\t"
                                        (itoa dimCnt) "\t" (itoa lineCnt) "\t" (itoa hatchCnt) "\t"
                                        bestTitle) f)
                    
                    ;; Ghi các text mẫu
                    (foreach tSample (reverse txtList)
                      (write-line (strcat "TXT\t" (itoa k) "\t" tSample) f)
                    )

                    (setq k (1+ k))
                  )
                )
              )
            )
          )
        )
      )
    )
  )

  (close f)
  (princ "\nScan complete.\n")
  (princ)
)
