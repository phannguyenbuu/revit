;;; =========================================================================
;;; MEP_CLEANER_AND_LEADER.LSP
;;; RevitAI Studio - AutoCAD Automation Tool
;;; 1. Xóa toàn bộ Hatch Solid & Solid (kể cả bên trong Block)
;;; 2. Nối đường dẫn Leader nghiêng từ đáy Text/MText cao độ (+) đến Line/Polyline gần nhất
;;; =========================================================================

(vl-load-com)

;;; =========================================================================
;;; HÀM 1: XÓA TẤT CẢ HATCH SOLID VÀ SOLID (KỂ CẢ TRONG BLOCK)
;;; =========================================================================
(defun RunDeleteSolids ( / count ssSolidHatch ssSolidEnt blk ent ed etype nextEnt )
  (setq count 0)
  
  ;; 1. Xóa Hatch SOLID trong ModelSpace và PaperSpace
  (if (setq ssSolidHatch (ssget "X" '((0 . "HATCH") (2 . "SOLID"))))
    (repeat (setq i (sslength ssSolidHatch))
      (if (entdel (ssname ssSolidHatch (setq i (1- i))))
        (setq count (1+ count))
      )
    )
  )

  ;; 2. Xóa thực thể SOLID (2D Solid) ngoài ModelSpace và PaperSpace
  (if (setq ssSolidEnt (ssget "X" '((0 . "SOLID"))))
    (repeat (setq i (sslength ssSolidEnt))
      (if (entdel (ssname ssSolidEnt (setq i (1- i))))
        (setq count (1+ count))
      )
    )
  )

  ;; 3. Quét sạch SOLID và HATCH SOLID bên trong tất cả Block Definitions
  (setq blk (tblnext "BLOCK" T))
  (while blk
    (setq ent (cdr (assoc -2 blk)))
    (while ent
      (setq ed (entget ent))
      (setq etype (cdr (assoc 0 ed)))
      (setq nextEnt (entnext ent))
      (cond
        ((and (= etype "HATCH") (= (strcase (cdr (assoc 2 ed))) "SOLID"))
         (if (entdel ent) (setq count (1+ count)))
        )
        ((= etype "SOLID")
         (if (entdel ent) (setq count (1+ count)))
        )
      )
      (setq ent nextEnt)
    )
    (setq blk (tblnext "BLOCK"))
  )

  (command "_.REGEN")
  (princ (strcat "\n[RevitAI] Đã xóa thành công " (itoa count) " đối tượng Hatch Solid / Solid (kể cả trong Block)."))
  count
)

(defun c:DeleteAllSolids ()
  (RunDeleteSolids)
  (princ)
)

;;; =========================================================================
;;; HÀM 2: TÌM LINE GẦN NHẤT & KÉO LINE NGHIÊNG (LEADER) TỪ ĐÁY TEXT CAO ĐỘ
;;; (Hạ thấp điểm xuất phát theo trục Y xuống 250mm dưới chân chữ)
;;; =========================================================================
(setq *MEP_LEADER_OFFSET_Y* 250.0)

(defun RunMepLeader ( targetLayer searchChar maxDist / 
                      ssPipes pipeList ssAllTexts textList i ent ed p1 p2 x1 x2 y1 y2
                      txtStr txtPt x0 y0 yLeader refPt tagLeft winMinX winMaxX winMinY winMaxY
                      bestDist bestPt pItem minX minY maxX maxY testPt ptStart leaderCount
                      offsetY ClosestPointOnSegment ssOld pEnt )

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

  (if (or (null targetLayer) (= targetLayer "")) (setq targetLayer "P-PIPE*"))
  (if (or (null searchChar) (= searchChar "")) (setq searchChar "+"))
  (if (or (null maxDist) (<= maxDist 0)) (setq maxDist 5000.0))
  (if (or (null *MEP_LEADER_OFFSET_Y*) (not (numberp *MEP_LEADER_OFFSET_Y*)))
    (setq offsetY 250.0)
    (setq offsetY *MEP_LEADER_OFFSET_Y*)
  )
  (setq leaderCount 0)

  ;; Đăng ký ứng dụng XData RevitAI
  (regapp "REVITAI_LEADER")

  ;; Xóa các leader RevitAI đã tạo trước đó trên mọi layer liên quan
  (if (setq ssOld (ssget "X" (list '(0 . "LINE") '(-3 ("REVITAI_LEADER")))))
    (repeat (setq i (sslength ssOld))
      (entdel (ssname ssOld (setq i (1- i))))
    )
  )

  ;; 1. Thu thập tất cả Line thuộc layer chỉ định (hỗ trợ P-PIPE và P-PIPE-CNTR)
  (setq ssPipes (ssget "X" (list '(0 . "LINE") (cons 8 targetLayer))))
  (if (null ssPipes)
    (cond
      ((wcmatch (strcase targetLayer) "*CNTR*")
       (setq targetLayer (vl-string-right-trim "-CNTR" (vl-string-right-trim "_CNTR" targetLayer)))
       (setq ssPipes (ssget "X" (list '(0 . "LINE") (cons 8 targetLayer))))
      )
      ((= (strcase targetLayer) "P-PIPE")
       (setq ssPipes (ssget "X" (list '(0 . "LINE") '(8 . "P-PIPE,P-PIPE-CNTR"))))
      )
    )
  )
  (if (null ssPipes)
    (setq ssPipes (ssget "X" (list '(0 . "LINE") (cons 8 (strcat targetLayer "*")))))
  )

  (setq pipeList nil actualLayer "P-PIPE")
  (if ssPipes
    (repeat (setq i (sslength ssPipes))
      (setq ent (ssname ssPipes (setq i (1- i))))
      (setq ed (entget ent))
      (setq p1 (cdr (assoc 10 ed))
            p2 (cdr (assoc 11 ed)))
      (if (= i 0) (setq actualLayer (cdr (assoc 8 ed))))
      (setq x1 (car p1) y1 (cadr p1) x2 (car p2) y2 (cadr p2))
      (setq pipeList (cons (list p1 p2 (min x1 x2) (min y1 y2) (max x1 x2) (max y1 y2)) pipeList))
    )
  )

  (if (null pipeList)
    (progn
      (princ (strcat "\n[RevitAI CẢNH BÁO] Không tìm thấy Line nào trên layer: " targetLayer))
      0
    )
    (progn
      ;; 2. Thu thập toàn bộ Text/MText một lần vào bộ nhớ
      (setq ssAllTexts (ssget "X" '((0 . "TEXT,MTEXT"))))
      (setq textList nil)
      (if ssAllTexts
        (repeat (setq i (sslength ssAllTexts))
          (setq ent (ssname ssAllTexts (setq i (1- i))))
          (setq ed (entget ent))
          (setq txtStr (cdr (assoc 1 ed)))
          (setq txtPt (cdr (assoc 10 ed)))
          (setq textList (cons (list txtStr txtPt (car txtPt) (cadr txtPt)) textList))
        )
      )

      ;; 3. Xử lý từng text cao độ chứa ký tự lọc (loại trừ bullet \U+2022)
      (foreach tItem textList
        (setq txtStr (car tItem)
              txtPt  (cadr tItem)
              x0     (caddr tItem)
              y0     (cadddr tItem))

        (if (and (wcmatch txtStr (strcat "*" searchChar "*"))
                 (not (wcmatch txtStr "*U+2022*"))
                 (not (wcmatch txtStr "*\\U+2022*")))
          (progn
            ;; Tìm tọa độ X tận cùng bên trái của cụm nhãn (ví dụ "25ø") trên cùng đường gióng y0
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

            ;; Quét tuyến ống trong cửa sổ va chạm không gian (AABB Filter)
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
                ;; Hạ thấp đường leader theo trục Y xuống offsetY (mặc định 250mm dưới chân chữ)
                (setq yLeader (- y0 offsetY))
                (if (< (car bestPt) tagLeft)
                  (setq ptStart (list tagLeft yLeader 0.0))
                  (setq ptStart (list x0 yLeader 0.0))
                )
                ;; Tạo đường line nghiêng leader trỏ vào tim ống kèm XData nhận diện
                (entmake (list '(0 . "LINE")
                               (cons 8 actualLayer)
                               (cons 10 ptStart)
                               (cons 11 bestPt)
                               (list -3 '("REVITAI_LEADER" (1000 . "PIPE_LEADER")))))
                (setq leaderCount (1+ leaderCount))
              )
            )
          )
        )
      )

      (command "_.REGEN")
      (princ (strcat "\n[RevitAI] Đã tạo thành công " (itoa leaderCount) " đường leader trỏ từ Text đến tuyến ống (Layer: " actualLayer ", Dịch Y: -" (rtos offsetY 2 1) "mm)."))
      leaderCount
    )
  )
)

(defun RunMepLeaderEx ( targetLayer searchChar maxDist offsetY / )
  (if offsetY (setq *MEP_LEADER_OFFSET_Y* offsetY))
  (RunMepLeader targetLayer searchChar maxDist)
)

(defun c:AddPipeLeaders ()
  (RunMepLeader "P-PIPE*" "+" 5000.0)
  (princ)
)

;;; =========================================================================
;;; HÀM 3: CHẠY ĐỒNG THỜI CẢ 2 TÁC VỤ (CLEAN SOLID + LEADER CAO ĐỘ)
;;; =========================================================================
(defun RunFullMepPolish ( targetLayer searchChar maxDist / resHatch resLeader )
  (princ "\n=== BẮT ĐẦU TỐI ƯU HÓA BẢN VẼ MEP AUTOCAD ===")
  (setq resHatch (RunDeleteSolids))
  (setq resLeader (RunMepLeader targetLayer searchChar maxDist))
  (princ (strcat "\n=== HOÀN TẤT: Xóa " (itoa resHatch) " Solid/Hatch • Tạo " (itoa resLeader) " Leader ==="))
  (list resHatch resLeader)
)

(defun RunFullMepPolishEx ( targetLayer searchChar maxDist offsetY / )
  (if offsetY (setq *MEP_LEADER_OFFSET_Y* offsetY))
  (RunFullMepPolish targetLayer searchChar maxDist)
)

(defun c:MepPolish ()
  (RunFullMepPolish "P-PIPE-CNTR" "+" 5000.0)
  (princ)
)

(princ "\n[RevitAI Studio] Đã nạp thành công bộ công cụ MEP_CLEANER_AND_LEADER.LSP!\n")
(princ)
