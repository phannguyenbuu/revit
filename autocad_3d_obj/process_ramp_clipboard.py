import struct
import subprocess
import os

ole_path = r"C:\Users\Admin\.gemini\antigravity\scratch\new_clipboard_ole.bin"
dwg_path = r"C:\Users\Admin\.gemini\antigravity\scratch\ramp_extracted.dwg"
dxf_path = r"C:\Users\Admin\.gemini\antigravity\scratch\ramp_extracted.dxf"

with open(ole_path, "rb") as f:
    data = f.read()

sector_shift = struct.unpack_from("<H", data, 30)[0]
sector_size = 1 << sector_shift
first_dir_sector = struct.unpack_from("<I", data, 48)[0]
mini_cutoff = struct.unpack_from("<I", data, 56)[0]

fat_sectors = [struct.unpack_from("<I", data, 76 + i*4)[0] for i in range(109) if struct.unpack_from("<I", data, 76 + i*4)[0] < 0xFFFFFFFD]
fat = []
for sec in fat_sectors:
    off = (sec + 1) * sector_size
    fat.extend(struct.unpack(f"<{sector_size // 4}I", data[off:off+sector_size]))

def get_chain(start_sec):
    chain = []
    sec = start_sec
    while sec < 0xFFFFFFFD and sec < len(fat):
        chain.append(sec)
        sec = fat[sec]
    return chain

dir_chain = get_chain(first_dir_sector)
dir_data = b"".join(data[(s+1)*sector_size : (s+2)*sector_size] for s in dir_chain)

dwg_found = False
for i in range(len(dir_data) // 128):
    eb = dir_data[i*128 : (i+1)*128]
    n_len = struct.unpack_from("<H", eb, 64)[0]
    if n_len <= 2:
        continue
    name = eb[:n_len-2].decode("utf-16le", errors="replace")
    obj_type = eb[66]
    start_sec = struct.unpack_from("<I", eb, 116)[0]
    size = struct.unpack_from("<Q", eb, 120)[0]
    if obj_type == 2 and size >= mini_cutoff:
        s_chain = get_chain(start_sec)
        s_data = b"".join(data[(s+1)*sector_size : (s+2)*sector_size] for s in s_chain)[:size]
        if s_data.startswith(b"AC10"):
            with open(dwg_path, "wb") as f_out:
                f_out.write(s_data)
            print(f"Extracted DWG ({s_data[:6].decode('latin1')}, {size} bytes)")
            dwg_found = True
            break

if not dwg_found:
    print("DWG not found")
    exit(1)

# Convert to DXF via accoreconsole
accore = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
scr_path = r"C:\Users\Admin\.gemini\antigravity\scratch\_temp_ramp.scr"
with open(scr_path, "w", encoding="utf-8") as f:
    f.write(f'DXFOUT "{dxf_path.replace(os.sep, "/")}" 16\nQUIT\n')

res = subprocess.run([accore, "/i", dwg_path, "/s", scr_path], capture_output=True, text=True)
if os.path.exists(scr_path):
    os.remove(scr_path)

print("DXF output exists:", os.path.exists(dxf_path), "size:", os.path.getsize(dxf_path) if os.path.exists(dxf_path) else 0)
