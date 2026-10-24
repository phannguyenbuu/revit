/**
 * mep_3d_hub.js - Client-side Controller & Three.js WebGL Viewer for RevitAI MEP Studio
 * Tích hợp toàn diện 6 chức năng tự động 3D:
 * 1. Thiết kế điện & chiếu sáng (Đèn LED, Máng cáp, Tủ điện)
 * 2. Thiết kế cấp thoát nước (Ống PPR, Ống uPVC dốc 2%, Thiết bị vệ sinh)
 * 3. Thiết kế điều hòa, thông gió HVAC (FCU, Ống gió, Miệng gió, Quạt hút)
 * 4. Dựng mô hình BIM 3D chuyên nghiệp (Three.js WebGL, IFC, OBJ, DXF)
 * 5. Kiểm tra xung đột hệ thống MEP (Clash Detection & 3D Glowing Markers)
 * 6. Bóc tách khối lượng (BOQ Schedule) & Xuất bản vẽ kỹ thuật CAD
 */

let mep3dScene, mep3dCamera, mep3dRenderer, mep3dControls;
let mep3dCurrentModel = null;
let mep3dInitialized = false;
let mepRaycaster = new THREE.Raycaster();
let mepMouse = new THREE.Vector2();
let mepClashMarkersGroup = null;

// Quản lý trạng thái hiển thị từng hệ (Layer Filter)
let mepFilterState = {
  arch: true,
  elec: true,
  plumb: true,
  hvac: true,
  clashes: true
};

let currentMepData = null;

// Khởi tạo tab khi người dùng chuyển tab
function initMepDashboard() {
  if (!mep3dInitialized) {
    initMepThreeViewer();
    mep3dInitialized = true;
    // Tự động load mô hình mặc định
    runMepGeneratePipeline(false);
  } else {
    setTimeout(onMep3dResize, 100);
  }
}

// Khởi tạo Three.js Viewer
function initMepThreeViewer() {
  const container = document.getElementById('mep3dCanvasContainer');
  if (!container) return;

  const w = container.clientWidth || 640;
  const h = container.clientHeight || 520;

  // 1. Scene
  mep3dScene = new THREE.Scene();
  mep3dScene.background = new THREE.Color(0x0f172a); // slate-900

  // 2. Camera
  mep3dCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
  mep3dCamera.position.set(22, 18, 26);

  // 3. Renderer
  mep3dRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  mep3dRenderer.setSize(w, h);
  mep3dRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  mep3dRenderer.outputEncoding = THREE.sRGBEncoding;
  mep3dRenderer.shadowMap.enabled = true;
  container.innerHTML = '';
  container.appendChild(mep3dRenderer.domElement);

  // 4. OrbitControls
  if (typeof THREE.OrbitControls !== 'undefined') {
    mep3dControls = new THREE.OrbitControls(mep3dCamera, mep3dRenderer.domElement);
    mep3dControls.enableDamping = true;
    mep3dControls.dampingFactor = 0.08;
    mep3dControls.screenSpacePanning = true;
    mep3dControls.minDistance = 1;
    mep3dControls.maxDistance = 600;
    mep3dControls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN
    };
  }

  // 5. Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
  mep3dScene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0xfffbeb, 0.8);
  dirLight1.position.set(40, 60, 40);
  mep3dScene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x93c5fd, 0.5);
  dirLight2.position.set(-40, -20, -40);
  mep3dScene.add(dirLight2);

  // 6. Ground Grid & Axes
  const gridHelper = new THREE.GridHelper(40, 40, 0x06b6d4, 0x334155);
  gridHelper.position.y = -0.01;
  mep3dScene.add(gridHelper);

  const axesHelper = new THREE.AxesHelper(3);
  mep3dScene.add(axesHelper);

  // 7. Nhóm chứa điểm va chạm xung đột (Clash Markers)
  mepClashMarkersGroup = new THREE.Group();
  mepClashMarkersGroup.name = "ClashMarkersGroup";
  mep3dScene.add(mepClashMarkersGroup);

  // 8. Event listeners
  window.addEventListener('resize', onMep3dResize);
  if (window.ResizeObserver) {
    new ResizeObserver(() => onMep3dResize()).observe(container);
  }

  container.addEventListener('click', onMepCanvasClick);

  // 9. Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    if (mep3dControls) mep3dControls.update();

    // Hiệu ứng nhấp nháy phát sáng cho điểm xung đột
    if (mepClashMarkersGroup && mepClashMarkersGroup.children.length > 0) {
      const time = Date.now() * 0.005;
      const scale = 1.0 + 0.25 * Math.sin(time);
      mepClashMarkersGroup.children.forEach(marker => {
        marker.scale.set(scale, scale, scale);
      });
    }

    mep3dRenderer.render(mep3dScene, mep3dCamera);
  }
  animate();
}

function onMep3dResize() {
  const container = document.getElementById('mep3dCanvasContainer');
  if (!container || !mep3dRenderer || !mep3dCamera) return;
  const w = container.clientWidth;
  const h = container.clientHeight || 520;
  if (w <= 0 || h <= 0) return;
  mep3dCamera.aspect = w / h;
  mep3dCamera.updateProjectionMatrix();
  mep3dRenderer.setSize(w, h);
}

// Preset Views
function setMepView(viewType) {
  if (!mep3dCurrentModel || !mep3dCamera) return;
  const box = new THREE.Box3().setFromObject(mep3dCurrentModel);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = mep3dCamera.fov * (Math.PI / 180);
  let camDist = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
  camDist = Math.max(camDist, 10);

  if (viewType === 'iso') {
    mep3dCamera.position.set(center.x + camDist * 0.7, center.y + camDist * 0.55, center.z + camDist * 0.85);
  } else if (viewType === 'top') {
    mep3dCamera.position.set(center.x, center.y + camDist * 1.3, center.z + 0.001);
  } else if (viewType === 'front') {
    mep3dCamera.position.set(center.x, center.y, center.z + camDist * 1.3);
  } else if (viewType === 'side') {
    mep3dCamera.position.set(center.x + camDist * 1.3, center.y, center.z);
  }

  mep3dCamera.lookAt(center);
  if (mep3dControls) {
    mep3dControls.target.copy(center);
    mep3dControls.update();
  }
}

// Bộ lọc hiển thị (Layer Filter Toggle)
function toggleMepFilter(filterKey) {
  mepFilterState[filterKey] = !mepFilterState[filterKey];
  const btn = document.getElementById(`btnFilter_${filterKey}`);
  if (btn) {
    if (mepFilterState[filterKey]) {
      btn.classList.add('bg-cyan-600', 'text-white');
      btn.classList.remove('bg-slate-800', 'text-slate-400', 'opacity-60');
    } else {
      btn.classList.remove('bg-cyan-600', 'text-white');
      btn.classList.add('bg-slate-800', 'text-slate-400', 'opacity-60');
    }
  }

  if (filterKey === 'clashes') {
    if (mepClashMarkersGroup) mepClashMarkersGroup.visible = mepFilterState.clashes;
    return;
  }

  if (!mep3dCurrentModel) return;

  mep3dCurrentModel.traverse(child => {
    if (child.isMesh) {
      const name = (child.name || '').toUpperCase();
      const matName = (child.material?.name || '').toUpperCase();

      let targetVisible = true;
      if (matName.includes('CONCRETE') || matName.includes('BRICK') || name.includes('WALL') || name.includes('SLAB') || name.includes('BEAM') || name.includes('COL')) {
        targetVisible = mepFilterState.arch;
      } else if (matName.includes('HVAC') || name.includes('DUCT') || name.includes('FCU') || name.includes('DIFFUSER') || name.includes('EXHAUST')) {
        targetVisible = mepFilterState.hvac;
      } else if (matName.includes('PIPE') || matName.includes('SANITARY') || name.includes('PIPE') || name.includes('WC') || name.includes('LAVABO') || name.includes('TANK')) {
        targetVisible = mepFilterState.plumb;
      } else if (matName.includes('CABLE') || matName.includes('LIGHT') || name.includes('TRAY') || name.includes('LIGHT') || name.includes('DB') || name.includes('PANEL')) {
        targetVisible = mepFilterState.elec;
      }
      child.visible = targetVisible;
    }
  });
}

// Click vào đối tượng để kiểm tra thuộc tính BIM (Raycaster Inspection)
function onMepCanvasClick(e) {
  const container = document.getElementById('mep3dCanvasContainer');
  if (!container || !mep3dRenderer || !mep3dCamera || !mep3dScene) return;

  const rect = container.getBoundingClientRect();
  mepMouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mepMouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  mepRaycaster.setFromCamera(mepMouse, mep3dCamera);

  // 1. Kiểm tra click vào Clash Marker trước
  if (mepClashMarkersGroup && mepClashMarkersGroup.visible) {
    const clashHits = mepRaycaster.intersectObjects(mepClashMarkersGroup.children);
    if (clashHits.length > 0) {
      const hitMarker = clashHits[0].object;
      const cData = hitMarker.userData;
      showMepClashDetail(cData);
      return;
    }
  }

  // 2. Kiểm tra click vào Model Meshes
  if (mep3dCurrentModel) {
    const hits = mepRaycaster.intersectObject(mep3dCurrentModel, true);
    if (hits.length > 0) {
      const hitMesh = hits[0].object;
      showMepElementDetail(hitMesh);
    }
  }
}

function showMepElementDetail(mesh) {
  const propBox = document.getElementById('mepSelectedElementProperties');
  if (!propBox) return;

  const name = mesh.name || 'Phần tử MEP';
  const matName = mesh.material?.name || 'Vật liệu tiêu chuẩn';

  let category = 'Hệ thống Khác';
  let badgeColor = 'bg-slate-700 text-slate-300';
  if (name.includes('DUCT') || matName.includes('HVAC')) {
    category = 'Hệ Điều Hòa Thông Gió HVAC';
    badgeColor = 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';
  } else if (name.includes('PIPE') || matName.includes('PIPE') || name.includes('WC') || name.includes('LAVABO')) {
    category = 'Hệ Cấp Thoát Nước';
    badgeColor = 'bg-blue-500/20 text-blue-300 border border-blue-500/40';
  } else if (name.includes('TRAY') || name.includes('LIGHT') || name.includes('DB')) {
    category = 'Hệ Điện & Chiếu Sáng';
    badgeColor = 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
  } else if (name.includes('WALL') || name.includes('BEAM') || name.includes('COL') || name.includes('SLAB')) {
    category = 'Kiến Trúc & Kết Cấu';
    badgeColor = 'bg-slate-500/20 text-slate-300 border border-slate-500/40';
  }

  propBox.innerHTML = `
    <div class="space-y-2 text-xs">
      <div class="flex items-center justify-between">
        <span class="font-bold text-slate-200 truncate">${name}</span>
        <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${badgeColor}">${category}</span>
      </div>
      <div class="grid grid-cols-2 gap-2 text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
        <div>Vật liệu: <span class="text-slate-200 font-medium">${matName.replace('Mat_', '')}</span></div>
        <div>Mã ID: <span class="text-slate-200 font-mono">${mesh.id}</span></div>
        <div>Vị trí Y: <span class="text-slate-200">${mesh.position.y.toFixed(2)}m</span></div>
        <div>Trạng thái: <span class="text-emerald-400 font-medium">BIM 3D Valid</span></div>
      </div>
    </div>
  `;
}

function showMepClashDetail(clashData) {
  const propBox = document.getElementById('mepSelectedElementProperties');
  if (!propBox) return;

  propBox.innerHTML = `
    <div class="space-y-2 text-xs bg-rose-950/40 p-3 rounded-lg border border-rose-600/50">
      <div class="flex items-center justify-between">
        <span class="font-bold text-rose-300 flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
          ${clashData.clash_id} - ${clashData.severity} CLASH
        </span>
        <span class="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-200 border border-rose-500/40">Va Chạm Kỹ Thuật</span>
      </div>
      <p class="text-slate-300">${clashData.description}</p>
      <div class="bg-black/40 p-2 rounded text-[11px] text-slate-300 space-y-1">
        <div>Đối tượng A: <span class="text-cyan-300 font-medium">${clashData.element_a.name}</span></div>
        <div>Đối tượng B: <span class="text-amber-300 font-medium">${clashData.element_b.name}</span></div>
        <div>Độ sâu va chạm: <span class="text-rose-400 font-bold">${clashData.penetration_depth_mm} mm</span></div>
        <div>Tọa độ (X, Y, Z): <span class="text-slate-400 font-mono">${clashData.clash_point.x}, ${clashData.clash_point.y}, ${clashData.clash_point.z}</span></div>
      </div>
      <div class="text-[11px] text-emerald-300 bg-emerald-950/30 p-2 rounded border border-emerald-500/30">
        💡 <b>Đề xuất xử lý:</b> ${clashData.recommendation}
      </div>
    </div>
  `;
}

// Chạy pipeline thiết kế tự động MEP
async function runMepGeneratePipeline(autoResolve = true) {
  const btn = document.getElementById('btnMepGenerate');
  const statusEl = document.getElementById('mepLiveStatus');
  if (btn) btn.disabled = true;
  if (statusEl) statusEl.innerHTML = '<span class="inline-block animate-spin mr-1.5">⚙️</span> Đang tính toán tải, thiết kế tự động MEP & sinh mô hình 3D...';

  const width = parseFloat(document.getElementById('mepParamWidth')?.value || 12);
  const depth = parseFloat(document.getElementById('mepParamDepth')?.value || 8);
  const height = parseFloat(document.getElementById('mepParamHeight')?.value || 3.6);
  const floors = parseInt(document.getElementById('mepParamFloors')?.value || 2);
  const resolveChecked = document.getElementById('mepParamAutoResolve')?.checked ?? autoResolve;

  try {
    const res = await fetch('/api/mep/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        width_m: width,
        depth_m: depth,
        height_m: height,
        floors: floors,
        auto_resolve: resolveChecked
      })
    });

    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Thao tác thất bại');
    }

    currentMepData = data;
    renderMepStats(data);
    renderMepBoqTable(data.boq_schedule);
    renderMepClashesTable(data.clash_detection);

    // Tải mô hình OBJ 3D vào canvas Three.js
    if (data.obj_url && data.mtl_url) {
      loadMepObjModel(data.obj_url, data.mtl_url, data.clash_detection?.clashes || []);
    }

    if (statusEl) {
      statusEl.innerHTML = `✅ Thiết kế & sinh 3D hoàn tất trong <b>${data.elapsed_seconds}s</b>! Tổng số phần tử: <b>${data.summary.total_elements}</b>`;
    }
  } catch (err) {
    if (statusEl) statusEl.innerHTML = `❌ Lỗi: <span class="text-rose-400">${err.message}</span>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Nạp mô hình 3D OBJ & MTL vào Three.js
function loadMepObjModel(objUrl, mtlUrl, clashes) {
  if (!mep3dScene) return;

  const mtlLoader = new THREE.MTLLoader();
  mtlLoader.load(mtlUrl, (materials) => {
    materials.preload();
    const objLoader = new THREE.OBJLoader();
    objLoader.setMaterials(materials);

    objLoader.load(objUrl, (object) => {
      if (mep3dCurrentModel) {
        mep3dScene.remove(mep3dCurrentModel);
      }
      mep3dCurrentModel = object;
      mep3dScene.add(object);

      // Đặt các quả cầu đỏ phát sáng tại các điểm va chạm xung đột
      renderClashMarkers(clashes);

      // Căn giữa góc nhìn camera
      setMepView('iso');
    });
  });
}

// Vẽ điểm xung đột bằng quả cầu phát sáng (Clash Markers)
function renderClashMarkers(clashes) {
  if (!mepClashMarkersGroup) return;
  mepClashMarkersGroup.clear();

  if (!clashes || clashes.length === 0) return;

  const sphereGeo = new THREE.SphereGeometry(0.35, 16, 16);
  const sphereMat = new THREE.MeshStandardMaterial({
    color: 0xef4444,
    emissive: 0xff0000,
    emissiveIntensity: 0.8,
    roughness: 0.2
  });

  clashes.forEach(c => {
    const marker = new THREE.Mesh(sphereGeo, sphereMat);
    // Tọa độ mm đổi sang Mét (Scale 0.001) và map chuẩn Three.js: X=X, Y=Z, Z=-Y
    const scale = 0.001;
    const x = c.clash_point.x * scale;
    const y = c.clash_point.z * scale;
    const z = -c.clash_point.y * scale;

    marker.position.set(x, y, z);
    marker.userData = c;
    mepClashMarkersGroup.add(marker);
  });
}

// Hiển thị thẻ thống kê nhanh
function renderMepStats(data) {
  const s = data.summary;
  const boq = data.boq_schedule;
  const clashes = data.clash_detection;

  const elElements = document.getElementById('mepStatTotalElements');
  const elPower = document.getElementById('mepStatTotalPower');
  const elHvac = document.getElementById('mepStatTotalHvac');
  const elPipes = document.getElementById('mepStatTotalPipes');
  const elCost = document.getElementById('mepStatTotalCost');
  const elClashes = document.getElementById('mepStatClashesCount');

  if (elElements) elElements.innerText = s.total_elements;
  if (elPower) elPower.innerText = `${s.total_lighting_power_kw} kW`;
  if (elHvac) elHvac.innerText = `${s.total_hvac_cooling_kw} kW`;
  if (elPipes) elPipes.innerText = `${s.total_pipes_linear_meters} m`;
  if (elCost) elCost.innerText = boq.formatted_total;
  if (elClashes) {
    const initC = clashes.initial_clashes_count || 0;
    const resolvedC = clashes.auto_resolve?.resolved_count || 0;
    elClashes.innerHTML = `<span class="text-rose-400 font-bold">${initC}</span> <span class="text-slate-400 text-xs">(-${resolvedC} đã xử lý)</span>`;
  }
}

// Render bảng Bóc Tách Khối Lượng (BOQ Schedule)
function renderMepBoqTable(boq) {
  const container = document.getElementById('mepBoqTableBody');
  if (!container || !boq || !boq.items) return;

  let html = '';
  boq.items.forEach(item => {
    html += `
      <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition">
        <td class="p-2 text-center text-slate-400">${item.item_no}</td>
        <td class="p-2 font-medium text-slate-200">${item.description}</td>
        <td class="p-2 text-center text-slate-300">${item.unit}</td>
        <td class="p-2 text-right font-mono font-bold text-cyan-400">${item.quantity}</td>
        <td class="p-2 text-right font-mono text-slate-300">${item.material_price_vnd.toLocaleString('vi-VN')}</td>
        <td class="p-2 text-right font-mono font-bold text-amber-400">${item.total_amount_vnd.toLocaleString('vi-VN')} đ</td>
      </tr>
    `;
  });
  container.innerHTML = html;

  const totalEl = document.getElementById('mepBoqGrandTotal');
  if (totalEl) totalEl.innerText = boq.formatted_total;
}

// Render bảng Báo Cáo Xung Đột (Clash Detection Table)
function renderMepClashesTable(clashData) {
  const container = document.getElementById('mepClashesTableBody');
  if (!container) return;

  const clashes = clashData?.clashes || [];
  if (clashes.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="5" class="p-4 text-center text-emerald-400 font-semibold bg-emerald-950/20">
          🎉 Không phát hiện xung đột MEP nào! Toàn bộ hệ thống đạt chuẩn không gian BIM.
        </td>
      </tr>
    `;
    return;
  }

  let html = '';
  clashes.forEach(c => {
    const sevBadge = c.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
    html += `
      <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition">
        <td class="p-2 text-center font-mono font-bold text-slate-300">${c.clash_id}</td>
        <td class="p-2 text-center"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${sevBadge}">${c.severity}</span></td>
        <td class="p-2 text-slate-200">
          <div class="font-medium">${c.description}</div>
          <div class="text-[11px] text-slate-400">${c.element_a.name} ⚔️ ${c.element_b.name}</div>
        </td>
        <td class="p-2 text-right font-mono font-bold text-rose-400">${c.penetration_depth_mm} mm</td>
        <td class="p-2 text-slate-300 text-xs">
          <div class="text-emerald-300">${c.recommendation}</div>
        </td>
      </tr>
    `;
  });
  container.innerHTML = html;
}

// Chạy tự động triệt tiêu xung đột (Auto-resolve Clashes)
async function runMepAutoResolve() {
  const statusEl = document.getElementById('mepLiveStatus');
  if (statusEl) statusEl.innerHTML = '<span class="inline-block animate-spin mr-1.5">⚙️</span> Đang tự động nắn tuyến hạ cốt và dịch chuyển đối tượng...';

  try {
    const res = await fetch('/api/mep/auto-resolve', { method: 'POST' });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Lỗi xử lý');

    // Cập nhật lại UI và 3D
    await runMepGeneratePipeline(true);
    if (statusEl) {
      statusEl.innerHTML = `✅ Đã tự động triệt tiêu <b>${data.resolved_count}</b> xung đột! Các tuyến ống đã được nắn an toàn.`;
    }
  } catch (err) {
    if (statusEl) statusEl.innerHTML = `❌ Lỗi: <span class="text-rose-400">${err.message}</span>`;
  }
}

// Mở thư mục chứa các file đã xuất
async function openMepExportFolder() {
  try {
    await fetch('/api/mep/open-folder', { method: 'POST' });
  } catch (err) {
    console.error(err);
  }
}

// Tải các định dạng file trực tiếp
function downloadMepFile(fileType) {
  if (!currentMepData || !currentMepData.exported_files) {
    alert("Vui lòng sinh mô hình MEP trước khi tải file!");
    return;
  }
  const files = currentMepData.exported_files;
  const filePath = files[fileType];
  if (!filePath) {
    alert(`Không tìm thấy file ${fileType.toUpperCase()}`);
    return;
  }
  const filename = filePath.split(/[\\/]/).pop();
  window.open(`/api/mep/models/${encodeURIComponent(filename)}`, '_blank');
}
