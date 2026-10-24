(vl-load-com)

(defun c:RunDiagLeader ( / ssPipes pipeList ssAllTexts textList i ent ed p1 p2 x1 x2 y1 y2
                           txtStr txtPt x0 y0 yLeader tagLeft winMinX winMaxX winMinY winMaxY
                           bestDist bestPt pItem minX minY maxX maxY testPt ptStart leaderCount
                           targetLayer searchChar maxDist offsetY ClosestPointOnSegment f 
                           resEnt makeCount matchTextCount )

  (defun ClosestPointOnSegment (p a b / vx vy l2 tval)
    (setq vx (- (car b) (car a))
          vy (- (cadr b) (cadr a))
          l2 (+ (* vx vx) (* vy vy)))
    (if (<= l2 1e-6)
      a
      (progn
        (setq tval (/ (+ (* (- (car p) (car a)) vx) (* (- (cadr p) (cadr a)) vy)) l2))
        (if (< tval 0.0) (setq tval 0.0)
          (if (> tval 1.0) (setq tval 1.0)))
        (list (+ (car a) (* tval vx)) (+ (cadr a) (* tval vy)) 0.0)
      )
    )
  )

  (setq targetLayer "P-PIPE*"
        searchChar "+"
        maxDist 5000.0
        offsetY 250.0
        leaderCount 0
        makeCount 0
        matchTextCount 0)

  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_diag_log.txt" "w"))
  (write-line "--- BẮT ĐẦU CHẨN ĐOÁN ---" f)

  (regapp "REVITAI_LEADER")
  (if (setq ssOld (ssget "X" '((0 . "LINE") (-3 ("REVITAI_LEADER")))))
    (progn
      (write-line (strcat "Xóa leader cũ: " (itoa (sslength ssOld))) f)
      (repeat (setq i (sslength ssOld))
        (entdel (ssname ssOld (setq i (1- i))))
      )
    )
    (write-line "Không có leader cũ nào mang XData REVITAI_LEADER" f)
  )

  ;; 1. Thu thập tất cả Line thuộc P-PIPE*
  (setq ssPipes (ssget "X" (list '(0 . "LINE") (cons 8 targetLayer))))
  (setq pipeList nil)
  (if ssPipes
    (progn
      (write-line (strcat "Số lượng Pipes tìm thấy: " (itoa (sslength ssPipes))) f)
      (repeat (setq i (sslength ssPipes))
        (setq ent (ssname ssPipes (setq i (1- i))))
        (setq ed (entget ent))
        (setq p1 (cdr (assoc 10 ed))
              p2 (cdr (assoc 11 ed)))
        (setq x1 (car p1) y1 (cadr p1) x2 (car p2) y2 (cadr p2))
        (setq pipeList (cons (list p1 p2 (min x1 x2) (min y1 y2) (max x1 x2) (max y1 y2)) pipeList))
      )
    )
    (write-line "KHÔNG TÌM THẤY LINE NÀO TRÊN P-PIPE*" f)
  )

  (if pipeList
    (progn
      ;; 2. Thu thập toàn bộ Text/MText
      (setq ssAllTexts (ssget "X" '((0 . "TEXT,MTEXT"))))
      (setq textList nil)
      (if ssAllTexts
        (progn
          (write-line (strcat "Tổng số Text/MText trong bản vẽ: " (itoa (sslength ssAllTexts))) f)
          (repeat (setq i (sslength ssAllTexts))
            (setq ent (ssname ssAllTexts (setq i (1- i))))
            (setq ed (entget ent))
            (setq txtStr (cdr (assoc 1 ed)))
            (setq txtPt (cdr (assoc 10 ed)))
            (setq textList (cons (list txtStr txtPt (car txtPt) (cadr txtPt)) textList))
          )
        )
      )

      ;; 3. Quét từng text cao độ
      (foreach tItem textList
        (setq txtStr (car tItem)
              txtPt  (cadr tItem)
              x0     (caddr tItem)
              y0     (cadddr tItem))

        (if (and (wcmatch txtStr (strcat "*" searchChar "*"))
                 (not (wcmatch txtStr "*U+2022*"))
                 (not (wcmatch txtStr "*\\U+2022*")))
          (progn
            (setq matchTextCount (1+ matchTextCount))
            ;; Tìm mép trái của cụm text
            (setq tagLeft x0)
            (foreach neighbor textList
              (setq ny (cadddr neighbor)
                    nx (caddr neighbor))
              (if (and (< (abs (- ny y0)) 50.0)
                       (< nx x0)
                       (> nx (- x0 2500.0)))
                (if (< nx tagLeft) (setq tagLeft nx))
              )
            )

            (setq winMinX (- x0 maxDist)
                  winMaxX (+ x0 maxDist)
                  winMinY (- y0 maxDist)
                  winMaxY (+ y0 maxDist))

            (setq bestDist 1e12 bestPt nil)

            (foreach pItem pipeList
              (setq minX (caddr pItem)
                    minY (cadddr pItem)
                    maxX (nth 4 pItem)
                    maxY (nth 5 pItem))

              (if (not (or (< maxX winMinX) (> minX winMaxX) (< maxY winMinY) (> minY winMaxY)))
                (progn
                  (setq testPt (ClosestPointOnSegment txtPt (car pItem) (cadr pItem)))
                  (setq d (distance txtPt testPt))
                  (if (< d bestDist)
                    (setq bestDist d bestPt testPt)
                  )
                )
              )
            )

            (if (and bestPt (<= bestDist maxDist))
              (progn
                (setq yLeader (- y0 offsetY))
                (if (< (car bestPt) tagLeft)
                  (setq ptStart (list tagLeft yLeader 0.0))
                  (setq ptStart (list x0 yLeader 0.0))
                )
                (setq resEnt (entmake (list '(0 . "LINE")
                                            '(8 . "P-PIPE")
                                            (cons 10 ptStart)
                                            (cons 11 bestPt)
                                            (list -3 '("REVITAI_LEADER" (1000 . "PIPE_LEADER"))))))
                (if resEnt
                  (setq makeCount (1+ makeCount))
                  (write-line (strcat "ENTMAKE THẤT BẠI cho text: " txtStr) f)
                )
                (setq leaderCount (1+ leaderCount))
              )
            )
          )
        )
      )
    )
  )

  (write-line (strcat "Số Text chứa '+': " (itoa matchTextCount)) f)
  (write-line (strcat "Số Leader tìm được: " (itoa leaderCount)) f)
  (write-line (strcat "Số Line entmake thành công: " (itoa makeCount)) f)
  (command "_.REGEN")
  (close f)
  (princ)
)
(c:RunDiagLeader)
