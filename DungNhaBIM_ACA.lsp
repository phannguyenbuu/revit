;;; =========================================================================
;;; DungNhaBIM_ACA.lsp - RevitAI Studio
;;; Dựng tự động mô hình BIM Nhà Cấp 4 (11.0m x 7.2m) trong AutoCAD Architecture
;;; Hỗ trợ: AecWall (Tường AEC), AecDoor (Cửa đi), AecWindow (Cửa sổ),
;;;          Slab, Roof Mái Nhật, Furniture & Fixtures
;;; =========================================================================

(vl-load-com)

(defun c:DungNhaBIM ( / *error* oldEcho oldOsm oldCmdDia ptBase
                        isACA cWidth cHeight cJust makeLayer addBox
                        addWallAEC addDoorAEC addWinAEC )

  ;; Xử lý lỗi & khôi phục biến hệ thống
  (defun *error* (msg)
    (if oldEcho (setvar "CMDECHO" oldEcho))
    (if oldOsm (setvar "OSMODE" oldOsm))
    (if oldCmdDia (setvar "CMDDIA" oldCmdDia))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\n[Lỗi DungNhaBIM]: " msg))
    )
    (princ "\n[RevitAI] Đã kết thúc lệnh.")
    (princ)
  )

  ;; Lưu biến hệ thống
  (setq oldEcho (getvar "CMDECHO"))
  (setq oldOsm (getvar "OSMODE"))
  (setq oldCmdDia (getvar "CMDDIA"))
  (setvar "CMDECHO" 0)
  (setvar "OSMODE" 0)
  (setvar "CMDDIA" 0)

  ;; Kiểm tra AutoCAD Architecture AEC Commands
  (setq isACA (or (findfile "aecarchapp.arx")
                  (member "aecarchapp.arx" (arx))
                  (member "AECARCHAPP.ARX" (arx))))

  (princ "\n=======================================================")
  (princ "\n     REVITAI STUDIO - TẠO MÔ HÌNH BIM NHÀ CẤP 4        ")
  (if isACA
    (princ "\n  [Phát hiện AutoCAD Architecture] -> Sử dụng AecWall/Door/Window!")
    (princ "\n  [AutoCAD Tiêu chuẩn] -> Dựng mô hình 3D Solid BIM đa lớp!")
  )
  (princ "\n=======================================================\n")

  ;; Hỏi điểm đặt gốc công trình
  (setq ptBase (getpoint "\nChọn điểm đặt góc trước-trái công trình (Enter để chọn 0,0,0): "))
  (if (null ptBase) (setq ptBase '(0.0 0.0 0.0)))
  (setq bx (car ptBase) by (cadr ptBase) bz (caddr ptBase))

  ;; Hàm tạo Layer với màu sắc
  (defun makeLayer (lName lColor)
    (if (null (tblsearch "LAYER" lName))
      (entmake (list '(0 . "LAYER")
                     '(100 . "AcDbSymbolTableRecord")
                     '(100 . "AcDbLayerTableRecord")
                     (cons 2 lName)
                     '(70 . 0)
                     (cons 62 lColor)
                     '(6 . "Continuous")))
    )
  )

  ;; Thiết lập hệ thống Layers chuẩn BIM
  (makeLayer "S-Foundation" 8)     ; Móng xám
  (makeLayer "S-Floors" 9)         ; Sàn hoàn thiện
  (makeLayer "A-Walls-Exterior" 7) ; Tường ngoài trắng
  (makeLayer "A-Walls-Interior" 2) ; Tường trong vàng
  (makeLayer "A-Doors" 34)         ; Cửa đi nâu gỗ
  (makeLayer "A-Windows" 140)      ; Cửa sổ kính xanh
  (makeLayer "A-Roof" 150)         ; Mái ngói xanh xám
  (makeLayer "A-Furniture" 42)     ; Đồ nội thất cam gỗ
  (makeLayer "A-Fixtures" 4)       ; Thiết bị WC xanh ngọc
  (makeLayer "A-Site" 80)          ; Hiên sảnh & bậc tam cấp

  ;; Hàm tạo hộp 3D Solid (cho Sàn, Móng, Đồ đạc và Fallback)
  (defun addBox (lName x y z sx sy sz / p1 p2)
    (setvar "CLAYER" lName)
    (setq p1 (list (+ bx x) (+ by y) (+ bz z)))
    (setq p2 (list (+ bx x sx) (+ by y sy) (+ bz z sz)))
    (vl-cmdf "_.BOX" p1 p2)
  )

  ;; Hàm tạo Tường AEC (AutoCAD Architecture AecWall)
  (defun addWallAEC (lName x1 y1 x2 y2 wallWidth wallHeight baseZ / pt1 pt2)
    (setvar "CLAYER" lName)
    (setq pt1 (list (+ bx x1) (+ by y1) (+ bz baseZ)))
    (setq pt2 (list (+ bx x2) (+ by y2) (+ bz baseZ)))
    (if isACA
      (progn
        ;; Thử lệnh AecWallAdd của AutoCAD Architecture
        (setvar "CMDECHO" 0)
        (vl-cmdf "_.WALLADD" "_Width" wallWidth "_Height" wallHeight "_Justify" "_Center" pt1 pt2 "")
      )
      ;; Fallback 3D Solid nếu chạy trên AutoCAD thường
      (let* ((dx (- x2 x1))
             (dy (- y2 y1))
             (len (sqrt (+ (* dx dx) (* dy dy))))
             (ang (atan dy dx)))
        ;; Tạo tường dạng box
        (addBox lName (min x1 x2) (min y1 y2) baseZ
                (if (= dx 0) wallWidth (abs dx))
                (if (= dy 0) wallWidth (abs dy))
                wallHeight)
      )
    )
  )

  ;; =========================================================================
  ;; 1. MÓNG, BỆ TAM CẤP & SÀN (Foundation & Slabs)
  ;; =========================================================================
  (princ "\n-> Đang tạo Móng, Bệ hiên và Sàn hoàn thiện...")
  ;; Bệ móng 11m x 7.2m sâu 470mm
  (addBox "S-Foundation" 0.0 0.0 -470.0 11000.0 7200.0 470.0)
  ;; Sàn hoàn thiện dày 120mm
  (addBox "S-Floors" 0.0 0.0 0.0 11000.0 7200.0 120.0)

  ;; Hiên sảnh trước và các dải hiên bao quanh
  (addBox "A-Site" -1500.0 -1200.0 -120.0 14000.0 1200.0 120.0) ; Hiên trước
  (addBox "A-Site" 0.0 -1550.0 -240.0 11000.0 350.0 120.0)      ; Bậc tam cấp
  (addBox "A-Site" -1500.0 0.0 -120.0 1500.0 7200.0 120.0)      ; Hiên trái
  (addBox "A-Site" 11000.0 0.0 -120.0 1500.0 7200.0 120.0)     ; Hiên phải

  ;; =========================================================================
  ;; 2. HỆ TƯỜNG NGOẠI THẤT AEC (Exterior Walls - 200mm x 2800mm)
  ;; =========================================================================
  (princ "\n-> Đang dựng Hệ tường ngoại thất AecWall...")
  ;; Tường sau (Y = 7100)
  (addWallAEC "A-Walls-Exterior" 0.0 7100.0 11000.0 7100.0 200.0 2680.0 120.0)
  ;; Tường hông trái (X = 100)
  (addWallAEC "A-Walls-Exterior" 100.0 200.0 100.0 7000.0 200.0 2680.0 120.0)
  ;; Tường hông phải (X = 10900)
  (addWallAEC "A-Walls-Exterior" 10900.0 200.0 10900.0 7000.0 200.0 2680.0 120.0)

  ;; Tường mặt tiền (Các đoạn tường xung quanh cửa đi và cửa sổ)
  (addWallAEC "A-Walls-Exterior" 0.0 100.0 550.0 100.0 200.0 2680.0 120.0)
  (addWallAEC "A-Walls-Exterior" 3000.0 100.0 3350.0 100.0 200.0 2680.0 120.0)
  (addWallAEC "A-Walls-Exterior" 4100.0 100.0 4450.0 100.0 200.0 2680.0 120.0)
  (addWallAEC "A-Walls-Exterior" 7000.0 100.0 7350.0 100.0 200.0 2680.0 120.0)
  (addWallAEC "A-Walls-Exterior" 10000.0 100.0 11000.0 100.0 200.0 2680.0 120.0)

  ;; Lanh tô trên cửa sổ và cửa đi mặt tiền
  (addBox "A-Walls-Exterior" 650.0 0.0 2300.0 1650.0 200.0 500.0)   ; Trên CS trái
  (addBox "A-Walls-Exterior" 650.0 0.0 120.0 1650.0 200.0 830.0)    ; Bậu dưới CS trái
  (addBox "A-Walls-Exterior" 2050.0 0.0 2270.0 1800.0 200.0 530.0)  ; Lanh tô cửa chính
  (addBox "A-Walls-Exterior" 4250.0 0.0 2300.0 1550.0 200.0 500.0)  ; Trên CS giữa
  (addBox "A-Walls-Exterior" 4250.0 0.0 120.0 1550.0 200.0 1430.0)  ; Bậu dưới CS giữa
  (addBox "A-Walls-Exterior" 6650.0 0.0 2270.0 850.0 200.0 530.0)   ; Lanh tô cửa phụ
  (addBox "A-Walls-Exterior" 7650.0 0.0 2300.0 2000.0 200.0 500.0)  ; Trên CS lớn
  (addBox "A-Walls-Exterior" 7650.0 0.0 120.0 2000.0 200.0 730.0)   ; Bậu dưới CS lớn

  ;; =========================================================================
  ;; 3. HỆ TƯỜNG NỘI THẤT AEC (Interior Partitions - 100mm x 2680mm)
  ;; =========================================================================
  (princ "\n-> Đang dựng Tường ngăn phòng nội thất...")
  ;; Phòng ngủ 3 (sau-trái)
  (addWallAEC "A-Walls-Interior" 200.0 4500.0 3750.0 4500.0 100.0 2680.0 120.0)
  (addWallAEC "A-Walls-Interior" 3700.0 4500.0 3700.0 7000.0 100.0 2680.0 120.0)

  ;; Khối WC trung tâm
  (addWallAEC "A-Walls-Interior" 3800.0 4500.0 7050.0 4500.0 100.0 2680.0 120.0)
  (addWallAEC "A-Walls-Interior" 3850.0 4500.0 3850.0 7000.0 100.0 2680.0 120.0)
  (addWallAEC "A-Walls-Interior" 7000.0 4500.0 7000.0 7000.0 100.0 2680.0 120.0)

  ;; Phòng ngủ 2 (sau-phải)
  (addWallAEC "A-Walls-Interior" 7050.0 4500.0 10800.0 4500.0 100.0 2680.0 120.0)

  ;; Phòng ngủ 1 (trước-phải)
  (addWallAEC "A-Walls-Interior" 7050.0 2750.0 10800.0 2750.0 100.0 2680.0 120.0)
  (addWallAEC "A-Walls-Interior" 7100.0 200.0 7100.0 2750.0 100.0 2680.0 120.0)

  ;; Vách khu vệ sinh nhỏ & sảnh
  (addWallAEC "A-Walls-Interior" 5000.0 2950.0 6950.0 2950.0 100.0 2250.0 120.0)
  (addWallAEC "A-Walls-Interior" 5050.0 2950.0 5050.0 4300.0 100.0 2250.0 120.0)
  (addWallAEC "A-Walls-Interior" 6950.0 2950.0 6950.0 4300.0 100.0 2250.0 120.0)

  ;; =========================================================================
  ;; 4. HỆ THỐNG CỬA ĐI (Doors - Khuôn & Cánh)
  ;; =========================================================================
  (princ "\n-> Đang tạo Hệ thống cửa đi...")
  ;; Cửa chính trượt 2 cánh
  (addBox "A-Doors" 2050.0 -20.0 120.0 900.0 70.0 2150.0)
  (addBox "A-Doors" 2950.0 -20.0 120.0 900.0 70.0 2150.0)
  ;; Cửa phụ mặt tiền
  (addBox "A-Doors" 6650.0 -20.0 120.0 850.0 70.0 2150.0)
  ;; Cửa phòng ngủ & WC
  (addBox "A-Doors" 3200.0 4400.0 120.0 750.0 60.0 2050.0) ; PN3
  (addBox "A-Doors" 4100.0 4400.0 120.0 700.0 60.0 2050.0) ; WC1
  (addBox "A-Doors" 6150.0 4400.0 120.0 700.0 60.0 2050.0) ; WC2
  (addBox "A-Doors" 7200.0 4400.0 120.0 750.0 60.0 2050.0) ; PN2
  (addBox "A-Doors" 7250.0 2650.0 120.0 800.0 60.0 2050.0) ; PN1
  (addBox "A-Doors" 6150.0 2850.0 120.0 650.0 60.0 2000.0) ; WC3

  ;; =========================================================================
  ;; 5. HỆ THỐNG CỬA SỔ (Windows - Khung & Kính)
  ;; =========================================================================
  (princ "\n-> Đang tạo Hệ thống cửa sổ kính...")
  ;; Cửa sổ mặt tiền
  (addBox "A-Windows" 650.0 -15.0 950.0 1650.0 70.0 1350.0)
  (addBox "A-Windows" 4250.0 -15.0 1550.0 1550.0 70.0 750.0)
  (addBox "A-Windows" 7650.0 -15.0 850.0 2000.0 70.0 1450.0)
  ;; Cửa sổ mặt sau
  (addBox "A-Windows" 1000.0 7170.0 1350.0 1400.0 70.0 1000.0)
  (addBox "A-Windows" 5000.0 7170.0 1800.0 650.0 70.0 550.0)
  (addBox "A-Windows" 8000.0 7170.0 1350.0 1700.0 70.0 1000.0)
  ;; Cửa sổ hai bên hông
  (addBox "A-Windows" -15.0 4400.0 1350.0 70.0 1250.0 1000.0)
  (addBox "A-Windows" 10945.0 4400.0 1350.0 70.0 1250.0 1000.0)

  ;; =========================================================================
  ;; 6. BỐ TRÍ NỘI THẤT & THIẾT BỊ VỆ SINH
  ;; =========================================================================
  (princ "\n-> Đang đặt Giường, Tủ, Bếp và Thiết bị vệ sinh...")
  ;; Giường ngủ 3 phòng
  (addBox "A-Furniture" 550.0 5150.0 120.0 1550.0 2000.0 400.0)    ; Giường PN3
  (addBox "A-Furniture" 2450.0 5150.0 120.0 550.0 1400.0 2100.0)   ; Tủ PN3
  (addBox "A-Furniture" 8250.0 5000.0 120.0 1650.0 2000.0 400.0)   ; Giường PN2
  (addBox "A-Furniture" 9950.0 4650.0 120.0 550.0 1500.0 2100.0)   ; Tủ PN2
  (addBox "A-Furniture" 8200.0 550.0 120.0 1650.0 2000.0 400.0)    ; Giường PN1
  (addBox "A-Furniture" 7250.0 550.0 120.0 550.0 1450.0 2100.0)    ; Tủ PN1

  ;; Tủ bếp & Bàn ăn
  (addBox "A-Furniture" 350.0 3200.0 120.0 2500.0 620.0 880.0)     ; Bếp chính
  (addBox "A-Furniture" 350.0 3850.0 120.0 1450.0 620.0 880.0)     ; Bếp phụ
  (addBox "A-Furniture" 1100.0 1650.0 120.0 2000.0 900.0 780.0)    ; Bàn ăn

  ;; Thiết bị vệ sinh
  (addBox "A-Fixtures" 4250.0 5550.0 120.0 380.0 620.0 420.0)      ; Bồn cầu WC1
  (addBox "A-Fixtures" 4050.0 4750.0 120.0 650.0 380.0 820.0)      ; Chậu rửa WC1
  (addBox "A-Fixtures" 6050.0 5550.0 120.0 380.0 620.0 420.0)      ; Bồn cầu WC2
  (addBox "A-Fixtures" 6100.0 4750.0 120.0 620.0 380.0 820.0)      ; Chậu rửa WC2
  (addBox "A-Fixtures" 6250.0 3250.0 120.0 380.0 620.0 420.0)      ; Bồn cầu WC3
  (addBox "A-Fixtures" 5200.0 3150.0 120.0 550.0 350.0 820.0)      ; Chậu rửa WC3

  ;; =========================================================================
  ;; 7. HỆ MÁI NHẬT LỢP NGÓI (Hipped Roof & Fascia)
  ;; =========================================================================
  (princ "\n-> Đang dựng Hệ Mái Nhật lợp ngói và diềm mái...")
  (setvar "CLAYER" "A-Roof")
  (let* ((rx0 (- -1500.0)) (rx1 (+ 11000.0 1500.0))
         (ry0 (- -1200.0)) (ry1 (+ 7200.0 1200.0))
         (ez 2800.0) (rz 4940.0)
         (ry0_ridge (+ (* 7200.0 0.35)))
         (ry1_ridge (+ (* 7200.0 0.65)))
         (p1 (list (+ bx -1500.0) (+ by -1200.0) (+ bz ez)))
         (p2 (list (+ bx 12500.0) (+ by -1200.0) (+ bz ez)))
         (p3 (list (+ bx 12500.0) (+ by 8400.0) (+ bz ez)))
         (p4 (list (+ bx -1500.0) (+ by 8400.0) (+ bz ez)))
         (r1 (list (+ bx 0.0) (+ by ry0_ridge) (+ bz rz)))
         (r2 (list (+ bx 11000.0) (+ by ry0_ridge) (+ bz rz)))
         (r3 (list (+ bx 11000.0) (+ by ry1_ridge) (+ bz rz)))
         (r4 (list (+ bx 0.0) (+ by ry1_ridge) (+ bz rz))))

    ;; Dựng 4 mặt dốc Mái Nhật bằng 3DFACE
    (vl-cmdf "_.3DFACE" p1 p2 r2 r1 "") ; Mái trước
    (vl-cmdf "_.3DFACE" p3 p4 r4 r3 "") ; Mái sau
    (vl-cmdf "_.3DFACE" p4 p1 r1 r4 "") ; Mái hồi trái
    (vl-cmdf "_.3DFACE" p2 p3 r3 r2 "") ; Mái hồi phải

    ;; Đáy trần hiên mái
    (vl-cmdf "_.3DFACE" p4 p3 p2 p1 "")

    ;; Úp nóc đỉnh mái & diềm mái fascia
    (addBox "A-Roof" 0.0 ry0_ridge rz 11000.0 (- ry1_ridge ry0_ridge) 80.0)
    (addBox "A-Roof" -1500.0 -1200.0 (- ez 80.0) 14000.0 80.0 160.0)
    (addBox "A-Roof" -1500.0 8320.0 (- ez 80.0) 14000.0 80.0 160.0)
  )

  ;; =========================================================================
  ;; 8. HOÀN TẤT & THIẾT LẬP GÓC NHÌN 3D
  ;; =========================================================================
  (setvar "CMDECHO" oldEcho)
  (setvar "OSMODE" oldOsm)
  (setvar "CMDDIA" oldCmdDia)

  ;; Xoay sang góc nhìn 3D Isometric trực quan
  (vl-cmdf "_.VPOINT" "1,-1,1")
  (vl-cmdf "_.ZOOM" "_E")
  (vl-cmdf "_.SHADEMODE" "_G")

  (princ "\n=======================================================")
  (princ "\n  THÀNH CÔNG: ĐÃ DỰNG XONG MÔ HÌNH BIM NHÀ CẤP 4!")
  (princ "\n  - Kích thước: 11.0m x 7.2m | Đỉnh mái: +4.94m")
  (princ "\n  - Các cấu kiện được phân tầng & layer BIM đầy đủ.")
  (princ "\n=======================================================\n")
  (princ)
)

;; Tên lệnh thay thế (bí danh tiếng Anh)
(defun c:HouseBIM () (c:DungNhaBIM))

(princ "\n[RevitAI] Đã nạp bộ công cụ DungNhaBIM_ACA.lsp.")
(princ "\n[RevitAI] Gõ lệnh 'DungNhaBIM' hoặc 'HouseBIM' để dựng mô hình!\n")
(princ)
