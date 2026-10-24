import sys

with open('web_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''          <div id="subpane-etabs-3d" class="etabs-subpane hidden space-y-3">



            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">



              <div class="flex items-center gap-3">



                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">



                  <i data-lucide="box" class="w-3.5 h-3.5 text-indigo-600"></i> Điều khiển 3D:



                </span>



                <span class="text-[11px] text-slate-500">Chuột trái: Xoay 360° • Lăn chuột: Phóng to/nhỏ • Chuột phải: Dời hình • Bấm vào dầm: Chọn cốt thép</span>



              </div>



            </div>'''

replacement1 = '''          <div id="subpane-etabs-3d" class="etabs-subpane hidden space-y-3">

            <!-- AEC 3D Interactive Studio Toolbar (Wall Line, Door Block, Snap & Round 50/100) -->
            <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2">
              <div class="flex flex-wrap items-center justify-between gap-2.5">
                <!-- 1. Tool Modes -->
                <div class="inline-flex items-center gap-1 p-1 bg-slate-200/90 rounded-xl border border-slate-300">
                  <button type="button" onclick="setAecToolMode('select')" id="aecBtnModeSelect" class="py-1 px-3 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-xs transition cursor-pointer flex items-center gap-1.5" title="Chế độ xoay, phóng to và chọn đối tượng">
                    🖐️ Xem 3D
                  </button>
                  <button type="button" onclick="setAecToolMode('wall')" id="aecBtnModeWall" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-white/80 transition cursor-pointer flex items-center gap-1.5" title="Vẽ Tường dạng đường Line (Bấm điểm đầu, rê chuột, bấm điểm cuối)">
                    🧱 Vẽ Tường (Line)
                  </button>
                  <button type="button" onclick="setAecToolMode('door')" id="aecBtnModeDoor" class="py-1 px-3 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-white/80 transition cursor-pointer flex items-center gap-1.5" title="Đặt Cửa dạng Block (Phím Space để xoay 90°)">
                    🚪 Đặt Cửa (Block)
                  </button>
                </div>

                <!-- 2. Snap & Round 50 / 100 -->
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-slate-700 flex items-center gap-1">
                    🧲 Snap & Round:
                  </span>
                  <div class="inline-flex items-center gap-0.5 p-0.5 bg-slate-200/90 rounded-lg border border-slate-300 text-xs font-bold">
                    <button type="button" onclick="setAecSnapRound(50)" id="aecBtnSnap50" class="py-1 px-2.5 rounded text-slate-700 hover:bg-white/80 transition cursor-pointer" title="Làm tròn tọa độ 50 mm">
                      50 mm
                    </button>
                    <button type="button" onclick="setAecSnapRound(100)" id="aecBtnSnap100" class="py-1 px-2.5 rounded bg-indigo-600 text-white shadow-xs transition cursor-pointer" title="Làm tròn tọa độ 100 mm">
                      100 mm
                    </button>
                    <button type="button" onclick="setAecSnapRound(0)" id="aecBtnSnapOff" class="py-1 px-2 rounded text-slate-500 hover:bg-white/80 transition cursor-pointer" title="Tắt làm tròn tọa độ">
                      Tắt
                    </button>
                  </div>

                  <label class="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer select-none ml-1 font-semibold">
                    <input type="checkbox" id="aecChkSnapGeom" checked onchange="toggleAecSnapGeom(this.checked)" class="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
                    <span>Snap Cột/Dầm</span>
                  </label>
                </div>

                <!-- 3. Story Elevation Selection & Actions -->
                <div class="flex items-center gap-2">
                  <div class="flex items-center gap-1 text-xs">
                    <span class="font-bold text-slate-700">Tầng:</span>
                    <select id="aecStorySelect" onchange="changeAecStory(this.value)" class="py-1 px-2 rounded-lg border border-slate-300 bg-white text-xs font-bold text-slate-700 shadow-xs focus:ring-1 focus:ring-indigo-500">
                      <option value="T1">Tầng 1 (0.0 m)</option>
                      <option value="T2">Tầng 2 (7.6 m)</option>
                      <option value="T3" selected>Tầng 3 (11.8 m)</option>
                      <option value="T4">Tầng 4 (15.6 m)</option>
                      <option value="TM">Mái (18.4 m)</option>
                    </select>
                  </div>

                  <button type="button" onclick="undoLastAecElement()" class="py-1 px-2.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-bold transition flex items-center gap-1 cursor-pointer" title="Hoàn tác vật thể vừa vẽ (Ctrl+Z)">
                    ↩️ Hoàn Tác
                  </button>

                  <button type="button" onclick="clearAllAecElements()" class="py-1 px-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold transition flex items-center gap-1 cursor-pointer" title="Xóa toàn bộ Tường & Cửa đã vẽ">
                    🗑️ Xóa AEC
                  </button>

                  <span id="aecBadgeCount" class="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold">
                    0 Tường • 0 Cửa
                  </span>
                </div>
              </div>

              <!-- Parameter Sub-Row: Wall & Door Quick Options -->
              <div id="aecParamSubRow" class="flex flex-wrap items-center justify-between text-xs pt-1.5 border-t border-slate-200 text-slate-600">
                <div id="aecWallParams" class="flex items-center gap-3">
                  <span class="font-bold text-amber-700 flex items-center gap-1">🧱 Tường Line:</span>
                  <span class="text-slate-500 font-medium">Bề dày:</span>
                  <div class="inline-flex p-0.5 bg-slate-200 rounded border border-slate-300 text-[11px] font-bold">
                    <button type="button" onclick="setAecWallThickness(100)" id="aecBtnWall100" class="px-2 py-0.5 rounded bg-amber-600 text-white cursor-pointer">100 mm</button>
                    <button type="button" onclick="setAecWallThickness(200)" id="aecBtnWall200" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">200 mm</button>
                  </div>
                  <span class="text-slate-500 font-medium ml-1">Chiều cao:</span>
                  <div class="inline-flex p-0.5 bg-slate-200 rounded border border-slate-300 text-[11px] font-bold">
                    <button type="button" onclick="setAecWallHeight(3000)" id="aecBtnWallH3000" class="px-2 py-0.5 rounded bg-amber-600 text-white cursor-pointer">3,000 mm</button>
                    <button type="button" onclick="setAecWallHeight(3800)" id="aecBtnWallH3800" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">3,800 mm</button>
                  </div>
                  <span class="text-[11px] text-slate-400 italic">💡 Bấm điểm đầu ➔ kéo chuột ➔ bấm điểm cuối (Giữ Shift khóa trục, Esc hủy)</span>
                </div>

                <div id="aecDoorParams" class="hidden flex items-center gap-3">
                  <span class="font-bold text-emerald-700 flex items-center gap-1">🚪 Cửa Block:</span>
                  <span class="text-slate-500 font-medium">Bề rộng:</span>
                  <div class="inline-flex p-0.5 bg-slate-200 rounded border border-slate-300 text-[11px] font-bold">
                    <button type="button" onclick="setAecDoorWidth(800)" id="aecBtnDoor800" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">800 mm</button>
                    <button type="button" onclick="setAecDoorWidth(900)" id="aecBtnDoor900" class="px-2 py-0.5 rounded bg-emerald-600 text-white cursor-pointer">900 mm</button>
                    <button type="button" onclick="setAecDoorWidth(1200)" id="aecBtnDoor1200" class="px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer">1,200 mm</button>
                  </div>
                  <button type="button" onclick="rotateAecDoor()" class="py-0.5 px-2.5 rounded bg-slate-200 hover:bg-slate-300 font-bold text-[11px] flex items-center gap-1 cursor-pointer" title="Xoay hướng cửa 90° (hoặc bấm phím Space)">
                    🔄 Xoay: <span id="aecDoorAngleLabel" class="text-indigo-600 font-mono">0°</span> (Phím Space)
                  </button>
                  <span class="text-[11px] text-slate-400 italic">💡 Rê chuột đến tường hoặc mặt bằng ➔ bấm chuột để đặt</span>
                </div>
              </div>
            </div>'''

target2 = '''              <div id="etabs3DContainer" class="w-full h-full"></div>'''

replacement2 = '''              <div id="etabs3DContainer" class="w-full h-full"></div>

              <!-- Floating 3D AEC HUD Hint & Coordinates -->
              <div id="aec3DHintHUD" class="absolute bottom-3 right-3 z-20 hidden bg-slate-900/90 backdrop-blur-md text-white text-xs px-3.5 py-2 rounded-xl border border-indigo-400/50 shadow-xl pointer-events-none transition-all space-y-1">
                <div class="flex items-center gap-2">
                  <span id="aec3DHintIcon" class="text-base">🧱</span>
                  <span id="aec3DHintText" class="font-bold text-amber-300">Vẽ Tường (Line)</span>
                </div>
                <div id="aec3DHintCoord" class="text-[11px] font-mono text-slate-300">Snap: 100mm • Bấm điểm đầu</div>
              </div>'''

if target1 in content and target2 in content:
    content = content.replace(target1, replacement1, 1)
    content = content.replace(target2, replacement2, 1)
    with open('web_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: web_dashboard.py updated!")
else:
    print("ERROR: targets not found!")
    print("target1 found:", target1 in content)
    print("target2 found:", target2 in content)
