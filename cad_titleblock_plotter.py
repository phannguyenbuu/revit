#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cad_titleblock_plotter.py
Mô-đun quét, phân tích, sắp xếp và in hàng loạt (Batch Plot) các khung tên (Titleblock)
trong AutoCAD từ các đối tượng mảng (Associative Array) hoặc Block Reference đơn lẻ.
"""

import os
import sys
import re
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import send_to_acad

LSP_SCANNER_PATH = os.path.join(CURRENT_DIR, "cad_scan_titleblocks.lsp").replace("\\", "/")

def decode_acad_text(txt):
    """Giải mã các chuỗi ký tự đặc biệt của AutoCAD (Unicode hex, %%U, %%C, %%D, %%P...)."""
    if not txt:
        return ""
    try:
        txt = re.sub(r'\\U\+([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), txt)
    except Exception:
        pass
    txt = re.sub(r'%%[uU]', '', txt)
    txt = re.sub(r'%%[dD]', '°', txt)
    txt = re.sub(r'%%[pP]', '±', txt)
    txt = re.sub(r'%%[cC]', 'Ø', txt)
    txt = re.sub(r'\\P', ' ', txt)
    txt = re.sub(r'\{[^}]*\}', '', txt)
    txt = re.sub(r'\\[A-Za-z0-9]+;', '', txt)
    return txt.strip()

def scan_titleblocks_in_acad(scope="selection", skip_empty=True, sort_mode="x_then_y", min_entities=1):
    """
    Quét các khung tên trong AutoCAD (trong Selection hoặc toàn bản vẽ).
    Tự động bóc tách các mảng Associative Array (*U...) và xác định khung có nội dung.
    """
    hwnd, title = send_to_acad.get_acad_hwnd()
    if not hwnd:
        return {
            "success": False,
            "message": "Không tìm thấy cửa sổ AutoCAD đang mở trên màn hình.",
            "items": []
        }

    doc_name = title.split("[")[-1].replace("]", "") if "[" in title else title
    run_id = int(time.time() * 1000)
    out_file = os.path.join(CURRENT_DIR, f"scratch_tb_scan_{run_id}.txt").replace("\\", "/")

    # Gọi LISP quét
    cmd = f'(progn (load "{LSP_SCANNER_PATH}") (setq f (open "{out_file}" "w")) (c:ScanTitleblocksEx) )\n'
    
    # Chuẩn bị lệnh chạy
    run_lsp = os.path.join(CURRENT_DIR, f"scratch_run_scan_{run_id}.lsp").replace("\\", "/")
    run_lsp_content = f"""(vl-load-com)
(load "{LSP_SCANNER_PATH}")
;; Ghi đè outFile
(defun c:RunMyScan ( / )
  (setq oldF (open "{out_file}" "w"))
  (close oldF)
)
"""
    # Thay vào đó, tạo 1 lsp nhỏ gọi trực tiếp hàm với tham số đường dẫn
    mini_runner = f"""(vl-load-com)
(load "{LSP_SCANNER_PATH}")
(defun c:DoScan ( / )
  (setq f (open "{out_file}" "w"))
  (setq ss nil)
  {"(setq ss (ssget \"_I\")) (if (not ss) (setq ss (ssget \"_P\")))" if scope == "selection" else "(setq ss (ssget \"X\" '((0 . \"INSERT\"))))"}
  (if (not ss)
    {"(setq ss (ssget \"X\" '((0 . \"INSERT\") (2 . \"`*U*\"))))" if scope == "selection" else "(setq ss (ssget \"X\" '((0 . \"INSERT\"))))"}
  )
  (if ss
    (repeat (setq i (sslength ss))
      (setq ent (ssname ss (setq i (1- i))))
      (setq ed (entget ent))
      (setq bn (cdr (assoc 2 ed)))
      (if (and bn (wcmatch (strcase bn) "`*U*"))
        (progn
          (setq btrEnt (tblobjname "BLOCK" bn))
          (if btrEnt
            (progn
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
              (if (> (length cellOffsets) 1)
                (progn
                  (setq cellOffsets (reverse cellOffsets))
                  (setq cellNames (reverse cellNames))
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
                  (setq arrPos (cdr (assoc 10 ed)))
                  (setq arrBaseX (car arrPos))
                  (setq arrBaseY (cadr arrPos))
                  (setq tbW 42957.9)
                  (setq tbH 27533.7)
                  (setq k 0)
                  (foreach cOff cellOffsets
                    (setq cellBaseX (+ arrBaseX (car cOff) (car tbRelOffset)))
                    (setq cellBaseY (+ arrBaseY (cadr cOff) (cadr tbRelOffset)))
                    (setq xmin cellBaseX)
                    (setq ymin cellBaseY)
                    (setq xmax (+ xmin tbW))
                    (setq ymax (+ ymin tbH))
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
                    (setq bestTitle "")
                    (foreach tStr (reverse txtList)
                      (if (or (wcmatch (strcase tStr) "*MB*")
                              (wcmatch (strcase tStr) "*B*N V*")
                              (wcmatch (strcase tStr) "*KH*I NH*")
                              (wcmatch (strcase tStr) "*CHI TI*T*")
                              (wcmatch (strcase tStr) "*S* *")
                              (wcmatch (strcase tStr) "*HI*N TR*NG*")
                              (wcmatch (strcase tStr) "*TR*C*"))
                        (if (equal bestTitle "")
                          (setq bestTitle tStr)
                        )
                      )
                    )
                    (if (and (equal bestTitle "") (> (length txtList) 0))
                      (setq bestTitle (car (reverse txtList)))
                    )
                    (write-line (strcat "ROW\t" bn "\t" (itoa k) "\t" (if tbBlockName tbBlockName "") "\t"
                                        (rtos xmin 2 2) "\t" (rtos ymin 2 2) "\t"
                                        (rtos xmax 2 2) "\t" (rtos ymax 2 2) "\t"
                                        (rtos tbW 2 2) "\t" (rtos tbH 2 2) "\t"
                                        (itoa totalEnts) "\t" (itoa textCnt) "\t"
                                        (itoa dimCnt) "\t" (itoa lineCnt) "\t" (itoa hatchCnt) "\t"
                                        bestTitle) f)
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
  (princ "\nDone DoScan\n")
  (princ)
)
(c:DoScan)
"""
    try:
        with open(run_lsp, "w", encoding="utf-8") as f:
            f.write(mini_runner)

        # Clear active prompt & load LISP without clearing selection
        send_to_acad.send_acad_command('")" ) ) ) ) (princ)\n', skip_esc=True)
        time.sleep(0.1)
        ok, msg = send_to_acad.send_acad_command(f'(load "{run_lsp}")\n', timeout_ms=30000, skip_esc=True)
        if not ok:
            return {"success": False, "message": f"Không thể gửi lệnh AutoLISP vào AutoCAD: {msg}", "items": []}

        # Wait for TXT file
        for _ in range(40):
            time.sleep(0.5)
            if os.path.exists(out_file):
                break
        else:
            return {"success": False, "message": "Quá thời gian chờ AutoCAD phản hồi kết quả quét.", "items": []}

        # Đọc dữ liệu phân tích
        lines = []
        with open(out_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.rstrip("\r\n") for l in f]

        raw_items = []
        sample_texts_dict = {}

        for l in lines:
            if not l:
                continue
            parts = l.split("\t")
            if parts[0] == "TXT" and len(parts) >= 3:
                k_idx = int(parts[1])
                txt_val = parts[2].strip()
                if txt_val:
                    sample_texts_dict.setdefault(k_idx, []).append(txt_val)
            elif parts[0] == "ROW" and len(parts) >= 16:
                raw_items.append({
                    "arrayBlock": parts[1],
                    "cellIndex": int(parts[2]),
                    "tbName": parts[3],
                    "xmin": float(parts[4]),
                    "ymin": float(parts[5]),
                    "xmax": float(parts[6]),
                    "ymax": float(parts[7]),
                    "width": float(parts[8]),
                    "height": float(parts[9]),
                    "totalEntities": int(parts[10]),
                    "textCount": int(parts[11]),
                    "dimCount": int(parts[12]),
                    "lineCount": int(parts[13]),
                    "hatchCount": int(parts[14]),
                    "rawTitle": parts[15] if len(parts) > 15 else ""
                })

        processed_items = []
        for idx, it in enumerate(raw_items):
            total_ents = it["totalEntities"]
            text_cnt = it["textCount"]
            dim_cnt = it["dimCount"]
            line_cnt = it["lineCount"]
            hatch_cnt = it["hatchCount"]
            k_idx = it["cellIndex"]

            # Phán đoán có nội dung để in
            has_content = (total_ents >= min_entities) or (text_cnt > 0 and (line_cnt > 0 or dim_cnt > 0 or hatch_cnt > 0))
            if skip_empty and not has_content:
                continue

            raw_title = it["rawTitle"]
            sample_list = [decode_acad_text(s) for s in sample_texts_dict.get(k_idx, []) if s]
            
            # Ưu tiên tìm tên bản vẽ chuẩn trong danh sách text
            prioritized_title = ""
            for s in sample_list:
                s_up = s.upper()
                if any(k in s_up for k in ["MB HIỆN TRẠNG", "MẶT BẰNG HIỆN TRẠNG", "MẶT BẰNG ĐỊNH VỊ", "MẶT CẮT", "MẶT ĐỨNG", "BẢN VẼ XIN PHÉP", "KHỐI NHÀ 3 TẦNG"]):
                    prioritized_title = s
                    break
            if not prioritized_title:
                for s in sample_list:
                    s_up = s.upper()
                    if s_up.startswith("MB ") or s_up.startswith("MẶT BẰNG ") or s_up.startswith("MC ") or s_up.startswith("MĐ "):
                        prioritized_title = s
                        break
            if not prioritized_title and raw_title:
                prioritized_title = decode_acad_text(raw_title)

            decoded_title = prioritized_title
            if not decoded_title:
                decoded_title = " | ".join(sample_list[:2]) if sample_list else ("(Khung trống)" if not has_content else "(Bản vẽ không tên)")

            # Chuẩn hóa một số từ viết tắt / lỗi font thường gặp
            decoded_title = re.sub(r'\bXY DỰNG\b', 'XÂY DỰNG', decoded_title)
            decoded_title = re.sub(r'\bPHP\b', 'PHÉP', decoded_title)
            decoded_title = re.sub(r'\bNH Ở\b', 'NHÀ Ở', decoded_title)
            decoded_title = re.sub(r'\bMI\b', 'MÁI', decoded_title)

            # Bổ sung thông tin địa chỉ nếu là trang bìa
            col_name = "Cột 1" if it["xmin"] < 160000 else "Cột 2"
            addr_suffix = " (163 Phan Bội Châu)" if it["xmin"] < 160000 else " (165 Phan Bội Châu)"
            if "BẢN VẼ XIN PHÉP" in decoded_title.upper() or "ĐỊNH VỊ" in decoded_title.upper():
                if "163" not in decoded_title and "165" not in decoded_title:
                    decoded_title += addr_suffix

            # Phân loại loại bản vẽ
            sheet_type = "Bản vẽ chi tiết"
            title_upper = decoded_title.upper()
            if "BẢN VẼ XIN PHÉP" in title_upper or "CHỦ ĐẦU TƯ" in title_upper or "BÌA" in title_upper:
                sheet_type = "Bìa / Pháp lý"
            elif "MẶT BẰNG ĐỊNH VỊ" in title_upper or "HỌA ĐỒ" in title_upper or "VỊ TRÍ" in title_upper:
                sheet_type = "Mặt bằng định vị"
            elif "MẶT BẰNG" in title_upper or "MB" in title_upper:
                sheet_type = "Mặt bằng kiến trúc"
            elif "MẶT CẮT" in title_upper:
                sheet_type = "Mặt cắt"
            elif "MẶT ĐỨNG" in title_upper:
                sheet_type = "Mặt đứng"

            processed_items.append({
                "id": idx + 1,
                "columnName": col_name,
                "arrayBlock": it["arrayBlock"],
                "cellIndex": it["cellIndex"],
                "tbName": it["tbName"],
                "xmin": it["xmin"],
                "ymin": it["ymin"],
                "xmax": it["xmax"],
                "ymax": it["ymax"],
                "width": it["width"],
                "height": it["height"],
                "totalEntities": total_ents,
                "textCount": text_cnt,
                "dimCount": dim_cnt,
                "lineCount": line_cnt,
                "hatchCount": hatch_cnt,
                "hasContent": has_content,
                "title": decoded_title,
                "sheetType": sheet_type,
                "sampleTexts": sample_list[:5]
            })

        # Sắp xếp theo yêu cầu
        if sort_mode == "x_then_y":
            def sort_key(item):
                col_bucket = round(item["xmin"] / 2000.0)
                return (col_bucket, item["ymin"])
            processed_items.sort(key=sort_key)
        elif sort_mode == "y_then_x":
            def sort_key(item):
                row_bucket = round(item["ymin"] / 2000.0)
                return (row_bucket, item["xmin"])
            processed_items.sort(key=sort_key)

        for i, item in enumerate(processed_items):
            item["stt"] = i + 1

        total_scanned = len(raw_items)
        total_content = len(processed_items) if skip_empty else len([x for x in processed_items if x["hasContent"]])
        total_empty = total_scanned - total_content

        return {
            "success": True,
            "message": f"Quét thành công {total_scanned} khung tên từ AutoCAD [{doc_name}]. Tìm thấy {total_content} khung có nội dung bản vẽ.",
            "dwgName": doc_name,
            "totalScanned": total_scanned,
            "totalWithContent": total_content,
            "totalEmpty": total_empty,
            "items": processed_items
        }
    finally:
        for f_temp in [run_lsp, out_file]:
            try:
                if os.path.exists(f_temp):
                    os.remove(f_temp)
            except Exception:
                pass


def zoom_to_region_in_acad(xmin, ymin, xmax, ymax):
    """Zoom màn hình AutoCAD vào khung tên chỉ định kèm 5% margin lề."""
    hwnd, title = send_to_acad.get_acad_hwnd()
    if not hwnd:
        return False, "Không tìm thấy cửa sổ AutoCAD đang mở."

    dx = xmax - xmin
    dy = ymax - ymin
    margin_x = dx * 0.05
    margin_y = dy * 0.05

    z_xmin = xmin - margin_x
    z_ymin = ymin - margin_y
    z_xmax = xmax + margin_x
    z_ymax = ymax + margin_y

    cmd = f'(command "_.ZOOM" "_W" (list {z_xmin:.2f} {z_ymin:.2f} 0.0) (list {z_xmax:.2f} {z_ymax:.2f} 0.0))\n'
    ok, msg = send_to_acad.send_acad_command(cmd, skip_esc=False)
    return ok, msg


def generate_batch_plot_script(items, plot_device="DWG To PDF.pc3", paper_size="ISO_full_bleed_A3_(420.00_x_297.00_MM)", plot_style="monochrome.ctb", output_dir=None):
    """
    Tạo mã AutoLISP in hàng loạt (Batch Plot) các vùng Region đã chọn sang PDF.
    """
    if not output_dir:
        output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "BatchPlot_PDF").replace("\\", "/")
    else:
        output_dir = output_dir.replace("\\", "/")
    os.makedirs(output_dir, exist_ok=True)

    lsp_lines = [
        "(vl-load-com)",
        f";; Batch Plot Generated by RevitAI Studio - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "(defun c:BatchPlotAll ( / oldCmdecho oldFiledia )",
        "  (setq oldCmdecho (getvar \"CMDECHO\"))",
        "  (setq oldFiledia (getvar \"FILEDIA\"))",
        "  (setvar \"CMDECHO\" 0)",
        "  (setvar \"FILEDIA\" 0)",
        "  (princ \"\\n=== BẮT ĐẦU IN HÀNG LOẠT (BATCH PLOT) ===\\n\")"
    ]

    for item in items:
        stt = item.get("stt", item.get("id", 1))
        title = item.get("title", f"Sheet_{stt}")
        clean_title = re.sub(r'[^\w\-]+', '_', title).strip('_')
        if not clean_title:
            clean_title = f"Sheet_{stt}"

        pdf_name = f"{stt:02d}_{clean_title}.pdf"
        full_pdf_path = f"{output_dir}/{pdf_name}".replace("\\", "/")

        xmin = item.get("xmin", 0.0)
        ymin = item.get("ymin", 0.0)
        xmax = item.get("xmax", 0.0)
        ymax = item.get("ymax", 0.0)

        lsp_lines.append(f'  (princ "\\n[{stt:02d}] Đang in: {pdf_name}...\\n")')
        lsp_lines.append(
            f'  (command "-PLOT" "Y" "" "{plot_device}" "{paper_size}" "M" "L" "N" "W" '
            f'(list {xmin:.2f} {ymin:.2f} 0.0) (list {xmax:.2f} {ymax:.2f} 0.0) '
            f'"F" "C" "Y" "{plot_style}" "Y" "A" "{full_pdf_path}" "N" "Y")'
        )

    lsp_lines.append("  (setvar \"CMDECHO\" oldCmdecho)")
    lsp_lines.append("  (setvar \"FILEDIA\" oldFiledia)")
    lsp_lines.append(f'  (princ "\\n=== IN HOÀN TẤT: Toàn bộ PDF đã lưu tại: {output_dir} ===\\n")')
    lsp_lines.append("  (princ)")
    lsp_lines.append(")")
    lsp_lines.append("(c:BatchPlotAll)")

    script_path = os.path.join(output_dir, "batch_plot_run.lsp").replace("\\", "/")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lsp_lines))

    return script_path, output_dir


def execute_batch_plot_in_acad(items, plot_device="DWG To PDF.pc3", paper_size="ISO_full_bleed_A3_(420.00_x_297.00_MM)", plot_style="monochrome.ctb", output_dir=None):
    """Thực thi trực tiếp lệnh in hàng loạt vào AutoCAD."""
    script_path, out_dir = generate_batch_plot_script(items, plot_device, paper_size, plot_style, output_dir)
    send_to_acad.send_acad_command('")" ) ) ) ) (princ)\n', skip_esc=False)
    time.sleep(0.2)
    ok, msg = send_to_acad.send_acad_command(f'(load "{script_path}")\n', timeout_ms=60000, skip_esc=True)
    return {
        "success": ok,
        "message": f"Đã gửi lệnh in hàng loạt {len(items)} bản vẽ vào AutoCAD! Thư mục xuất: {out_dir}",
        "scriptPath": script_path,
        "outputDir": out_dir
    }


if __name__ == "__main__":
    res = scan_titleblocks_in_acad(scope="selection", skip_empty=True, sort_mode="x_then_y")
    print("Scan status:", res["success"])
    print("Message:", res["message"])
    print(f"Total Scanned: {res.get('totalScanned')}, With Content: {res.get('totalWithContent')}, Empty: {res.get('totalEmpty')}")
    for it in res.get("items", []):
        print(f"[{it['stt']:02d}] {it['title']} ({it['sheetType']}) | {it['columnName']} | Region: ({it['xmin']:.1f}, {it['ymin']:.1f}) -> ({it['xmax']:.1f}, {it['ymax']:.1f}) | WxH: {it['width']:.1f}x{it['height']:.1f} | Ents: {it['totalEntities']}")
