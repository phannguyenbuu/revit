/**
 * cad_3d_hub.js - Client-side Controller for AutoCAD 3D OBJ & 2D Vision Pipeline
 * Supports:
 * 1. Three.js 3D WebGL Viewer for Architectural Wavefront OBJ Models
 * 2. 2D Vision Floorplan & Door/Window/Column Detection Inspector
 * 3. 1-Click Clipboard Extraction & 3D OBJ Generation
 */

let cad3dScene, cad3dCamera, cad3dRenderer, cad3dControls;
let cad3dCurrentModel = null;
let cad3dSubMeshes = {};
let cad3dLoaded = false;
let cad3dInitialized = false;
let cadActiveSubTab = 'cad-subtab-3d';
let cadActiveLayer = 'all';

// Initialize when switching to tab-cad
function initCad3dDashboard() {
  try {
    const savedStairs = localStorage.getItem('cadExpectedStairs');
    const sel = document.getElementById('cadExpectedStairsSelect');
    if (savedStairs && sel) {
      sel.value = savedStairs;
    }
  } catch (e) {}
  loadCadStatus();
  if (!cad3dInitialized) {
    initCad3dThreeViewer();
    cad3dInitialized = true;
  }
}

// Switch sub-tabs inside AutoCAD tab
function switchCadSubTab(subTabId) {
  cadActiveSubTab = subTabId;
  ['cad-subtab-3d', 'cad-subtab-2d', 'cad-subtab-text'].forEach(id => {
    const el = document.getElementById(id);
    const btn = document.getElementById('btn-' + id);
    if (el) {
      if (id === subTabId) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
    if (btn) {
      if (id === subTabId) {
        btn.classList.remove('bg-slate-100', 'text-slate-600', 'hover:bg-slate-200');
        btn.classList.add('bg-indigo-600', 'text-white', 'shadow-xs');
      } else {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-xs');
        btn.classList.add('bg-slate-100', 'text-slate-600', 'hover:bg-slate-200');
      }
    }
  });

  if (subTabId === 'cad-subtab-3d' && cad3dRenderer && cad3dCamera) {
    setTimeout(onCad3dResize, 100);
  }
  if (subTabId === 'cad-subtab-2d') {
    setTimeout(() => {
      resizeCadVisionCanvas();
      cadCanvasFitView();
    }, 100);
  }
}

// Load CAD status, models and vision results
async function loadCadStatus() {
  try {
    const res = await fetch('/api/cad/status');
    const data = await res.json();
    renderCadStatusBadges(data);
    renderVisionResults(data.vision);
    renderModelInfo(data.models);

    // If 3D model exists and not loaded, load it
    if (data.models && data.models['building_full.obj'] && data.models['building_full.obj'].exists && !cad3dLoaded) {
      loadCad3dObjModel('building_full.obj');
    }
  } catch (err) {
    console.warn("Lỗi load trạng thái CAD:", err);
  }
}

function renderCadStatusBadges(data) {
  const clipBadge = document.getElementById('cadClipboardBadge');
  if (clipBadge) {
    if (data.clipboard_has_cad) {
      clipBadge.className = 'text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 flex items-center gap-1';
      clipBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Clipboard CAD Sẵn Sàng';
    } else {
      clipBadge.className = 'text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium border border-slate-200 flex items-center gap-1';
      clipBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Chưa có AutoCAD OLE';
    }
  }

  const acadBadge = document.getElementById('cadAccoreBadge');
  if (acadBadge) {
    if (data.acad_installed) {
      acadBadge.className = 'text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-200';
      acadBadge.innerText = 'AutoCAD 2022 Accore OK';
    } else {
      acadBadge.className = 'text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-bold border border-amber-200';
      acadBadge.innerText = 'Chưa thấy AutoCAD 2022';
    }
  }
}

// ==============================================================================
// 2. 2D VISION & INTERACTIVE STUDIO CANVAS (ZOOM/PAN & MANUAL RE-DESIGNATION)
// ==============================================================================

const CAD_CATEGORIES = {
  stairs:   { name: 'Cầu thang', color: '#f59e0b', fill: 'rgba(245, 158, 11, 0.22)', border: '#f59e0b', icon: '🪜', prefix: 'STAIR' },
  tam_cap:  { name: 'Tam cấp',   color: '#a855f7', fill: 'rgba(168, 85, 247, 0.22)', border: '#a855f7', icon: '🏛️', prefix: 'STEP' },
  ramps:    { name: 'Ram dốc',   color: '#f43f5e', fill: 'rgba(244, 63, 94, 0.22)', border: '#f43f5e', icon: '📐', prefix: 'RAMP' },
  doors:    { name: 'Cửa đi',    color: '#10b981', fill: 'rgba(16, 185, 129, 0.18)', border: '#10b981', icon: '🚪', prefix: 'DOOR' },
  windows:  { name: 'Cửa sổ',    color: '#06b6d4', fill: 'rgba(6, 182, 212, 0.18)', border: '#06b6d4', icon: '🪟', prefix: 'WIN' },
  columns:  { name: 'Cột',       color: '#eab308', fill: 'rgba(234, 179, 8, 0.30)', border: '#eab308', icon: '🏛️', prefix: 'COL' },
  walls:    { name: 'Tường',     color: '#ef4444', fill: 'rgba(239, 68, 68, 0.10)', border: '#ef4444', icon: '🧱', prefix: 'WALL' }
};

let cadVisionState = {
  initialized: false,
  baseImage: null,
  baseImageLoaded: false,
  canvas: null,
  ctx: null,
  mode: 'pan', // 'pan' or 'draw'
  drawCategory: 'stairs',
  scale: 0.25,
  panX: 0,
  panY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  panStartX: 0,
  panStartY: 0,
  isDrawing: false,
  drawStartImgX: 0,
  drawStartImgY: 0,
  drawCurImgX: 0,
  drawCurImgY: 0,
  annotations: [],
  selectedBox: null,
  selectedIdx: -1,
  categoryVis: {
    stairs: true,
    tam_cap: true,
    ramps: true,
    doors: true,
    windows: true,
    columns: true,
    walls: false // default false to avoid clutter
  },
  cadExtents: { min_x: 0, max_x: 40000, min_y: 0, max_y: 25000, width: 40000, height: 25000 },
  imgWidth: 4000,
  imgHeight: 2320,
  rawVision: null
};

function renderVisionResults(vision) {
  if (!vision || !vision.has_result) return;
  cadVisionState.rawVision = vision;

  // 1. Update 7 KPI Cards
  const countDoors = document.getElementById('cadCountDoors');
  const countWindows = document.getElementById('cadCountWindows');
  const countCols = document.getElementById('cadCountColumns');
  const countWalls = document.getElementById('cadCountWalls');
  const countStairs = document.getElementById('cadCountStairs');
  const countTamCap = document.getElementById('cadCountTamCap');
  const countRamps = document.getElementById('cadCountRamps');

  if (vision.counts) {
    if (countDoors) countDoors.innerText = vision.counts.doors ?? (vision.doors ? vision.doors.length : 0);
    if (countWindows) countWindows.innerText = vision.counts.windows ?? (vision.windows ? vision.windows.length : 0);
    if (countCols) countCols.innerText = vision.counts.columns ?? (vision.columns ? vision.columns.length : 0);
    if (countWalls) countWalls.innerText = vision.counts.major_walls ?? (vision.walls ? vision.walls.length : 0);
    if (countStairs) countStairs.innerText = vision.counts.stairs ?? (vision.stairs ? vision.stairs.length : 0);
    if (countTamCap) countTamCap.innerText = vision.counts.tam_cap ?? (vision.tam_cap ? vision.tam_cap.length : 0);
    if (countRamps) countRamps.innerText = vision.counts.ramps ?? (vision.ramps ? vision.ramps.length : 0);
  }

  // 2. Parse Extents
  if (vision.cad_extents_mm) {
    cadVisionState.cadExtents = Object.assign({}, vision.cad_extents_mm);
  }

  // 3. Assemble flat annotations list from vision data
  const flat = [];
  const addCategoryItems = (arr, catKey) => {
    if (!Array.isArray(arr)) return;
    arr.forEach((it, idx) => {
      const box = Object.assign({}, it);
      box.category = catKey;
      if (!box.id) box.id = `${CAD_CATEGORIES[catKey].prefix}_${idx + 1 < 10 ? '0' : ''}${idx + 1}`;
      if (!box.type) box.type = CAD_CATEGORIES[catKey].name;
      flat.push(box);
    });
  };

  addCategoryItems(vision.stairs, 'stairs');
  addCategoryItems(vision.tam_cap, 'tam_cap');
  addCategoryItems(vision.ramps, 'ramps');
  addCategoryItems(vision.doors, 'doors');
  addCategoryItems(vision.windows, 'windows');
  addCategoryItems(vision.columns, 'columns');
  addCategoryItems(vision.walls, 'walls');

  cadVisionState.annotations = flat;

  // 4. Initialize or update Canvas Studio
  initCadVisionCanvas(vision);

  // 5. Render Door Crops gallery
  const gallery = document.getElementById('cadDoorsGallery');
  const sampleDoors = vision.doors_sample || (vision.doors ? vision.doors.slice(0, 6) : []);
  if (gallery && sampleDoors.length > 0) {
    gallery.innerHTML = sampleDoors.map(d => `
      <div class="p-2 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center text-center hover:bg-emerald-50/50 hover:border-emerald-200 transition group cursor-pointer" onclick="zoomToCadBox('${d.id}')">
        <div class="w-full h-20 bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center border border-slate-300/80 mb-1.5">
          <img src="${d.crop_url || ('/api/cad/vision-crop/' + d.id + '.png')}" class="max-h-full max-w-full object-contain group-hover:scale-105 transition-transform" alt="${d.id}" onerror="this.src='/favicon.ico'; this.style.opacity=0.3;">
        </div>
        <div class="text-[11px] font-bold text-slate-800">${d.id}</div>
        <div class="text-[10px] text-emerald-700 font-semibold">${d.type}</div>
        <div class="text-[9.5px] text-slate-500 font-mono">${Math.round(d.width_mm || 0)} mm</div>
      </div>
    `).join('');
  }

  if (window.lucide) lucide.createIcons();
}

function initCadVisionCanvas(vision) {
  const canvas = document.getElementById('cadVisionCanvas');
  if (!canvas) return;

  cadVisionState.canvas = canvas;
  cadVisionState.ctx = canvas.getContext('2d');

  // Load Base Image
  const imgUrl = (vision && vision.base_image) ? vision.base_image : '/api/cad/vision-image/floorplan_base.png';
  if (!cadVisionState.baseImage) {
    cadVisionState.baseImage = new Image();
    cadVisionState.baseImage.crossOrigin = 'anonymous';
    cadVisionState.baseImage.onload = () => {
      cadVisionState.baseImageLoaded = true;
      cadVisionState.imgWidth = cadVisionState.baseImage.naturalWidth || 4000;
      cadVisionState.imgHeight = cadVisionState.baseImage.naturalHeight || 2320;
      resizeCadVisionCanvas();
      cadCanvasFitView();
    };
    cadVisionState.baseImage.onerror = () => {
      // Fallback to annotated image if base isn't available
      if (vision && vision.annotated_image && imgUrl !== vision.annotated_image) {
        cadVisionState.baseImage.src = vision.annotated_image;
      }
    };
    cadVisionState.baseImage.src = imgUrl + '?t=' + Date.now();
  } else {
    resizeCadVisionCanvas();
    renderCadVisionCanvas();
  }

  if (!cadVisionState.initialized) {
    setupCadVisionCanvasEvents(canvas);
    cadVisionState.initialized = true;
  }
}

function resizeCadVisionCanvas() {
  const canvas = cadVisionState.canvas;
  if (!canvas) return;
  const container = canvas.parentElement;
  const rect = container ? container.getBoundingClientRect() : canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  canvas.width = Math.max(300, rect.width) * dpr;
  canvas.height = Math.max(300, rect.height) * dpr;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  const ctx = cadVisionState.ctx;
  if (ctx) ctx.scale(dpr, dpr);
}

// Grip definitions for Interactive Box Resizing & Moving
const CAD_GRIPS = [
  { id: 'nw', cursor: 'nwse-resize', getPos: (x1, y1, x2, y2) => ({ x: x1, y: y1 }) },
  { id: 'ne', cursor: 'nesw-resize', getPos: (x1, y1, x2, y2) => ({ x: x2, y: y1 }) },
  { id: 'se', cursor: 'nwse-resize', getPos: (x1, y1, x2, y2) => ({ x: x2, y: y2 }) },
  { id: 'sw', cursor: 'nesw-resize', getPos: (x1, y1, x2, y2) => ({ x: x1, y: y2 }) },
  { id: 'n',  cursor: 'ns-resize',   getPos: (x1, y1, x2, y2) => ({ x: (x1 + x2)/2, y: y1 }) },
  { id: 's',  cursor: 'ns-resize',   getPos: (x1, y1, x2, y2) => ({ x: (x1 + x2)/2, y: y2 }) },
  { id: 'w',  cursor: 'ew-resize',   getPos: (x1, y1, x2, y2) => ({ x: x1, y: (y1 + y2)/2 }) },
  { id: 'e',  cursor: 'ew-resize',   getPos: (x1, y1, x2, y2) => ({ x: x2, y: (y1 + y2)/2 }) }
];

function getGripAtScreenPos(mouseX, mouseY) {
  if (!cadVisionState.selectedBox || !cadVisionState.selectedBox.bbox_pixels) return null;
  const [x1, y1, x2, y2] = cadVisionState.selectedBox.bbox_pixels;
  const scale = cadVisionState.scale;
  const panX = cadVisionState.panX;
  const panY = cadVisionState.panY;
  const hitDist = 10; // 10 screen pixels hit tolerance

  for (const g of CAD_GRIPS) {
    const p = g.getPos(x1, y1, x2, y2);
    const sx = p.x * scale + panX;
    const sy = p.y * scale + panY;
    if (Math.hypot(mouseX - sx, mouseY - sy) <= hitDist) {
      return g;
    }
  }
  return null;
}

function isInsideSelectedBox(imgX, imgY) {
  if (!cadVisionState.selectedBox || !cadVisionState.selectedBox.bbox_pixels) return false;
  const [x1, y1, x2, y2] = cadVisionState.selectedBox.bbox_pixels;
  return (imgX >= Math.min(x1, x2) && imgX <= Math.max(x1, x2) &&
          imgY >= Math.min(y1, y2) && imgY <= Math.max(y1, y2));
}

function findBoxAtImgPos(imgX, imgY) {
  for (let i = cadVisionState.annotations.length - 1; i >= 0; i--) {
    const box = cadVisionState.annotations[i];
    if (!cadVisionState.categoryVis[box.category]) continue;
    const bp = box.bbox_pixels;
    if (!bp || bp.length !== 4) continue;
    const [x1, y1, x2, y2] = bp;
    if (imgX >= Math.min(x1, x2) && imgX <= Math.max(x1, x2) &&
        imgY >= Math.min(y1, y2) && imgY <= Math.max(y1, y2)) {
      return box;
    }
  }
  return null;
}

function syncBoxCadDimensions(box) {
  if (!box || !box.bbox_pixels) return;
  const [x1, y1, x2, y2] = box.bbox_pixels;
  const ext = cadVisionState.cadExtents;
  const imgW = cadVisionState.imgWidth || 4000;
  const imgH = cadVisionState.imgHeight || 2320;

  const minImgX = Math.min(x1, x2);
  const maxImgX = Math.max(x1, x2);
  const minImgY = Math.min(y1, y2);
  const maxImgY = Math.max(y1, y2);

  const cadX1 = Math.round(ext.min_x + (minImgX / imgW) * ext.width);
  const cadX2 = Math.round(ext.min_x + (maxImgX / imgW) * ext.width);
  const cadY1 = Math.round(ext.max_y - (maxImgY / imgH) * ext.height);
  const cadY2 = Math.round(ext.max_y - (minImgY / imgH) * ext.height);

  box.cad_box = [cadX1, cadY1, cadX2, cadY2];
  box.width_mm = Math.round(Math.abs(cadX2 - cadX1));
  box.depth_mm = Math.round(Math.abs(cadY2 - cadY1));
  box.center_cad = [Math.round((cadX1 + cadX2) / 2), Math.round((cadY1 + cadY2) / 2)];
}

function setupCadVisionCanvasEvents(canvas) {
  // Resize listener
  window.addEventListener('resize', () => {
    resizeCadVisionCanvas();
    renderCadVisionCanvas();
  });

  // 1. Mouse Wheel Zoom (Scroll to Zoom at Cursor)
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const imgX = (mouseX - cadVisionState.panX) / cadVisionState.scale;
    const imgY = (mouseY - cadVisionState.panY) / cadVisionState.scale;

    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    const newScale = Math.min(Math.max(cadVisionState.scale * factor, 0.03), 15.0);

    cadVisionState.panX = mouseX - imgX * newScale;
    cadVisionState.panY = mouseY - imgY * newScale;
    cadVisionState.scale = newScale;

    updateCadCanvasZoomBadge();
    renderCadVisionCanvas();
  }, { passive: false });

  // 2. Mouse Down (Separate Pan vs Select/Grip/Move vs Draw)
  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const imgX = (mouseX - cadVisionState.panX) / cadVisionState.scale;
    const imgY = (mouseY - cadVisionState.panY) / cadVisionState.scale;

    const isWheelButton = (e.button === 1); // Wheel press / Middle click
    const isSpaceKey = (e.getModifierState && e.getModifierState('Space'));

    // A. ALWAYS PAN with Wheel press (Middle click) or Space + Drag
    if (isWheelButton || isSpaceKey) {
      cadVisionState.isPanning = true;
      cadVisionState.dragStartX = mouseX;
      cadVisionState.dragStartY = mouseY;
      cadVisionState.panStartX = cadVisionState.panX;
      cadVisionState.panStartY = cadVisionState.panY;
      canvas.style.cursor = 'grabbing';
      e.preventDefault();
      return;
    }

    // B. Left button in Draw mode -> Draw rubberband
    if (cadVisionState.mode === 'draw' && e.button === 0) {
      cadVisionState.isDrawing = true;
      cadVisionState.drawStartImgX = imgX;
      cadVisionState.drawStartImgY = imgY;
      cadVisionState.drawCurImgX = imgX;
      cadVisionState.drawCurImgY = imgY;
      renderCadVisionCanvas();
      return;
    }

    // C. Left button in Pan / Select mode -> Prioritize Grips & Box Move over Pan!
    if (e.button === 0) {
      // 1. Clicked on a Grip Handle of selected box? -> Start Resizing Grip
      const hitGrip = getGripAtScreenPos(mouseX, mouseY);
      if (hitGrip) {
        cadVisionState.activeGrip = hitGrip.id;
        cadVisionState.gripStartImgX = imgX;
        cadVisionState.gripStartImgY = imgY;
        cadVisionState.boxOrigBbox = [...cadVisionState.selectedBox.bbox_pixels];
        canvas.style.cursor = hitGrip.cursor;
        e.preventDefault();
        return;
      }

      // 2. Clicked inside selected box? -> Start Moving Box Body
      if (isInsideSelectedBox(imgX, imgY)) {
        cadVisionState.activeGrip = 'body';
        cadVisionState.gripStartImgX = imgX;
        cadVisionState.gripStartImgY = imgY;
        cadVisionState.boxOrigBbox = [...cadVisionState.selectedBox.bbox_pixels];
        canvas.style.cursor = 'move';
        e.preventDefault();
        return;
      }

      // 3. Clicked on another box? -> Select it immediately
      const hitBox = findBoxAtImgPos(imgX, imgY);
      if (hitBox) {
        cadVisionState.selectedBox = hitBox;
        cadVisionState.activeGrip = 'body';
        cadVisionState.gripStartImgX = imgX;
        cadVisionState.gripStartImgY = imgY;
        cadVisionState.boxOrigBbox = [...hitBox.bbox_pixels];
        showCadSelectedBoxInspector(hitBox);
        renderCadVisionCanvas();
        canvas.style.cursor = 'move';
        e.preventDefault();
        return;
      }

      // 4. Clicked on empty space -> Deselect box & allow background pan drag
      cadVisionState.selectedBox = null;
      hideCadSelectedBoxInspector();
      renderCadVisionCanvas();

      cadVisionState.isPanning = true;
      cadVisionState.dragStartX = mouseX;
      cadVisionState.dragStartY = mouseY;
      cadVisionState.panStartX = cadVisionState.panX;
      cadVisionState.panStartY = cadVisionState.panY;
      canvas.style.cursor = 'grabbing';
    }
  });

  // 3. Mouse Move (Grip Resizing, Box Moving, Pan, Hover Cursor Feedback)
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const imgX = (mouseX - cadVisionState.panX) / cadVisionState.scale;
    const imgY = (mouseY - cadVisionState.panY) / cadVisionState.scale;

    updateCadCoordsHud(imgX, imgY);

    // 1. If Panning
    if (cadVisionState.isPanning) {
      const dx = mouseX - cadVisionState.dragStartX;
      const dy = mouseY - cadVisionState.dragStartY;
      cadVisionState.panX = cadVisionState.panStartX + dx;
      cadVisionState.panY = cadVisionState.panStartY + dy;
      renderCadVisionCanvas();
      return;
    }

    // 2. If Dragging Grip or Moving Box Body
    if (cadVisionState.activeGrip && cadVisionState.selectedBox && cadVisionState.boxOrigBbox) {
      const [ox1, oy1, ox2, oy2] = cadVisionState.boxOrigBbox;
      const dx = imgX - cadVisionState.gripStartImgX;
      const dy = imgY - cadVisionState.gripStartImgY;
      let nx1 = ox1, ny1 = oy1, nx2 = ox2, ny2 = oy2;

      switch (cadVisionState.activeGrip) {
        case 'body':
          nx1 = ox1 + dx; ny1 = oy1 + dy;
          nx2 = ox2 + dx; ny2 = oy2 + dy;
          break;
        case 'nw': nx1 = ox1 + dx; ny1 = oy1 + dy; break;
        case 'ne': nx2 = ox2 + dx; ny1 = oy1 + dy; break;
        case 'se': nx2 = ox2 + dx; ny2 = oy2 + dy; break;
        case 'sw': nx1 = ox1 + dx; ny2 = oy2 + dy; break;
        case 'n':  ny1 = oy1 + dy; break;
        case 's':  ny2 = oy2 + dy; break;
        case 'w':  nx1 = ox1 + dx; break;
        case 'e':  nx2 = ox2 + dx; break;
      }

      const minSz = 10;
      if (cadVisionState.activeGrip !== 'body') {
        if (nx2 - nx1 < minSz && (cadVisionState.activeGrip === 'e' || cadVisionState.activeGrip.includes('e'))) nx2 = nx1 + minSz;
        if (nx2 - nx1 < minSz && (cadVisionState.activeGrip === 'w' || cadVisionState.activeGrip.includes('w'))) nx1 = nx2 - minSz;
        if (ny2 - ny1 < minSz && (cadVisionState.activeGrip === 's' || cadVisionState.activeGrip.includes('s'))) ny2 = ny1 + minSz;
        if (ny2 - ny1 < minSz && (cadVisionState.activeGrip === 'n' || cadVisionState.activeGrip.includes('n'))) ny1 = ny2 - minSz;
      }

      cadVisionState.selectedBox.bbox_pixels = [
        Math.round(Math.min(nx1, nx2)),
        Math.round(Math.min(ny1, ny2)),
        Math.round(Math.max(nx1, nx2)),
        Math.round(Math.max(ny1, ny2))
      ];

      syncBoxCadDimensions(cadVisionState.selectedBox);
      showCadSelectedBoxInspector(cadVisionState.selectedBox);
      renderCadVisionCanvas();
      return;
    }

    // 3. If Drawing
    if (cadVisionState.isDrawing) {
      cadVisionState.drawCurImgX = imgX;
      cadVisionState.drawCurImgY = imgY;
      renderCadVisionCanvas();
      return;
    }

    // 4. Hover Cursor Feedback
    if (cadVisionState.mode === 'draw') {
      canvas.style.cursor = 'crosshair';
      return;
    }

    // In Pan / Select mode:
    const hitGrip = getGripAtScreenPos(mouseX, mouseY);
    if (hitGrip) {
      canvas.style.cursor = hitGrip.cursor;
    } else if (isInsideSelectedBox(imgX, imgY)) {
      canvas.style.cursor = 'move';
    } else if (findBoxAtImgPos(imgX, imgY)) {
      canvas.style.cursor = 'pointer';
    } else {
      canvas.style.cursor = 'default';
    }
  });

  // 4. Mouse Up
  window.addEventListener('mouseup', (e) => {
    if (!cadVisionState.canvas) return;

    if (cadVisionState.isPanning) {
      cadVisionState.isPanning = false;
      cadVisionState.canvas.style.cursor = cadVisionState.mode === 'draw' ? 'crosshair' : 'default';
    }

    if (cadVisionState.activeGrip) {
      if (cadVisionState.selectedBox) {
        syncBoxCadDimensions(cadVisionState.selectedBox);
        showCadSelectedBoxInspector(cadVisionState.selectedBox);
        updateLocalCategoryCounts();
      }
      cadVisionState.activeGrip = null;
      cadVisionState.boxOrigBbox = null;
      renderCadVisionCanvas();
    }

    if (cadVisionState.isDrawing) {
      cadVisionState.isDrawing = false;
      finalizeDrawnBoundingBox();
    }
  });

  // 5. Double Click: Fit View
  canvas.addEventListener('dblclick', () => {
    cadCanvasFitView();
  });

  // 6. Keyboard Shortcuts: Delete to remove selected box, Escape to cancel
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'SELECT' || activeEl.tagName === 'TEXTAREA')) {
        return;
      }
      if (cadVisionState.selectedBox) {
        e.preventDefault();
        deleteSelectedCadBox();
      }
    } else if (e.key === 'Escape') {
      if (cadVisionState.isDrawing) {
        cadVisionState.isDrawing = false;
        renderCadVisionCanvas();
      } else if (cadVisionState.selectedBox) {
        cadVisionState.selectedBox = null;
        cadVisionState.selectedIdx = -1;
        hideCadSelectedBoxInspector();
        renderCadVisionCanvas();
      }
    }
  });
}

function updateCadCoordsHud(imgX, imgY) {
  const hud = document.getElementById('cadHudCoords');
  if (!hud) return;
  const ext = cadVisionState.cadExtents;
  const imgW = cadVisionState.imgWidth || 4000;
  const imgH = cadVisionState.imgHeight || 2320;

  const cadX = ext.min_x + (imgX / imgW) * ext.width;
  const cadY = ext.max_y - (imgY / imgH) * ext.height;

  hud.innerText = `CAD: X: ${Math.round(cadX).toLocaleString()} mm | Y: ${Math.round(cadY).toLocaleString()} mm`;
}

function updateCadCanvasZoomBadge() {
  const badge = document.getElementById('cadCanvasZoomBadge');
  if (badge) {
    badge.innerText = `${Math.round(cadVisionState.scale * 100)}%`;
  }
}

// Fit entire floorplan into canvas with padding
function cadCanvasFitView() {
  if (!cadVisionState.canvas) return;
  const rect = cadVisionState.canvas.getBoundingClientRect();
  const w = rect.width;
  const h = rect.height;
  const imgW = cadVisionState.imgWidth || 4000;
  const imgH = cadVisionState.imgHeight || 2320;

  const pad = 24;
  const scaleX = (w - pad * 2) / imgW;
  const scaleY = (h - pad * 2) / imgH;
  cadVisionState.scale = Math.min(scaleX, scaleY);
  cadVisionState.panX = (w - imgW * cadVisionState.scale) / 2;
  cadVisionState.panY = (h - imgH * cadVisionState.scale) / 2;

  updateCadCanvasZoomBadge();
  renderCadVisionCanvas();
}

function cadCanvasZoomIn() {
  const rect = cadVisionState.canvas.getBoundingClientRect();
  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const imgX = (cx - cadVisionState.panX) / cadVisionState.scale;
  const imgY = (cy - cadVisionState.panY) / cadVisionState.scale;
  cadVisionState.scale = Math.min(cadVisionState.scale * 1.25, 15.0);
  cadVisionState.panX = cx - imgX * cadVisionState.scale;
  cadVisionState.panY = cy - imgY * cadVisionState.scale;
  updateCadCanvasZoomBadge();
  renderCadVisionCanvas();
}

function cadCanvasZoomOut() {
  const rect = cadVisionState.canvas.getBoundingClientRect();
  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const imgX = (cx - cadVisionState.panX) / cadVisionState.scale;
  const imgY = (cy - cadVisionState.panY) / cadVisionState.scale;
  cadVisionState.scale = Math.max(cadVisionState.scale / 1.25, 0.03);
  cadVisionState.panX = cx - imgX * cadVisionState.scale;
  cadVisionState.panY = cy - imgY * cadVisionState.scale;
  updateCadCanvasZoomBadge();
  renderCadVisionCanvas();
}

function cadCanvasZoom100() {
  const rect = cadVisionState.canvas.getBoundingClientRect();
  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const imgX = (cx - cadVisionState.panX) / cadVisionState.scale;
  const imgY = (cy - cadVisionState.panY) / cadVisionState.scale;
  cadVisionState.scale = 1.0;
  cadVisionState.panX = cx - imgX;
  cadVisionState.panY = cy - imgY;
  updateCadCanvasZoomBadge();
  renderCadVisionCanvas();
}

// Mode toggle: Pan vs Draw
function setCadCanvasMode(mode) {
  cadVisionState.mode = mode;
  const btnPan = document.getElementById('cadCanvasModePan');
  const btnDraw = document.getElementById('cadCanvasModeDraw');

  if (mode === 'pan') {
    if (btnPan) {
      btnPan.className = 'px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 bg-indigo-600 text-white shadow';
    }
    if (btnDraw) {
      btnDraw.className = 'px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 text-zinc-400 hover:text-white';
    }
    if (cadVisionState.canvas) cadVisionState.canvas.style.cursor = 'default';
  } else {
    if (btnPan) {
      btnPan.className = 'px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 text-zinc-400 hover:text-white';
    }
    if (btnDraw) {
      btnDraw.className = 'px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 bg-indigo-600 text-white shadow';
    }
    if (cadVisionState.canvas) cadVisionState.canvas.style.cursor = 'crosshair';
  }
}

// Category visibility filter
function toggleCadCategoryVis(cat, isVisible) {
  cadVisionState.categoryVis[cat] = !!isVisible;
  renderCadVisionCanvas();
}

function showCadSelectedBoxInspector(box) {
  const panel = document.getElementById('cadSelectedBoxInspector');
  if (!panel) return;
  panel.classList.remove('hidden');

  const meta = CAD_CATEGORIES[box.category] || { name: box.type || 'Phần tử', icon: '📦' };
  const iconEl = document.getElementById('cadInspectorTypeIcon');
  const idEl = document.getElementById('cadInspectorId');
  const dimsEl = document.getElementById('cadInspectorDims');
  const centerEl = document.getElementById('cadInspectorCenter');
  const catSelect = document.getElementById('cadInspectorCategorySelect');

  if (iconEl) iconEl.innerText = meta.icon;
  if (idEl) idEl.innerText = box.id || 'BOX';
  if (dimsEl) dimsEl.innerText = `${Math.round(box.width_mm || 0)} x ${Math.round(box.depth_mm || 0)} mm`;
  if (centerEl && box.center_cad) centerEl.innerText = `${Math.round(box.center_cad[0])}, ${Math.round(box.center_cad[1])}`;
  if (catSelect) catSelect.value = box.category;

  if (window.lucide) lucide.createIcons();
}

function hideCadSelectedBoxInspector() {
  const panel = document.getElementById('cadSelectedBoxInspector');
  if (panel) panel.classList.add('hidden');
}

// Re-classify selected bounding box category
function changeSelectedBoxCategory(newCategory) {
  if (!cadVisionState.selectedBox || !CAD_CATEGORIES[newCategory]) return;
  cadVisionState.selectedBox.category = newCategory;
  cadVisionState.selectedBox.type = CAD_CATEGORIES[newCategory].name;

  const prefix = CAD_CATEGORIES[newCategory].prefix;
  const sameCat = cadVisionState.annotations.filter(b => b.category === newCategory);
  cadVisionState.selectedBox.id = `${prefix}_${sameCat.length < 10 ? '0' : ''}${sameCat.length}`;

  showCadSelectedBoxInspector(cadVisionState.selectedBox);
  updateLocalCategoryCounts();
  renderCadVisionCanvas();
  log(`Đã chuyển ${cadVisionState.selectedBox.id} sang danh mục: ${CAD_CATEGORIES[newCategory].name}`, 'info');
}

// Delete selected bounding box
function deleteSelectedCadBox() {
  if (!cadVisionState.selectedBox) return;
  const id = cadVisionState.selectedBox.id;
  cadVisionState.annotations = cadVisionState.annotations.filter(b => b !== cadVisionState.selectedBox);
  cadVisionState.selectedBox = null;
  cadVisionState.selectedIdx = -1;
  hideCadSelectedBoxInspector();
  updateLocalCategoryCounts();
  renderCadVisionCanvas();
  log(`Đã xóa bounding box: ${id}`, 'info');
}

// Finalize drawn bounding box
function finalizeDrawnBoundingBox() {
  const x1 = Math.min(cadVisionState.drawStartImgX, cadVisionState.drawCurImgX);
  const x2 = Math.max(cadVisionState.drawStartImgX, cadVisionState.drawCurImgX);
  const y1 = Math.min(cadVisionState.drawStartImgY, cadVisionState.drawCurImgY);
  const y2 = Math.max(cadVisionState.drawStartImgY, cadVisionState.drawCurImgY);

  const drawCatSelect = document.getElementById('cadDrawCategory');
  const cat = drawCatSelect ? drawCatSelect.value : cadVisionState.drawCategory;
  const meta = CAD_CATEGORIES[cat] || CAD_CATEGORIES.stairs;

  // Minimum size in pixels to prevent accidental clicks
  if (Math.abs(x2 - x1) < 8 || Math.abs(y2 - y1) < 8) {
    renderCadVisionCanvas();
    return;
  }

  // Calculate CAD extents
  const ext = cadVisionState.cadExtents;
  const imgW = cadVisionState.imgWidth || 4000;
  const imgH = cadVisionState.imgHeight || 2320;

  const cadX1 = Math.round(ext.min_x + (x1 / imgW) * ext.width);
  const cadX2 = Math.round(ext.min_x + (x2 / imgW) * ext.width);
  const cadY1 = Math.round(ext.max_y - (y2 / imgH) * ext.height);
  const cadY2 = Math.round(ext.max_y - (y1 / imgH) * ext.height);

  const countCat = cadVisionState.annotations.filter(b => b.category === cat).length + 1;
  const newId = `${meta.prefix}_${countCat < 10 ? '0' : ''}${countCat}`;

  const newBox = {
    id: newId,
    name: `${meta.name} #${countCat}`,
    category: cat,
    type: meta.name,
    bbox_pixels: [Math.round(x1), Math.round(y1), Math.round(x2), Math.round(y2)],
    cad_box: [Math.min(cadX1, cadX2), Math.min(cadY1, cadY2), Math.max(cadX1, cadX2), Math.max(cadY1, cadY2)],
    width_mm: Math.round(Math.abs(cadX2 - cadX1)),
    depth_mm: Math.round(Math.abs(cadY2 - cadY1)),
    center_cad: [Math.round((cadX1 + cadX2) / 2), Math.round((cadY1 + cadY2) / 2)]
  };

  cadVisionState.annotations.push(newBox);
  cadVisionState.selectedBox = newBox;
  cadVisionState.selectedIdx = cadVisionState.annotations.length - 1;

  showCadSelectedBoxInspector(newBox);
  updateLocalCategoryCounts();
  renderCadVisionCanvas();
  log(`Đã vẽ và chỉ định mới: ${newBox.id} (${meta.name} ${newBox.width_mm}x${newBox.depth_mm}mm)`, 'success');
}

function updateLocalCategoryCounts() {
  const counts = { doors: 0, windows: 0, columns: 0, walls: 0, stairs: 0, tam_cap: 0, ramps: 0 };
  cadVisionState.annotations.forEach(b => {
    if (counts[b.category] !== undefined) counts[b.category]++;
  });

  const countDoors = document.getElementById('cadCountDoors');
  const countWindows = document.getElementById('cadCountWindows');
  const countCols = document.getElementById('cadCountColumns');
  const countWalls = document.getElementById('cadCountWalls');
  const countStairs = document.getElementById('cadCountStairs');
  const countTamCap = document.getElementById('cadCountTamCap');
  const countRamps = document.getElementById('cadCountRamps');

  if (countDoors) countDoors.innerText = counts.doors;
  if (countWindows) countWindows.innerText = counts.windows;
  if (countCols) countCols.innerText = counts.columns;
  if (countWalls) countWalls.innerText = counts.walls;
  if (countStairs) countStairs.innerText = counts.stairs;
  if (countTamCap) countTamCap.innerText = counts.tam_cap;
  if (countRamps) countRamps.innerText = counts.ramps;
}

// Master Canvas Render Loop with 8-Grip Handles & Move Indicator
function renderCadVisionCanvas() {
  const ctx = cadVisionState.ctx;
  const canvas = cadVisionState.canvas;
  if (!ctx || !canvas) return;

  // Clear viewport
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#18181b';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.restore();

  ctx.save();
  ctx.translate(cadVisionState.panX, cadVisionState.panY);
  ctx.scale(cadVisionState.scale, cadVisionState.scale);

  // 1. Draw Floorplan Base Image
  if (cadVisionState.baseImage && cadVisionState.baseImageLoaded) {
    ctx.drawImage(cadVisionState.baseImage, 0, 0, cadVisionState.imgWidth, cadVisionState.imgHeight);
  }

  // 2. Draw Annotations
  const scale = cadVisionState.scale;
  cadVisionState.annotations.forEach(box => {
    if (!cadVisionState.categoryVis[box.category]) return;
    const bp = box.bbox_pixels;
    if (!bp || bp.length !== 4) return;
    const [x1, y1, x2, y2] = bp;
    const bw = x2 - x1;
    const bh = y2 - y1;
    const meta = CAD_CATEGORIES[box.category] || CAD_CATEGORIES.stairs;
    const isSelected = (box === cadVisionState.selectedBox);

    // Box Fill
    ctx.fillStyle = isSelected ? 'rgba(99, 102, 241, 0.32)' : meta.fill;
    ctx.fillRect(x1, y1, bw, bh);

    // Box Border
    ctx.strokeStyle = isSelected ? '#ffffff' : meta.border;
    ctx.lineWidth = (isSelected ? 3 : 2) / scale;
    if (box.category === 'ramps') {
      ctx.setLineDash([8 / scale, 6 / scale]);
    } else {
      ctx.setLineDash([]);
    }
    ctx.strokeRect(x1, y1, bw, bh);
    ctx.setLineDash([]);

    // 8 Interactive Grip Handles if selected!
    if (isSelected) {
      const gripPositions = [
        { x: x1, y: y1 }, { x: x2, y: y1 }, { x: x2, y: y2 }, { x: x1, y: y2 }, // 4 corners
        { x: (x1+x2)/2, y: y1 }, { x: (x1+x2)/2, y: y2 }, { x: x1, y: (y1+y2)/2 }, { x: x2, y: (y1+y2)/2 } // 4 edges
      ];

      const handleSz = 10 / scale;
      gripPositions.forEach((gp, idx) => {
        // High contrast white square with indigo border
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(gp.x - handleSz/2, gp.y - handleSz/2, handleSz, handleSz);
        ctx.strokeStyle = idx < 4 ? '#4f46e5' : '#6366f1';
        ctx.lineWidth = 2 / scale;
        ctx.strokeRect(gp.x - handleSz/2, gp.y - handleSz/2, handleSz, handleSz);
      });

      // Center move indicator dot
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      ctx.beginPath();
      ctx.arc(cx, cy, 4.5 / scale, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#4f46e5';
      ctx.lineWidth = 1.5 / scale;
      ctx.stroke();

      // Live dimension tooltip during active grip drag
      if (cadVisionState.activeGrip) {
        const dimText = `📐 ${Math.round(box.width_mm)} × ${Math.round(box.depth_mm)} mm`;
        const fz = Math.max(12, 14 / scale);
        ctx.font = `bold ${fz}px sans-serif`;
        const tm = ctx.measureText(dimText);
        const tw = tm.width;
        const th = fz * 1.4;
        const hx = cx - tw / 2 - (6 / scale);
        const hy = y1 - th - (8 / scale);

        ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
        ctx.fillRect(hx, hy, tw + (12 / scale), th);
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 1.5 / scale;
        ctx.strokeRect(hx, hy, tw + (12 / scale), th);
        ctx.fillStyle = '#38bdf8';
        ctx.fillText(dimText, hx + (6 / scale), hy + fz * 1.05);
      }
    }

    // Label Badge (visible when zoom is sufficient or selected)
    if (scale > 0.08 || isSelected) {
      const labelText = `${box.id} (${Math.round(box.width_mm || 0)}mm)`;
      const fontSize = Math.max(10, Math.min(18, 13 / scale));
      ctx.font = `bold ${fontSize}px sans-serif`;
      const textMetrics = ctx.measureText(labelText);
      const textW = textMetrics.width;
      const textH = fontSize * 1.25;

      const badgeY = y1 - textH - (4 / scale);
      ctx.fillStyle = meta.color;
      ctx.fillRect(x1, badgeY, textW + (8 / scale), textH);
      ctx.fillStyle = '#000000';
      ctx.fillText(labelText, x1 + (4 / scale), badgeY + fontSize * 0.95);
    }
  });

  // 3. Draw Rubberband Preview if in Drawing Mode
  if (cadVisionState.isDrawing) {
    const rx1 = Math.min(cadVisionState.drawStartImgX, cadVisionState.drawCurImgX);
    const ry1 = Math.min(cadVisionState.drawStartImgY, cadVisionState.drawCurImgY);
    const rw = Math.abs(cadVisionState.drawCurImgX - cadVisionState.drawStartImgX);
    const rh = Math.abs(cadVisionState.drawCurImgY - cadVisionState.drawStartImgY);

    const drawCatSelect = document.getElementById('cadDrawCategory');
    const cat = drawCatSelect ? drawCatSelect.value : cadVisionState.drawCategory;
    const meta = CAD_CATEGORIES[cat] || CAD_CATEGORIES.stairs;

    ctx.fillStyle = meta.fill;
    ctx.fillRect(rx1, ry1, rw, rh);

    ctx.strokeStyle = meta.border;
    ctx.lineWidth = 2.5 / scale;
    ctx.setLineDash([8 / scale, 4 / scale]);
    ctx.strokeRect(rx1, ry1, rw, rh);
    ctx.setLineDash([]);

    // Live dimension tag
    const ext = cadVisionState.cadExtents;
    const imgW = cadVisionState.imgWidth || 4000;
    const imgH = cadVisionState.imgHeight || 2320;
    const wMm = Math.round((rw / imgW) * ext.width);
    const hMm = Math.round((rh / imgH) * ext.height);

    const tagText = `+ ${meta.name}: ${wMm} x ${hMm} mm`;
    const fz = Math.max(11, 14 / scale);
    ctx.font = `bold ${fz}px sans-serif`;
    const tm = ctx.measureText(tagText);
    ctx.fillStyle = '#18181b';
    ctx.fillRect(rx1, ry1 - fz * 1.4, tm.width + 10 / scale, fz * 1.3);
    ctx.fillStyle = meta.color;
    ctx.fillText(tagText, rx1 + 5 / scale, ry1 - fz * 0.35);
  }

  ctx.restore();
}

// Zoom directly to specific box from Doors Gallery or ID
function zoomToCadBox(boxId) {
  const box = cadVisionState.annotations.find(b => b.id === boxId);
  if (!box || !box.bbox_pixels) return;

  const [x1, y1, x2, y2] = box.bbox_pixels;
  const cx = (x1 + x2) / 2;
  const cy = (y1 + y2) / 2;
  const rect = cadVisionState.canvas.getBoundingClientRect();

  cadVisionState.scale = 0.8;
  cadVisionState.panX = rect.width / 2 - cx * cadVisionState.scale;
  cadVisionState.panY = rect.height / 2 - cy * cadVisionState.scale;

  cadVisionState.selectedBox = box;
  showCadSelectedBoxInspector(box);
  updateCadCanvasZoomBadge();
  renderCadVisionCanvas();
}

// Save Annotations back to server
async function saveCadVisionAnnotations() {
  const btn = document.getElementById('btnCadSaveAnnotations');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="inline-block animate-spin mr-1">⌛</span> Đang lưu...';
  }

  try {
    const res = await fetch('/api/cad/update-annotations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ annotations: cadVisionState.annotations })
    });
    const result = await res.json();
    if (result.status === 'success') {
      log(`Đã lưu thành công ${cadVisionState.annotations.length} vùng nhận diện vào hệ thống!`, 'success');
      alert(`Đã lưu thành công ${cadVisionState.annotations.length} vùng nhận diện (Cầu thang, Tam cấp, Ram dốc, Cửa,...)!`);
      // Reload status to sync models and counts
      loadCadStatus();
    } else {
      log(`Lỗi lưu chỉ định: ${result.message || 'Không rõ lỗi'}`, 'error');
      alert(`Lỗi lưu: ${result.message}`);
    }
  } catch (err) {
    log(`Lỗi kết nối khi lưu: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="save" class="w-3.5 h-3.5"></i> Lưu Chỉ Định';
      if (window.lucide) lucide.createIcons();
    }
  }
}

// Reset annotations back to original server result
function resetCadVisionAnnotations() {
  if (!confirm('Khôi phục lại toàn bộ vùng nhận diện ban đầu từ hệ thống?')) return;
  loadCadStatus();
  log('Đã nạp lại kết quả nhận diện ban đầu.', 'info');
}

// Re-generate 3D OBJ from Vision Studio
async function generate3dFromVisionStudio() {
  await saveCadVisionAnnotations();
  runCadGenerate3d();
}

function renderModelInfo(models) {
  if (!models) return;
  const listEl = document.getElementById('cadModelsList');
  if (!listEl) return;

  const files = ['building_full.obj', 'wall.obj', 'door.obj', 'window.obj', 'stair.obj', 'ramp.obj'];
  const labels = {
    'building_full.obj': { name: 'Full Building Model', color: 'indigo' },
    'wall.obj': { name: 'Tường & Cột kết cấu', color: 'slate' },
    'door.obj': { name: 'Cửa đi & Vòm mở', color: 'emerald' },
    'window.obj': { name: 'Cửa sổ & Kính', color: 'cyan' },
    'stair.obj': { name: 'Cầu thang & Tam cấp', color: 'amber' },
    'ramp.obj': { name: 'Ram dốc tiền sảnh', color: 'rose' }
  };

  listEl.innerHTML = files.map(f => {
    const m = models[f] || {};
    const meta = labels[f] || { name: f, color: 'slate' };
    const exists = m.exists !== false;
    return `
      <div class="p-2.5 rounded-xl border ${exists ? 'bg-white border-slate-200 hover:border-indigo-300' : 'bg-slate-50/50 border-slate-100 opacity-60'} flex items-center justify-between text-xs transition">
        <div class="flex items-center gap-2 min-w-0">
          <span class="w-2 h-2 rounded-full bg-${meta.color}-500 shrink-0"></span>
          <div class="min-w-0">
            <div class="font-bold text-slate-800 truncate">${meta.name}</div>
            <div class="text-[10px] text-slate-500 font-mono truncate">${f} ${exists ? '• ' + (m.file_size_kb || 0) + ' KB' : '• Chưa sinh'}</div>
          </div>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          ${exists ? `
            <button onclick="loadCad3dObjModel('${f}')" class="px-2 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-bold transition flex items-center gap-1 cursor-pointer" title="Xem 3D Model này">
              <i data-lucide="eye" class="w-3 h-3"></i> Xem
            </button>
            <a href="/api/cad/3d-models/${f}?download=1" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition flex items-center gap-1 cursor-pointer" title="Tải file .obj về máy">
              <i data-lucide="download" class="w-3 h-3"></i> Tải
            </a>
          ` : `
            <span class="text-[10px] text-slate-400 italic">Chưa có</span>
          `}
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

// ==============================================================================
// THREE.JS 3D WEBGL VIEWER FOR CAD WAVEFRONT OBJ
// ==============================================================================

function initCad3dThreeViewer() {
  const container = document.getElementById('cad3dCanvasContainer');
  if (!container) return;

  const w = container.clientWidth || 800;
  const h = container.clientHeight || 480;

  // 1. Scene
  cad3dScene = new THREE.Scene();
  cad3dScene.background = new THREE.Color(0x18181b); // dark zinc-900

  // 2. Camera
  cad3dCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
  cad3dCamera.position.set(30, 25, 40);

  // 3. Renderer
  cad3dRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
  cad3dRenderer.setSize(w, h);
  cad3dRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  cad3dRenderer.outputEncoding = THREE.sRGBEncoding;
  container.innerHTML = '';
  container.appendChild(cad3dRenderer.domElement);

  // 4. OrbitControls
  if (typeof THREE.OrbitControls !== 'undefined') {
    cad3dControls = new THREE.OrbitControls(cad3dCamera, cad3dRenderer.domElement);
    cad3dControls.enableDamping = true;
    cad3dControls.dampingFactor = 0.08;
    cad3dControls.screenSpacePanning = true;
    cad3dControls.minDistance = 2;
    cad3dControls.maxDistance = 300;
    // Pan bằng nút cuộn chuột (Wheel / Middle button) chuẩn CAD, không ảnh hưởng thao tác click
    cad3dControls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN
    };
  }

  // 5. Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  cad3dScene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight1.position.set(50, 80, 50);
  cad3dScene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x93c5fd, 0.4); // soft sky fill
  dirLight2.position.set(-50, -30, -50);
  cad3dScene.add(dirLight2);

  // 6. Ground Grid & Axes
  const gridHelper = new THREE.GridHelper(60, 60, 0x4f46e5, 0x334155);
  gridHelper.position.y = -0.01;
  gridHelper.name = "GridHelper";
  cad3dScene.add(gridHelper);

  const axesHelper = new THREE.AxesHelper(5);
  axesHelper.name = "AxesHelper";
  cad3dScene.add(axesHelper);

  // 7. Resize Observer
  window.addEventListener('resize', onCad3dResize);
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => onCad3dResize());
    ro.observe(container);
  }

  // 8. Animation loop
  function animate() {
    requestAnimationFrame(animate);
    if (cad3dControls) cad3dControls.update();
    cad3dRenderer.render(cad3dScene, cad3dCamera);
  }
  animate();
}

function onCad3dResize() {
  const container = document.getElementById('cad3dCanvasContainer');
  if (!container || !cad3dRenderer || !cad3dCamera) return;
  const w = container.clientWidth;
  const h = container.clientHeight || 480;
  if (w <= 0 || h <= 0) return;
  cad3dCamera.aspect = w / h;
  cad3dCamera.updateProjectionMatrix();
  cad3dRenderer.setSize(w, h);
}

// Load Wavefront OBJ model into Three.js
function loadCad3dObjModel(modelFileName = 'building_full.obj') {
  if (!cad3dScene) return;

  const statusEl = document.getElementById('cad3dLoadingOverlay');
  if (statusEl) statusEl.classList.remove('hidden');

  // Remove existing model
  if (cad3dCurrentModel) {
    cad3dScene.remove(cad3dCurrentModel);
    cad3dCurrentModel = null;
    cad3dSubMeshes = {};
  }

  const mtlLoader = new THREE.MTLLoader();
  mtlLoader.load('/api/cad/3d-models/materials.mtl', function(materials) {
    materials.preload();

    const objLoader = new THREE.OBJLoader();
    objLoader.setMaterials(materials);
    objLoader.load('/api/cad/3d-models/' + modelFileName, function(object) {
      cad3dCurrentModel = object;

      // Color maps fallback & DoubleSided material
      object.traverse(function(child) {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          if (child.material) {
            child.material.side = THREE.DoubleSide;
            // Name matching
            const n = (child.name || '').toLowerCase();
            if (n.includes('wall') || n.includes('cot')) {
              child.material.color = new THREE.Color(0xd4d4d8); // zinc-300
              cad3dSubMeshes['wall'] = child;
            } else if (n.includes('door') || n.includes('cua')) {
              child.material.color = new THREE.Color(0x10b981); // emerald-500
              cad3dSubMeshes['door'] = child;
            } else if (n.includes('window') || n.includes('glaz')) {
              child.material.color = new THREE.Color(0x06b6d4); // cyan-500
              child.material.transparent = true;
              child.material.opacity = 0.65;
              cad3dSubMeshes['window'] = child;
            } else if (n.includes('stair') || n.includes('thang')) {
              child.material.color = new THREE.Color(0xf59e0b); // amber-500
              cad3dSubMeshes['stair'] = child;
            } else if (n.includes('ramp')) {
              child.material.color = new THREE.Color(0xf43f5e); // rose-500
              cad3dSubMeshes['ramp'] = child;
            }
          }
        }
      });

      // Fit camera to bounding box
      const box = new THREE.Box3().setFromObject(object);
      const size = new THREE.Vector3();
      box.getSize(size);
      const center = new THREE.Vector3();
      box.getCenter(center);

      // Center object
      object.position.x = -center.x;
      object.position.y = -box.min.y; // sit on ground
      object.position.z = -center.z;

      cad3dScene.add(object);
      cad3dLoaded = true;

      // Update Camera & Controls
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = cad3dCamera.fov * (Math.PI / 180);
      let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
      cad3dCamera.position.set(cameraZ * 0.7, cameraZ * 0.6, cameraZ * 0.9);
      cad3dCamera.lookAt(0, size.y / 3, 0);
      if (cad3dControls) {
        cad3dControls.target.set(0, size.y / 3, 0);
        cad3dControls.update();
      }

      // Update Dimension Badges
      const dimEl = document.getElementById('cad3dDimensions');
      if (dimEl) {
        dimEl.innerText = `${size.x.toFixed(1)}m x ${size.z.toFixed(1)}m • Cao ${size.y.toFixed(1)}m`;
      }
      const titleEl = document.getElementById('cad3dCurrentTitle');
      if (titleEl) {
        titleEl.innerText = modelFileName;
      }

      if (statusEl) statusEl.classList.add('hidden');
      log(`Đã nạp 3D model: ${modelFileName} (${size.x.toFixed(1)}m x ${size.z.toFixed(1)}m x ${size.y.toFixed(1)}m)`, 'success');
    }, function(xhr) {
      // Progress
    }, function(error) {
      if (statusEl) statusEl.classList.add('hidden');
      log(`Lỗi nạp OBJ: ${error.message || error}`, 'error');
    });
  });
}

function resetCad3dCamera() {
  if (!cad3dCurrentModel || !cad3dCamera) return;
  const box = new THREE.Box3().setFromObject(cad3dCurrentModel);
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = cad3dCamera.fov * (Math.PI / 180);
  let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
  cad3dCamera.position.set(cameraZ * 0.7, cameraZ * 0.6, cameraZ * 0.9);
  cad3dCamera.lookAt(0, size.y / 3, 0);
  if (cad3dControls) {
    cad3dControls.target.set(0, size.y / 3, 0);
    cad3dControls.update();
  }
}

function setCad3dViewTop() {
  if (!cad3dCurrentModel || !cad3dCamera) return;
  const box = new THREE.Box3().setFromObject(cad3dCurrentModel);
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.z);
  cad3dCamera.position.set(0, maxDim * 1.6, 0.001);
  cad3dCamera.lookAt(0, 0, 0);
  if (cad3dControls) {
    cad3dControls.target.set(0, 0, 0);
    cad3dControls.update();
  }
}

function toggleCad3dWireframe() {
  if (!cad3dCurrentModel) return;
  cad3dCurrentModel.traverse(function(child) {
    if (child.isMesh && child.material) {
      child.material.wireframe = !child.material.wireframe;
    }
  });
}

function filterCad3dLayer(layerName) {
  cadActiveLayer = layerName;
  ['all', 'wall', 'door', 'window', 'stair', 'ramp'].forEach(l => {
    const btn = document.getElementById('cadLayerBtn-' + l);
    if (btn) {
      if (l === layerName) {
        btn.classList.add('ring-2', 'ring-indigo-400', 'font-bold');
      } else {
        btn.classList.remove('ring-2', 'ring-indigo-400', 'font-bold');
      }
    }
  });

  if (!cad3dCurrentModel) return;

  cad3dCurrentModel.traverse(function(child) {
    if (child.isMesh) {
      const n = (child.name || '').toLowerCase();
      if (layerName === 'all') {
        child.visible = true;
      } else if (layerName === 'wall') {
        child.visible = n.includes('wall') || n.includes('cot');
      } else if (layerName === 'door') {
        child.visible = n.includes('door') || n.includes('cua');
      } else if (layerName === 'window') {
        child.visible = n.includes('window') || n.includes('glaz');
      } else if (layerName === 'stair') {
        child.visible = n.includes('stair') || n.includes('thang');
      } else if (layerName === 'ramp') {
        child.visible = n.includes('ramp');
      }
    }
  });
}

// ==============================================================================
// BACKEND ACTION TRIGGERS (1-CLICK PIPELINE)
// ==============================================================================

async function runCadClipboardPipeline() {
  const srcSelect = document.getElementById('cadPipelineSource');
  const source = srcSelect ? srcSelect.value : 'clipboard';
  const customPathInput = document.getElementById('cadCustomDxfPath');
  const customPath = customPathInput ? customPathInput.value.trim() : '';

  const btn = document.getElementById('btnRunCadPipeline');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="inline-block animate-spin mr-1">⌛</span> Đang trích xuất & nhận diện 2D...';
  }

  log(`[AutoCAD Hub] Bắt đầu tiến trình trích xuất nguồn: ${source}...`, 'info');

  try {
    const expectedStairs = getCadExpectedStairsValue();
    const res = await fetch('/api/cad/run-clipboard-pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: source, customPath: customPath, expected_stairs: expectedStairs })
    });
    const result = await res.json();

    if (result.success) {
      log(result.message, 'success');
      loadCadStatus();
      // Switch to 2D view to inspect results
      switchCadSubTab('cad-subtab-2d');
    } else {
      log(`Lỗi Pipeline: ${result.message}`, 'error');
      alert(`Lỗi Pipeline AutoCAD: ${result.message}`);
    }
  } catch (err) {
    log(`Lỗi kết nối Pipeline: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="play" class="w-4 h-4 fill-white"></i> 1-Click Clipboard &rarr; DXF &rarr; Vision 2D';
      if (window.lucide) lucide.createIcons();
    }
  }
}

async function runCadGenerate3d() {
  const btn = document.getElementById('btnRunCadGenerate3d');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="inline-block animate-spin mr-1">⌛</span> Đang dựng 3D Mesh...';
  }

  log('[AutoCAD Hub] Đang tính toán hình học 3D (Tường, Cửa, Cửa sổ, Cầu thang, Ram dốc)...', 'info');

  try {
    const expectedStairs = getCadExpectedStairsValue();
    const res = await fetch('/api/cad/generate-3d', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expected_stairs: expectedStairs })
    });
    const result = await res.json();

    if (result.success) {
      log(result.message, 'success');
      loadCadStatus();
      loadCad3dObjModel('building_full.obj');
      switchCadSubTab('cad-subtab-3d');
    } else {
      log(`Lỗi sinh 3D: ${result.message}`, 'error');
      alert(`Lỗi sinh 3D: ${result.message}`);
    }
  } catch (err) {
    log(`Lỗi kết nối 3D: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="box" class="w-4 h-4"></i> Sinh Model 3D OBJ Tự Động';
      if (window.lucide) lucide.createIcons();
    }
  }
}

async function openCadModelFolder() {
  try {
    const res = await fetch('/api/cad/open-folder', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      log(`Đã mở thư mục: ${data.folder}`, 'success');
    } else {
      log(`Không thể mở thư mục: ${data.error}`, 'error');
    }
  } catch (err) {
    log(`Lỗi: ${err.message}`, 'error');
  }
}

function zoomToDoor(doorId) {
  log(`Đang chọn cửa: ${doorId}`, 'info');
}

// Auto init if tab is active on load
document.addEventListener('DOMContentLoaded', function() {
  const cadTab = document.getElementById('tab-cad');
  if (cadTab && !cadTab.classList.contains('hidden')) {
    initCad3dDashboard();
  }
  const srcSelect = document.getElementById('cadPipelineSource');
  if (srcSelect) {
    srcSelect.addEventListener('change', function() {
      const customInp = document.getElementById('cadCustomDxfPath');
      if (customInp) {
        if (this.value === 'custom') {
          customInp.classList.remove('hidden');
        } else {
          customInp.classList.add('hidden');
        }
      }
    });
  }
});

// ==============================================================================
// EXPECTED STAIRS USER CONFIGURATION & PERSISTENCE
// ==============================================================================

function getCadExpectedStairsValue() {
  const sel = document.getElementById('cadExpectedStairsSelect');
  if (sel) return sel.value;
  try {
    return localStorage.getItem('cadExpectedStairs') || 'auto';
  } catch (e) {
    return 'auto';
  }
}

function onCadExpectedStairsChange(val) {
  try {
    localStorage.setItem('cadExpectedStairs', val);
  } catch (e) {}
  if (typeof log === 'function') {
    log(`[AutoCAD Hub] Đã cấu hình số lượng cầu thang: ${val}`, 'info');
  }
}

window.getCadExpectedStairsValue = getCadExpectedStairsValue;
window.onCadExpectedStairsChange = onCadExpectedStairsChange;
