/**
 * etabs_hub.js
 * Client-side Controller for ETABS Structural AI Hub in RevitAI Dashboard
 * 1. 2D Canvas Framing Plan Viewer with TRUE BEAM WIDTH & section labels
 * 2. 3D WebGL / Three.js Solid Model with realistic cross-sections, 3D grids, 3D moments M33
 * 3. Beam click-to-inspect & rebar selection modal (no tab switching needed)
 * 4. TCVN 5574-2012 Rebar Calculation Table & Selection Filter
 * 5. One-click Deploy to https://mr.pkld.online (VPS Sync)
 */

let etabsData = null;
let current2DStory = 'T4';
let last2DStory = null;
let lastModal2DStory = null;

let view2D = {
  scale: 0.024,
  offsetX: 0,
  offsetY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  hasUserInteracted: false
};
let modalView2D = {
  scale: 0.024,
  offsetX: 0,
  offsetY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  hasUserInteracted: false
};


// Three.js instances & states
let threeScene = null, threeCamera = null, threeRenderer = null, threeControls = null;
let threeMeshes = [];
let threeBeamMeshes = [];
let threeGridsGroup = null;
let threeMomentsGroup = null;
let threeLabelsGroup = null;

let modalThreeScene = null, modalThreeCamera = null, modalThreeRenderer = null, modalThreeControls = null;
let modalThreeMeshes = [];
let modalThreeBeamMeshes = [];
let modalThreeGridsGroup = null;
let modalThreeMomentsGroup = null;
let modalThreeLabelsGroup = null;

// Display toggles - Defaults per user requirements:
let is3DWireframe = false;  // Mặc định tắt khung dây
let show3DGrids = true;      // (1) Hiện lưới trục
let show3DMoments = true;    // (3) Hiển thị moment trên 3D luôn
let show3DBeamLabels = true; // (5) Hiện tên dầm

// Raycaster & Interaction
const threeRaycaster = new THREE.Raycaster();
const threeMouse = new THREE.Vector2();
let hoveredBeamMesh = null;
let selectedBeamForRebar = null;

// Rebar options catalog with exact areas (cm2)
const REBAR_CATALOG = [
  { label: '2D14', area: 3.08 },
  { label: '2D16', area: 4.02 },
  { label: '3D16', area: 6.03 },
  { label: '2D18', area: 5.09 },
  { label: '2D18+1D16', area: 7.10 },
  { label: '3D18', area: 7.63 },
  { label: '2D20', area: 6.28 },
  { label: '2D20+1D18', area: 8.83 },
  { label: '3D20', area: 9.42 },
  { label: '4D18', area: 10.18 },
  { label: '2D22', area: 7.60 },
  { label: '2D22+1D20', area: 10.74 },
  { label: '3D22', area: 11.40 },
  { label: '4D20', area: 12.57 },
  { label: '2D25', area: 9.82 },
  { label: '2D25+1D22', area: 13.62 },
  { label: '3D25', area: 14.73 },
  { label: '4D22', area: 15.21 },
  { label: '4D25', area: 19.63 }
];

const MAIN_REBAR_CATALOG = [
  { label: '2D14', area: 3.08, count: 2, diam: 14 },
  { label: '2D16', area: 4.02, count: 2, diam: 16 },
  { label: '3D16', area: 6.03, count: 3, diam: 16 },
  { label: '2D18', area: 5.09, count: 2, diam: 18 },
  { label: '3D18', area: 7.63, count: 3, diam: 18 },
  { label: '2D20', area: 6.28, count: 2, diam: 20 },
  { label: '3D20', area: 9.42, count: 3, diam: 20 },
  { label: '4D18', area: 10.18, count: 4, diam: 18 },
  { label: '2D22', area: 7.60, count: 2, diam: 22 },
  { label: '3D22', area: 11.40, count: 3, diam: 22 },
  { label: '4D20', area: 12.57, count: 4, diam: 20 },
  { label: '2D25', area: 9.82, count: 2, diam: 25 },
  { label: '3D25', area: 14.73, count: 3, diam: 25 },
  { label: '4D22', area: 15.21, count: 4, diam: 22 },
  { label: '4D25', area: 19.63, count: 4, diam: 25 }
];

const EXTRA_REBAR_CATALOG = [
  { label: '0 (Không TC)', area: 0.0, count: 0, diam: 0 },
  { label: '1D14', area: 1.54, count: 1, diam: 14 },
  { label: '2D14', area: 3.08, count: 2, diam: 14 },
  { label: '1D16', area: 2.01, count: 1, diam: 16 },
  { label: '2D16', area: 4.02, count: 2, diam: 16 },
  { label: '3D16', area: 6.03, count: 3, diam: 16 },
  { label: '1D18', area: 2.54, count: 1, diam: 18 },
  { label: '2D18', area: 5.09, count: 2, diam: 18 },
  { label: '3D18', area: 7.63, count: 3, diam: 18 },
  { label: '1D20', area: 3.14, count: 1, diam: 20 },
  { label: '2D20', area: 6.28, count: 2, diam: 20 },
  { label: '3D20', area: 9.42, count: 3, diam: 20 },
  { label: '1D22', area: 3.80, count: 1, diam: 22 },
  { label: '2D22', area: 7.60, count: 2, diam: 22 },
  { label: '1D25', area: 4.91, count: 1, diam: 25 },
  { label: '2D25', area: 9.82, count: 2, diam: 25 }
];

const STIRRUP_OPTIONS_D6 = [
  'd6a100/a200',
  'd6a100',
  'd6a150',
  'd6a200'
];

const STIRRUP_OPTIONS_D8 = [
  'd8a100/a200',
  'd8a100',
  'd8a150',
  'd8a200'
];

const STIRRUP_OPTIONS = STIRRUP_OPTIONS_D6;
window.currentStirrupDiam = 6;

function populateStirrupDropdown(diam = 6, selectedVal = null) {
  const stirrupSel = document.getElementById('brmSelStirrup');
  if (!stirrupSel) return;
  stirrupSel.innerHTML = '';
  const options = (diam === 8) ? STIRRUP_OPTIONS_D8 : STIRRUP_OPTIONS_D6;
  options.forEach(opt => {
    const el = document.createElement('option');
    el.value = opt;
    el.textContent = opt.replace(/^d/i, 'Φ');
    stirrupSel.appendChild(el);
  });
  if (selectedVal) {
    let matched = false;
    for (let i = 0; i < stirrupSel.options.length; i++) {
      if (stirrupSel.options[i].value === selectedVal || stirrupSel.options[i].value.replace(/^d/i, 'Φ') === selectedVal.replace(/^d/i, 'Φ')) {
        stirrupSel.selectedIndex = i;
        matched = true;
        break;
      }
    }
    if (!matched) stirrupSel.selectedIndex = 0;
  } else {
    stirrupSel.selectedIndex = 0;
  }
}

function onStirrupDiamRadioChange(diam) {
  window.currentStirrupDiam = diam;
  const currentBeam = window.currentBeamInModal || selectedBeamForRebar;
  if (!currentBeam) return;

  const chainInfo = findContinuousBeamChain(currentBeam);
  if (chainInfo && chainInfo.chain) {
    chainInfo.chain.forEach(spanBeam => {
      let curVal = spanBeam.stirrup || '';
      let dense = '100';
      let mid = '200';
      const m = curVal.match(/a(\d+)(?:\/a?(\d+))?/i);
      if (m) {
        dense = m[1];
        mid = m[2] ? m[2] : '';
      }
      let newVal = `d${diam}a${dense}` + (mid ? `/a${mid}` : '');
      const opts = (diam === 8) ? STIRRUP_OPTIONS_D8 : STIRRUP_OPTIONS_D6;
      if (!opts.includes(newVal)) newVal = opts[0];
      spanBeam.stirrup = newVal;
      spanBeam._stirrupUserModified = true;
    });
  }

  populateStirrupDropdown(diam, currentBeam.stirrup);
  onRebarSelectChange();
}

// ==============================================================================
// 1. DATA INITIALIZATION & HUB TOGGLING
// ==============================================================================

async function loadEtabsData() {
  try {
    let res = null;
    try {
      res = await fetch('/api/etabs-data');
    } catch (e) {
      console.warn('[ETABS Hub] Failed fetching /api/etabs-data, trying /etabs_beam_data.json fallback');
    }

    if (!res || !res.ok) {
      res = await fetch('/etabs_beam_data.json');
    }

    if (!res.ok) throw new Error('HTTP ' + res.status);
    etabsData = await res.json();
    window.etabsData = etabsData;
    console.log('[ETABS Hub] Loaded data successfully:', etabsData);
    
    // Mặc định cốt đai là Phi 6 cho toàn bộ dầm theo yêu cầu kỹ thuật
    if (etabsData && etabsData.beams) {
      etabsData.beams.forEach(b => {
        if (!b._stirrupUserModified) {
          const m = (b.stirrup || '').match(/a(\d+)(?:\/a?(\d+))?/i);
          const dense = m ? m[1] : '100';
          const mid = (m && m[2]) ? m[2] : '200';
          b.stirrup = `d6a${dense}/a${mid}`;
        }
      });
    }

    // Initialize continuous long beam labels (DX{index} & DY{index})
    initContinuousBeamLabels();

    // Update story select options
    populateStorySelects();
    
    // Populate Rebar tables
    populateRebarTable('rebarTableBody', 'rebarFilterStory', 'rebarSearchInput');
    populateRebarTable('modalRebarTableBody', null, null);
    
    // Render 2D
    renderEtabs2DPlan();

    // Tự động khôi phục cấu hình thép dầm đã lưu trong DB (PostgreSQL / SQLite)
    loadSavedDesignsFromDb();
    
    // Initialize 3D
    setTimeout(() => {
      initThree3D('etabs3DContainer');
    }, 200);

  } catch (err) {
    console.error('[ETABS Hub] Error loading data:', err);
  }
}

// ------------------------------------------------------------------------------
// CONTINUOUS LONG BEAM LABELING (DX{index} FOR X DIRECTION, DY{index} FOR Y DIRECTION)
// ------------------------------------------------------------------------------

function initContinuousBeamLabels() {
  if (!etabsData || !etabsData.beams) return;

  const beams = etabsData.beams;
  const grids = etabsData.grids || {};
  const gridY = grids.Y || [];
  const gridX = grids.X || [];

  function matchGrid(coord, gridList, tol = 500) {
    for (const g of gridList) {
      if (Math.abs(g.ordinate - coord) <= tol) return g.id;
    }
    return null;
  }

  // Pre-load from json if already enriched
  let needsClustering = false;
  beams.forEach(b => {
    if (b.long_beam_id) {
      b.longBeamId = b.long_beam_id;
      b.spanIndex = b.span_index;
      b.spanCount = b.span_count;
      b.direction = b.direction || ((Math.abs(b.p2[0] - b.p1[0]) >= Math.abs(b.p2[1] - b.p1[1])) ? 'X' : 'Y');
      b.axisName = b.axis_name || (b.direction === 'X' ? 'Phương X' : 'Phương Y');
    } else {
      needsClustering = true;
    }
  });

  if (!needsClustering) {
    console.log('[ETABS Hub] Long beam IDs initialized directly from data.');
    syncContinuousBeamsRebarDefaults();
    return;
  }

  const stories = Array.from(new Set(beams.map(b => b.story)));

  stories.forEach(story => {
    const storyBeams = beams.filter(b => b.story === story);
    const xBeams = storyBeams.filter(b => Math.abs(b.p2[0] - b.p1[0]) >= Math.abs(b.p2[1] - b.p1[1]));
    const yBeams = storyBeams.filter(b => Math.abs(b.p2[0] - b.p1[0]) < Math.abs(b.p2[1] - b.p1[1]));

    // 1. Cluster X Beams (DX)
    const yGroups = [];
    xBeams.forEach(b => {
      const yMid = (b.p1[1] + b.p2[1]) / 2.0;
      let grp = yGroups.find(g => Math.abs(g.y - yMid) <= 350);
      if (!grp) {
        grp = { y: yMid, beams: [] };
        yGroups.push(grp);
      }
      grp.beams.push(b);
    });

    const allXChains = [];
    yGroups.forEach(yg => {
      yg.beams.sort((a, b) => Math.min(a.p1[0], a.p2[0]) - Math.min(b.p1[0], b.p2[0]));
      let curr = [];
      yg.beams.forEach(b => {
        const xMin = Math.min(b.p1[0], b.p2[0]);
        const xMax = Math.max(b.p1[0], b.p2[0]);
        if (curr.length === 0) {
          curr.push(b);
        } else {
          const prev = curr[curr.length - 1];
          const prevMax = Math.max(prev.p1[0], prev.p2[0]);
          if (Math.abs(xMin - prevMax) <= 500) {
            curr.push(b);
          } else {
            allXChains.push({ y: yg.y, chain: curr });
            curr = [b];
          }
        }
      });
      if (curr.length > 0) allXChains.push({ y: yg.y, chain: curr });
    });

    // Priority sort: Trục A (1), Trục B (2), Trục C (3), then Y descending, X ascending
    allXChains.sort((a, b) => {
      const gidA = matchGrid(a.y, gridY);
      const gidB = matchGrid(b.y, gridY);
      const xStartA = Math.min(...a.chain.map(x => Math.min(x.p1[0], x.p2[0])));
      const xStartB = Math.min(...b.chain.map(x => Math.min(x.p1[0], x.p2[0])));
      const pMap = { 'A': 1, 'B': 2, 'C': 3 };
      const pA = pMap[gidA] || 99;
      const pB = pMap[gidB] || 99;
      if (pA !== pB) return pA - pB;
      if (Math.abs(b.y - a.y) > 100) return b.y - a.y;
      return xStartA - xStartB;
    });

    allXChains.forEach((item, idx) => {
      const name = `DX${idx + 1}`;
      const gid = matchGrid(item.y, gridY);
      const axisName = gid ? `Trục ${gid}` : `Y=${(item.y/1000).toFixed(1)}m`;
      item.chain.forEach((b, sIdx) => {
        b.longBeamId = name;
        b.spanIndex = sIdx + 1;
        b.spanCount = item.chain.length;
        b.direction = 'X';
        b.axisName = axisName;
      });
    });

    // 2. Cluster Y Beams (DY)
    const xGroups = [];
    yBeams.forEach(b => {
      const xMid = (b.p1[0] + b.p2[0]) / 2.0;
      let grp = xGroups.find(g => Math.abs(g.x - xMid) <= 350);
      if (!grp) {
        grp = { x: xMid, beams: [] };
        xGroups.push(grp);
      }
      grp.beams.push(b);
    });

    const allYChains = [];
    xGroups.forEach(xg => {
      xg.beams.sort((a, b) => Math.min(a.p1[1], a.p2[1]) - Math.min(b.p1[1], b.p2[1]));
      let curr = [];
      xg.beams.forEach(b => {
        const yMin = Math.min(b.p1[1], b.p2[1]);
        const yMax = Math.max(b.p1[1], b.p2[1]);
        if (curr.length === 0) {
          curr.push(b);
        } else {
          const prev = curr[curr.length - 1];
          const prevMax = Math.max(prev.p1[1], prev.p2[1]);
          if (Math.abs(yMin - prevMax) <= 500) {
            curr.push(b);
          } else {
            allYChains.push({ x: xg.x, chain: curr });
            curr = [b];
          }
        }
      });
      if (curr.length > 0) allYChains.push({ x: xg.x, chain: curr });
    });

    // Priority sort: Trục 1..7 ascending, then X ascending, Y ascending
    allYChains.sort((a, b) => {
      const gidA = matchGrid(a.x, gridX);
      const gidB = matchGrid(b.x, gridX);
      const numA = gidA && !isNaN(Number(gidA)) ? Number(gidA) : 999;
      const numB = gidB && !isNaN(Number(gidB)) ? Number(gidB) : 999;
      if (numA !== numB) return numA - numB;
      if (Math.abs(a.x - b.x) > 100) return a.x - b.x;
      const yStartA = Math.min(...a.chain.map(x => Math.min(x.p1[1], x.p2[1])));
      const yStartB = Math.min(...b.chain.map(x => Math.min(x.p1[1], x.p2[1])));
      return yStartA - yStartB;
    });

    allYChains.forEach((item, idx) => {
      const name = `DY${idx + 1}`;
      const gid = matchGrid(item.x, gridX);
      const axisName = gid ? `Trục ${gid}` : `X=${(item.x/1000).toFixed(1)}m`;
      item.chain.forEach((b, sIdx) => {
        b.longBeamId = name;
        b.spanIndex = sIdx + 1;
        b.spanCount = item.chain.length;
        b.direction = 'Y';
        b.axisName = axisName;
      });
    });
  });

  console.log('[ETABS Hub] Initialized DX & DY continuous long beam labels.');
  syncContinuousBeamsRebarDefaults();
}

function selectEtabs2DStory(storyName, containerId = 'etabs2DStoryButtons', inputId = 'etabs2DStorySelect') {
  const input = document.getElementById(inputId);
  if (input) input.value = storyName;

  const container = document.getElementById(containerId);
  if (container) {
    const btns = container.querySelectorAll('.brm-story-btn');
    btns.forEach(b => {
      const isSel = (b.dataset.story === storyName);
      if (isSel) {
        b.className = 'brm-story-btn px-3 py-1.5 rounded-xl font-extrabold text-xs bg-indigo-600 text-white shadow-xs transition flex items-center gap-1 cursor-default';
      } else {
        b.className = 'brm-story-btn px-3 py-1.5 rounded-xl font-semibold text-xs bg-white hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-300 transition cursor-pointer flex items-center gap-1';
      }
    });
  }

  if (containerId === 'etabs2DStoryButtons' || inputId === 'etabs2DStorySelect') {
    renderEtabs2DPlan('etabs2DCanvas', 'etabs2DStorySelect', view2D);
  } else {
    renderModal2DPlan();
  }
}
window.selectEtabs2DStory = selectEtabs2DStory;

function renderStoryButtons(containerId, inputId, defaultStory = 'T3') {
  const container = document.getElementById(containerId);
  const input = document.getElementById(inputId);
  if (!container) return;

  container.innerHTML = '';
  const currentStory = (input && input.value) ? input.value : defaultStory;
  if (input && !input.value) input.value = currentStory;

  const buttonConfigs = [
    { id: 'DK', label: 'DK', title: 'Mặt bằng Đà Kiềng / Móng (Cao độ +1.800m)' },
    { id: 'T1', label: 'T1', title: 'Tầng 1 (Cao độ Z = 1.8m)' },
    { id: 'T2', label: 'T2', title: 'Tầng 2 (Cao độ Z = 7.6m)' },
    { id: 'T3', label: 'T3', title: 'Tầng 3 (Cao độ Z = 11.8m)' },
    { id: 'T4', label: 'T4', title: 'Tầng 4 (Cao độ Z = 15.6m)' },
    { id: 'C',  label: 'C',  title: 'Mặt bằng Định vị & Bố trí Cột toàn nhà' }
  ];

  buttonConfigs.forEach(st => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.story = st.id;
    btn.title = st.title;
    btn.textContent = st.label;

    const isActive = (st.id === currentStory);
    btn.className = isActive
      ? 'brm-story-btn px-3 py-1.5 rounded-xl font-extrabold text-xs bg-indigo-600 text-white shadow-xs transition flex items-center gap-1 cursor-default'
      : 'brm-story-btn px-3 py-1.5 rounded-xl font-semibold text-xs bg-white hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-300 transition cursor-pointer flex items-center gap-1';

    btn.onclick = () => {
      selectEtabs2DStory(st.id, containerId, inputId);
    };

    container.appendChild(btn);
  });
}

function populateStorySelects() {
  if (!etabsData || !etabsData.stories) return;

  renderStoryButtons('etabs2DStoryButtons', 'etabs2DStorySelect', 'T3');
  renderStoryButtons('modal2DStoryButtons', 'modal2DStorySelect', 'T3');

  const selects = ['etabs2DStorySelect', 'modal2DStorySelect'];
  selects.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === 'SELECT') {
      el.innerHTML = '';
      const sorted = [...etabsData.stories].reverse();
      sorted.forEach(st => {
        const opt = document.createElement('option');
        opt.value = st.name;
        opt.textContent = `${st.name} (Cao độ Z = ${(st.elevation/1000).toFixed(1)}m)`;
        el.appendChild(opt);
      });
      if (!el.value) el.value = 'T3';
    } else if (el.tagName === 'INPUT' && !el.value) {
      el.value = 'T3';
    }
  });
}

function openEtabsHub(mode = 'middle') {
  if (!etabsData) {
    loadEtabsData();
  }
  
  if (mode === 'modal') {
    const modal = document.getElementById('etabsModal');
    if (modal) {
      modal.classList.remove('hidden');
      setTimeout(() => {
        fit2DView('modal2DCanvas', modalView2D);
        renderModal2DPlan();
        initModalThree3D('modal3DContainer');
      }, 150);
    }
  } else {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    const tab = document.getElementById('tab-etabs-hub');
    if (tab) {
      tab.classList.remove('hidden');
      tab.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setTimeout(() => {
        fit2DView('etabs2DCanvas', view2D);
        renderEtabs2DPlan();
        if (threeRenderer) {
          resizeThreeRenderer('etabs3DContainer', threeRenderer, threeCamera);
        }
      }, 150);
    }
  }
}

function closeEtabsModal() {
  const modal = document.getElementById('etabsModal');
  if (modal) modal.classList.add('hidden');
}

function switchEtabsSubTab(tabName) {
  const tabs = [
    { id: 'etabs-3d', btnId: 'subtab-btn-3d', paneId: 'subpane-etabs-3d' },
    { id: 'etabs-2d', btnId: 'subtab-btn-2d', paneId: 'subpane-etabs-2d' },
    { id: 'etabs-rebar', btnId: 'subtab-btn-rebar', paneId: 'subpane-etabs-rebar' },
    { id: 'etabs-column-cad', btnId: 'subtab-btn-column-cad', paneId: 'subpane-etabs-column-cad' },
    { id: 'etabs-tie-beam-cad', btnId: 'subtab-btn-tie-beam-cad', paneId: 'subpane-etabs-tie-beam-cad' },
    { id: 'etabs-notes', btnId: 'subtab-btn-notes', paneId: 'subpane-etabs-notes' }
  ];

  if (tabName !== 'etabs-notes' && typeof closeNotesDropdown === 'function') {
    closeNotesDropdown();
  }

  tabs.forEach(t => {
    const btn = document.getElementById(t.btnId);
    const pane = document.getElementById(t.paneId);
    const isActive = (t.id === tabName);

    if (pane) {
      if (isActive) pane.classList.remove('hidden');
      else pane.classList.add('hidden');
    }

    if (btn) {
      if (isActive) {
        btn.className = 'etabs-subtab-btn py-1.5 px-3 rounded-lg font-bold text-xs flex items-center gap-1.5 bg-indigo-600 text-white shadow-xs transition-all duration-150 cursor-pointer';
      } else {
        btn.className = 'etabs-subtab-btn py-1.5 px-3 rounded-lg font-semibold text-xs flex items-center gap-1.5 text-slate-700 hover:text-slate-900 hover:bg-white/60 transition-all duration-150 cursor-pointer';
      }
    }
  });

  if (tabName === 'etabs-2d') {
    setTimeout(() => {
      fit2DView('etabs2DCanvas', view2D);
      renderEtabs2DPlan();
    }, 100);
  } else if (tabName === 'etabs-3d') {
    setTimeout(() => {
      if (!threeRenderer) {
        initThree3D('etabs3DContainer');
      } else {
        resizeThreeRenderer('etabs3DContainer', threeRenderer, threeCamera);
      }
    }, 150);
  } else if (tabName === 'etabs-column-cad') {
    setTimeout(() => {
      fitTabColumnCadView();
      renderTabColumnCad();
    }, 100);
  } else if (tabName === 'etabs-tie-beam-cad') {
    setTimeout(() => {
      fitTabTieBeamCadView();
      renderTabTieBeamCad();
    }, 100);
  } else if (tabName === 'etabs-notes') {
    setTimeout(() => {
      if (typeof initNotesImage === 'function') {
        initNotesImage(() => {
          fitNotesCanvas('tabGnInteractiveCanvas');
        });
      }
    }, 100);
  }
}

function switchEtabsModalTab(tabName) {
  const modalTabs = [
    { id: 'modal-2d', btnId: 'modal-tabbtn-2d', paneId: 'modal-pane-2d' },
    { id: 'modal-3d', btnId: 'modal-tabbtn-3d', paneId: 'modal-pane-3d' },
    { id: 'modal-rebar', btnId: 'modal-tabbtn-rebar', paneId: 'modal-pane-rebar' },
    { id: 'modal-column', btnId: 'modal-tabbtn-column', paneId: 'modal-pane-column' },
    { id: 'modal-notes', btnId: 'modal-tabbtn-notes', paneId: 'modal-pane-notes' }
  ];

  modalTabs.forEach(t => {
    const btn = document.getElementById(t.btnId);
    const pane = document.getElementById(t.paneId);
    const isActive = (t.id === tabName);

    if (pane) {
      if (isActive) pane.classList.remove('hidden');
      else pane.classList.add('hidden');
    }

    if (btn) {
      if (isActive) {
        btn.className = 'py-1 px-3 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-sm transition';
      } else {
        btn.className = 'py-1 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition';
      }
    }
  });

  if (tabName === 'modal-2d') {
    setTimeout(() => {
      fit2DView('modal2DCanvas', modalView2D);
      renderModal2DPlan();
    }, 100);
  } else if (tabName === 'modal-3d') {
    setTimeout(() => {
      if (!modalThreeRenderer) {
        initModalThree3D('modal3DContainer');
      } else {
        resizeThreeRenderer('modal3DContainer', modalThreeRenderer, modalThreeCamera);
      }
    }, 150);
  } else if (tabName === 'modal-column') {
    setTimeout(() => {
      fitModalColumnCadView();
      renderModalColumnCad();
    }, 100);
  } else if (tabName === 'modal-notes') {
    setTimeout(() => {
      if (typeof initNotesImage === 'function') {
        initNotesImage(() => {
          fitNotesCanvas('modalGnInteractiveCanvas');
          fitNotesCanvas('gnInteractiveCanvas');
        });
      }
    }, 100);
  }
}

async function refreshEtabsDataLive() {
  const btn = document.getElementById('btnRefreshEtabs');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="animate-spin inline-block mr-1">⏳</span> Đang nạp ETABS...';
  }
  try {
    const res = await fetch('/api/etabs-refresh', { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'Làm mới thành công!');
    await loadEtabsData();
  } catch (e) {
    alert('Lỗi làm mới: ' + e);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-indigo-600"></i> Làm mới EDB';
      if (window.lucide) lucide.createIcons();
    }
  }
}

// ==============================================================================
// 2. 2D CANVAS FRAMING PLAN VIEWER
// ==============================================================================

let hoveredBeam2D = null;

function draw2DGridBubble(ctx, x, y, label, vState) {
  const R = 15 / vState.scale;
  ctx.save();
  ctx.setLineDash([]);

  // Clean circular bubble with solid white fill & dark slate border
  ctx.beginPath();
  ctx.arc(x, y, R, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  ctx.strokeStyle = '#0f172a';
  ctx.lineWidth = 1.6 / vState.scale;
  ctx.stroke();

  // Axis text inside circle (inverting Y to match text orientation)
  ctx.scale(1, -1);
  ctx.fillStyle = '#0f172a';
  ctx.font = `bold ${Math.max(11, 13 / vState.scale)}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label || '?', x, -y);

  ctx.restore();
}

let hoveredCol2D = null;

function findColumnAt2DCoords(worldX, worldY, scale = 1.0) {
  if (!etabsData || !etabsData.columns) return null;
  const tol = Math.max(350, 20 / scale);
  for (const c of etabsData.columns) {
    const cx = c.p1[0], cy = c.p1[1];
    const cw = c.width || 300, cd = c.depth || 300;
    if (worldX >= cx - cw/2 - tol && worldX <= cx + cw/2 + tol &&
        worldY >= cy - cd/2 - tol && worldY <= cy + cd/2 + tol) {
      return c;
    }
  }
  return null;
}

function findBeamAt2DCoords(worldX, worldY, story, scale = 1.0) {
  if (!etabsData || !etabsData.beams) return null;
  const actualStory = (story === 'DK') ? 'T1' : story;
  const storyBeams = etabsData.beams.filter(b => b.story === actualStory);
  let closest = null;
  let minDist = 999999;

  for (const b of storyBeams) {
    const x1 = b.p1[0], y1 = b.p1[1];
    const x2 = b.p2[0], y2 = b.p2[1];
    const dx = x2 - x1, dy = y2 - y1;
    const lenSq = dx * dx + dy * dy;
    if (lenSq < 1) continue;

    const t = Math.max(0, Math.min(1, ((worldX - x1) * dx + (worldY - y1) * dy) / lenSq));
    const projX = x1 + t * dx;
    const projY = y1 + t * dy;
    const dist = Math.hypot(worldX - projX, worldY - projY);

    const bWidth = b.width || 300;
    const tol = Math.max(bWidth / 2 + 180, 18 / scale, 450);

    if (dist <= tol && dist < minDist) {
      minDist = dist;
      closest = b;
    }
  }
  return closest;
}

function renderEtabs2DPlan(canvasId = 'etabs2DCanvas', selectId = 'etabs2DStorySelect', vState = view2D) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !etabsData) return;
  const ctx = canvas.getContext('2d');
  
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

  const width = rect.width;
  const height = rect.height;

  // Clear background with gray #AAA
  ctx.fillStyle = '#aaaaaa';
  ctx.fillRect(0, 0, width, height);

  const selStory = document.getElementById(selectId) ? document.getElementById(selectId).value : 'T4';
  const showLabels = document.getElementById('chkShow2DLabels') ? document.getElementById('chkShow2DLabels').checked : true;

  // Auto-fit whenever story changes or before user manually pans/zooms
  const isModal = (canvasId === 'modal2DCanvas');
  const prevStory = isModal ? lastModal2DStory : last2DStory;
  if (selStory !== prevStory) {
    if (isModal) lastModal2DStory = selStory;
    else last2DStory = selStory;
    vState.hasUserInteracted = false;
  }

  if (!vState.hasUserInteracted) {
    fit2DView(canvasId, vState);
  }

  const isColumnMode = (selStory === 'C');
  const isTieBeamMode = (selStory === 'DK');
  const actualBeamStory = isTieBeamMode ? 'T1' : selStory;

  const storyBeams = isColumnMode ? [] : etabsData.beams.filter(b => b.story === actualBeamStory);

  let storyCols = [];
  if (isColumnMode) {
    const seen = new Set();
    etabsData.columns.forEach(c => {
      const id = c.label || c.name;
      if (!seen.has(id)) {
        seen.add(id);
        storyCols.push(c);
      }
    });
  } else {
    storyCols = etabsData.columns.filter(c => c.story === (isTieBeamMode ? 'T1' : selStory));
  }

  ctx.save();
  ctx.translate(vState.offsetX, vState.offsetY);
  ctx.scale(vState.scale, -vState.scale); // Invert Y so up is positive Y

  // 1. Draw Grid Lines with Circular Axis Bubbles
  if (etabsData.grids) {
    const bubbleR = 15 / vState.scale;
    const yBot = -1400;
    const yTop = 13400;
    const xLeft = -2000;
    const xRight = 34800;

    // X Grids (Vertical lines: 1, 2, 3, 4, 5, 6, 7)
    (etabsData.grids.X || []).forEach(gx => {
      ctx.lineWidth = 1.2 / vState.scale;
      ctx.setLineDash([5 / vState.scale, 4 / vState.scale]);
      ctx.strokeStyle = '#475569';
      ctx.beginPath();
      ctx.moveTo(gx.ordinate, yBot + bubbleR);
      ctx.lineTo(gx.ordinate, yTop - bubbleR);
      ctx.stroke();
      ctx.setLineDash([]);

      draw2DGridBubble(ctx, gx.ordinate, yBot, gx.id, vState);
      draw2DGridBubble(ctx, gx.ordinate, yTop, gx.id, vState);
    });

    // Y Grids (Horizontal lines: C, B, A)
    (etabsData.grids.Y || []).forEach(gy => {
      ctx.lineWidth = 1.2 / vState.scale;
      ctx.setLineDash([5 / vState.scale, 4 / vState.scale]);
      ctx.strokeStyle = '#475569';
      ctx.beginPath();
      ctx.moveTo(xLeft + bubbleR, gy.ordinate);
      ctx.lineTo(xRight - bubbleR, gy.ordinate);
      ctx.stroke();
      ctx.setLineDash([]);

      draw2DGridBubble(ctx, xLeft, gy.ordinate, gy.id, vState);
      draw2DGridBubble(ctx, xRight, gy.ordinate, gy.id, vState);
    });
  }

  // 2. Draw Beams with TRUE WIDTH
  storyBeams.forEach(b => {
    const x1 = b.p1[0], y1 = b.p1[1];
    const x2 = b.p2[0], y2 = b.p2[1];
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.sqrt(dx*dx + dy*dy);
    if (len < 1) return;

    const bWidth = b.width || 200;
    const hw = bWidth / 2.0;

    const nx = -dy / len;
    const ny = dx / len;

    const v1x = x1 - hw * nx, v1y = y1 - hw * ny;
    const v2x = x1 + hw * nx, v2y = y1 + hw * ny;
    const v3x = x2 + hw * nx, v3y = y2 + hw * ny;
    const v4x = x2 - hw * nx, v4y = y2 - hw * ny;

    ctx.beginPath();
    ctx.moveTo(v1x, v1y);
    ctx.lineTo(v2x, v2y);
    ctx.lineTo(v3x, v3y);
    ctx.lineTo(v4x, v4y);
    ctx.closePath();

    const isHovered = hoveredBeam2D && (hoveredBeam2D.label === b.label) && (hoveredBeam2D.story === b.story);

    if (isHovered) {
      ctx.fillStyle = 'rgba(245, 158, 11, 0.9)'; // Amber 500 highlight
      ctx.strokeStyle = '#d97706';
      ctx.lineWidth = 3.0 / vState.scale;
    } else if (bWidth >= 300) {
      ctx.fillStyle = 'rgba(2, 132, 199, 0.85)'; // Sky 600
      ctx.strokeStyle = '#0369a1';
      ctx.lineWidth = 1.5 / vState.scale;
    } else if (bWidth >= 250) {
      ctx.fillStyle = 'rgba(14, 165, 233, 0.8)';
      ctx.strokeStyle = '#0284c7';
      ctx.lineWidth = 1.5 / vState.scale;
    } else {
      ctx.fillStyle = 'rgba(56, 189, 248, 0.8)';
      ctx.strokeStyle = '#0ea5e9';
      ctx.lineWidth = 1.5 / vState.scale;
    }

    ctx.fill();
    ctx.stroke();

    // Centerline
    ctx.setLineDash([2 / vState.scale, 2 / vState.scale]);
    ctx.strokeStyle = isHovered ? '#78350f' : 'rgba(15, 23, 42, 0.45)';
    ctx.lineWidth = 1.0 / vState.scale;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);
  });

  // 3. Draw Columns
  storyCols.forEach(c => {
    const cx = c.p1[0];
    const cy = c.p1[1];
    const cw = c.width || 300;
    const cd = c.depth || 300;

    const isColHovered = isColumnMode && hoveredCol2D && ((hoveredCol2D.label || hoveredCol2D.name) === (c.label || c.name));

    ctx.fillStyle = isColHovered ? 'rgba(245, 158, 11, 0.95)' : (isColumnMode ? '#0284c7' : '#1e293b');
    ctx.strokeStyle = isColHovered ? '#b45309' : '#0f172a';
    ctx.lineWidth = (isColHovered ? 3.0 : 1.5) / vState.scale;

    ctx.fillRect(cx - cw/2, cy - cd/2, cw, cd);
    ctx.strokeRect(cx - cw/2, cy - cd/2, cw, cd);

    // Cross-hair center lines inside column
    ctx.save();
    ctx.setLineDash([2 / vState.scale, 2 / vState.scale]);
    ctx.strokeStyle = isColHovered ? '#78350f' : 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 1.0 / vState.scale;
    ctx.beginPath();
    ctx.moveTo(cx - cw/2, cy); ctx.lineTo(cx + cw/2, cy);
    ctx.moveTo(cx, cy - cd/2); ctx.lineTo(cx, cy + cd/2);
    ctx.stroke();
    ctx.restore();

    // If Column Mode, draw Column Index Label & Section Dimensions
    if (isColumnMode && showLabels) {
      ctx.save();
      ctx.scale(1, -1);
      ctx.font = `bold ${Math.max(12, 14 / vState.scale)}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const tagText = c.label || c.name;
      const secText = (c.section || `${cw}x${cd}`).replace('C ', '').replace('COL ', '');
      
      const tagOffY = (cy > 8000) ? 600 : ((cy < 2000) ? -600 : 600);
      const tagOffX = (cy > 8000 || cy < 2000) ? 0 : (cx > 16000 ? 600 : -600);
      const tx = cx + tagOffX;
      const ty = -(cy + tagOffY);

      // Leader line
      ctx.strokeStyle = isColHovered ? '#b45309' : '#334155';
      ctx.lineWidth = 1.2 / vState.scale;
      ctx.beginPath();
      ctx.moveTo(cx, -cy);
      ctx.lineTo(tx, ty);
      ctx.stroke();

      // Tag Badge
      const fullLabel = `${tagText} (${secText})`;
      const tW = ctx.measureText(fullLabel).width + (10 / vState.scale);
      const tH = 20 / vState.scale;
      ctx.fillStyle = isColHovered ? 'rgba(245, 158, 11, 0.95)' : 'rgba(15, 23, 42, 0.9)';
      ctx.strokeStyle = isColHovered ? '#fbbf24' : '#38bdf8';
      ctx.lineWidth = 1.2 / vState.scale;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(tx - tW/2, ty - tH/2, tW, tH, 3 / vState.scale);
      else ctx.rect(tx - tW/2, ty - tH/2, tW, tH);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = isColHovered ? '#ffffff' : '#38bdf8';
      ctx.fillText(fullLabel, tx, ty);
      ctx.restore();
    }
  });

  // 4. Draw Beam Text Labels (Rotated 90 deg CCW for DY beams)
  if (showLabels && !isColumnMode) {
    ctx.save();
    ctx.scale(1, -1);
    ctx.font = `bold ${Math.max(11, 12 / vState.scale)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    storyBeams.forEach(b => {
      const mx = (b.p1[0] + b.p2[0]) / 2.0;
      const my = -(b.p1[1] + b.p2[1]) / 2.0;

      const rawName = b.longBeamId || b.label;
      const name = isTieBeamMode ? rawName.replace(/^D([XY])/i, 'DK-$1') : rawName;
      const labelText = `${name}: ${b.section.replace('B ', '')}`;
      const textWidth = ctx.measureText(labelText).width;
      const pad = 4 / vState.scale;
      const boxW = textWidth + pad * 2;
      const boxH = 16 / vState.scale;

      const isDY = (b.longBeamId && b.longBeamId.startsWith('DY')) || (b.direction === 'Y') || (Math.abs(b.p2[1] - b.p1[1]) > Math.abs(b.p2[0] - b.p1[0]));
      const isHovered = hoveredBeam2D && (hoveredBeam2D.label === b.label) && (hoveredBeam2D.story === b.story);

      ctx.save();
      ctx.translate(mx, my);
      if (isDY) {
        ctx.rotate(-Math.PI / 2); // Xoay 90 độ CCW theo yêu cầu
      }

      ctx.fillStyle = isHovered ? 'rgba(245, 158, 11, 0.95)' : 'rgba(15, 23, 42, 0.88)';
      ctx.strokeStyle = isHovered ? '#fbbf24' : '#38bdf8';
      ctx.lineWidth = isHovered ? (1.8 / vState.scale) : (1.0 / vState.scale);

      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(-boxW / 2, -boxH / 2, boxW, boxH, 3 / vState.scale);
      } else {
        ctx.rect(-boxW / 2, -boxH / 2, boxW, boxH);
      }
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = isHovered ? '#ffffff' : '#38bdf8';
      ctx.fillText(labelText, 0, 0);

      ctx.restore();
    });

    ctx.restore();
  }

  ctx.restore();
}

function fit2DView(canvasId = 'etabs2DCanvas', vState = view2D) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height || rect.width < 50 || rect.height < 50) return;

  // Exact bounds of all content including circular grid bubbles & labels:
  // X: from -3600 (leftmost Trục A/B/C bubbles) to 36500 (rightmost grid & beams)
  // Y: from -2600 (bottom Trục 1..7 bubbles) to 14600 (top Trục 1..7 bubbles)
  const minX = -3600;
  const maxX = 36500;
  const minY = -2600;
  const maxY = 14600;

  const modelW = maxX - minX;          // 40100 mm
  const modelH = maxY - minY;          // 17200 mm
  const centerX = (minX + maxX) / 2.0; // 16450 mm
  const centerY = (minY + maxY) / 2.0; // 6000 mm

  // Scale with 94% width padding & 90% height padding for clear framing
  const scaleX = (rect.width * 0.94) / modelW;
  const scaleY = (rect.height * 0.90) / modelH;
  vState.scale = Math.min(scaleX, scaleY);

  // Exact mathematical centering
  vState.offsetX = (rect.width / 2.0) - (centerX * vState.scale);
  vState.offsetY = (rect.height / 2.0) + (centerY * vState.scale);
}

function zoomEtabs2D(factor) {
  view2D.scale *= factor;
  view2D.hasUserInteracted = true;
  renderEtabs2DPlan('etabs2DCanvas', 'etabs2DStorySelect', view2D);
}

function resetEtabs2DView() {
  view2D.hasUserInteracted = false;
  fit2DView('etabs2DCanvas', view2D);
  renderEtabs2DPlan('etabs2DCanvas', 'etabs2DStorySelect', view2D);
}

function renderModal2DPlan() {
  renderEtabs2DPlan('modal2DCanvas', 'modal2DStorySelect', modalView2D);
}

function zoomModal2D(factor) {
  modalView2D.scale *= factor;
  modalView2D.hasUserInteracted = true;
  renderModal2DPlan();
}

function resetModal2DView() {
  modalView2D.hasUserInteracted = false;
  fit2DView('modal2DCanvas', modalView2D);
  renderModal2DPlan();
}

function setup2DCanvasEvents(canvasId, vState, renderFn) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const tooltip = (canvasId === 'etabs2DCanvas') ? document.getElementById('etabs2DTooltip') : null;

  canvas.addEventListener('mousedown', e => {
    vState.isDragging = true;
    vState.hasDragged = false;
    vState.dragStartX = e.clientX - vState.offsetX;
    vState.dragStartY = e.clientY - vState.offsetY;
    vState.downX = e.clientX;
    vState.downY = e.clientY;
  });

  window.addEventListener('mousemove', e => {
    if (vState.isDragging) {
      if (Math.hypot(e.clientX - vState.downX, e.clientY - vState.downY) > 5) {
        vState.hasDragged = true;
      }
      vState.offsetX = e.clientX - vState.dragStartX;
      vState.offsetY = e.clientY - vState.dragStartY;
      vState.hasUserInteracted = true; // User manually panned
      if (tooltip) tooltip.classList.add('hidden');
      renderFn();
      return;
    }

    if (e.target !== canvas) {
      if (hoveredBeam2D && canvasId === 'etabs2DCanvas') {
        hoveredBeam2D = null;
        renderFn();
      }
      if (tooltip) tooltip.classList.add('hidden');
      return;
    }

    // Hover detection on 2D Plan
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const worldX = (mouseX - vState.offsetX) / vState.scale;
    const worldY = -((mouseY - vState.offsetY) / vState.scale);

    const selectEl = document.getElementById(canvasId === 'modal2DCanvas' ? 'modal2DStorySelect' : 'etabs2DStorySelect');
    const selStory = (selectEl && selectEl.value) || (etabsData && etabsData.beams && etabsData.beams[0]?.story) || 'T1';

    if (selStory === 'C') {
      const col = findColumnAt2DCoords(worldX, worldY, vState.scale);
      if (col) {
        canvas.style.cursor = 'pointer';
        if (hoveredCol2D !== col) {
          hoveredCol2D = col;
          renderFn();
        }
        if (tooltip) {
          const colName = col.label || col.name;
          const sec = (col.section || `${col.width}x${col.depth}`).replace('C ', '');
          tooltip.innerHTML = `
            <div class="font-bold text-white flex items-center justify-between gap-3 border-b border-slate-700 pb-1 mb-1">
              <span class="text-amber-400 font-mono text-sm">${colName}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/30 text-sky-300">Cột BTCT (${sec})</span>
            </div>
            <div class="text-[11px] text-slate-300 space-y-0.5">
              <div>📍 Tọa độ: X=${(col.p1[0]/1000).toFixed(2)}m, Y=${(col.p1[1]/1000).toFixed(2)}m</div>
              <div>⚡ Cốt thép: <span class="text-emerald-400 font-bold">${col.rebar_str || '4Φ18'}</span> (Đai d6a100/200)</div>
              <div>🏢 Tầng: <span class="text-sky-300 font-semibold">T1 - T4</span></div>
            </div>
            <div class="mt-1.5 pt-1 border-t border-slate-700/60 text-[10px] text-cyan-300 font-bold flex items-center gap-1">
              <span>👉 Bấm chuột để xem Bản Vẽ Cột (Grid 15x4)</span>
            </div>
          `;
          tooltip.style.left = `${Math.min(rect.width - 240, mouseX + 15)}px`;
          tooltip.style.top = `${Math.min(rect.height - 140, mouseY + 15)}px`;
          tooltip.classList.remove('hidden');
        }
        return;
      } else {
        if (hoveredCol2D) {
          hoveredCol2D = null;
          renderFn();
        }
      }
    }

    const actualStory = (selStory === 'DK') ? 'T1' : selStory;
    const beam = findBeamAt2DCoords(worldX, worldY, actualStory, vState.scale);

    if (beam) {
      canvas.style.cursor = 'pointer';
      if (hoveredBeam2D !== beam) {
        hoveredBeam2D = beam;
        renderFn();
      }

      if (tooltip) {
        const { mLeft, mMid, mRight } = calculateBeamMoments(beam);
        const rawName = beam.longBeamId || beam.label;
        const bName = (selStory === 'DK') ? rawName.replace(/^D([XY])/i, 'DK-$1') : rawName;
        tooltip.innerHTML = `
          <div class="font-bold text-white flex items-center justify-between gap-3 border-b border-slate-700 pb-1 mb-1">
            <span class="text-amber-400 font-mono text-sm">${bName}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/30 text-indigo-300">${selStory === 'DK' ? 'Đà Kiềng' : ('Nhịp ' + (beam.spanIndex || 1) + '/' + (beam.spanCount || 1))} • ${beam.story}</span>
          </div>
          <div class="text-[11px] text-slate-300 space-y-0.5">
            <div>📐 Tiết diện: <strong class="text-white">${beam.section}</strong> (L = ${(beam.length/1000).toFixed(2)}m)</div>
            <div>⚡ Moment: <span class="text-rose-400 font-semibold">${mLeft}</span> / <span class="text-emerald-400 font-bold">+${mMid}</span> / <span class="text-rose-400 font-semibold">${mRight}</span> kNm</div>
            <div>🔩 Thép chọn: <span class="text-sky-300 font-mono font-semibold">${beam.rebar_top_left} / ${beam.rebar_bot_mid} / ${beam.rebar_top_right}</span></div>
          </div>
          <div class="mt-1.5 pt-1 border-t border-slate-700/60 text-[10px] text-cyan-300 font-bold flex items-center gap-1">
            <span>👉 Bấm chuột để chọn cốt thép dầm</span>
          </div>
        `;
        tooltip.style.left = `${Math.min(rect.width - 240, mouseX + 15)}px`;
        tooltip.style.top = `${Math.min(rect.height - 140, mouseY + 15)}px`;
        tooltip.classList.remove('hidden');
      }
    } else {
      canvas.style.cursor = 'grab';
      if (hoveredBeam2D) {
        hoveredBeam2D = null;
        renderFn();
      }
      if (tooltip) tooltip.classList.add('hidden');
    }
  });

  window.addEventListener('mouseup', () => {
    vState.isDragging = false;
  });

  canvas.addEventListener('click', e => {
    if (vState.hasDragged) return; // User was panning, ignore click
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const worldX = (mouseX - vState.offsetX) / vState.scale;
    const worldY = -((mouseY - vState.offsetY) / vState.scale);

    const selectEl = document.getElementById(canvasId === 'modal2DCanvas' ? 'modal2DStorySelect' : 'etabs2DStorySelect');
    const selStory = (selectEl && selectEl.value) || (etabsData && etabsData.beams && etabsData.beams[0]?.story) || 'T1';

    if (selStory === 'C') {
      const col = findColumnAt2DCoords(worldX, worldY, vState.scale);
      if (col) {
        if (tooltip) tooltip.classList.add('hidden');
        openColumnDrawingModal();
        return;
      }
    }

    const actualStory = (selStory === 'DK') ? 'T1' : selStory;
    const beam = findBeamAt2DCoords(worldX, worldY, actualStory, vState.scale);
    if (beam) {
      if (tooltip) tooltip.classList.add('hidden');
      openBeamRebarModal(beam);
    }
  });

  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    vState.scale *= zoomFactor;
    vState.hasUserInteracted = true; // User manually zoomed
    if (tooltip) tooltip.classList.add('hidden');
    renderFn();
  }, { passive: false });

  // Responsive: Automatically re-fit whenever container size changes or becomes visible
  if (window.ResizeObserver && canvas.parentElement) {
    const ro = new ResizeObserver(() => {
      if (!vState.hasUserInteracted) {
        fit2DView(canvasId, vState);
      }
      renderFn();
    });
    ro.observe(canvas.parentElement);
  }
}


// ==============================================================================
// 3. THREE.JS 3D SOLID CROSS-SECTION VIEWER (WITH GRIDS, MOMENTS, RAYCASTER)
// ==============================================================================

function initThree3D(containerId) {
  const container = document.getElementById(containerId);
  if (!container || !window.THREE || !etabsData) return;
  if (container.children.length > 0) return;

  const width = container.clientWidth;
  const height = container.clientHeight;

  threeScene = new THREE.Scene();
  threeScene.background = new THREE.Color(0xaaaaaa); // Gray #AAA

  threeCamera = new THREE.PerspectiveCamera(45, width / height, 100, 200000);
  threeCamera.position.set(16500, 16000, 24000);

  threeRenderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  threeRenderer.setSize(width, height);
  threeRenderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(threeRenderer.domElement);

  if (window.THREE.OrbitControls) {
    threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
    threeControls.target.set(16500, 7600, -6000);
    threeControls.enableDamping = true;
    threeControls.dampingFactor = 0.08;
    threeControls.screenSpacePanning = true;
    threeControls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN
    };
    threeControls.update();
  }

  threeScene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.85);
  dirLight1.position.set(20000, 40000, 30000);
  threeScene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x93c5fd, 0.45);
  dirLight2.position.set(-20000, -20000, -20000);
  threeScene.add(dirLight2);

  // Ground Grid
  const gridHelper = new THREE.GridHelper(50000, 50, 0x475569, 0x888888);
  gridHelper.position.set(16500, 0, -6000);
  threeScene.add(gridHelper);

  // Build Model & Layers
  build3DModel(threeScene, false);

  // Setup Raycaster Hover & Click for Beams
  setupThreeRaycaster(container, threeRenderer, threeCamera, threeBeamMeshes, 'etabs3DTooltip');

  // Setup AEC 3D Studio Interaction (Wall Line, Door Block, Snap & Round)
  initAecStudio();
  setupAec3DInteraction(container, threeRenderer, threeCamera, threeScene, false);

  // Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    if (threeControls) threeControls.update();
    threeRenderer.render(threeScene, threeCamera);
  }
  animate();
}

function initModalThree3D(containerId) {
  const container = document.getElementById(containerId);
  if (!container || !window.THREE || !etabsData) return;
  if (container.children.length > 0) return;

  const width = container.clientWidth;
  const height = container.clientHeight;

  modalThreeScene = new THREE.Scene();
  modalThreeScene.background = new THREE.Color(0xaaaaaa); // Gray #AAA

  modalThreeCamera = new THREE.PerspectiveCamera(45, width / height, 100, 200000);
  modalThreeCamera.position.set(16500, 16000, 24000);

  modalThreeRenderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  modalThreeRenderer.setSize(width, height);
  modalThreeRenderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(modalThreeRenderer.domElement);

  if (window.THREE.OrbitControls) {
    modalThreeControls = new THREE.OrbitControls(modalThreeCamera, modalThreeRenderer.domElement);
    modalThreeControls.target.set(16500, 7600, -6000);
    modalThreeControls.enableDamping = true;
    modalThreeControls.dampingFactor = 0.08;
    modalThreeControls.screenSpacePanning = true;
    modalThreeControls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN
    };
    modalThreeControls.update();
  }

  modalThreeScene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.85);
  dirLight.position.set(20000, 40000, 30000);
  modalThreeScene.add(dirLight);

  const gridHelper = new THREE.GridHelper(50000, 50, 0x475569, 0x888888);
  gridHelper.position.set(16500, 0, -6000);
  modalThreeScene.add(gridHelper);

  build3DModel(modalThreeScene, true);

  setupThreeRaycaster(container, modalThreeRenderer, modalThreeCamera, modalThreeBeamMeshes, 'etabs3DTooltip');

  // Setup Modal AEC 3D Interaction
  setupAec3DInteraction(container, modalThreeRenderer, modalThreeCamera, modalThreeScene, true);

  function animate() {
    requestAnimationFrame(animate);
    if (modalThreeControls) modalThreeControls.update();
    modalThreeRenderer.render(modalThreeScene, modalThreeCamera);
  }
  animate();
}

// ------------------------------------------------------------------------------
// BUILD 3D MODEL (COLUMNS, BEAMS, BALCONY/STAIR SLABS, GRIDS, MOMENTS, LABELS)
// ------------------------------------------------------------------------------

function build3DModel(scene, isModal = false) {
  if (!etabsData) return;

  const targetMeshes = isModal ? modalThreeMeshes : threeMeshes;
  const targetBeamMeshes = isModal ? modalThreeBeamMeshes : threeBeamMeshes;
  targetMeshes.length = 0;
  targetBeamMeshes.length = 0;

  const beamMaterial = new THREE.MeshStandardMaterial({
    color: 0x0ea5e9, // Sky 500
    roughness: 0.4,
    metalness: 0.1,
    wireframe: is3DWireframe
  });

  const colMaterial = new THREE.MeshStandardMaterial({
    color: 0x6366f1, // Indigo 500
    roughness: 0.4,
    metalness: 0.1,
    wireframe: is3DWireframe
  });

  const stairMaterial = new THREE.MeshStandardMaterial({
    color: 0xef4444, // Red
    roughness: 0.3,
    transparent: true,
    opacity: 0.85,
    side: THREE.DoubleSide,
    wireframe: is3DWireframe
  });

  // 1. Columns (Extruded Solid Boxes along Z)
  (etabsData.columns || []).forEach(c => {
    const w = c.width || 300;
    const d = c.depth || 300;
    const h = c.height || 3800;

    const geom = new THREE.BoxGeometry(w, h, d);
    const mesh = new THREE.Mesh(geom, colMaterial);

    const mx = c.p1[0];
    const my = (c.p1[2] + c.p2[2]) / 2.0; // Three.js Y is ETABS Z (Height)
    const mz = -c.p1[1];                   // Three.js Z is -ETABS Y (Fix Z-Up flip)

    mesh.position.set(mx, my, mz);
    scene.add(mesh);
    targetMeshes.push(mesh);

    const edges = new THREE.EdgesGeometry(geom);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x1e1b4b, linewidth: 1 }));
    mesh.add(line);
  });

  // 2. Beams (Oriented Solid Boxes with real b x h)
  (etabsData.beams || []).forEach(b => {
    const x1 = b.p1[0], y1 = b.p1[1], z1 = b.p1[2];
    const x2 = b.p2[0], y2 = b.p2[1], z2 = b.p2[2];

    const dx = x2 - x1;
    const dy = y2 - y1;
    const dz = z2 - z1;
    const length = Math.sqrt(dx*dx + dy*dy + dz*dz);
    if (length < 10) return;

    const bWidth = b.width || 200;
    const bDepth = b.depth || 400;

    const geom = new THREE.BoxGeometry(bWidth, bDepth, length);
    // Distinct material clone per beam so we can highlight individually
    const meshMat = beamMaterial.clone();
    const mesh = new THREE.Mesh(geom, meshMat);

    const mx = (x1 + x2) / 2.0;
    const my = (z1 + z2) / 2.0;
    const mz = -(y1 + y2) / 2.0; // Three.js Z is -ETABS Y (Fix Z-Up flip)

    mesh.position.set(mx, my, mz);

    const dir = new THREE.Vector3(dx, dz, -dy).normalize();
    const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir);
    mesh.setRotationFromQuaternion(quat);

    // Attach data for Raycaster inspection & click selection
    mesh.userData = { isBeam: true, beam: b, origColor: 0x0ea5e9 };

    scene.add(mesh);
    targetMeshes.push(mesh);
    targetBeamMeshes.push(mesh);

    const edges = new THREE.EdgesGeometry(geom);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x0369a1, linewidth: 1 }));
    mesh.add(line);
  });

  // 3. Slabs & Balconies (Robust N-gon Triangulation to fix Balcony gap at Trục 7)
  (etabsData.areas || []).forEach(a => {
    if (a.coords && a.coords.length >= 3) {
      const pts = a.coords.map(c => new THREE.Vector3(c[0], c[2], -c[1]));
      const geom = new THREE.BufferGeometry();
      const vertices = [];

      if (pts.length === 3) {
        vertices.push(pts[0].x, pts[0].y, pts[0].z);
        vertices.push(pts[1].x, pts[1].y, pts[1].z);
        vertices.push(pts[2].x, pts[2].y, pts[2].z);
      } else if (pts.length === 4) {
        vertices.push(pts[0].x, pts[0].y, pts[0].z);
        vertices.push(pts[1].x, pts[1].y, pts[1].z);
        vertices.push(pts[2].x, pts[2].y, pts[2].z);

        vertices.push(pts[0].x, pts[0].y, pts[0].z);
        vertices.push(pts[2].x, pts[2].y, pts[2].z);
        vertices.push(pts[3].x, pts[3].y, pts[3].z);
      } else {
        // N-gon (e.g. 6-point Balcony F29 at Trục 7)
        try {
          const pts2D = pts.map(p => ({ x: p.x, y: p.z }));
          const faces = (THREE.ShapeUtils && THREE.ShapeUtils.triangulateShape)
            ? THREE.ShapeUtils.triangulateShape(pts2D, [])
            : null;
          if (faces && faces.length > 0) {
            faces.forEach(f => {
              const pA = pts[f[0]], pB = pts[f[1]], pC = pts[f[2]];
              vertices.push(pA.x, pA.y, pA.z);
              vertices.push(pB.x, pB.y, pB.z);
              vertices.push(pC.x, pC.y, pC.z);
            });
          } else {
            // Fan fallback
            for (let i = 1; i < pts.length - 1; i++) {
              vertices.push(pts[0].x, pts[0].y, pts[0].z);
              vertices.push(pts[i].x, pts[i].y, pts[i].z);
              vertices.push(pts[i+1].x, pts[i+1].y, pts[i+1].z);
            }
          }
        } catch (e) {
          for (let i = 1; i < pts.length - 1; i++) {
            vertices.push(pts[0].x, pts[0].y, pts[0].z);
            vertices.push(pts[i].x, pts[i].y, pts[i].z);
            vertices.push(pts[i+1].x, pts[i+1].y, pts[i+1].z);
          }
        }
      }

      geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geom.computeVertexNormals();

      const meshMat = stairMaterial.clone();
      const mesh = new THREE.Mesh(geom, meshMat);
      scene.add(mesh);
      targetMeshes.push(mesh);

      // Clean perimeter line loop
      const lineGeom = new THREE.BufferGeometry().setFromPoints(pts);
      const edgeLoop = new THREE.LineLoop(lineGeom, new THREE.LineBasicMaterial({ color: 0xf43f5e, linewidth: 2 }));
      scene.add(edgeLoop);
    }
  });

  // 4. (1) Grid Lines & Billboard Bubbles
  const gridsGrp = build3DGrids(scene);
  if (isModal) modalThreeGridsGroup = gridsGrp;
  else threeGridsGroup = gridsGrp;

  // 5. (3) 3D Moment M33 Diagrams
  const momentsGrp = build3DMoments(scene);
  if (isModal) modalThreeMomentsGroup = momentsGrp;
  else threeMomentsGroup = momentsGrp;

  // 6. (5) 3D Beam Labels
  const labelsGrp = build3DBeamLabels(scene);
  if (isModal) modalThreeLabelsGroup = labelsGrp;
  else threeLabelsGroup = labelsGrp;

  // 7. (6) AEC 3D Objects (Walls & Doors)
  const aecGrp = buildAecMeshes(scene, isModal);
  if (isModal) modalAecThreeGroup = aecGrp;
  else aecThreeGroup = aecGrp;
}

// ------------------------------------------------------------------------------
// 3D GRID SYSTEM (TRỤC 1-7, A-C)
// ------------------------------------------------------------------------------

function createTextBubbleSprite(text, bgColor = 'transparent', textColor = '#0f172a', borderColor = '#0284c7') {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');

  ctx.clearRect(0, 0, 128, 128);

  // NO FILL: Clean circular border outline only
  ctx.beginPath();
  ctx.arc(64, 64, 52, 0, Math.PI * 2);
  ctx.lineWidth = 6;
  ctx.strokeStyle = borderColor;
  ctx.stroke();

  // Text inside bubble: Crisp slate text, zero background fill
  ctx.fillStyle = textColor;
  ctx.font = 'bold 52px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 64, 64);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(1800, 1800, 1);
  return sprite;
}

function build3DGrids(scene) {
  const group = new THREE.Group();
  group.name = 'etabs_grids_group';
  group.visible = show3DGrids;
  if (!etabsData || !etabsData.grids) return group;

  const minX = -2000, maxX = 36000;
  const gridY = 0; // Elevation Z=0 in ETABS -> Y=0 in Three.js
  const minZ = -14000, maxZ = 2000; // -maxY to -minY

  const lineMat = new THREE.LineDashedMaterial({
    color: 0x0284c7,
    dashSize: 500,
    gapSize: 250,
    linewidth: 1,
    opacity: 0.75,
    transparent: true
  });

  // X Grids (Vertical in plan -> lines along Z in Three.js)
  (etabsData.grids.X || []).forEach(gx => {
    const x = gx.ordinate;
    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, gridY, minZ),
      new THREE.Vector3(x, gridY, maxZ)
    ]);
    const line = new THREE.Line(geom, lineMat);
    line.computeLineDistances();
    group.add(line);

    // Bubble at minZ & maxZ
    const sp1 = createTextBubbleSprite(gx.id);
    sp1.position.set(x, gridY + 200, minZ - 1200);
    group.add(sp1);

    const sp2 = createTextBubbleSprite(gx.id);
    sp2.position.set(x, gridY + 200, maxZ + 1200);
    group.add(sp2);
  });

  // Y Grids (Horizontal in plan -> lines along X in Three.js)
  (etabsData.grids.Y || []).forEach(gy => {
    const z = -gy.ordinate; // -ETABS Y
    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(minX, gridY, z),
      new THREE.Vector3(maxX, gridY, z)
    ]);
    const line = new THREE.Line(geom, lineMat);
    line.computeLineDistances();
    group.add(line);

    const sp1 = createTextBubbleSprite(gy.id);
    sp1.position.set(minX - 1200, gridY + 200, z);
    group.add(sp1);

    const sp2 = createTextBubbleSprite(gy.id);
    sp2.position.set(maxX + 1200, gridY + 200, z);
    group.add(sp2);
  });

  scene.add(group);
  return group;
}

// ------------------------------------------------------------------------------
// (3) 3D MOMENT M33 CALCULATION & PARABOLIC DIAGRAMS
// ------------------------------------------------------------------------------

function calculateBeamMoments(b) {
  const h0 = Math.max(100, (b.depth || 400) - 40);
  // M (kNm) = As (cm2) * 100 * 350 * 0.9 * h0 * 1e-6 = As * 0.0315 * h0
  const mLeft = -Math.round((b.as_top_left_cm2 || 0) * 0.0315 * h0 * 10) / 10;
  const mRight = -Math.round((b.as_top_right_cm2 || 0) * 0.0315 * h0 * 10) / 10;
  const mMid = Math.round((b.as_bot_mid_cm2 || 0) * 0.0315 * h0 * 10) / 10;
  return { mLeft, mMid, mRight, h0 };
}

function build3DMoments(scene) {
  const group = new THREE.Group();
  group.name = 'etabs_moments_group';
  group.visible = show3DMoments;
  if (!etabsData || !etabsData.beams) return group;

  const scaleM = 10.0; // 1 kNm = 10mm visual height

  etabsData.beams.forEach(b => {
    const x1 = b.p1[0], y1 = b.p1[1], z1 = b.p1[2];
    const x2 = b.p2[0], y2 = b.p2[1], z2 = b.p2[2];
    const p1 = new THREE.Vector3(x1, z1, -y1);
    const p2 = new THREE.Vector3(x2, z2, -y2);
    const L = p1.distanceTo(p2);
    if (L < 10) return;

    const { mLeft, mMid, mRight } = calculateBeamMoments(b);
    b._calculatedMoments = { mLeft, mMid, mRight };
    if (Math.abs(mLeft) < 0.1 && Math.abs(mMid) < 0.1 && Math.abs(mRight) < 0.1) return;

    const curvePts = [];
    const hatchVerts = [];
    const segments = 24;

    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const basePt = new THREE.Vector3().lerpVectors(p1, p2, t);
      // Parabolic formulation: M(t) = mL*(1-t) + mR*t + 4*mM*t*(1-t)
      const mVal = mLeft * (1 - t) + mRight * t + 4.0 * mMid * t * (1 - t);
      // Offset upward (+Y) for negative moment, downward (-Y) for positive moment
      const offsetY = -mVal * scaleM;
      const momentPt = new THREE.Vector3(basePt.x, basePt.y + offsetY, basePt.z);
      curvePts.push(momentPt);

      // Hatch line every 2 steps
      if (i % 2 === 0 && Math.abs(mVal) > 0.5) {
        hatchVerts.push(basePt.x, basePt.y, basePt.z);
        hatchVerts.push(momentPt.x, momentPt.y, momentPt.z);
      }
    }

    // Parabolic Moment Curve
    const curveGeom = new THREE.BufferGeometry().setFromPoints(curvePts);
    const curveMat = new THREE.LineBasicMaterial({ color: 0xf59e0b, linewidth: 2 }); // Amber
    const curveLine = new THREE.Line(curveGeom, curveMat);
    group.add(curveLine);

    // Hatch Lines
    if (hatchVerts.length > 0) {
      const hatchGeom = new THREE.BufferGeometry();
      hatchGeom.setAttribute('position', new THREE.Float32BufferAttribute(hatchVerts, 3));
      const hatchMat = new THREE.LineBasicMaterial({ color: 0xfbbf24, opacity: 0.45, transparent: true });
      const hatchMesh = new THREE.LineSegments(hatchGeom, hatchMat);
      group.add(hatchMesh);
    }
  });

  scene.add(group);
  return group;
}

// ------------------------------------------------------------------------------
// (5) 3D BEAM LABELS (BILLBOARD SPRITES)
// ------------------------------------------------------------------------------

function createBeamLabelSprite(name, section) {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 96;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.roundRect(8, 8, 240, 80, 16);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = '#38bdf8';
  ctx.font = 'bold 32px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(name, 128, 42);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '24px sans-serif';
  ctx.fillText(section.replace('B ', ''), 128, 72);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(1600, 600, 1);
  return sprite;
}

function build3DBeamLabels(scene) {
  const group = new THREE.Group();
  group.name = 'etabs_beam_labels_group';
  group.visible = show3DBeamLabels;
  if (!etabsData || !etabsData.beams) return group;

  etabsData.beams.forEach(b => {
    const mx = (b.p1[0] + b.p2[0]) / 2.0;
    const my = (b.p1[2] + b.p2[2]) / 2.0 + (b.depth || 400) / 2.0 + 350;
    const mz = -(b.p1[1] + b.p2[1]) / 2.0;

    const sp = createBeamLabelSprite(b.longBeamId || b.label, b.section);
    sp.position.set(mx, my, mz);
    group.add(sp);
  });

  scene.add(group);
  return group;
}

// ------------------------------------------------------------------------------
// RAYCASTER HOVER & CLICK LISTENER FOR 3D BEAMS
// ------------------------------------------------------------------------------

function setupThreeRaycaster(container, renderer, camera, beamMeshes, tooltipId) {
  const tooltip = document.getElementById(tooltipId);

  container.addEventListener('mousemove', e => {
    if (typeof aecToolMode !== 'undefined' && aecToolMode !== 'select') return;
    const rect = container.getBoundingClientRect();
    threeMouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    threeMouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    threeRaycaster.setFromCamera(threeMouse, camera);
    const intersects = threeRaycaster.intersectObjects(beamMeshes);

    if (intersects.length > 0) {
      const hit = intersects[0];
      const mesh = hit.object;
      const b = mesh.userData.beam;

      if (hoveredBeamMesh && hoveredBeamMesh !== mesh) {
        hoveredBeamMesh.material.color.setHex(hoveredBeamMesh.userData.origColor);
      }

      mesh.material.color.setHex(0xf59e0b); // Highlight Amber
      hoveredBeamMesh = mesh;
      container.style.cursor = 'pointer';

      if (tooltip && b) {
        const { mLeft, mMid, mRight } = calculateBeamMoments(b);
        tooltip.innerHTML = `
          <div class="font-bold text-white flex items-center justify-between gap-3 border-b border-slate-700 pb-1 mb-1.5">
            <span class="text-amber-400 font-mono text-sm">${b.longBeamId || b.label}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/30 text-indigo-300">Nhịp ${b.spanIndex || 1}/${b.spanCount || 1} • ${b.story}</span>
          </div>
          <div class="text-[11px] text-slate-300 space-y-0.5">
            <div>📐 Tiết diện: <strong class="text-white">${b.section}</strong> (L = ${(b.length/1000).toFixed(2)}m)</div>
            <div>⚡ Moment: <span class="text-rose-400 font-semibold">${mLeft}</span> / <span class="text-emerald-400 font-bold">+${mMid}</span> / <span class="text-rose-400 font-semibold">${mRight}</span> kNm</div>
            <div>🔩 Thép chọn: <span class="text-sky-300 font-mono font-semibold">${b.rebar_top_left} / ${b.rebar_bot_mid} / ${b.rebar_top_right}</span></div>
          </div>
          <div class="mt-2 pt-1 border-t border-slate-700/60 text-[10px] text-cyan-300 font-bold flex items-center gap-1">
            <span>👉 Bấm chuột để chọn cốt thép dầm</span>
          </div>
        `;
        tooltip.style.left = `${Math.min(rect.width - 240, e.clientX - rect.left + 15)}px`;
        tooltip.style.top = `${Math.min(rect.height - 140, e.clientY - rect.top + 15)}px`;
        tooltip.classList.remove('hidden');
      }
    } else {
      if (hoveredBeamMesh) {
        hoveredBeamMesh.material.color.setHex(hoveredBeamMesh.userData.origColor);
        hoveredBeamMesh = null;
      }
      container.style.cursor = 'default';
      if (tooltip) tooltip.classList.add('hidden');
    }
  });

  let isDragging3D = false;
  let start3DX = 0;
  let start3DY = 0;

  container.addEventListener('mousedown', e => {
    start3DX = e.clientX;
    start3DY = e.clientY;
    isDragging3D = false;
  });

  container.addEventListener('mousemove', e => {
    if (Math.hypot(e.clientX - start3DX, e.clientY - start3DY) > 5) {
      isDragging3D = true;
    }
  });

  container.addEventListener('click', e => {
    if (typeof aecToolMode !== 'undefined' && aecToolMode !== 'select') return;
    if (isDragging3D) {
      return; // Đã kéo chuột (xoay hoặc pan), không kích hoạt click mở modal
    }
    if (e.button !== 0) return; // Chỉ nhận click chuột trái

    const rect = container.getBoundingClientRect();
    threeMouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    threeMouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    threeRaycaster.setFromCamera(threeMouse, camera);
    const intersects = threeRaycaster.intersectObjects(beamMeshes);

    if (intersects.length > 0) {
      const b = intersects[0].object.userData.beam;
      if (b) {
        openBeamRebarModal(b);
      }
    }
  });
}

// ------------------------------------------------------------------------------
// (5) BEAM REBAR INSPECTOR, CAD DRAWINGS & CONTINUOUS BEAM ENGINE
// ------------------------------------------------------------------------------

let beamDrawingMode = 'chain'; // 'chain' (Dầm dài liên tục) | '3d'
const scaleCAD = 0.08; // True Isometric Scale: 1mm thực tế = 0.08px trên bản vẽ

// State đường bao Layout trang in A3 và khoảng hở mặt cắt (Mặc định 1/50, Zoom MC/Dầm: 2:1, MarginX: 500, MarginY: 400, Gap X: -100, Gap Y: -100)
const brmLayoutState = {
  scale: 50,     // Mặc định tỉ lệ 1/50
  sheetW: 21000, // 420 * 50 = 21000 mm
  sheetH: 14850, // 297 * 50 = 14850 mm
  csRatio: 2,    // Tỉ lệ zoom phóng to Cross Section so với Dầm Dọc (Mặc định 2:1)
  marginX: 500,  // mm lề X toàn trang
  marginY: 400,  // mm lề Y toàn trang
  gapX: -100,    // mm (Mặc định -100)
  gapY: -100,    // mm (Mặc định -100)
  leaderLen: 160,     // mm Chiều dài nằm ngang của tất cả leader
  leaderDist: 60,     // mm Khoảng cách xiên từ leader đến điểm destination
  dimSpace1: 350,     // mm Spacing Dim 1: khoảng cách từ dầm đến đường kích thước đầu tiên
  dimSpace2: 260,     // mm Spacing Dim 2: khoảng cách giữa các đường kích thước liên tiếp
  dimScale: 1.0,      // Hệ số scale chữ và gạch chéo kích thước (longitudinal + cross sections)
  _userChanged: false
};
window.brmLayoutState = brmLayoutState;

function loadBrmLayoutState() {
  try {
    const raw = localStorage.getItem('brmLayoutState');
    if (raw) {
      const data = JSON.parse(raw);
      if (data && typeof data === 'object') {
        if (data.scale !== undefined && data.scale !== null) brmLayoutState.scale = parseInt(data.scale, 10) || 50;
        if (data.csRatio !== undefined && data.csRatio !== null) brmLayoutState.csRatio = parseFloat(data.csRatio) || 2;
        if (data.marginX !== undefined && data.marginX !== null && !isNaN(parseInt(data.marginX, 10))) brmLayoutState.marginX = parseInt(data.marginX, 10);
        if (data.marginY !== undefined && data.marginY !== null && !isNaN(parseInt(data.marginY, 10))) brmLayoutState.marginY = parseInt(data.marginY, 10);
        if (data.gapX !== undefined && data.gapX !== null && !isNaN(parseInt(data.gapX, 10))) brmLayoutState.gapX = parseInt(data.gapX, 10);
        if (data.gapY !== undefined && data.gapY !== null && !isNaN(parseInt(data.gapY, 10))) brmLayoutState.gapY = parseInt(data.gapY, 10);
        if (data.leaderLen !== undefined && !isNaN(parseInt(data.leaderLen, 10))) brmLayoutState.leaderLen = parseInt(data.leaderLen, 10);
        if (data.leaderDist !== undefined && !isNaN(parseInt(data.leaderDist, 10))) brmLayoutState.leaderDist = parseInt(data.leaderDist, 10);
        if (data.dimSpace1 !== undefined && !isNaN(parseInt(data.dimSpace1, 10))) brmLayoutState.dimSpace1 = parseInt(data.dimSpace1, 10);
        if (data.dimSpace2 !== undefined && !isNaN(parseInt(data.dimSpace2, 10))) brmLayoutState.dimSpace2 = parseInt(data.dimSpace2, 10);
        if (data.dimScale !== undefined && !isNaN(parseFloat(data.dimScale))) brmLayoutState.dimScale = parseFloat(data.dimScale);
        brmLayoutState._userChanged = true;
      }
    }
  } catch (err) {
    console.warn('Lỗi đọc brmLayoutState từ localStorage:', err);
  }
  const sc = parseInt(brmLayoutState.scale, 10) || 50;
  brmLayoutState.scale = sc;
  brmLayoutState.sheetW = 420 * sc;
  brmLayoutState.sheetH = 297 * sc;
  if (brmLayoutState.csRatio === undefined) brmLayoutState.csRatio = 2;
  if (brmLayoutState.marginX === undefined) brmLayoutState.marginX = 500;
  if (brmLayoutState.marginY === undefined) brmLayoutState.marginY = 400;
  if (brmLayoutState.gapX === undefined) brmLayoutState.gapX = -100;
  if (brmLayoutState.gapY === undefined) brmLayoutState.gapY = -100;
  if (brmLayoutState.leaderLen === undefined) brmLayoutState.leaderLen = 160;
  if (brmLayoutState.leaderDist === undefined) brmLayoutState.leaderDist = 60;
  if (brmLayoutState.dimSpace1 === undefined) brmLayoutState.dimSpace1 = 350;
  if (brmLayoutState.dimSpace2 === undefined) brmLayoutState.dimSpace2 = 260;
  if (brmLayoutState.dimScale === undefined) brmLayoutState.dimScale = 1.0;
}
loadBrmLayoutState(); // Tự động load ngay khi khởi tạo script

function saveBrmLayoutState() {
  try {
    localStorage.setItem('brmLayoutState', JSON.stringify({
      scale: brmLayoutState.scale,
      csRatio: brmLayoutState.csRatio,
      marginX: brmLayoutState.marginX,
      marginY: brmLayoutState.marginY,
      gapX: brmLayoutState.gapX,
      gapY: brmLayoutState.gapY,
      leaderLen: brmLayoutState.leaderLen,
      leaderDist: brmLayoutState.leaderDist,
      dimSpace1: brmLayoutState.dimSpace1,
      dimSpace2: brmLayoutState.dimSpace2,
      dimScale: brmLayoutState.dimScale
    }));
  } catch (err) {
    console.warn('Lỗi ghi brmLayoutState vào localStorage:', err);
  }
}

function updateBrmLayoutSheetControls() {
  const selScale = document.getElementById('brmSelScale');
  const selCsZoom = document.getElementById('brmSelCsZoom');
  const inMx = document.getElementById('brmInputMarginX');
  const inMy = document.getElementById('brmInputMarginY');
  const inGx = document.getElementById('brmInputGapX');
  const inGy = document.getElementById('brmInputGapY');
  const inLdLen = document.getElementById('brmInputLeaderLen');
  const inLdDist = document.getElementById('brmInputLeaderDist');
  const inDs1 = document.getElementById('brmInputDimSpace1');
  const inDs2 = document.getElementById('brmInputDimSpace2');
  const selDs = document.getElementById('brmSelDimScale');

  if (selScale) selScale.value = String(brmLayoutState.scale || 50);
  if (selCsZoom) selCsZoom.value = String(brmLayoutState.csRatio !== undefined ? brmLayoutState.csRatio : 2);
  if (inMx) inMx.value = (brmLayoutState.marginX !== undefined) ? brmLayoutState.marginX : 500;
  if (inMy) inMy.value = (brmLayoutState.marginY !== undefined) ? brmLayoutState.marginY : 400;
  if (inGx) inGx.value = (brmLayoutState.gapX !== undefined) ? brmLayoutState.gapX : -100;
  if (inGy) inGy.value = (brmLayoutState.gapY !== undefined) ? brmLayoutState.gapY : -100;
  if (inLdLen) inLdLen.value = (brmLayoutState.leaderLen !== undefined) ? brmLayoutState.leaderLen : 160;
  if (inLdDist) inLdDist.value = (brmLayoutState.leaderDist !== undefined) ? brmLayoutState.leaderDist : 60;
  if (inDs1) inDs1.value = (brmLayoutState.dimSpace1 !== undefined) ? brmLayoutState.dimSpace1 : 350;
  if (inDs2) inDs2.value = (brmLayoutState.dimSpace2 !== undefined) ? brmLayoutState.dimSpace2 : 260;
  if (selDs) selDs.value = String(brmLayoutState.dimScale !== undefined ? brmLayoutState.dimScale : 1.0);
}

function initBrmLayoutSheetControls() {
  loadBrmLayoutState();
  updateBrmLayoutSheetControls();

  const selScale = document.getElementById('brmSelScale');
  const selCsZoom = document.getElementById('brmSelCsZoom');
  const inMx = document.getElementById('brmInputMarginX');
  const inMy = document.getElementById('brmInputMarginY');
  const inGx = document.getElementById('brmInputGapX');
  const inGy = document.getElementById('brmInputGapY');
  const inLdLen = document.getElementById('brmInputLeaderLen');
  const inLdDist = document.getElementById('brmInputLeaderDist');
  const inDs1 = document.getElementById('brmInputDimSpace1');
  const inDs2 = document.getElementById('brmInputDimSpace2');
  const selDs = document.getElementById('brmSelDimScale');

  if (selScale && !selScale._hasListener) {
    selScale._hasListener = true;
    ['change', 'input'].forEach(evt => {
      selScale.addEventListener(evt, (e) => {
        const sc = parseInt(e.target.value, 10) || 50;
        brmLayoutState.scale = sc;
        brmLayoutState.sheetW = 420 * sc;
        brmLayoutState.sheetH = 297 * sc;
        brmLayoutState._userChanged = true;
        saveBrmLayoutState();
        renderBeamDrawings();
      });
    });
  }

  if (selCsZoom && !selCsZoom._hasListener) {
    selCsZoom._hasListener = true;
    ['change', 'input'].forEach(evt => {
      selCsZoom.addEventListener(evt, (e) => {
        const val = parseFloat(e.target.value) || 2.0;
        brmLayoutState.csRatio = val;
        brmLayoutState._userChanged = true;
        saveBrmLayoutState();
        renderBeamDrawings();
      });
    });
  }

  if (inMx && !inMx._hasListener) {
    inMx._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inMx.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.marginX = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inMy && !inMy._hasListener) {
    inMy._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inMy.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.marginY = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inGx && !inGx._hasListener) {
    inGx._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inGx.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.gapX = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inGy && !inGy._hasListener) {
    inGy._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inGy.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.gapY = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inLdLen && !inLdLen._hasListener) {
    inLdLen._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inLdLen.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.leaderLen = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inLdDist && !inLdDist._hasListener) {
    inLdDist._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inLdDist.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.leaderDist = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inDs1 && !inDs1._hasListener) {
    inDs1._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inDs1.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.dimSpace1 = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (inDs2 && !inDs2._hasListener) {
    inDs2._hasListener = true;
    ['input', 'change'].forEach(evt => {
      inDs2.addEventListener(evt, (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
          brmLayoutState.dimSpace2 = val;
          brmLayoutState._userChanged = true;
          saveBrmLayoutState();
          renderBeamDrawings();
        }
      });
    });
  }

  if (selDs && !selDs._hasListener) {
    selDs._hasListener = true;
    ['change', 'input'].forEach(evt => {
      selDs.addEventListener(evt, (e) => {
        const val = parseFloat(e.target.value) || 1.0;
        brmLayoutState.dimScale = val;
        brmLayoutState._userChanged = true;
        saveBrmLayoutState();
        renderBeamDrawings();
      });
    });
  }
}
let chainInteractiveBoxes = [];

function setBeamDrawingMode(mode) {
  const view3D = document.getElementById('brm3DViewContainer');
  // Bỏ hoàn toàn 3D cho dầm dài nếu không có container 3D
  if (mode === '3d' && !view3D) mode = 'chain';
  beamDrawingMode = (mode === '3d' && view3D) ? '3d' : 'chain';
  const btnChain = document.getElementById('btnBrmModeChain');
  const btn3D = document.getElementById('btnBrmMode3D');
  const legend = document.getElementById('brmCanvasLegend');
  const cadCanvas = document.getElementById('brmDrawingCanvas');
  const cadLegend = document.getElementById('brmCadLegendBadge');
  const cadHud = document.getElementById('brmCadHudControls');

  [btnChain, btn3D].forEach(btn => {
    if (!btn) return;
    btn.className = 'px-3 py-1 rounded-xl font-semibold text-slate-600 hover:text-slate-900 transition flex items-center gap-1 cursor-pointer';
  });

  const layoutBar = document.getElementById('brmLayoutSheetBar');
  if (beamDrawingMode === '3d' && view3D) {
    if (btn3D) btn3D.className = 'px-3 py-1 rounded-xl font-bold bg-white text-indigo-700 shadow-sm transition flex items-center gap-1 cursor-default';
    if (cadCanvas) cadCanvas.style.display = 'none';
    if (cadLegend) cadLegend.classList.add('hidden');
    if (cadHud) cadHud.classList.add('hidden');
    if (layoutBar) layoutBar.classList.add('hidden');
    view3D.classList.remove('hidden');
    renderBeam3DRebar();
  } else {
    if (view3D) view3D.classList.add('hidden');
    if (cadCanvas) cadCanvas.style.display = 'block';
    if (cadLegend) cadLegend.classList.add('hidden');
    if (cadHud) cadHud.classList.remove('hidden');
    if (layoutBar) layoutBar.classList.remove('hidden');
    if (btnChain) btnChain.className = 'px-3 py-1 rounded-xl font-bold bg-white text-indigo-700 shadow-sm transition flex items-center gap-1 cursor-default';
    initBrmLayoutSheetControls();
    updateBrmLayoutSheetControls();
    renderBeamDrawings();
  }
}

function parseRebarSpec(rebarStr, defaultCount = 2, defaultDiam = 16) {
  if (!rebarStr) return { count: defaultCount, diam: defaultDiam, extraCount: 0, extraDiam: defaultDiam, label: `${defaultCount}Φ${defaultDiam}` };
  
  const matches = [...rebarStr.matchAll(/(\d+)\s*[dDΦØøϕ]\s*(\d+)/gi)];
  if (matches.length > 0) {
    let totalCount = 0;
    let mainDiam = parseInt(matches[0][2], 10);
    let extraCount = 0;
    let extraDiam = mainDiam;
    
    matches.forEach((m, idx) => {
      const c = parseInt(m[1], 10);
      const d = parseInt(m[2], 10);
      totalCount += c;
      if (idx === 0) {
        mainDiam = d;
      } else {
        extraCount += c;
        extraDiam = d;
      }
    });

    const labelStr = (matches.length > 1) 
      ? matches.map(m => `${m[1]}Φ${m[2]}`).join('+')
      : `${totalCount}Φ${mainDiam}`;

    return { 
      count: totalCount, 
      diam: mainDiam, 
      extraCount,
      extraDiam,
      label: labelStr 
    };
  }
  return { count: defaultCount, diam: defaultDiam, extraCount: 0, extraDiam: defaultDiam, label: `${defaultCount}Φ${defaultDiam}` };
}

function parseStirrupSpec(stirrupStr) {
  const defaultD = (typeof window !== 'undefined' && window.currentStirrupDiam) ? window.currentStirrupDiam : 6;
  if (!stirrupStr) return { diam: defaultD, label: `Φ${defaultD}a100/a200`, zoneDense: 'a100', zoneMid: 'a200', shortDense: `Ø${defaultD}a100`, shortMid: `Ø${defaultD}a200` };
  let diam = defaultD;
  const dm = stirrupStr.match(/[dDΦØøϕ]?\s*(\d+)\s*a/i);
  if (dm) diam = parseInt(dm[1], 10);

  let dense = 'a100';
  let mid = 'a200';
  const m = stirrupStr.match(/a(\d+)(?:\/a?(\d+))?/i);
  if (m) {
    dense = 'a' + m[1];
    mid = m[2] ? 'a' + m[2] : 'a200';
  }
  return {
    diam,
    label: `Φ${diam}${dense}/${mid}`,
    zoneDense: dense,
    zoneMid: mid,
    shortDense: `Ø${diam}${dense}`,
    shortMid: `Ø${diam}${mid}`
  };
}

// Kiểm tra xem tại vị trí tọa độ (x, y) có cột thực sự trong mô hình hay không
function hasColumnAt(story, x, y, tol = 450) {
  if (!etabsData || !etabsData.columns) return false;
  for (const c of etabsData.columns) {
    const cx = (c.p1 && c.p1[0] !== undefined) ? c.p1[0] : (c.x || 0);
    const cy = (c.p1 && c.p1[1] !== undefined) ? c.p1[1] : (c.y || 0);
    const dist = Math.hypot(cx - x, cy - y);
    if (dist <= tol) return true;
  }
  return false;
}

// Kiểm tra gối thứ supportIndex trong tuyến dầm chain có cột hay không
function checkColumnAtSupport(chain, supportIndex, isX) {
  if (!chain || chain.length === 0) return true;
  const numSpans = chain.length;
  let b, xJ, yJ;
  if (supportIndex < numSpans) {
    b = chain[supportIndex];
    if (isX) {
      xJ = Math.min(b.p1[0], b.p2[0]);
      yJ = (b.p1[1] + b.p2[1]) / 2;
    } else {
      xJ = (b.p1[0] + b.p2[0]) / 2;
      yJ = Math.min(b.p1[1], b.p2[1]);
    }
  } else {
    b = chain[numSpans - 1];
    if (isX) {
      xJ = Math.max(b.p1[0], b.p2[0]);
      yJ = (b.p1[1] + b.p2[1]) / 2;
    } else {
      xJ = (b.p1[0] + b.p2[0]) / 2;
      yJ = Math.max(b.p1[1], b.p2[1]);
    }
  }
  return hasColumnAt(b.story, xJ, yJ, 450);
}

// Gom nhóm toàn bộ danh sách dầm thành các Dầm Dài Liên Tục (Long Beams)
function getLongBeamsList() {
  if (!etabsData || !etabsData.beams) return [];
  const groups = new Map();
  etabsData.beams.forEach(b => {
    const story = b.story || 'T1';
    const longId = b.longBeamId || b.label;
    const key = `${story}::${longId}`;
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        story,
        longBeamId: longId,
        beams: [],
        axisName: b.axisName || '',
        direction: b.direction || 'X'
      });
    }
    const g = groups.get(key);
    g.beams.push(b);
    if (!g.axisName && b.axisName) g.axisName = b.axisName;
  });

  const list = Array.from(groups.values()).map(g => {
    g.beams.sort((a, b) => {
      if ((a.spanIndex || 0) !== (b.spanIndex || 0)) {
        return (a.spanIndex || 0) - (b.spanIndex || 0);
      }
      return (a.p1[0] + a.p1[1]) - (b.p1[0] + b.p1[1]);
    });
    let totalLen = 0;
    g.beams.forEach(b => totalLen += (b.length || 0));
    let commonSection = g.beams[0]?.section || `${g.beams[0]?.width || 200}x${g.beams[0]?.depth || 400}`;
    if (commonSection.startsWith('B ')) commonSection = commonSection.substring(2);
    return {
      key: g.key,
      story: g.story,
      longBeamId: g.longBeamId,
      numSpans: g.beams.length,
      totalLength: totalLen,
      commonSection,
      axisName: g.axisName,
      direction: g.direction,
      firstBeam: g.beams[0],
      beams: g.beams
    };
  });

  list.sort((a, b) => {
    if (a.story !== b.story) return (a.story || '').localeCompare(b.story || '');
    const isDX_A = a.longBeamId.startsWith('DX');
    const isDX_B = b.longBeamId.startsWith('DX');
    if (isDX_A && !isDX_B) return -1;
    if (!isDX_A && isDX_B) return 1;
    return a.longBeamId.localeCompare(b.longBeamId, undefined, { numeric: true });
  });

  return list;
}

// ==============================================================================
// CONTINUOUS BEAM REBAR UNIFICATION & SAFETY CHECKS (TOÀN BỘ DẦM DÀI)
// ==============================================================================

function formatStoryLabel(story) {
  if (!story) return '';
  const s = String(story).trim();
  if (s.toUpperCase() === 'DK' || s.toUpperCase() === 'DA KIENG' || s.toUpperCase() === 'ĐÀ KIỀNG') {
    return 'ĐÀ KIỀNG';
  }
  const m = s.match(/^T(\d+)$/i);
  if (m) return `TẦNG ${m[1]}`;
  const mStory = s.match(/^STORY(\d+)$/i);
  if (mStory) return `TẦNG ${mStory[1]}`;
  if (s.toUpperCase().startsWith('TẦNG')) return s.toUpperCase();
  return `TẦNG ${s}`;
}

function getRebarArea(rebarStr) {
  if (!rebarStr) return 0;
  const am = rebarStr.match(/\(([\d\.]+)\s*cm[²2]?\)/i);
  if (am) return parseFloat(am[1]);

  const matches = [...rebarStr.matchAll(/(\d+)\s*[dDΦØøϕ]\s*(\d+)/gi)];
  if (matches.length > 0) {
    let a = 0;
    matches.forEach(m => {
      const count = parseInt(m[1], 10);
      const diam = parseInt(m[2], 10);
      a += count * Math.PI * Math.pow(diam / 10, 2) / 4;
    });
    return Math.round(a * 100) / 100;
  }
  return 0;
}

function parseMaxDiameter(rebarStr) {
  if (!rebarStr) return 0;
  const matches = [...rebarStr.matchAll(/(\d+)\s*[dDΦØøϕ]\s*(\d+)/gi)];
  if (matches.length === 0) return 0;
  return Math.max(...matches.map(m => parseInt(m[2], 10)));
}

function selectOptimalRebarForChain(catalog, maxAsReq, minBars = 2, minDiam = 16) {
  const validBars = catalog.filter(item => {
    const parsed = parseRebarSpec(item.label);
    return parsed.count >= minBars;
  });
  const list = validBars.length > 0 ? validBars : catalog;

  // 1. Ưu tiên tìm loại thép có đường kính >= minDiam (ví dụ D18 cho toàn dầm) VÀ As >= maxAsReq
  const candWithDiam = list.filter(item => {
    const parsed = parseRebarSpec(item.label);
    const d = Math.max(parsed.diam, parsed.extraDiam || 0);
    return d >= minDiam && item.area >= maxAsReq;
  });
  if (candWithDiam.length > 0) {
    candWithDiam.sort((a, b) => a.area - b.area);
    return candWithDiam[0];
  }

  // 2. Nếu không có loại thép nào vừa đủ minDiam vừa đủ As, tìm loại thép thỏa mãn As >= maxAsReq
  const candSafe = list.filter(item => item.area >= maxAsReq);
  if (candSafe.length > 0) {
    candSafe.sort((a, b) => a.area - b.area);
    return candSafe[0];
  }

  // 3. Fallback: Chọn loại thép có diện tích lớn nhất trong catalog
  const sorted = [...list].sort((a, b) => b.area - a.area);
  return sorted[0];
}

function selectOptimalHangerForChain(maxB, minDiam = 16) {
  const minBars = (maxB >= 300) ? 3 : 2;
  const diam = Math.max(16, minDiam);
  if (minBars >= 3) {
    if (diam >= 20) return '3D20 (9.42cm²)';
    if (diam >= 18) return '3D18 (7.63cm²)';
    return '3D16 (6.03cm²)';
  } else {
    if (diam >= 20) return '2D20 (6.28cm²)';
    if (diam >= 18) return '2D18 (5.09cm²)';
    return '2D16 (4.02cm²)';
  }
}

function selectMandatoryExtraRebar(deficit, isSpanShort = false) {
  if (isSpanShort) return { label: '0 (Không TC)', area: 0 };
  // BẮT BUỘC CẤU TẠO: Tối thiểu 2 thanh thép tăng cường đặt về 2 mép dầm (2D14 = 3.08 cm² hoặc 2D16 = 4.02 cm²)
  const minArea = 3.08;
  const targetArea = Math.max(minArea, deficit || 0);
  const candidates = EXTRA_REBAR_CATALOG.filter(x => x.count >= 2 && x.area >= targetArea);
  if (candidates.length > 0) {
    candidates.sort((a, b) => a.area - b.area);
    return candidates[0];
  }
  return EXTRA_REBAR_CATALOG[EXTRA_REBAR_CATALOG.length - 1];
}

function syncContinuousBeamsRebarDefaults() {
  if (!etabsData || !etabsData.beams) return;
  const longBeams = getLongBeamsList();

  longBeams.forEach(lb => {
    const chain = lb.beams;
    if (!chain || chain.length === 0) return;

    const userModified = chain.some(b => b._rebarUserModified);
    if (userModified) return;

    // 1. Tìm đường kính lớn nhất trong dầm
    const allDiams = [];
    chain.forEach(b => {
      [b.rebar_top_left, b.rebar_bot_mid, b.rebar_top_right, b.rebar_hanger].forEach(str => {
        const d = parseMaxDiameter(str);
        if (d > 0) allDiams.push(d);
      });
    });
    const maxChainDiam = allDiams.length > 0 ? Math.max(...allDiams) : 16;

    // 2. Tìm giá trị As yêu cầu lớn nhất của tất cả các đoạn dầm cho từng vị trí
    const maxAsTopL = Math.max(...chain.map(b => b.as_top_left_cm2 || 0));
    const maxAsBotMid = Math.max(...chain.map(b => b.as_bot_mid_cm2 || 0));
    const maxAsTopR = Math.max(...chain.map(b => b.as_top_right_cm2 || 0));
    const maxAsTopOverall = Math.max(maxAsTopL, maxAsTopR);

    // 3. Bề rộng lớn nhất trong dầm
    const maxB = Math.max(...chain.map(b => b.width || 200));
    const minBars = (maxB >= 300) ? 3 : 2;

    // 4. BẮT BUỘC CẤU TẠO PHẢI CÓ TĂNG CƯỜNG LƯNG VÀ BỤNG:
    // Thép tăng cường 2 thanh có thể gánh từ 2D14 (3.08 cm²) đến 2D25 (9.82 cm²).
    // Thép chủ suốt chỉ cần chọn vừa đủ để làm khung chịu lực cơ bản:
    // - Dầm b < 300: Thép chủ cơ bản là 2D16 (4.02 cm²) hoặc 2D18 (5.09 cm²).
    // - Dầm b >= 300: Thép chủ cơ bản là 3D16 (6.03 cm²) hoặc 3D18 (7.63 cm²).
    // Nếu moment đỉnh quá lớn vượt quá khả năng bù của thép tăng cường 2D25 (9.82 cm²),
    // lúc đó mới tính tăng cấp thép chủ:
    const baseTopArea = (minBars >= 3) ? 7.63 : 5.09;
    const reqMainTopArea = Math.max(baseTopArea, maxAsTopOverall - 9.82);
    let optMainTop = MAIN_REBAR_CATALOG.filter(x => x.count >= minBars && x.area >= reqMainTopArea);
    optMainTop.sort((a, b) => a.area - b.area);
    const chosenMainTop = (optMainTop.length > 0) ? optMainTop[0] : (minBars >= 3 ? { label: '3D18', area: 7.63 } : { label: '2D18', area: 5.09 });

    const baseBotArea = (minBars >= 3) ? 7.63 : 5.09;
    const reqMainBotArea = Math.max(baseBotArea, maxAsBotMid - 9.82);
    let optMainBot = MAIN_REBAR_CATALOG.filter(x => x.count >= minBars && x.area >= reqMainBotArea);
    optMainBot.sort((a, b) => a.area - b.area);
    const chosenMainBot = (optMainBot.length > 0) ? optMainBot[0] : (minBars >= 3 ? { label: '3D18', area: 7.63 } : { label: '2D18', area: 5.09 });

    const hangerStr = selectOptimalHangerForChain(maxB, maxChainDiam);
    const stirrupVal = 'd6a100/a200';

    // 5. Gán Thép Chủ suốt và Thép Tăng Cường cho từng đoạn dầm trong chuỗi liên tục
    chain.forEach(b => {
      const isShort = (b.length < 2000);
      const reqL = b.as_top_left_cm2 || 0;
      const reqM = b.as_bot_mid_cm2 || 0;
      const reqR = b.as_top_right_cm2 || 0;

      // Thép tăng cường lưng (Gối T, Gối P): BẮT BUỘC PHẢI CÓ (tối thiểu 2D14 = 3.08 cm²)
      const spanExtraL = selectMandatoryExtraRebar(reqL - chosenMainTop.area, false);
      const spanExtraR = selectMandatoryExtraRebar(reqR - chosenMainTop.area, false);
      // Thép tăng cường bụng: BẮT BUỘC PHẢI CÓ cho nhịp >= 2000 (tối thiểu 2D14 = 3.08 cm²)
      const spanExtraM = selectMandatoryExtraRebar(reqM - chosenMainBot.area, isShort);

      const totL = chosenMainTop.area + spanExtraL.area;
      const totM = chosenMainBot.area + spanExtraM.area;
      const totR = chosenMainTop.area + spanExtraR.area;

      b.rebar_main_top = `${chosenMainTop.label} (${chosenMainTop.area.toFixed(2)}cm²)`;
      b.rebar_main_bot = `${chosenMainBot.label} (${chosenMainBot.area.toFixed(2)}cm²)`;
      b.extra_top_left = spanExtraL.label;
      b.extra_bot_mid = spanExtraM.label;
      b.extra_top_right = spanExtraR.label;
      b.rebar_top_left = (spanExtraL.area > 0) ? `${chosenMainTop.label}+${spanExtraL.label} (${totL.toFixed(2)}cm²)` : `${chosenMainTop.label} (${totL.toFixed(2)}cm²)`;
      b.rebar_bot_mid = (spanExtraM.area > 0) ? `${chosenMainBot.label}+${spanExtraM.label} (${totM.toFixed(2)}cm²)` : `${chosenMainBot.label} (${totM.toFixed(2)}cm²)`;
      b.rebar_top_right = (spanExtraR.area > 0) ? `${chosenMainTop.label}+${spanExtraR.label} (${totR.toFixed(2)}cm²)` : `${chosenMainTop.label} (${totR.toFixed(2)}cm²)`;
      b.rebar_hanger = hangerStr;
      b.stirrup = stirrupVal;
    });
  });

  console.log(`[ETABS Hub] Synchronized unified rebar design (Mandatory TC Lưng & Bụng) for ${longBeams.length} continuous long beams.`);
}

function evaluateChainSafety(chain) {
  if (!chain || chain.length === 0) return { isSafe: true, reason: 'Toàn bộ dầm đạt chuẩn TCVN', shortReason: 'Toàn dầm Đạt', worstSpan: null };

  let worstLack = 0;
  let failureInfo = null;

  for (let i = 0; i < chain.length; i++) {
    const span = chain[i];
    const spanIdx = span.spanIndex || (i + 1);

    // Gối Trái (Top Left)
    const reqL = span.as_top_left_cm2 || 0;
    let aL = getRebarArea(span.rebar_top_left);
    if (span.rebar_main_top) {
      const aMain = getRebarArea(span.rebar_main_top);
      const aExtra = (span.extra_top_left && !span.extra_top_left.startsWith('0')) ? getRebarArea(span.extra_top_left) : 0;
      aL = Math.max(aL, aMain + aExtra);
    }
    if (reqL > 0 && aL < reqL) {
      const lack = Math.round(((reqL - aL) / reqL) * 100);
      if (lack > worstLack) {
        worstLack = lack;
        failureInfo = {
          isSafe: false,
          reason: `Nhịp ${spanIdx} (${span.label}) gối trái thiếu ${lack}% (chọn ${aL.toFixed(2)} / y/c ${reqL.toFixed(2)} cm²)`,
          shortReason: `Nhịp ${spanIdx} thiếu ${lack}%`,
          worstSpan: span,
          worstPosition: 'top_left',
          lack
        };
      }
    }

    // Bụng Nhịp (Bottom Mid)
    const reqM = span.as_bot_mid_cm2 || 0;
    let aM = getRebarArea(span.rebar_bot_mid);
    if (span.rebar_main_bot) {
      const aMain = getRebarArea(span.rebar_main_bot);
      const aExtra = (span.extra_bot_mid && !span.extra_bot_mid.startsWith('0')) ? getRebarArea(span.extra_bot_mid) : 0;
      aM = Math.max(aM, aMain + aExtra);
    }
    if (reqM > 0 && aM < reqM) {
      const lack = Math.round(((reqM - aM) / reqM) * 100);
      if (lack > worstLack) {
        worstLack = lack;
        failureInfo = {
          isSafe: false,
          reason: `Nhịp ${spanIdx} (${span.label}) bụng nhịp thiếu ${lack}% (chọn ${aM.toFixed(2)} / y/c ${reqM.toFixed(2)} cm²)`,
          shortReason: `Nhịp ${spanIdx} thiếu ${lack}%`,
          worstSpan: span,
          worstPosition: 'bot_mid',
          lack
        };
      }
    }

    // Gối Phải (Top Right)
    const reqR = span.as_top_right_cm2 || 0;
    let aR = getRebarArea(span.rebar_top_right);
    if (span.rebar_main_top) {
      const aMain = getRebarArea(span.rebar_main_top);
      const aExtra = (span.extra_top_right && !span.extra_top_right.startsWith('0')) ? getRebarArea(span.extra_top_right) : 0;
      aR = Math.max(aR, aMain + aExtra);
    }
    if (reqR > 0 && aR < reqR) {
      const lack = Math.round(((reqR - aR) / reqR) * 100);
      if (lack > worstLack) {
        worstLack = lack;
        failureInfo = {
          isSafe: false,
          reason: `Nhịp ${spanIdx} (${span.label}) gối phải thiếu ${lack}% (chọn ${aR.toFixed(2)} / y/c ${reqR.toFixed(2)} cm²)`,
          shortReason: `Nhịp ${spanIdx} thiếu ${lack}%`,
          worstSpan: span,
          worstPosition: 'top_right',
          lack
        };
      }
    }
  }

  if (failureInfo) return failureInfo;
  return { isSafe: true, reason: 'Toàn bộ dầm đạt chuẩn TCVN', shortReason: 'Toàn dầm Đạt', worstSpan: null };
}

function jumpToSpanAndHighlight(targetSpan, pos) {
  if (!targetSpan) return;
  const fullTarget = (etabsData && etabsData.beams) 
    ? (etabsData.beams.find(x => x.label === targetSpan.label && x.story === targetSpan.story) || targetSpan)
    : targetSpan;

  openBeamRebarModal(fullTarget);
  setTimeout(() => {
    if (typeof focusActiveSpanCad === 'function') focusActiveSpanCad();
    highlightFailingPropField(pos);
    showToastNotification(`📍 Đã chuyển tới Nhịp ${targetSpan.spanIndex || targetSpan.label} để kiểm tra vị trí chưa đạt!`, 'warning');
  }, 100);
}
window.jumpToSpanAndHighlight = jumpToSpanAndHighlight;

function updateMainRebarStatusBadges(chain) {
  if (!chain || chain.length === 0) return;

  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const badgeMainTop = document.getElementById('brmStatusMainTop');
  const badgeMainBot = document.getElementById('brmStatusMainBot');

  if (selMainTop && badgeMainTop) {
    const opt = selMainTop.options[selMainTop.selectedIndex];
    const area = opt ? (parseFloat(opt.dataset.area) || getRebarArea(opt.value)) : 5.09;
    let maxReqTop = 0;
    chain.forEach(span => {
      const reqL = span.as_top_left_cm2 || 0;
      const reqR = span.as_top_right_cm2 || 0;
      if (reqL > maxReqTop) maxReqTop = reqL;
      if (reqR > maxReqTop) maxReqTop = reqR;
    });

    if (maxReqTop <= 0.8) {
      badgeMainTop.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
      badgeMainTop.innerHTML = '🟢 Đạt (Cấu tạo)';
      badgeMainTop.title = `Thép chủ trên (${area.toFixed(2)} cm²) đạt yêu cầu cấu tạo TCVN (y/c: ${(maxReqTop || 0.8).toFixed(2)} cm²)`;
    } else if (area >= maxReqTop) {
      const ratio = Math.round((area / maxReqTop) * 100);
      const k = (area / maxReqTop).toFixed(1);
      badgeMainTop.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
      badgeMainTop.innerHTML = (ratio > 200) ? `🟢 Đạt (K=${k})` : `🟢 Đạt ${ratio}%`;
      badgeMainTop.title = `Thép chủ trên (${area.toFixed(2)} cm²) tự gánh đủ 100% moment âm lớn nhất trên toàn dầm (Max y/c: ${maxReqTop.toFixed(2)} cm²)`;
    } else {
      const ratio = Math.round((area / maxReqTop) * 100);
      badgeMainTop.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-blue-100 text-blue-800 border border-blue-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
      badgeMainTop.innerHTML = `🔵 Gánh ${ratio}% (Cần TC gối)`;
      badgeMainTop.title = `Thép chủ trên (${area.toFixed(2)} cm²) gánh ${ratio}% moment âm lớn nhất (${maxReqTop.toFixed(2)} cm²). Phần thiếu do thép tăng cường gối gánh thêm.`;
    }
  }

  if (selMainBot && badgeMainBot) {
    const opt = selMainBot.options[selMainBot.selectedIndex];
    const area = opt ? (parseFloat(opt.dataset.area) || getRebarArea(opt.value)) : 5.09;
    let maxReqBot = 0;
    chain.forEach(span => {
      const reqM = span.as_bot_mid_cm2 || 0;
      if (reqM > maxReqBot) maxReqBot = reqM;
    });

    if (maxReqBot <= 0.8) {
      badgeMainBot.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
      badgeMainBot.innerHTML = '🟢 Đạt (Cấu tạo)';
      badgeMainBot.title = `Thép chủ dưới (${area.toFixed(2)} cm²) đạt yêu cầu cấu tạo TCVN (y/c: ${(maxReqBot || 0.8).toFixed(2)} cm²)`;
    } else if (area >= maxReqBot) {
      const ratio = Math.round((area / maxReqBot) * 100);
      const k = (area / maxReqBot).toFixed(1);
      badgeMainBot.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
      badgeMainBot.innerHTML = (ratio > 200) ? `🟢 Đạt (K=${k})` : `🟢 Đạt ${ratio}%`;
      badgeMainBot.title = `Thép chủ dưới (${area.toFixed(2)} cm²) tự gánh đủ 100% moment dương lớn nhất trên toàn dầm (Max y/c: ${maxReqBot.toFixed(2)} cm²)`;
    } else {
      const ratio = Math.round((area / maxReqBot) * 100);
      badgeMainBot.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-blue-100 text-blue-800 border border-blue-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
      badgeMainBot.innerHTML = `🔵 Gánh ${ratio}% (Cần TC bụng)`;
      badgeMainBot.title = `Thép chủ dưới (${area.toFixed(2)} cm²) gánh ${ratio}% moment dương lớn nhất (${maxReqBot.toFixed(2)} cm²). Phần thiếu do thép tăng cường bụng gánh thêm.`;
    }
  }
}

function updateContinuousRebarRatio(selectId, posKey, statusBadgeId, chain) {
  const sel = document.getElementById(selectId);
  const badge = document.getElementById(statusBadgeId);
  if (!sel || !badge) return;

  const chosenOpt = sel.options[sel.selectedIndex];
  const chosenExtraArea = chosenOpt ? (parseFloat(chosenOpt.dataset.area) || getRebarArea(chosenOpt.value)) : 0;

  // Lấy diện tích Thép Chủ Trên hoặc Thép Chủ Dưới (chạy suốt dầm)
  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const optMainTop = selMainTop && selMainTop.selectedIndex >= 0 ? selMainTop.options[selMainTop.selectedIndex] : null;
  const optMainBot = selMainBot && selMainBot.selectedIndex >= 0 ? selMainBot.options[selMainBot.selectedIndex] : null;

  const mainTopArea = optMainTop ? (parseFloat(optMainTop.dataset.area) || getRebarArea(optMainTop.value)) : 5.09;
  const mainBotArea = optMainBot ? (parseFloat(optMainBot.dataset.area) || getRebarArea(optMainBot.value)) : 5.09;

  let chosenArea = chosenExtraArea;
  if (posKey === 'top_left' || posKey === 'top_right') {
    chosenArea = mainTopArea + chosenExtraArea;
  } else if (posKey === 'bot_mid') {
    chosenArea = mainBotArea + chosenExtraArea;
  }

  // Cập nhật nhãn trạng thái của Thép Chủ
  updateMainRebarStatusBadges(chain);

  if (!chain || chain.length === 0) {
    badge.innerHTML = '🟢 Đạt';
    badge.onclick = null;
    return;
  }

  let allPass = true;
  let worstSpan = null;
  let maxReq = 0;
  let worstLack = 0;

  chain.forEach((span, idx) => {
    let req = 0;
    if (posKey === 'top_left') req = span.as_top_left_cm2 || 0;
    else if (posKey === 'bot_mid') req = span.as_bot_mid_cm2 || 0;
    else if (posKey === 'top_right') req = span.as_top_right_cm2 || 0;

    if (req > maxReq) maxReq = req;

    if (req > 0 && chosenArea < req) {
      allPass = false;
      const spanLack = Math.round(((req - chosenArea) / req) * 100);
      if (spanLack > worstLack) {
        worstLack = spanLack;
        worstSpan = { span, idx: span.spanIndex || (idx + 1), req, lack: spanLack };
      }
    }
  });

  if (allPass) {
    const k = (maxReq > 0) ? (chosenArea / maxReq).toFixed(1) : '2.0';
    const ratio = (maxReq > 0) ? Math.round((chosenArea / maxReq) * 100) : 200;
    badge.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-default';
    if (maxReq <= 0.8) {
      badge.innerHTML = '🟢 Toàn dầm Đạt (Cấu tạo)';
    } else if (ratio > 200) {
      badge.innerHTML = `🟢 Toàn dầm Đạt (K=${k})`;
    } else {
      badge.innerHTML = `🟢 Toàn dầm Đạt ${ratio}%`;
    }
    badge.title = `Tất cả ${chain.length} nhịp đều đạt! As chọn: ${chosenArea.toFixed(2)} cm² / Max yêu cầu: ${maxReq.toFixed(2)} cm² (Hệ số an toàn K = ${(chosenArea / (maxReq || 0.1)).toFixed(2)})`;
    badge.onclick = null;
  } else {
    badge.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1 whitespace-nowrap shrink-0 cursor-pointer hover:bg-rose-200 hover:ring-2 hover:ring-rose-400 active:scale-95 transition';
    badge.innerHTML = `🔴 Không đạt (Nhịp ${worstSpan.idx} thiếu ${worstSpan.lack}%) <span class="underline text-[9px] font-extrabold ml-0.5">Bấm xem ➔</span>`;
    badge.title = `Không đạt toàn dầm: Nhịp ${worstSpan.idx} (${worstSpan.span.label}) yêu cầu As=${worstSpan.req.toFixed(2)} cm² > chọn ${chosenArea.toFixed(2)} cm² (Thiếu ${worstSpan.lack}%). Bấm để chuyển tới vị trí dầm!`;
    const targetSpan = worstSpan.span;
    badge.onclick = (e) => {
      e.stopPropagation();
      jumpToSpanAndHighlight(targetSpan, posKey);
    };
  }
}

function findContinuousBeamChain(targetBeam) {
  if (!targetBeam || !etabsData || !etabsData.beams) {
    return { chain: [targetBeam], axisName: 'Dầm', targetIndex: 0, isX: true };
  }

  // If longBeamId is assigned, return the unified continuous chain directly
  if (targetBeam.longBeamId) {
    const chain = etabsData.beams
      .filter(b => b.story === targetBeam.story && b.longBeamId === targetBeam.longBeamId)
      .sort((a, b) => (a.spanIndex || 0) - (b.spanIndex || 0));

    if (chain.length > 0) {
      const targetIndex = Math.max(0, chain.findIndex(b => b.label === targetBeam.label));
      const isX = (targetBeam.direction === 'X') || (Math.abs(targetBeam.p2[0] - targetBeam.p1[0]) >= Math.abs(targetBeam.p2[1] - targetBeam.p1[1]));
      const axisName = targetBeam.axisName || (isX ? 'Phương X' : 'Phương Y');
      return { chain, axisName, targetIndex, isX };
    }
  }

  // Fallback: Filter floor beams on same story (horizontal: abs(dz) < 100)
  const storyBeams = etabsData.beams.filter(b => 
    b.story === targetBeam.story && 
    Math.abs(b.p2[2] - b.p1[2]) < 100
  );

  const tdx = targetBeam.p2[0] - targetBeam.p1[0];
  const tdy = targetBeam.p2[1] - targetBeam.p1[1];
  const isX = Math.abs(tdx) >= Math.abs(tdy);

  // Find collinear beams
  const collinear = [];
  storyBeams.forEach(b => {
    const bdx = b.p2[0] - b.p1[0];
    const bdy = b.p2[1] - b.p1[1];
    const bIsX = Math.abs(bdx) >= Math.abs(bdy);
    if (isX !== bIsX) return;

    let pStart, pEnd;
    if (isX) {
      if (Math.abs(b.p1[1] - targetBeam.p1[1]) > 250) return;
      if (b.p1[0] <= b.p2[0]) {
        pStart = b.p1; pEnd = b.p2;
      } else {
        pStart = b.p2; pEnd = b.p1;
      }
    } else {
      if (Math.abs(b.p1[0] - targetBeam.p1[0]) > 250) return;
      if (b.p1[1] <= b.p2[1]) {
        pStart = b.p1; pEnd = b.p2;
      } else {
        pStart = b.p2; pEnd = b.p1;
      }
    }
    collinear.push({ beam: b, pStart, pEnd });
  });

  // Sort along axis
  if (isX) {
    collinear.sort((a, b) => a.pStart[0] - b.pStart[0]);
  } else {
    collinear.sort((a, b) => a.pStart[1] - b.pStart[1]);
  }

  // Group contiguous segments (tolerance gap <= 450mm)
  const coordIdx = isX ? 0 : 1;
  const clusters = [];
  let currentCluster = [];

  collinear.forEach(item => {
    if (currentCluster.length === 0) {
      currentCluster.push(item);
    } else {
      const prev = currentCluster[currentCluster.length - 1];
      const gap = Math.abs(item.pStart[coordIdx] - prev.pEnd[coordIdx]);
      if (gap <= 450) {
        currentCluster.push(item);
      } else {
        clusters.push(currentCluster);
        currentCluster = [item];
      }
    }
  });
  if (currentCluster.length > 0) {
    clusters.push(currentCluster);
  }

  // Find target cluster
  let targetCluster = clusters.find(c => c.some(it => it.beam.label === targetBeam.label && it.beam.story === targetBeam.story));
  if (!targetCluster) {
    targetCluster = [{ beam: targetBeam, pStart: targetBeam.p1, pEnd: targetBeam.p2 }];
  }

  // Axis identification
  let axisName = 'Trục';
  if (isX) {
    const yCoord = targetBeam.p1[1];
    let closestGrid = null, minDist = 999999;
    (etabsData.grids?.Y || []).forEach(g => {
      const d = Math.abs(g.ordinate - yCoord);
      if (d < minDist) { minDist = d; closestGrid = g; }
    });
    if (closestGrid && minDist <= 500) {
      axisName = `Trục ${closestGrid.id}`;
    } else {
      axisName = `Trục Y=${(yCoord/1000).toFixed(1)}m`;
    }
  } else {
    const xCoord = targetBeam.p1[0];
    let closestGrid = null, minDist = 999999;
    (etabsData.grids?.X || []).forEach(g => {
      const d = Math.abs(g.ordinate - xCoord);
      if (d < minDist) { minDist = d; closestGrid = g; }
    });
    if (closestGrid && minDist <= 500) {
      axisName = `Trục ${closestGrid.id}`;
    } else {
      axisName = `Trục X=${(xCoord/1000).toFixed(1)}m`;
    }
  }

  const chain = targetCluster.map(it => it.beam);
  const targetIndex = chain.findIndex(b => b.label === targetBeam.label);

  return { chain, axisName, targetIndex, isX };
}

function getGridBubbleLabel(coord, isXCoord) {
  if (!etabsData || !etabsData.grids) return null;
  const list = isXCoord ? etabsData.grids.X : etabsData.grids.Y;
  if (!list) return null;
  let match = null, minDist = 500;
  list.forEach(g => {
    const d = Math.abs(g.ordinate - coord);
    if (d <= minDist) {
      minDist = d;
      match = g.id;
    }
  });
  return match;
}

function drawCadDimension(ctx, x1, y1, x2, y2, text, offset = 0, isVertical = false, color = null) {
  ctx.save();
  const strokeCol = color || '#64748b';
  const textCol = color || '#334155';
  const dScale = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimScale !== undefined) ? parseFloat(brmLayoutState.dimScale) : 1.0;
  const fontDimSz = Math.max(6, Math.round(9 * dScale * 10) / 10);
  const tickSz = Math.max(2, Math.round(3 * dScale * 10) / 10);

  ctx.strokeStyle = strokeCol;
  ctx.fillStyle = textCol;
  ctx.lineWidth = Math.max(0.8, Math.round(1 * dScale * 10) / 10);
  ctx.font = `bold ${fontDimSz}px monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';

  // Chiều dài chân đường dóng (Witness Line Fit Length) cố định 300mm theo tiêu chuẩn CAD/Revit
  const effScaleCad = (typeof scaleCAD !== 'undefined' ? scaleCAD : 0.08);
  const fitLen = Math.round(300 * effScaleCad * dScale); // 300mm thực tế = 24px trên bản vẽ
  const ext = 4 * dScale;

  if (!isVertical) {
    const y = y1 + offset;
    if (offset !== 0) {
      const startY1 = (Math.abs(offset) > fitLen) ? (y - (offset > 0 ? fitLen : -fitLen)) : y1;
      const startY2 = (Math.abs(offset) > fitLen) ? (y - (offset > 0 ? fitLen : -fitLen)) : y2;
      ctx.beginPath();
      ctx.moveTo(x1, startY1); ctx.lineTo(x1, y + (offset > 0 ? ext : -ext));
      ctx.moveTo(x2, startY2); ctx.lineTo(x2, y + (offset > 0 ? ext : -ext));
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(x1, y); ctx.lineTo(x2, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x1 - tickSz, y + tickSz); ctx.lineTo(x1 + tickSz, y - tickSz);
    ctx.moveTo(x2 - tickSz, y + tickSz); ctx.lineTo(x2 + tickSz, y - tickSz);
    ctx.stroke();
    ctx.fillText(text, (x1 + x2) / 2, y - 2 * dScale);
  } else {
    const x = x1 + offset;
    if (offset !== 0) {
      const startX1 = (Math.abs(offset) > fitLen) ? (x - (offset > 0 ? fitLen : -fitLen)) : x1;
      const startX2 = (Math.abs(offset) > fitLen) ? (x - (offset > 0 ? fitLen : -fitLen)) : x2;
      ctx.beginPath();
      ctx.moveTo(startX1, y1); ctx.lineTo(x + (offset > 0 ? ext : -ext), y1);
      ctx.moveTo(startX2, y2); ctx.lineTo(x + (offset > 0 ? ext : -ext), y2);
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(x, y1); ctx.lineTo(x, y2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x - tickSz, y1 + tickSz); ctx.lineTo(x + tickSz, y1 - tickSz);
    ctx.moveTo(x - tickSz, y2 + tickSz); ctx.lineTo(x + tickSz, y2 - tickSz);
    ctx.stroke();
    ctx.save();
    ctx.translate(x - 3 * dScale, (y1 + y2) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(text, 0, 0);
    ctx.restore();
  }
  ctx.restore();
}

function drawCadGridBubble(ctx, x, y, label, isTop = true, targetY = null) {
  ctx.save();
  const dScale = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimScale !== undefined) ? parseFloat(brmLayoutState.dimScale) : 1.0;
  const bubbleR = Math.max(9, Math.round(12 * dScale));

  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = Math.max(0.8, Math.round(1 * dScale * 10) / 10);
  ctx.setLineDash([5, 3, 2, 3]);
  ctx.beginPath();
  const endY = targetY !== null ? targetY : (isTop ? y + 90 : y - 90);
  ctx.moveTo(x, isTop ? (y + bubbleR + 1) : (y - bubbleR - 1));
  ctx.lineTo(x, endY);
  ctx.stroke();
  ctx.setLineDash([]);

  // NO FILL: circular outline only
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = Math.max(1.0, Math.round(1.5 * dScale * 10) / 10);
  ctx.beginPath();
  ctx.arc(x, y, bubbleR, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = '#0f172a';
  ctx.font = `bold ${Math.max(8, Math.round(11 * dScale))}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label || '?', x, y);
  ctx.restore();
}

function drawCadRebarBalloon(ctx, cfg) {
  // cfg = { x, y, topNum, botNum, items: [{ text, target: {x, y}, dir: 'left'|'right', yOffset, num, color }] }
  ctx.save();
  const isDual = !!cfg.botNum;
  const r = isDual ? 12 : 10;

  // Chuẩn màu sắc đồng bộ: Thép chủ màu xanh (#0284c7), thép tăng cường màu hồng (#c026d3)
  const colorMain = '#0284c7';
  const colorExtra = '#c026d3';

  // Đọc quy cách leader từ Panel Layout (brmLayoutState)
  const effLeaderDist = (typeof brmLayoutState !== 'undefined' && brmLayoutState.leaderDist !== undefined) ? brmLayoutState.leaderDist : 60;
  const effLeaderLen = (typeof brmLayoutState !== 'undefined' && brmLayoutState.leaderLen !== undefined) ? brmLayoutState.leaderLen : 160;
  const scaleLd = (typeof scaleCAD !== 'undefined') ? (scaleCAD * 2.0) : 0.16;

  // Khoảng cách xiên và độ dài đoạn gác ngang (shelf) co giãn 1:1 theo Panel Layout
  const slantDist = Math.max(8, Math.round(effLeaderDist * scaleLd));
  const shelfBaseLen = Math.max(20, Math.round(effLeaderLen * scaleLd));

  ctx.lineWidth = 1.0;
  ctx.font = 'bold 9.5px monospace';

  if (isDual) {
    // =========================================================================
    // VÒNG TRÒN ĐÔI 1-2 (ĐỒNG BỘ 100% STYLE CAD: DOT + XIÊN + SHELF + BUBBLE)
    // =========================================================================
    const item1 = cfg.items?.find(it => it.num === '1') || cfg.items?.[0];
    const item2 = cfg.items?.find(it => it.num === '2') || cfg.items?.[1];

    const yShelf1 = cfg.y - 5.5; // Cao độ ngang nửa trên số 1
    const yShelf2 = cfg.y + 5.5; // Cao độ ngang nửa dưới số 2

    // 1. Nhánh 1 (Thanh 1 - Thép giá / chủ trên, màu xanh #0284c7)
    if (item1 && item1.target) {
      const col1 = item1.color || colorMain;
      const text1 = item1.text || '';
      const w1 = ctx.measureText(text1).width;
      const shelf1Len = Math.max(shelfBaseLen, w1 + 10);
      const circleLeftX = cfg.x - r;
      const elbow1X = circleLeftX - shelf1Len;
      const target1X = (item1.target.x !== undefined) ? item1.target.x : (elbow1X - slantDist);
      const target1Y = item1.target.y;

      // Solid dot trên thanh thép
      ctx.fillStyle = col1;
      ctx.beginPath();
      ctx.arc(target1X, target1Y, 2.2, 0, Math.PI * 2);
      ctx.fill();

      // Nét vẽ: từ target dot -> đoạn xiên lên elbow1 -> đoạn ngang shelf1 vào mép trái nửa trên số 1
      ctx.strokeStyle = col1;
      ctx.beginPath();
      ctx.moveTo(target1X, target1Y);
      ctx.lineTo(elbow1X, yShelf1);
      ctx.lineTo(circleLeftX, yShelf1);
      ctx.stroke();

      // Text note nằm ngay ngắn phẳng phiu TRÊN đường line ngang shelf
      ctx.fillStyle = col1;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(text1, elbow1X + shelf1Len / 2, yShelf1 - 2.5);
    }

    // 2. Nhánh 2 (Thanh 2 - Thép tăng cường gối trên, màu hồng #c026d3)
    if (item2 && item2.target) {
      const col2 = item2.color || colorExtra;
      const text2 = item2.text || '';
      const w2 = ctx.measureText(text2).width;
      const shelf2Len = Math.max(shelfBaseLen, w2 + 10);
      const circleRightX = cfg.x + r;
      const elbow2X = circleRightX + shelf2Len;
      const target2X = (item2.target.x !== undefined) ? item2.target.x : (elbow2X + slantDist);
      const target2Y = item2.target.y;

      // Solid dot trên thanh thép
      ctx.fillStyle = col2;
      ctx.beginPath();
      ctx.arc(target2X, target2Y, 2.2, 0, Math.PI * 2);
      ctx.fill();

      // Nét vẽ: từ mép phải nửa dưới số 2 -> đoạn ngang shelf2 -> đoạn xiên xuống target dot
      ctx.strokeStyle = col2;
      ctx.beginPath();
      ctx.moveTo(circleRightX, yShelf2);
      ctx.lineTo(elbow2X, yShelf2);
      ctx.lineTo(target2X, target2Y);
      ctx.stroke();

      // Text note nằm ngay ngắn phẳng phiu TRÊN đường line ngang shelf
      ctx.fillStyle = col2;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(text2, circleRightX + shelf2Len / 2, yShelf2 - 2.5);
    }

    // Vòng tròn đôi 1 / 2 nằm chính giữa
    ctx.strokeStyle = '#64748b';
    ctx.beginPath();
    ctx.arc(cfg.x, cfg.y, r, 0, Math.PI * 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cfg.x - r, cfg.y);
    ctx.lineTo(cfg.x + r, cfg.y);
    ctx.stroke();

    ctx.font = 'bold 9px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = colorMain;
    ctx.fillText(cfg.topNum || '1', cfg.x, cfg.y - 5.5);

    ctx.fillStyle = colorExtra;
    ctx.fillText(cfg.botNum || '2', cfg.x, cfg.y + 5.5);

  } else {
    // =========================================================================
    // VÒNG TRÒN ĐƠN 5, 6, 7 (ĐỒNG BỘ 100% STYLE CAD: DOT + XIÊN + SHELF + BUBBLE)
    // =========================================================================
    (cfg.items || []).forEach(item => {
      if (!item.target) return;
      const startY = item.yOffset !== undefined ? cfg.y + item.yOffset : cfg.y;

      // Màu sắc theo loại cốt thép
      let itemColor = item.color;
      if (!itemColor) {
        if (item.num === '1' || item.num === '5' || cfg.topNum === '5') {
          itemColor = colorMain; // Thép chủ xanh
        } else {
          itemColor = colorExtra; // Thép tăng cường hồng
        }
      }

      // 1. Solid dot tại tâm thanh thép
      ctx.fillStyle = itemColor;
      ctx.beginPath();
      ctx.arc(item.target.x, item.target.y, 2.2, 0, Math.PI * 2);
      ctx.fill();

      // 2. Tính toán elbow, shelf và bubble bám sát Panel Layout
      const textStr = item.text || '';
      const wText = ctx.measureText(textStr).width;
      const effShelf = Math.max(shelfBaseLen, wText + 10);
      const isTargetOnLeft = (item.dir !== 'left') && (item.target.x <= (cfg.x || (item.target.x + 1)));

      let elbowX, shelfEndX, bubbleX;
      if (isTargetOnLeft) {
        // Leader hướng sang phải: Target -> Elbow -> Shelf -> Bubble
        elbowX = item.target.x + slantDist;
        shelfEndX = elbowX + effShelf;
        bubbleX = shelfEndX + r;
      } else {
        // Leader hướng sang trái: Bubble <- Shelf <- Elbow <- Target
        elbowX = item.target.x - slantDist;
        shelfEndX = elbowX - effShelf;
        bubbleX = shelfEndX - r;
      }

      // Nét vẽ leader
      ctx.strokeStyle = itemColor;
      ctx.beginPath();
      ctx.moveTo(item.target.x, item.target.y);
      ctx.lineTo(elbowX, startY);
      ctx.lineTo(shelfEndX, startY);
      ctx.stroke();

      // Text note nằm ngay ngắn phẳng phiu TRÊN đường line ngang shelf
      ctx.fillStyle = itemColor;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(textStr, (elbowX + shelfEndX) / 2, startY - 2.5);

      // Vòng tròn số hiệu cốt thép (5, 6, 7) ở đầu shelf
      ctx.strokeStyle = itemColor;
      ctx.beginPath();
      ctx.arc(bubbleX, startY, r, 0, Math.PI * 2);
      ctx.stroke();

      ctx.fillStyle = itemColor;
      ctx.font = 'bold 9.5px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(cfg.topNum || '', bubbleX, startY);
    });
  }

  ctx.restore();
}

function drawSingleCrossSection(ctx, sec, beam) {
  const { 
    title, xCenter, 
    topMainCount, topMainDiam, topMainLabel,
    topExtraCount, topExtraDiam, topExtraLabel,
    botMainCount, botMainDiam, botMainLabel,
    botExtraCount, botExtraDiam, botExtraLabel,
    topCount, topLabel, botCount, botLabel,
    stirrupText, note 
  } = sec;
  
  let bWidth = beam.width || 200;
  let bDepth = beam.depth || 400;
  if (beam.section) {
    const sm = beam.section.match(/(\d+)\s*[xX]\s*(\d+)/);
    if (sm) {
      bWidth = parseInt(sm[1], 10);
      bDepth = parseInt(sm[2], 10);
    }
  }

  // Tỉ lệ zoom phóng to của Cross Section so với Dầm Dọc (True Isometric Scale 1:1)
  const csRatio = (brmLayoutState.csRatio !== undefined) ? parseFloat(brmLayoutState.csRatio) : 2.0;
  // scaleCS: tỉ lệ thực tế mm -> px của mặt cắt ngang (scaleCAD = 0.08)
  const scaleCS = scaleCAD * csRatio;

  // Tiết diện dầm đúng 100% tỉ lệ thật b x h (Tuyệt đối không bị méo, b=200 h=300 là hình chữ nhật 1.5:1)
  const wSec = Math.round(bWidth * scaleCS);
  const hSec = Math.round(bDepth * scaleCS);
  const ySec = (sec.ySec !== undefined) ? sec.ySec : 224;

  ctx.save();

  // Beam Concrete Web (Đã xóa bỏ hoàn toàn hình chữ nhật cánh sàn theo yêu cầu)
  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = Math.max(1.2, Math.round(1.8 * Math.sqrt(csRatio / 3.0) * 10) / 10);
  ctx.fillRect(xCenter - wSec/2, ySec, wSec, hSec);
  ctx.strokeRect(xCenter - wSec/2, ySec, wSec, hSec);

  // Stirrup (Rounded Rect with Inset representing 25mm concrete cover)
  const coverPx = Math.max(3.5, Math.round(25 * scaleCS));
  const stX = xCenter - wSec/2 + coverPx;
  const stY = ySec + coverPx;
  const stW = wSec - coverPx * 2;
  const stH = hSec - coverPx * 2;
  ctx.strokeStyle = '#0284c7';
  ctx.lineWidth = Math.max(1.1, Math.round(1.5 * Math.sqrt(csRatio / 3.0) * 10) / 10);
  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(stX, stY, stW, stH, Math.max(2, Math.round(12 * scaleCS)));
  } else {
    ctx.rect(stX, stY, stW, stH);
  }
  ctx.stroke();

  // 2 móc bẻ xéo 135° NẰM CÙNG 1 BÊN (góc trên cùng 1 bên)
  const hk = Math.max(4, Math.round(30 * scaleCS));
  ctx.beginPath();
  ctx.moveTo(stX + hk * 1.35, stY + hk * 1.35);
  ctx.lineTo(stX + 3, stY + 3);
  ctx.moveTo(stX + hk * 1.65, stY + hk * 1.35);
  ctx.lineTo(stX + 5.5, stY + 3);
  ctx.stroke();

  // Rebar Dots Setup
  const dotR = Math.max(2.2, Math.min(3.6, Math.round(10 * scaleCS * 10) / 10));
  const topY = stY + dotR + 1.2;
  const botY = stY + stH - dotR - 1.2;
  const innerLeft = stX + dotR + 1.2;
  const innerRight = stX + stW - dotR - 1.2;
  const rowGap = Math.max(7, Math.round(18 * scaleCS));

  function drawDot(c, x, y, r) {
    c.beginPath();
    c.arc(x, y, r, 0, Math.PI * 2);
    c.fill();
    c.stroke();
  }

  const nTopMain = (topMainCount !== undefined) ? topMainCount : (topCount || 2);
  const nTopExtra = (topExtraCount !== undefined) ? topExtraCount : 0;
  const nBotMain = (botMainCount !== undefined) ? botMainCount : (botCount || 2);
  const nBotExtra = (botExtraCount !== undefined) ? botExtraCount : 0;

  // Thép gia cường (cả lưng và bụng) luôn gồm tối thiểu 2 thanh nằm về 2 biên
  const effTopExtra = (nTopExtra > 0) ? Math.max(2, nTopExtra) : 0;
  const effBotExtra = (nBotExtra > 0) ? Math.max(2, nBotExtra) : 0;

  let lblTopMain = topMainLabel || (topLabel ? topLabel.split('+')[0].trim() : `${nTopMain}Φ${topMainDiam || 16}`);
  let lblTopExtra = (effTopExtra > 0) ? (topExtraLabel || `${effTopExtra}Φ${topExtraDiam || topMainDiam || 16}`) : '';
  if (lblTopExtra && lblTopExtra.startsWith('1Φ')) {
    lblTopExtra = lblTopExtra.replace('1Φ', '2Φ');
  } else if (lblTopExtra && lblTopExtra.startsWith('1Ø')) {
    lblTopExtra = lblTopExtra.replace('1Ø', '2Ø');
  }

  let lblBotMain = botMainLabel || (botLabel ? botLabel.split('+')[0].trim() : `${nBotMain}Φ${botMainDiam || 18}`);
  let lblBotExtra = (effBotExtra > 0) ? (botExtraLabel || `${effBotExtra}Φ${botExtraDiam || botMainDiam || 18}`) : '';
  if (lblBotExtra && lblBotExtra.startsWith('1Φ')) {
    lblBotExtra = lblBotExtra.replace('1Φ', '2Φ');
  } else if (lblBotExtra && lblBotExtra.startsWith('1Ø')) {
    lblBotExtra = lblBotExtra.replace('1Ø', '2Ø');
  }

  // 1. Top Layer 1: Thép chủ / giá trên (Red)
  ctx.fillStyle = '#dc2626';
  ctx.strokeStyle = '#7f1d1d';
  ctx.lineWidth = 1;
  if (nTopMain === 1) {
    drawDot(ctx, (innerLeft + innerRight) / 2, topY, dotR);
  } else {
    const step = (innerRight - innerLeft) / Math.max(1, nTopMain - 1);
    for (let i = 0; i < nTopMain; i++) {
      drawDot(ctx, innerLeft + i * step, topY, dotR);
    }
  }

  // 2. Top Layer 2: Thép tăng cường gối trên (Nhích xuống 1 lớp: topY + rowGap, màu hồng #c026d3)
  // Thép gia cường luôn nằm về 2 biên (tối thiểu 2 thanh), tuyệt đối không bao giờ nằm ở chính giữa!
  if (effTopExtra > 0) {
    ctx.fillStyle = '#c026d3';
    ctx.strokeStyle = '#86198f';
    const topY2 = topY + rowGap;
    if (effTopExtra <= 2) {
      drawDot(ctx, innerLeft, topY2, dotR);
      drawDot(ctx, innerRight, topY2, dotR);
    } else {
      const step = (innerRight - innerLeft) / (effTopExtra - 1);
      for (let i = 0; i < effTopExtra; i++) {
        drawDot(ctx, innerLeft + i * step, topY2, dotR);
      }
    }
  }

  // 3. Bottom Layer 1: Thép chủ dưới (Blue)
  ctx.fillStyle = '#2563eb';
  ctx.strokeStyle = '#1e3a8a';
  ctx.lineWidth = 1;
  if (nBotMain === 1) {
    drawDot(ctx, (innerLeft + innerRight) / 2, botY, dotR);
  } else {
    const step = (innerRight - innerLeft) / Math.max(1, nBotMain - 1);
    for (let i = 0; i < nBotMain; i++) {
      drawDot(ctx, innerLeft + i * step, botY, dotR);
    }
  }

  // 4. Bottom Layer 2: Thép tăng cường bụng nhịp (Nhích lên 1 lớp: botY - rowGap, màu hồng #c026d3)
  // Thép gia cường luôn nằm về 2 biên (tối thiểu 2 thanh), tuyệt đối không bao giờ nằm ở chính giữa!
  if (effBotExtra > 0) {
    ctx.fillStyle = '#c026d3';
    ctx.strokeStyle = '#86198f';
    const botY2 = botY - rowGap;
    if (effBotExtra <= 2) {
      drawDot(ctx, innerLeft, botY2, dotR);
      drawDot(ctx, innerRight, botY2, dotR);
    } else {
      const step = (innerRight - innerLeft) / (effBotExtra - 1);
      for (let i = 0; i < effBotExtra; i++) {
        drawDot(ctx, innerLeft + i * step, botY2, dotR);
      }
    }
  }

  // Đọc cấu hình từ Panel Layout (brmLayoutState)
  const effLeaderDist = (typeof brmLayoutState !== 'undefined' && brmLayoutState.leaderDist !== undefined) ? brmLayoutState.leaderDist : 60;
  const effLeaderLen = (typeof brmLayoutState !== 'undefined' && brmLayoutState.leaderLen !== undefined) ? brmLayoutState.leaderLen : 160;
  const effDimSpace1 = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimSpace1 !== undefined) ? brmLayoutState.dimSpace1 : 350;
  const effDimSpace2 = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimSpace2 !== undefined) ? brmLayoutState.dimSpace2 : 260;

  // Leader lines: Góc 135°, text nằm TRÊN line, bên trái canh lề trái, bên phải canh lề trái bắt đầu từ bend elbow
  const slantDist = Math.max(10, Math.round(effLeaderDist * scaleCS));
  const shelfLen = Math.max(20, Math.round(effLeaderLen * scaleCS));
  const fontLeaderSz = Math.max(8.5, Math.min(10.5, Math.round(35 * scaleCS)));

  ctx.font = `bold ${fontLeaderSz}px monospace`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';
  ctx.lineWidth = 1.2;

  // 1. TOP LAYER 1 LEADER (Thép giá / chủ - Đỏ)
  const elbowTopX1 = innerRight + slantDist;
  const elbowTopY1 = (effTopExtra > 0) ? (topY - slantDist - 8) : (topY - slantDist);
  const wTop1 = ctx.measureText(lblTopMain).width;
  const effShelfTop1 = Math.max(shelfLen, wTop1 + 10);
  const shelfTopEndX1 = elbowTopX1 + effShelfTop1;

  ctx.fillStyle = '#dc2626';
  ctx.strokeStyle = '#dc2626';
  ctx.beginPath();
  ctx.moveTo(innerRight, topY);
  ctx.lineTo(elbowTopX1, elbowTopY1);
  ctx.lineTo(shelfTopEndX1, elbowTopY1);
  ctx.stroke();
  ctx.fillText(lblTopMain, elbowTopX1 + 4, elbowTopY1 - 3);

  // 2. TOP LAYER 2 LEADER (Thép tăng cường gối trên - RIÊNG BIỆT - Hồng Magenta #c026d3)
  if (effTopExtra > 0 && lblTopExtra) {
    const topY2 = topY + rowGap;
    const elbowTopX2 = innerRight + slantDist + 6;
    const elbowTopY2 = elbowTopY1 + 18; // Cách dòng trên đúng 18px, song song hoàn hảo
    const wTop2 = ctx.measureText(lblTopExtra).width;
    const effShelfTop2 = Math.max(shelfLen, wTop2 + 10);
    const shelfTopEndX2 = elbowTopX2 + effShelfTop2;

    ctx.fillStyle = '#c026d3';
    ctx.strokeStyle = '#c026d3';
    ctx.beginPath();
    ctx.moveTo(innerRight, topY2);
    ctx.lineTo(elbowTopX2, elbowTopY2);
    ctx.lineTo(shelfTopEndX2, elbowTopY2);
    ctx.stroke();
    ctx.fillText(lblTopExtra, elbowTopX2 + 4, elbowTopY2 - 3);
  }

  // 3. BOTTOM LAYER 1 LEADER (Thép chủ đáy - Xanh)
  const elbowBotX1 = innerRight + slantDist;
  const elbowBotY1 = (effBotExtra > 0) ? (botY + slantDist + 8) : (botY + slantDist);
  const wBot1 = ctx.measureText(lblBotMain).width;
  const effShelfBot1 = Math.max(shelfLen, wBot1 + 10);
  const shelfBotEndX1 = elbowBotX1 + effShelfBot1;

  ctx.fillStyle = '#2563eb';
  ctx.strokeStyle = '#2563eb';
  ctx.beginPath();
  ctx.moveTo(innerRight, botY);
  ctx.lineTo(elbowBotX1, elbowBotY1);
  ctx.lineTo(shelfBotEndX1, elbowBotY1);
  ctx.stroke();
  ctx.fillText(lblBotMain, elbowBotX1 + 4, elbowBotY1 - 3);

  // 4. BOTTOM LAYER 2 LEADER (Thép tăng cường bụng nhịp - RIÊNG BIỆT - Hồng Magenta #c026d3)
  if (effBotExtra > 0 && lblBotExtra) {
    const botY2 = botY - rowGap;
    const elbowBotX2 = innerRight + slantDist + 6;
    const elbowBotY2 = elbowBotY1 - 18; // Cách dòng dưới đúng 18px, song song hoàn hảo
    const wBot2 = ctx.measureText(lblBotExtra).width;
    const effShelfBot2 = Math.max(shelfLen, wBot2 + 10);
    const shelfBotEndX2 = elbowBotX2 + effShelfBot2;

    ctx.fillStyle = '#c026d3';
    ctx.strokeStyle = '#c026d3';
    ctx.beginPath();
    ctx.moveTo(innerRight, botY2);
    ctx.lineTo(elbowBotX2, elbowBotY2);
    ctx.lineTo(shelfBotEndX2, elbowBotY2);
    ctx.stroke();
    ctx.fillText(lblBotExtra, elbowBotX2 + 4, elbowBotY2 - 3);
  }

  // Thép giá sườn khi H >= 700 (Thanh số 7: 2Φ12)
  let secH = beam.depth || 400;
  if (beam.section) {
    const sm = beam.section.match(/(\d+)\s*[xX]\s*(\d+)/);
    if (sm) secH = parseInt(sm[2], 10);
  }
  const isDeepBeam = (secH >= 700);

  if (isDeepBeam) {
    const midY = (topY + botY) / 2;
    ctx.fillStyle = '#d946ef';
    ctx.strokeStyle = '#86198f';
    ctx.lineWidth = 1;
    drawDot(ctx, innerLeft, midY, dotR);
    drawDot(ctx, innerRight, midY, dotR);

    // Leader for skin rebar
    const elbowMidX = innerRight + Math.max(8, Math.round(effLeaderDist * 0.75 * scaleCS));
    const elbowMidY = midY - Math.max(8, Math.round(effLeaderDist * 0.75 * scaleCS));
    const wMid = ctx.measureText('2Φ12').width;
    const effShelfMid = Math.max(Math.round(effLeaderLen * 0.8 * scaleCS), wMid + 10);
    const shelfMidEndX = elbowMidX + effShelfMid;
    ctx.fillStyle = '#c026d3';
    ctx.strokeStyle = '#c026d3';
    ctx.lineWidth = 1.1;
    ctx.font = `bold ${Math.max(8, Math.round(30 * scaleCS))}px monospace`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.beginPath();
    ctx.moveTo(innerRight, midY);
    ctx.lineTo(elbowMidX, elbowMidY);
    ctx.lineTo(shelfMidEndX, elbowMidY);
    ctx.stroke();
    ctx.fillText('2Φ12', elbowMidX + 4, elbowMidY - 3);
  }

  // Stirrup callout with leader: Bên trái hình CANH LỀ TRÁI, text nằm TRÊN đường line leader
  const stElbowX = stX - slantDist;
  const stElbowY = (stY + stH / 2) - slantDist;
  const stTextW = ctx.measureText(stirrupText).width;
  const stShelfLen = Math.max(shelfLen, stTextW + 10);
  const stShelfEndX = stElbowX - stShelfLen;
  ctx.fillStyle = '#0284c7';
  ctx.strokeStyle = '#0284c7';
  ctx.lineWidth = 1.1;

  // Solid dot tại điểm chỉ định cốt đai
  ctx.beginPath();
  ctx.arc(stX, stY + stH / 2, 2.2, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(stX, stY + stH / 2);
  ctx.lineTo(stElbowX, stElbowY);
  ctx.lineTo(stShelfEndX, stElbowY);
  ctx.stroke();
  ctx.font = `bold ${Math.max(8, Math.round(30 * scaleCS))}px monospace`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';
  ctx.fillText(stirrupText, stShelfEndX + 4, stElbowY - 3);

  // Dimensions (ĐÃ BỎ CHỮ b= và h=, chỉ ghi giá trị đo theo yêu cầu)
  // Cụm dimension b và h điều khiển theo Spacing Dim 1 từ Panel Layout
  const dimOffsetBottom = Math.max(24, Math.round(effDimSpace1 * 0.65 * scaleCS));
  const dimOffsetLeft = -Math.max(18, Math.round(effDimSpace1 * 0.40 * scaleCS));
  drawCadDimension(ctx, xCenter - wSec/2, ySec + hSec, xCenter + wSec/2, ySec + hSec, `${bWidth}`, dimOffsetBottom);
  drawCadDimension(ctx, xCenter - wSec/2, ySec, xCenter - wSec/2, ySec + hSec, `${bDepth}`, dimOffsetLeft, true);

  // TIÊU ĐỀ CROSS SECTION ĐƯỢC ĐƯA XUỐNG DƯỚI HÌNH MẶT CẮT (Cách hình theo Spacing Dim 2)
  const yTitleBelow = ySec + hSec + dimOffsetBottom + Math.max(14, Math.round(effDimSpace2 * 0.25 * scaleCS) + 6);
  ctx.fillStyle = '#0f172a';
  ctx.font = `bold ${Math.max(10, Math.round(38 * scaleCS))}px monospace`;
  ctx.textAlign = 'center';
  ctx.fillText(title, xCenter, yTitleBelow);

  if (note) {
    ctx.fillStyle = '#64748b';
    ctx.font = `${Math.max(8.5, Math.round(30 * scaleCS))}px sans-serif`;
    ctx.fillText(note, xCenter, yTitleBelow + 13);
  }

  ctx.restore();
}

// ------------------------------------------------------------------------------
// ------------------------------------------------------------------------------
// CAD CUT SYMBOL (Dấu mặt cắt 1-1, 2-2...)
// ------------------------------------------------------------------------------
function drawCadCutSymbol(ctx, x, label, yTopCenter = 22, yBotCenter = 180) {
  ctx.save();
  // Ký hiệu mặt cắt cross section: 1 line cao 200mm nằm bên trái text index, màu #999
  ctx.strokeStyle = '#999999';
  ctx.fillStyle = '#999999';
  const dScale = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimScale !== undefined) ? parseFloat(brmLayoutState.dimScale) : 1.0;
  ctx.lineWidth = Math.max(1.0, Math.round(1.6 * dScale * 10) / 10);

  const lineH = Math.max(10, Math.round(16 * dScale)); // 200mm thực tế = 16px CAD

  // 1. Ký hiệu section_index trên: Y cao ngang tên trục trên (yTopCenter = 22)
  ctx.beginPath();
  ctx.moveTo(x, yTopCenter - lineH / 2);
  ctx.lineTo(x, yTopCenter + lineH / 2);
  ctx.stroke();

  // 2. Ký hiệu section_index dưới: Hạ Y ngang với tên trục dưới (yBotCenter = yGridBot)
  ctx.beginPath();
  ctx.moveTo(x, yBotCenter - lineH / 2);
  ctx.lineTo(x, yBotCenter + lineH / 2);
  ctx.stroke();

  // Text index: nằm bên phải line (line nằm bên trái text index)
  ctx.font = `bold ${Math.max(7, Math.round(10 * dScale))}px monospace`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, x + Math.round(4 * dScale), yTopCenter);
  ctx.fillText(label, x + Math.round(4 * dScale), yBotCenter);

  ctx.restore();
}

// CAD BREAK LINE & COLUMN ELEVATION SYMBOL (No fill, no hatch, dấu break z-zigzag)
// ------------------------------------------------------------------------------
function drawCadVerticalBreakLine(ctx, x, yTop, yBot, breakW = 8, ext = 14) {
  const yc = (yTop + yBot) / 2;
  const bh = 14;
  ctx.save();
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  ctx.moveTo(x, yTop - ext);
  ctx.lineTo(x, yc - bh);
  ctx.lineTo(x - breakW / 2, yc - bh / 2);
  ctx.lineTo(x + breakW / 2, yc + bh / 2);
  ctx.lineTo(x, yc + bh);
  ctx.lineTo(x, yBot + ext);
  ctx.stroke();
  ctx.restore();
}

function drawCadBreakLine(ctx, x1, x2, y, breakH = 7, ext = 6) {
  const xc = (x1 + x2) / 2;
  const bw = 4;
  ctx.beginPath();
  ctx.moveTo(x1 - ext, y);
  ctx.lineTo(xc - bw, y);
  ctx.lineTo(xc - bw / 2, y - breakH);
  ctx.lineTo(xc + bw / 2, y + breakH);
  ctx.lineTo(xc + bw, y);
  ctx.lineTo(x2 + ext, y);
  ctx.stroke();
}

function drawCadColumnElevation(ctx, xc, colW, yBeam, hBeam, topExt = 16, botExt = 26) {
  const x1 = xc - colW / 2;
  const x2 = xc + colW / 2;
  const yTop = yBeam - topExt;
  const yBot = yBeam + hBeam + botExt;

  ctx.save();
  ctx.strokeStyle = '#64748b'; // Màu nét CAD chuẩn
  ctx.lineWidth = 1.3;

  // Hai đường biên đứng cột (No fill, no hatch chuẩn media_1792247794530.png)
  ctx.beginPath();
  ctx.moveTo(x1, yTop);
  ctx.lineTo(x1, yBot);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(x2, yTop);
  ctx.lineTo(x2, yBot);
  ctx.stroke();

  // Dấu break trên đỉnh cột
  drawCadBreakLine(ctx, x1, x2, yTop, 6, 6);

  // Dấu break dưới đáy cột
  drawCadBreakLine(ctx, x1, x2, yBot, 6, 6);

  ctx.restore();
}

function drawSpanCadDrawing(ctx, width, height, beam, chainInfo, rebarTopL, rebarBotM, rebarTopR, stirrupSpec) {
  // Dimensions
  let beamH = 400;
  let beamB = 200;
  if (beam.section) {
    const sm = beam.section.match(/(\d+)\s*[xX]\s*(\d+)/);
    if (sm) {
      beamB = parseInt(sm[1], 10);
      beamH = parseInt(sm[2], 10);
    }
  } else if (beam.depth) {
    beamH = beam.depth;
    beamB = beam.width || 200;
  }
  const isDeepBeam = (beamH >= 700);

  const yBeam = 76;
  const hBeam = 46;
  const colW = 38;
  const xColL = Math.max(90, width * 0.12);
  const xColR = Math.min(width - 90, width * 0.88);
  const spanW = xColR - xColL;
  const xInnerL = xColL + colW / 2;
  const xInnerR = xColR - colW / 2;
  const innerSpan = xInnerR - xInnerL;
  const lQuarter = innerSpan * 0.25;

  // Title (Align Bottom theo yêu cầu người dùng)
  ctx.save();
  ctx.fillStyle = '#1e293b';
  ctx.font = 'bold 12px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  const spanStr = beam.spanIndex ? `(Nhịp ${beam.spanIndex}/${beam.spanCount || chainInfo.chain.length})` : '';
  ctx.fillText(`MẶT CẮT DỌC DẦM: ${beam.longBeamId || beam.label} ${spanStr} • ${beam.section || `${beamB}x${beamH}`} • ${chainInfo.axisName} • ${formatStoryLabel(beam.story)}`, width / 2, height - 12);
  ctx.restore();

  // Find Grid Labels for Left & Right Supports
  const isX = chainInfo.isX;
  const coordStart = isX ? Math.min(beam.p1[0], beam.p2[0]) : Math.min(beam.p1[1], beam.p2[1]);
  const coordEnd = isX ? Math.max(beam.p1[0], beam.p2[0]) : Math.max(beam.p1[1], beam.p2[1]);
  const gridL = getGridBubbleLabel(coordStart, isX) || 'G1';
  const gridR = getGridBubbleLabel(coordEnd, isX) || 'G2';

  // Grid Bubbles above columns (y = 22)
  drawCadGridBubble(ctx, xColL, 22, gridL, true);
  drawCadGridBubble(ctx, xColR, 22, gridR, true);

  // 1. Chain Dimensions on Top (CAD green style matching media_1792244755010.png)
  const yDimTop = 38;
  const greenDim = '#059669';
  // Column left width (300)
  drawCadDimension(ctx, xColL - colW/2, yDimTop, xColL + colW/2, yDimTop, '300', 0, false, greenDim);
  // Left dense stirrup zone (600 Ø8a100)
  const denseLStr = `${Math.round(beam.length * 0.25)} ${stirrupSpec.label || 'Ø8'}${stirrupSpec.zoneDense || 'a100'}`;
  drawCadDimension(ctx, xInnerL, yDimTop, xInnerL + lQuarter, yDimTop, denseLStr, 0, false, greenDim);
  // Middle normal stirrup zone (800)
  const midLStr = `${Math.round(beam.length * 0.50)}`;
  drawCadDimension(ctx, xInnerL + lQuarter, yDimTop, xInnerR - lQuarter, yDimTop, midLStr, 0, false, greenDim);
  // Right dense stirrup zone (600 Ø8a100)
  drawCadDimension(ctx, xInnerR - lQuarter, yDimTop, xInnerR, yDimTop, denseLStr, 0, false, greenDim);
  // Right support width (150 | 150)
  drawCadDimension(ctx, xInnerR, yDimTop, xColR, yDimTop, '150', 0, false, greenDim);
  drawCadDimension(ctx, xColR, yDimTop, xColR + colW/2, yDimTop, '150', 0, false, greenDim);

  // 2. Supporting Columns (No fill, no hatch, 2 dấu break z-zigzag chuẩn media_1792247794530.png)
  drawCadColumnElevation(ctx, xColL, colW, yBeam, hBeam, 16, 26);
  drawCadColumnElevation(ctx, xColR, colW, yBeam, hBeam, 16, 26);

  // 3. Concrete Flange & Web
  ctx.save();
  ctx.fillStyle = '#f1f5f9';
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 1.2;
  ctx.fillRect(xColL - colW/2 - 10, yBeam - 8, spanW + colW + 20, 8);
  ctx.strokeRect(xColL - colW/2 - 10, yBeam - 8, spanW + colW + 20, 8);

  // Beam Concrete Web (2 đầu bbox dầm phủ ra cạnh cột ngoài ở 2 đầu luôn)
  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 2;
  ctx.fillRect(xColL - colW / 2, yBeam, spanW + colW, hBeam);
  ctx.strokeRect(xColL - colW / 2, yBeam, spanW + colW, hBeam);
  ctx.restore();

  // Height dimension on web (Ghi rõ chiều cao đúng tiết diện trên nền bê tông)
  drawCadDimension(ctx, xInnerR - lQuarter * 0.55, yBeam, xInnerR - lQuarter * 0.55, yBeam + hBeam, `${beamH}`, 0, true, greenDim);

  // 4. Stirrups (Thép đai chia 3 vùng)
  ctx.save();
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 1.2;
  // Left dense zone
  for (let x = xInnerL + 8; x <= xInnerL + lQuarter; x += 10) {
    ctx.beginPath(); ctx.moveTo(x, yBeam + 3); ctx.lineTo(x, yBeam + hBeam - 3); ctx.stroke();
  }
  // Mid normal zone
  for (let x = xInnerL + lQuarter + 12; x <= xInnerR - lQuarter; x += 20) {
    ctx.beginPath(); ctx.moveTo(x, yBeam + 3); ctx.lineTo(x, yBeam + hBeam - 3); ctx.stroke();
  }
  // Right dense zone
  for (let x = xInnerR - lQuarter; x <= xInnerR - 8; x += 10) {
    ctx.beginPath(); ctx.moveTo(x, yBeam + 3); ctx.lineTo(x, yBeam + hBeam - 3); ctx.stroke();
  }
  ctx.restore();

  // 5. Reinforcement Geometry (Chuẩn gDrawBeam.cs & media_1792244755010.png)
  const yTopMain = yBeam + 4;
  const yBotMain = yBeam + hBeam - 10; // Thụt vào so với bbox dầm thêm 25mm để hình chiếu tách biệt rõ ràng
  const yTopSupport = yTopMain + 2;
  const yBotSupport = yBotMain - 6; // Thép bụng dưới thụt cách thép chủ dưới 6px
  const yMidBar = yBeam + hBeam / 2;
  const rFilletCad = 3; // Giảm bán kính fillet 50% theo yêu cầu

  // A. Thép chủ trên (Cyan, nét đậm): Chạy suốt, neo vuông góc 90° cắm xuống hết chiều cao dầm - 25mm, nâng Y lên 25mm với mỏ neo bẻ xéo vào trong
  const dyRaise25_cad = Math.round(25 * scaleCAD); // 25mm thực tế = 2px trên CAD
  const yHookBotSingle = yBeam + hBeam - Math.round(25 * scaleCAD) - dyRaise25_cad;
  ctx.save();
  ctx.strokeStyle = '#06b6d4';
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  ctx.moveTo(xColL - colW/2 + 3 + 3, yHookBotSingle - 3);
  ctx.lineTo(xColL - colW/2 + 3, yHookBotSingle);
  ctx.arcTo(xColL - colW/2 + 3, yTopMain, xColR + colW/2 - 3, yTopMain, rFilletCad);
  // Nếu là nhịp biên phải thì cũng neo xuống + mỏ neo bẻ xéo vào trong
  if (!beam.spanIndex || beam.spanIndex === (beam.spanCount || chainInfo.chain.length)) {
    ctx.arcTo(xColR + colW/2 - 3, yTopMain, xColR + colW/2 - 3, yHookBotSingle, rFilletCad);
    ctx.lineTo(xColR + colW/2 - 3, yHookBotSingle);
    ctx.lineTo(xColR + colW/2 - 3 - 3, yHookBotSingle - 3);
  } else {
    ctx.lineTo(xColR + colW/2, yTopMain);
  }
  ctx.stroke();

  // B. Thép mũ gối trên (Magenta, nét 2.2): Neo 90° vào cột biên với fillet, bẻ xuống hết chiều cao dầm - 25mm với mỏ neo bẻ xéo vào trong
  const ySuppHookBot = yBeam + hBeam - Math.round(25 * scaleCAD) - 3;
  ctx.strokeStyle = '#d946ef';
  ctx.lineWidth = 2.2;
  // Gối trái
  ctx.beginPath();
  ctx.moveTo(xColL - colW/4 + 4 + 3, ySuppHookBot - 3);
  ctx.lineTo(xColL - colW/4 + 4, ySuppHookBot);
  ctx.arcTo(xColL - colW/4 + 4, yTopSupport, xInnerL + lQuarter, yTopSupport, rFilletCad);
  ctx.lineTo(xInnerL + lQuarter, yTopSupport);
  // Mỏ vát 45° chúc xuống BẺ VÀO TRONG (giảm 1/2: 3px)
  ctx.lineTo(xInnerL + lQuarter - 3, yTopSupport + 3);
  ctx.stroke();

  // Gối phải
  ctx.beginPath();
  // Mỏ vát 45° chúc xuống BẺ VÀO TRONG ở đầu nhịp (giảm 1/2: 3px)
  ctx.moveTo(xInnerR - lQuarter + 3, yTopSupport + 3);
  ctx.lineTo(xInnerR - lQuarter, yTopSupport);
  if (!beam.spanIndex || beam.spanIndex === (beam.spanCount || chainInfo.chain.length)) {
    ctx.arcTo(xColR + colW/4 - 4, yTopSupport, xColR + colW/4 - 4, ySuppHookBot, rFilletCad);
    ctx.lineTo(xColR + colW/4 - 4, ySuppHookBot);
    ctx.lineTo(xColR + colW/4 - 4 - 3, ySuppHookBot - 3);
  } else {
    ctx.lineTo(xColR + colW/4, yTopSupport);
  }
  ctx.stroke();

  // C. Thép giá cấu tạo sườn dầm (Thanh 7: 2Ø12 - Magenta) khi H >= 700 - Bẻ mỏ vào trong (3px)
  if (isDeepBeam) {
    ctx.strokeStyle = '#d946ef';
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(xInnerL + 7, yMidBar - 3);
    ctx.lineTo(xInnerL + 4, yMidBar);
    ctx.lineTo(xInnerR - 4, yMidBar);
    ctx.lineTo(xInnerR - 7, yMidBar - 3);
    ctx.stroke();
  }

  // D. Thép chủ dưới (Cyan, nét đậm): Mở rộng về mỗi bên 50mm (độ thụt còn 5px ~ 50mm so với cạnh ngoài)
  const dxIndent = 5; // Mở rộng về mỗi bên 50mm
  const dxRetract25_cad = Math.round(25 * scaleCAD); // Thu X vào 25mm ở đầu bên phải
  const xBotL_main = xColL - colW/2 + 3 + dxIndent;
  const xBotR_main = xColR + colW/2 - 3 - dxIndent - dxRetract25_cad;
  ctx.strokeStyle = '#06b6d4';
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  ctx.moveTo(xBotL_main + 3, yBotMain - 16 + 3);
  ctx.lineTo(xBotL_main, yBotMain - 16);
  ctx.arcTo(xBotL_main, yBotMain, xBotR_main, yBotMain, rFilletCad);
  if (!beam.spanIndex || beam.spanIndex === (beam.spanCount || chainInfo.chain.length)) {
    ctx.arcTo(xBotR_main, yBotMain, xBotR_main, yBotMain - 16, rFilletCad);
    ctx.lineTo(xBotR_main, yBotMain - 16);
    ctx.lineTo(xBotR_main - 3, yBotMain - 16 + 3);
  } else {
    ctx.lineTo(xBotR_main, yBotMain);
  }
  ctx.stroke();

  // E. Thép bụng dưới (Thanh 6: Magenta, nét 2.2)
  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const selL = document.getElementById('brmSelLeft');
  const selM = document.getElementById('brmSelMid');
  const selR = document.getElementById('brmSelRight');
  const selH = document.getElementById('brmSelHanger');

  const minMainSingle = (bWidth >= 300) ? 3 : 2;
  const rebarMainTop = (selMainTop && selMainTop.selectedIndex >= 0) ? parseRebarSpec(selMainTop.options[selMainTop.selectedIndex].value, minMainSingle, 18) : parseRebarSpec(beam.rebar_main_top || `${minMainSingle}D18`, minMainSingle, 18);
  const rebarMainBot = (selMainBot && selMainBot.selectedIndex >= 0) ? parseRebarSpec(selMainBot.options[selMainBot.selectedIndex].value, minMainSingle, 18) : parseRebarSpec(beam.rebar_main_bot || `${minMainSingle}D18`, minMainSingle, 18);

  const topMainCountSingle = Math.max(minMainSingle, rebarMainTop.count || minMainSingle);
  const topMainDiamSingle = rebarMainTop.diam || 18;
  const topMainTextSingle = `${topMainCountSingle}Ø${topMainDiamSingle}`;

  const botMainCountSingle = Math.max(minMainSingle, rebarMainBot.count || minMainSingle);
  const botMainDiamSingle = rebarMainBot.diam || 18;
  const botMainTextSingle = `${botMainCountSingle}Ø${botMainDiamSingle}`;

  const extraTopLStr = (selL && selL.selectedIndex >= 0) ? selL.options[selL.selectedIndex].value : (beam.extra_top_left || '0');
  const extraBotMStr = (selM && selM.selectedIndex >= 0) ? selM.options[selM.selectedIndex].value : (beam.extra_bot_mid || '0');
  const extraTopRStr = (selR && selR.selectedIndex >= 0) ? selR.options[selR.selectedIndex].value : (beam.extra_top_right || '0');

  const extraTopLSingle = parseRebarSpec(extraTopLStr, 0, 18).count;
  const topLDiamSingle = parseRebarSpec(extraTopLStr, 0, 18).diam;
  const extraTopRSingle = parseRebarSpec(extraTopRStr, 0, 18).count;
  const topRDiamSingle = parseRebarSpec(extraTopRStr, 0, 18).diam;

  const isShortSpanSingle = (beam.length < 2000);
  const extraBotCountSingle = isShortSpanSingle ? 0 : parseRebarSpec(extraBotMStr, 0, 18).count;
  const botExtraDiamSingle = parseRebarSpec(extraBotMStr, 0, 18).diam;

  if (extraBotCountSingle > 0) {
    const xBotL = xInnerL + innerSpan * 0.15;
    const xBotR = xInnerR - innerSpan * 0.15;
    ctx.strokeStyle = '#d946ef';
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(xBotL + 3, yBotSupport - 3);
    ctx.lineTo(xBotL, yBotSupport);
    ctx.lineTo(xBotR, yBotSupport);
    ctx.lineTo(xBotR - 3, yBotSupport - 3);
    ctx.stroke();
  }
  ctx.restore();

  // Balloon 1 & 2 (Top Main & Top Support)
  const suppTopLText = `${extraTopLSingle}Ø${topLDiamSingle}`;

  if (extraTopLSingle > 0) {
    drawCadRebarBalloon(ctx, {
      x: xInnerL + lQuarter * 0.55,
      y: yBeam - 22,
      topNum: '1',
      botNum: '2',
      items: [
        {
          text: topMainTextSingle,
          target: { x: xInnerL + 25, y: yTopMain },
          dir: 'left',
          yOffset: -6
        },
        {
          text: suppTopLText,
          target: { x: xInnerL + lQuarter * 0.88, y: yTopSupport },
          dir: 'right',
          yOffset: 6
        }
      ]
    });
  } else {
    drawCadRebarBalloon(ctx, {
      x: xInnerL + lQuarter * 0.55,
      y: yBeam - 22,
      topNum: '1',
      items: [
        {
          text: topMainTextSingle,
          target: { x: xInnerL + 25, y: yTopMain },
          dir: 'left',
          yOffset: 0
        }
      ]
    });
  }

  // Balloon 7 (Thép giá cấu tạo sườn dầm khi H >= 700)
  if (isDeepBeam) {
    drawCadRebarBalloon(ctx, {
      x: xInnerL + innerSpan * 0.55,
      y: yBeam + hBeam / 2 - 8,
      topNum: '7',
      items: [
        {
          text: '2Ø12',
          target: { x: xInnerL + innerSpan * 0.38, y: yMidBar }
        }
      ]
    });
  }

  // Balloon 5 (Thép chủ dưới)
  drawCadRebarBalloon(ctx, {
    x: xInnerL + 75,
    y: yBeam + hBeam + 26,
    topNum: '5',
    items: [
      {
        text: botMainTextSingle,
        target: { x: xInnerL + 25, y: yBotMain }
      }
    ]
  });

  // Balloon 6 (Thép gia cường bụng dưới) - Chỉ đặt khi có thép tăng cường bụng
  if (extraBotCountSingle > 0) {
    const botExtraText = `${extraBotCountSingle}Ø${botExtraDiamSingle}`;
    drawCadRebarBalloon(ctx, {
      x: xInnerL + innerSpan * 0.70,
      y: yBeam + hBeam + 26,
      topNum: '6',
      items: [
        {
          text: botExtraText,
          target: { x: xInnerL + innerSpan * 0.50, y: yBotSupport }
        }
      ]
    });
  }

  // 7. Section Cut Markers 1-1, 2-2, 3-3 (Hạ section_cross_index dưới 350mm)
  const dyTotal_span = Math.round((200 + 150) * 0.08);
  const yCutBot_span = yBeam + hBeam + 50 + dyTotal_span;
  drawCadCutSymbol(ctx, xInnerL + innerSpan * 0.12, '1', yBeam - 22, yCutBot_span);
  drawCadCutSymbol(ctx, (xInnerL + xInnerR) / 2, '2', yBeam - 22, yCutBot_span);
  drawCadCutSymbol(ctx, xInnerR - innerSpan * 0.12, '3', yBeam - 22, yCutBot_span);

  // Divider line
  ctx.save();
  ctx.strokeStyle = '#e2e8f0';
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(20, 195);
  ctx.lineTo(width - 20, 195);
  ctx.stroke();
  ctx.setLineDash([]);

  // Tag
  ctx.fillStyle = '#64748b';
  ctx.font = 'bold 10px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('BẢN VẼ CHI TIẾT MẶT CẮT NGANG (CROSS SECTIONS)', width / 2, 208);
  ctx.restore();

  // Detailed Cross Sections (Đầy đủ 2 lớp thép: Lưng nhích xuống, Bụng nhích lên)
  const secDefs = [
    {
      title: 'MẶT CẮT 1-1: GỐI TRÁI',
      xCenter: width * 0.20,
      topMainCount: topMainCountSingle,
      topMainDiam: topMainDiamSingle,
      topMainLabel: `${topMainCountSingle}Φ${topMainDiamSingle}`,
      topExtraCount: extraTopLSingle,
      topExtraDiam: topLDiamSingle,
      topExtraLabel: (extraTopLSingle > 0) ? `${extraTopLSingle}Φ${topLDiamSingle}` : '',
      botMainCount: botMainCountSingle,
      botMainDiam: botMainDiamSingle,
      botMainLabel: `${botMainCountSingle}Φ${botMainDiamSingle}`,
      botExtraCount: 0,
      botExtraDiam: botMainDiamSingle,
      botExtraLabel: '',
      stirrupText: stirrupSpec.shortDense,
      note: 'Vùng Moment Âm • c = 25mm'
    },
    {
      title: 'MẶT CẮT 2-2: BỤNG NHỊP',
      xCenter: width * 0.50,
      topMainCount: topMainCountSingle,
      topMainDiam: topMainDiamSingle,
      topMainLabel: `${topMainCountSingle}Φ${topMainDiamSingle}`,
      topExtraCount: (isShortSpanSingle && extraTopLSingle > 0) ? extraTopLSingle : 0,
      topExtraDiam: isShortSpanSingle ? topLDiamSingle : topMainDiamSingle,
      topExtraLabel: (isShortSpanSingle && extraTopLSingle > 0) ? `${extraTopLSingle}Φ${topLDiamSingle}` : '',
      botMainCount: botMainCountSingle,
      botMainDiam: botMainDiamSingle,
      botMainLabel: `${botMainCountSingle}Φ${botMainDiamSingle}`,
      botExtraCount: isShortSpanSingle ? 0 : extraBotCountSingle,
      botExtraDiam: botExtraDiamSingle,
      botExtraLabel: (isShortSpanSingle || extraBotCountSingle <= 0) ? '' : `${extraBotCountSingle}Φ${botExtraDiamSingle}`,
      stirrupText: isShortSpanSingle ? stirrupSpec.shortDense : stirrupSpec.shortMid,
      note: isShortSpanSingle ? 'Nhịp ngắn < 2m • c = 25mm' : 'Vùng Moment Dương • c = 25mm'
    },
    {
      title: 'MẶT CẮT 3-3: GỐI PHẢI',
      xCenter: width * 0.80,
      topMainCount: topMainCountSingle,
      topMainDiam: topMainDiamSingle,
      topMainLabel: `${topMainCountSingle}Φ${topMainDiamSingle}`,
      topExtraCount: extraTopRSingle,
      topExtraDiam: topRDiamSingle,
      topExtraLabel: (extraTopRSingle > 0) ? `${extraTopRSingle}Φ${topRDiamSingle}` : '',
      botMainCount: botMainCountSingle,
      botMainDiam: botMainDiamSingle,
      botMainLabel: `${botMainCountSingle}Φ${botMainDiamSingle}`,
      botExtraCount: 0,
      botExtraDiam: botMainDiamSingle,
      botExtraLabel: '',
      stirrupText: stirrupSpec.shortDense,
      note: 'Vùng Moment Âm • c = 25mm'
    }
  ];

  secDefs.forEach(sec => {
    drawSingleCrossSection(ctx, sec, beam);
  });
}

// ------------------------------------------------------------------------------
// DRAW FULL BEAM CAD CONTENT (HEURISTIC CONTINUOUS CAD ELEVATION)
// ------------------------------------------------------------------------------
function drawFullBeamCadContent(ctx, spanLayouts, numSpans, leftMargin, yChain, colW, isX, chain, totalLength, totalChainW, maxChainH, greenDim, yDimTop, yGridTop, numTiers, hasCol) {
  if (!hasCol) {
    hasCol = [];
    for (let i = 0; i <= numSpans; i++) {
      hasCol.push(checkColumnAtSupport(chain, i, isX));
    }
  }

  const effDimSpace1 = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimSpace1 !== undefined) ? brmLayoutState.dimSpace1 : 350;
  const effDimSpace2 = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimSpace2 !== undefined) ? brmLayoutState.dimSpace2 : 260;
  const scaleCadVal = (typeof scaleCAD !== 'undefined') ? scaleCAD : 0.08;
  const dSpace1_cad = Math.round(effDimSpace1 * scaleCadVal);
  const dSpace2_cad = Math.round(effDimSpace2 * scaleCadVal);

  // 2. Grid Bubbles & Column Elevations at all supports (Tên trục move Y lên cao, nét trục dóng thẳng xuyên cột)
  for (let i = 0; i <= numSpans; i++) {
    if (!hasCol[i]) continue; // KHÔNG HIỂN THỊ CỘT CŨNG NHƯ LƯỚI TRỤC TÊN TRỤC NẾU KHÔNG CÓ CỘT
    let xCol;
    let gridLabel;
    let colH;

    if (i < numSpans) {
      const b = chain[i];
      xCol = spanLayouts[i].xStart;
      const coord = isX ? Math.min(b.p1[0], b.p2[0]) : Math.min(b.p1[1], b.p2[1]);
      gridLabel = getGridBubbleLabel(coord, isX) || (i + 1);
      const hLeft = (i > 0) ? spanLayouts[i - 1].hSpan : spanLayouts[0].hSpan;
      const hRight = spanLayouts[i].hSpan;
      colH = Math.max(hLeft, hRight);
    } else {
      const b = chain[numSpans - 1];
      xCol = spanLayouts[numSpans - 1].xEnd;
      const coord = isX ? Math.max(b.p1[0], b.p2[0]) : Math.max(b.p1[1], b.p2[1]);
      gridLabel = getGridBubbleLabel(coord, isX) || (numSpans + 1);
      colH = spanLayouts[numSpans - 1].hSpan;
    }

    const yGridBotEst = yChain + maxChainH + dSpace1_cad + (numTiers > 1 ? dSpace2_cad : (dSpace2_cad * 2)) + Math.round(dSpace2_cad * 1.35);
    drawCadGridBubble(ctx, xCol, yGridTop, gridLabel, true, yGridBotEst - 13);
    drawCadColumnElevation(ctx, xCol, colW, yChain, colH, 16, 26);
  }

  // 3. Top Green CAD Dimension Chain (Thấy đầy đủ các chân dim dóng từ đỉnh dầm yChain lên yDimTop)
  const offsetTopDim = yDimTop - yChain;
  if (hasCol[0]) {
    drawCadDimension(ctx, leftMargin - colW/2, yChain, leftMargin + colW/2, yChain, '300', offsetTopDim, false, greenDim);
  }

  spanLayouts.forEach((span, idx) => {
    const isShort = (span.beam.length < 2000);
    if (isShort) {
      // Nhịp < 2000: Bố trí cốt đai dày toàn nhịp ngắn, chỉ 1 dim duy nhất
      const shortDenseStr = `${Math.round(span.beam.length)} ${span.stSpec.shortDense}`;
      drawCadDimension(ctx, span.xInnerL, yChain, span.xInnerR, yChain, shortDenseStr, offsetTopDim, false, greenDim);
    } else {
      const lQ = span.innerSpan * 0.25;
      const denseLStr = `${Math.round(span.beam.length * 0.25)} ${span.stSpec.shortDense}`;
      const midLStr = `${Math.round(span.beam.length * 0.50)}`;

      drawCadDimension(ctx, span.xInnerL, yChain, span.xInnerL + lQ, yChain, denseLStr, offsetTopDim, false, greenDim);
      drawCadDimension(ctx, span.xInnerL + lQ, yChain, span.xInnerR - lQ, yChain, midLStr, offsetTopDim, false, greenDim);
      drawCadDimension(ctx, span.xInnerR - lQ, yChain, span.xInnerR, yChain, denseLStr, offsetTopDim, false, greenDim);
    }

    if (idx < numSpans - 1 && hasCol[idx + 1]) {
      drawCadDimension(ctx, span.xInnerR, yChain, span.xEnd, yChain, '150', offsetTopDim, false, greenDim);
      drawCadDimension(ctx, span.xEnd, yChain, span.xEnd + colW/2, yChain, '150', offsetTopDim, false, greenDim);
    }
  });

  if (hasCol[numSpans]) {
    drawCadDimension(ctx, spanLayouts[numSpans - 1].xEnd - colW/2, yChain, spanLayouts[numSpans - 1].xEnd + colW/2, yChain, '300', offsetTopDim, false, greenDim);
  }

  // 4. Concrete Web for each span (Align Top: Đỉnh dầm phẳng yChain, đáy giật cấp theo hSpan)
  spanLayouts.forEach((span, i) => {
    ctx.save();
    const isExport = Boolean(ctx.isExport || (typeof Canvas2Svg !== 'undefined' && ctx instanceof Canvas2Svg));
    if (span.isActive && !isExport) {
      ctx.fillStyle = 'rgba(245, 158, 11, 0.18)';
      ctx.strokeStyle = '#d97706';
      ctx.lineWidth = 2.4;
    } else {
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#475569';
      ctx.lineWidth = 1.4;
    }
    const xBoxStart = (i === 0 && hasCol[0]) ? (span.xStart - colW / 2) : span.xStart;
    const boxSpanW = span.spanW + (i === 0 && hasCol[0] ? colW / 2 : 0) + (i === numSpans - 1 && hasCol[numSpans] ? colW / 2 : 0);

    ctx.fillRect(xBoxStart, yChain, boxSpanW, span.hSpan);
    ctx.strokeRect(xBoxStart, yChain, boxSpanW, span.hSpan);
    ctx.restore();
  });

  // Height dimension on web for each span (Ghi rõ chiều cao đúng tiết diện từng nhịp - vẽ trên nền bê tông)
  spanLayouts.forEach(span => {
    const xDimH = span.xInnerR - span.innerSpan * 0.25 * 0.55;
    drawCadDimension(ctx, xDimH, yChain, xDimH, yChain + span.hSpan, `${span.bDepth}`, 0, true, greenDim);
  });

  // 5. Stirrups in all spans (Chiều cao đai tương thích với hSpan từng nhịp)
  ctx.save();
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 1.1;
  spanLayouts.forEach(span => {
    const yTopSt = yChain + 2;
    const yBotSt = yChain + span.hSpan - 2;

    if (span.beam.length < 2000) {
      // Nhịp < 2000: Bố trí đai dày đều suốt nhịp (step = 12px)
      for (let x = span.xInnerL + 6; x <= span.xInnerR - 6; x += 12) {
        ctx.beginPath(); ctx.moveTo(x, yTopSt); ctx.lineTo(x, yBotSt); ctx.stroke();
      }
    } else {
      const lQ = span.innerSpan * 0.25;
      for (let x = span.xInnerL + 6; x <= span.xInnerL + lQ; x += 12) {
        ctx.beginPath(); ctx.moveTo(x, yTopSt); ctx.lineTo(x, yBotSt); ctx.stroke();
      }
      for (let x = span.xInnerL + lQ + 14; x <= span.xInnerR - lQ; x += 24) {
        ctx.beginPath(); ctx.moveTo(x, yTopSt); ctx.lineTo(x, yBotSt); ctx.stroke();
      }
      for (let x = span.xInnerR - lQ; x <= span.xInnerR - 6; x += 12) {
        ctx.beginPath(); ctx.moveTo(x, yTopSt); ctx.lineTo(x, yBotSt); ctx.stroke();
      }
    }
  });
  ctx.restore();

  // 6. Reinforcement across continuous chain
  const yTopMain = yChain + 3.5;
  const yTopSupport = yTopMain + 3.2;
  const rFilletChain = 2.5;
  const dxIndentChain = 4;

  ctx.save();

  // A. Continuous Bottom Main Rebar (Cyan 2.4 - Chạy đáy dầm, vuốt chuyển mức tại các gối có giật cấp)
  const dxRetract25_cad = Math.round(25 * scaleCAD); // Thu X vào 25mm ở đầu bên phải
  const xBotL_chain = leftMargin - (hasCol[0] ? (colW/2 - 3 - dxIndentChain) : -3);
  const xBotR_chain = leftMargin + totalChainW + (hasCol[numSpans] ? (colW/2 - 3 - dxIndentChain - dxRetract25_cad) : (-3 - dxRetract25_cad));
  ctx.strokeStyle = '#06b6d4';
  ctx.lineWidth = 2.4;
  ctx.beginPath();

  const yBot0 = spanLayouts[0].yBot;
  ctx.moveTo(xBotL_chain + 3, yBot0 - 14 + 3);
  ctx.lineTo(xBotL_chain, yBot0 - 14);
  ctx.arcTo(xBotL_chain, yBot0, spanLayouts[0].xEnd, yBot0, rFilletChain);

  for (let i = 0; i < numSpans; i++) {
    const curSpan = spanLayouts[i];
    const yBotCur = curSpan.yBot;

    if (i < numSpans - 1) {
      const nextSpan = spanLayouts[i + 1];
      const yBotNext = nextSpan.yBot;
      const xColMid = curSpan.xEnd;

      ctx.lineTo(xColMid - colW / 4, yBotCur);
      ctx.lineTo(xColMid + colW / 4, yBotNext);
    } else {
      ctx.arcTo(xBotR_chain, yBotCur, xBotR_chain, yBotCur - 14, rFilletChain);
      ctx.lineTo(xBotR_chain, yBotCur - 14);
      ctx.lineTo(xBotR_chain - 3, yBotCur - 14 + 3);
    }
  }
  ctx.stroke();

  // B. Continuous Top Main Rebar (Cyan 2.4 - Align Top: Chạy suốt thẳng hàng tại yTopMain)
  const xTopL_chain = leftMargin - (hasCol[0] ? (colW/2 - 3) : -3);
  const xTopR_chain = leftMargin + totalChainW + (hasCol[numSpans] ? (colW/2 - 3) : -3);
  const dyRaise25_cad = Math.round(25 * scaleCAD); // Nâng Y lên 25mm ở cả 2 đầu
  const yHookBotL = yChain + spanLayouts[0].hSpan - Math.round(25 * scaleCAD) - dyRaise25_cad;
  const yHookBotR = yChain + spanLayouts[numSpans - 1].hSpan - Math.round(25 * scaleCAD) - dyRaise25_cad;
  ctx.beginPath();
  // Đầu trái bẻ xuống hết chiều cao dầm - 25mm với mỏ neo bẻ xéo vào trong (nâng Y lên 25mm)
  ctx.moveTo(xTopL_chain + 3, yHookBotL - 3);
  ctx.lineTo(xTopL_chain, yHookBotL);
  ctx.arcTo(xTopL_chain, yTopMain, xTopR_chain, yTopMain, rFilletChain);
  ctx.arcTo(xTopR_chain, yTopMain, xTopR_chain, yHookBotR, rFilletChain);
  ctx.lineTo(xTopR_chain, yHookBotR);
  ctx.lineTo(xTopR_chain - 3, yHookBotR - 3);
  ctx.stroke();

  // C. Top Support Rebars (Magenta 2.2 - Thép mũ gối & Thép tăng cường lưng)
  // Quy tắc: Với đoạn dầm < 2000, thép tăng cường lưng đi suốt luôn không ngắt nhỏ
  ctx.strokeStyle = '#d946ef';
  ctx.lineWidth = 2.2;

  // Build raw intervals for each support joint
  const rawIntervals = [];
  for (let k = 0; k <= numSpans; k++) {
    let xL, xR;
    if (k === 0) {
      xL = spanLayouts[0].xStart - (hasCol[0] ? (Math.round(colW/4) - 2) : -3);
      if (spanLayouts[0].beam.length < 2000) {
        xR = (numSpans === 1) ? (spanLayouts[0].xEnd + (hasCol[numSpans] ? (Math.round(colW/4) - 2) : -3)) : spanLayouts[0].xEnd;
      } else {
        xR = spanLayouts[0].xInnerL + spanLayouts[0].innerSpan * 0.25;
      }
    } else if (k === numSpans) {
      xR = spanLayouts[numSpans - 1].xEnd + (hasCol[numSpans] ? (Math.round(colW/4) - 2) : -3);
      if (spanLayouts[numSpans - 1].beam.length < 2000) {
        xL = (numSpans === 1) ? (spanLayouts[0].xStart - (hasCol[0] ? (Math.round(colW/4) - 2) : -3)) : spanLayouts[numSpans - 1].xStart;
      } else {
        xL = spanLayouts[numSpans - 1].xInnerR - spanLayouts[numSpans - 1].innerSpan * 0.25;
      }
    } else {
      const prevSpan = spanLayouts[k - 1];
      const nextSpan = spanLayouts[k];
      if (prevSpan.beam.length < 2000) {
        xL = (k - 1 === 0) ? (prevSpan.xStart - (hasCol[0] ? (colW/2 - 3) : -3)) : prevSpan.xStart;
      } else {
        xL = prevSpan.xInnerR - prevSpan.innerSpan * 0.25;
      }
      if (nextSpan.beam.length < 2000) {
        xR = (k === numSpans - 1) ? (nextSpan.xEnd + (hasCol[numSpans] ? (colW/2 - 3) : -3)) : nextSpan.xEnd;
      } else {
        xR = nextSpan.xInnerL + nextSpan.innerSpan * 0.25;
      }
    }
    rawIntervals.push({ x1: Math.min(xL, xR), x2: Math.max(xL, xR) });
  }

  // Merge overlapping or contiguous intervals
  rawIntervals.sort((a, b) => a.x1 - b.x1);
  const mergedIntervals = [];
  rawIntervals.forEach(curr => {
    if (mergedIntervals.length === 0) {
      mergedIntervals.push({ ...curr });
    } else {
      const prev = mergedIntervals[mergedIntervals.length - 1];
      if (curr.x1 <= prev.x2 + 2) {
        prev.x2 = Math.max(prev.x2, curr.x2);
      } else {
        mergedIntervals.push({ ...curr });
      }
    }
  });

  mergedIntervals.forEach(seg => {
    ctx.beginPath();
    const isAtChainStart = (seg.x1 <= spanLayouts[0].xStart + 6);
    const isAtChainEnd = (seg.x2 >= spanLayouts[numSpans - 1].xEnd - 6);

    if (isAtChainStart) {
      // Móc neo đầu trái ngoài cùng bẻ xuống hết chiều cao dầm - 25mm với mỏ neo bẻ xéo vào trong
      const h0 = spanLayouts[0].hSpan;
      const hookDepth = yChain + h0 - Math.round(25 * scaleCAD) - 3;
      ctx.moveTo(seg.x1 + 3, hookDepth - 3);
      ctx.lineTo(seg.x1, hookDepth);
      ctx.arcTo(seg.x1, yTopSupport, seg.x1 + 10, yTopSupport, rFilletChain);
    } else {
      // Mỏ vát 45° chúc xuống đầu trái
      ctx.moveTo(seg.x1 + 3, yTopSupport + 3);
      ctx.lineTo(seg.x1, yTopSupport);
    }

    ctx.lineTo(seg.x2, yTopSupport);

    if (isAtChainEnd) {
      // Móc neo đầu phải ngoài cùng bẻ xuống hết chiều cao dầm - 25mm với mỏ neo bẻ xéo vào trong
      const hLast = spanLayouts[numSpans - 1].hSpan;
      const hookDepth = yChain + hLast - Math.round(25 * scaleCAD) - 3;
      ctx.arcTo(seg.x2, yTopSupport, seg.x2, hookDepth, rFilletChain);
      ctx.lineTo(seg.x2, hookDepth);
      ctx.lineTo(seg.x2 - 3, hookDepth - 3);
    } else {
      // Mỏ vát 45° chúc xuống đầu phải
      ctx.lineTo(seg.x2 - 3, yTopSupport + 3);
    }
    ctx.stroke();
  });

  // D. Bottom Support Rebars (Magenta 2.0 - Thép tăng cường bụng)
  // (1) Với đoạn dầm < 2000 thì không đặt thép tăng cường bụng!
  ctx.strokeStyle = '#d946ef';
  ctx.lineWidth = 2.0;
  spanLayouts.forEach(span => {
    if (span.beam.length < 2000) return; // BỎ QUA HOÀN TOÀN với dầm < 2000
    const extraBotCount = (span.extraBotM && span.extraBotM.count > 0) ? span.extraBotM.count : 0;
    if (extraBotCount <= 0) return;

    const xBotL = span.xInnerL + span.innerSpan * 0.15;
    const xBotR = span.xInnerR - span.innerSpan * 0.15;
    ctx.beginPath();
    ctx.moveTo(xBotL + 3, span.yBotSupport - 3);
    ctx.lineTo(xBotL, span.yBotSupport);
    ctx.lineTo(xBotR, span.yBotSupport);
    ctx.lineTo(xBotR - 3, span.yBotSupport - 3);
    ctx.stroke();
  });

  // E. Skin Rebar when H >= 700 (Thanh 7: 2Ø12 - Magenta)
  spanLayouts.forEach(span => {
    if (span.isDeepBeam) {
      const yMidBar = yChain + span.hSpan / 2;
      ctx.strokeStyle = '#d946ef';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(span.xInnerL + 6, yMidBar - 3);
      ctx.lineTo(span.xInnerL + 3, yMidBar);
      ctx.lineTo(span.xInnerR - 3, yMidBar);
      ctx.lineTo(span.xInnerR - 6, yMidBar - 3);
      ctx.stroke();
    }
  });
  ctx.restore();

  // 7. Rebar Balloons
  spanLayouts.forEach(span => {
    const lQ = span.innerSpan * 0.25;

    const minMain = (span.bWidth >= 300) ? 3 : 2;
    const topMainCount = Math.max(minMain, (span.rebarMainTop && span.rebarMainTop.count) ? span.rebarMainTop.count : minMain);
    const topMainDiam = (span.rebarMainTop && span.rebarMainTop.diam) ? span.rebarMainTop.diam : 18;
    const topMainText = `${topMainCount}Ø${topMainDiam}`;

    const suppTopLCount = (span.extraTopL && span.extraTopL.count > 0) ? span.extraTopL.count : 0;
    const suppTopLDiam = (span.extraTopL && span.extraTopL.diam) ? span.extraTopL.diam : topMainDiam;
    const suppTopLText = `${suppTopLCount}Ø${suppTopLDiam}`;

    // Không lặp lại balloon 1-2 cho nhịp ngắn < 2000 khi đã note ở nhịp trước
    if (span.beam.length >= 2000 || span.spanIndex === 0) {
      const xSuppEnd = span.xInnerL + lQ;
      // Điểm đặt target của thép tăng cường lưng: nằm lọt an toàn và chính xác trên thanh thép tăng cường, trước mỏ neo hook
      const xSuppTarget = Math.max(span.xInnerL + 12, Math.min(xSuppEnd - 12, span.xInnerL + Math.round(lQ * 0.55)));
      // Vị trí tâm bubble tròn (1 / 2) nằm ở khoảng 38% của lQ để 2 cánh vươn trái/phải cân đối, tránh giao cắt nét cột
      const xCircle = span.xInnerL + Math.max(32, Math.min(48, Math.round(lQ * 0.38)));

      if (suppTopLCount > 0) {
        drawCadRebarBalloon(ctx, {
          x: xCircle,
          y: yChain - 24,
          topNum: '1',
          botNum: '2',
          items: [
            {
              text: topMainText,
              target: { x: span.xInnerL - 6, y: yTopMain },
              yOffset: -6,
              num: '1',
              color: '#0284c7'
            },
            {
              text: suppTopLText,
              target: { x: xSuppTarget, y: yTopSupport },
              yOffset: 6,
              num: '2',
              color: '#c026d3'
            }
          ]
        });
      } else {
        drawCadRebarBalloon(ctx, {
          x: xCircle,
          y: yChain - 24,
          topNum: '1',
          items: [
            {
              text: topMainText,
              target: { x: span.xInnerL + 20, y: yTopMain },
              yOffset: 0,
              num: '1',
              color: '#0284c7'
            }
          ]
        });
      }
    }

    if (span.isDeepBeam) {
      drawCadRebarBalloon(ctx, {
        x: span.xInnerL + span.innerSpan * 0.55,
        y: yChain + span.hSpan / 2 - 8,
        topNum: '7',
        items: [
          {
            text: '2Ø12',
            target: { x: span.xInnerL + span.innerSpan * 0.38, y: yChain + span.hSpan / 2 },
            num: '7',
            color: '#c026d3'
          }
        ]
      });
    }

    const minBotMain = (span.bWidth >= 300) ? 3 : 2;
    const botMainCount = Math.max(minBotMain, (span.rebarMainBot && span.rebarMainBot.count) ? span.rebarMainBot.count : minBotMain);
    const botMainDiam = (span.rebarMainBot && span.rebarMainBot.diam) ? span.rebarMainBot.diam : 18;
    const botMainText = `${botMainCount}Ø${botMainDiam}`;

    drawCadRebarBalloon(ctx, {
      x: span.xInnerL + 75,
      y: span.yBot + 24,
      topNum: '5',
      items: [
        {
          text: botMainText,
          target: { x: span.xInnerL + 25, y: span.yBot },
          num: '5',
          color: '#0284c7'
        }
      ]
    });

    // Thanh 6: Thép tăng cường bụng (Chỉ đặt khi nhịp >= 2000 và có thép tăng cường bụng > 0)
    const extraBotCount = (span.extraBotM && span.extraBotM.count > 0) ? span.extraBotM.count : 0;
    if (span.beam.length >= 2000 && extraBotCount > 0) {
      const botExtraDiam = span.extraBotM.diam || botMainDiam;
      const botExtraText = `${extraBotCount}Ø${botExtraDiam}`;
      drawCadRebarBalloon(ctx, {
        x: span.xInnerL + span.innerSpan * 0.70,
        y: span.yBotSupport + 24,
        topNum: '6',
        items: [
          {
            text: botExtraText,
            target: { x: span.xInnerL + span.innerSpan * 0.50, y: span.yBotSupport },
            num: '6',
            color: '#c026d3'
          }
        ]
      });
    }
  });

  // 8. Dimensions & Grid Positions under each span
  // Line 1: Chi tiết cắt thép tăng cường bụng (0.15L - 0.70L - 0.15L) cho các nhịp >= 2000
  // Line 2: Chiều dài từng nhịp dầm
  // Line 3: Chiều dài tổng thể toàn bộ tuyến dầm
  // Cụm dimension dưới & section_cross_index điều khiển bằng Spacing Dim 1 & Spacing Dim 2 từ Panel Layout
  const yDimCutoff = yChain + maxChainH + dSpace1_cad;
  const yDimSpan = yDimCutoff + dSpace2_cad;
  const yDimTotal = yDimSpan + dSpace2_cad;
  const yGridBot = yDimTotal + Math.round(dSpace2_cad * 1.35);
  const yCutBot = yGridBot;

  // Section Cut Markers (Kéo dài xuống chạm yCutBot)
  spanLayouts.forEach(span => {
    if (span.cuts) {
      span.cuts.forEach(cut => {
        drawCadCutSymbol(ctx, cut.x, cut.label, yGridTop, yCutBot);
      });
    }
  });

  // 9. Dimensions under each span
  spanLayouts.forEach((span, i) => {
    ctx.save();
    // A. Đoạn dim 2 đầu thép tăng cường bụng (0.15L - 0.70L - 0.15L) nếu nhịp >= 2000
    if (span.beam.length >= 2000) {
      const lenCutL = Math.round(span.beam.length * 0.15);
      const lenMid = Math.round(span.beam.length * 0.70);
      const lenCutR = Math.round(span.beam.length) - lenCutL - lenMid;
      const xL_cut = span.xInnerL + span.innerSpan * 0.15;
      const xR_cut = span.xInnerR - span.innerSpan * 0.15;

      const offCut = yDimCutoff - (yChain + span.hSpan);
      drawCadDimension(ctx, span.xStart, yChain + span.hSpan, xL_cut, yChain + span.hSpan, `${lenCutL}`, offCut);
      drawCadDimension(ctx, xL_cut, yChain + span.hSpan, xR_cut, yChain + span.hSpan, `${lenMid}`, offCut);
      drawCadDimension(ctx, xR_cut, yChain + span.hSpan, span.xEnd, yChain + span.hSpan, `${lenCutR}`, offCut);
    }

    // B. Chiều dài thông thủy từng nhịp
    const offSpan = yDimSpan - (yChain + span.hSpan);
    drawCadDimension(ctx, span.xStart, yChain + span.hSpan, span.xEnd, yChain + span.hSpan, `${Math.round(span.beam.length)}`, offSpan);
    ctx.restore();
  });

  // 10. Overall Total Dimension Line: Luôn hiển thị đường dim tổng bên dưới ngang hàng lưới trục
  const offTotal = yDimTotal - (yChain + maxChainH);
  drawCadDimension(ctx, leftMargin, yChain + maxChainH, leftMargin + totalChainW, yChain + maxChainH, `${Math.round(totalLength)}`, offTotal);

  // 11. Bottom Grid Bubbles
  for (let i = 0; i <= numSpans; i++) {
    if (!hasCol[i]) continue; // KHÔNG HIỂN THỊ LƯỚI TRỤC DƯỚI NẾU KHÔNG CÓ CỘT
    const xCol = (i < numSpans) ? spanLayouts[i].xStart : spanLayouts[numSpans - 1].xEnd;
    let gridLabel;
    if (i < numSpans) {
      const b = chain[i];
      const coord = isX ? Math.min(b.p1[0], b.p2[0]) : Math.min(b.p1[1], b.p2[1]);
      gridLabel = getGridBubbleLabel(coord, isX) || (i + 1);
    } else {
      const b = chain[numSpans - 1];
      const coord = isX ? Math.max(b.p1[0], b.p2[0]) : Math.max(b.p1[1], b.p2[1]);
      gridLabel = getGridBubbleLabel(coord, isX) || (numSpans + 1);
    }
    drawCadGridBubble(ctx, xCol, yGridBot, gridLabel, false, yGridBot - 13);
  }
}

// ==============================================================================
// (5A-SVG) CANVAS-TO-SVG RECORDER: DIRECT 1:1 VECTOR CAD EXPORT
// ==============================================================================
class Canvas2Svg {
  constructor(width, height, options = {}) {
    this.width = width || 1680;
    this.height = height || 1188;
    this.isMonochrome = options.isMonochrome !== false;
    this.isExport = options.isExport !== false;
    this.scaleCad = options.scaleCad || 0.08;

    this.matrix = [1, 0, 0, 1, 0, 0];
    this.matrixStack = [];

    this.strokeStyle = '#000000';
    this.fillStyle = '#000000';
    this.lineWidth = 1.0;
    this.lineDash = [];
    this.font = '10px Tahoma, sans-serif';
    this.textAlign = 'left';
    this.textBaseline = 'alphabetic';
    this.lineCap = 'round';
    this.lineJoin = 'round';
    this.styleStack = [];

    this.currentPath = [];
    this.elements = [];

    this.currentClip = null;
    this.clipStack = [];
  }

  save() {
    this.matrixStack.push([...this.matrix]);
    this.clipStack.push(this.currentClip ? { ...this.currentClip } : null);
    this.styleStack.push({
      strokeStyle: this.strokeStyle,
      fillStyle: this.fillStyle,
      lineWidth: this.lineWidth,
      lineDash: [...this.lineDash],
      font: this.font,
      textAlign: this.textAlign,
      textBaseline: this.textBaseline,
      lineCap: this.lineCap,
      lineJoin: this.lineJoin
    });
  }

  restore() {
    if (this.matrixStack.length > 0) {
      this.matrix = this.matrixStack.pop();
    }
    if (this.clipStack.length > 0) {
      this.currentClip = this.clipStack.pop();
    }
    if (this.styleStack.length > 0) {
      const s = this.styleStack.pop();
      this.strokeStyle = s.strokeStyle;
      this.fillStyle = s.fillStyle;
      this.lineWidth = s.lineWidth;
      this.lineDash = s.lineDash;
      this.font = s.font;
      this.textAlign = s.textAlign;
      this.textBaseline = s.textBaseline;
      this.lineCap = s.lineCap;
      this.lineJoin = s.lineJoin;
    }
  }

  translate(dx, dy) {
    const [a, b, c, d, e, f] = this.matrix;
    this.matrix = [
      a, b, c, d,
      a * dx + c * dy + e,
      b * dx + d * dy + f
    ];
  }

  scale(sx, sy) {
    if (sy === undefined) sy = sx;
    const [a, b, c, d, e, f] = this.matrix;
    this.matrix = [
      a * sx, b * sx,
      c * sy, d * sy,
      e, f
    ];
  }

  rotate(angle) {
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    const [a, b, c, d, e, f] = this.matrix;
    this.matrix = [
      a * cos + c * sin,
      b * cos + d * sin,
      -a * sin + c * cos,
      -b * sin + d * cos,
      e, f
    ];
  }

  setTransform(a, b, c, d, e, f) {
    this.matrix = [a, b, c, d, e, f];
  }

  transformPoint(x, y) {
    const [a, b, c, d, e, f] = this.matrix;
    return [
      a * x + c * y + e,
      b * x + d * y + f
    ];
  }

  setLineDash(dash) {
    this.lineDash = Array.isArray(dash) ? dash : [];
  }

  getLineDash() {
    return [...this.lineDash];
  }

  beginPath() {
    this.currentPath = [];
  }

  closePath() {
    this.currentPath.push({ type: 'Z' });
  }

  moveTo(x, y) {
    const [tx, ty] = this.transformPoint(x, y);
    this.currentPath.push({ type: 'M', x: tx, y: ty });
  }

  lineTo(x, y) {
    const [tx, ty] = this.transformPoint(x, y);
    this.currentPath.push({ type: 'L', x: tx, y: ty });
  }

  arc(cx, cy, r, startAngle, endAngle, counterclockwise = false) {
    const [tcx, tcy] = this.transformPoint(cx, cy);
    const scale = Math.hypot(this.matrix[0], this.matrix[1]);
    const tr = r * scale;

    const da = endAngle - startAngle;
    const isFull = Math.abs(da) >= (Math.PI * 2 - 0.001);

    if (isFull) {
      this.currentPath.push({ type: 'M', x: tcx + tr, y: tcy });
      this.currentPath.push({ type: 'A', rx: tr, ry: tr, xRot: 0, largeArc: 1, sweep: 1, x: tcx - tr, y: tcy });
      this.currentPath.push({ type: 'A', rx: tr, ry: tr, xRot: 0, largeArc: 1, sweep: 1, x: tcx + tr, y: tcy });
    } else {
      const x1 = tcx + tr * Math.cos(startAngle);
      const y1 = tcy + tr * Math.sin(startAngle);
      const x2 = tcx + tr * Math.cos(endAngle);
      const y2 = tcy + tr * Math.sin(endAngle);
      let diff = counterclockwise ? (startAngle - endAngle) : (endAngle - startAngle);
      while (diff < 0) diff += Math.PI * 2;
      const largeArc = diff > Math.PI ? 1 : 0;
      const sweep = counterclockwise ? 0 : 1;

      this.currentPath.push({ type: 'L', x: x1, y: y1 });
      this.currentPath.push({ type: 'A', rx: tr, ry: tr, xRot: 0, largeArc, sweep, x: x2, y: y2 });
    }
  }

  arcTo(x1, y1, x2, y2, radius) {
    this.lineTo(x1, y1);
    this.lineTo(x2, y2);
  }

  rect(x, y, w, h) {
    this.moveTo(x, y);
    this.lineTo(x + w, y);
    this.lineTo(x + w, y + h);
    this.lineTo(x, y + h);
    this.closePath();
  }

  clipSegment(p1, p2, clip) {
    let t0 = 0.0, t1 = 1.0;
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const p = [-dx, dx, -dy, dy];
    const q = [p1.x - clip.minX, clip.maxX - p1.x, p1.y - clip.minY, clip.maxY - p1.y];

    for (let i = 0; i < 4; i++) {
      if (p[i] === 0) {
        if (q[i] < 0) return null;
      } else {
        const r = q[i] / p[i];
        if (p[i] < 0) {
          if (r > t1) return null;
          if (r > t0) t0 = r;
        } else {
          if (r < t0) return null;
          if (r < t1) t1 = r;
        }
      }
    }
    return {
      p1: { x: p1.x + t0 * dx, y: p1.y + t0 * dy },
      p2: { x: p1.x + t1 * dx, y: p1.y + t1 * dy }
    };
  }

  clipPath(pathArr, clip) {
    if (!clip) return pathArr;
    const clipped = [];
    let curPoint = null;
    let pendingMove = null;

    for (let i = 0; i < pathArr.length; i++) {
      const cmd = pathArr[i];
      if (cmd.type === 'M') {
        curPoint = { x: cmd.x, y: cmd.y };
        pendingMove = curPoint;
      } else if (cmd.type === 'L') {
        if (!curPoint) {
          curPoint = { x: cmd.x, y: cmd.y };
          continue;
        }
        const nextPoint = { x: cmd.x, y: cmd.y };
        const res = this.clipSegment(curPoint, nextPoint, clip);
        if (res) {
          if (clipped.length === 0 || pendingMove || Math.hypot(clipped[clipped.length - 1].x - res.p1.x, clipped[clipped.length - 1].y - res.p1.y) > 0.01) {
            clipped.push({ type: 'M', x: res.p1.x, y: res.p1.y });
          }
          clipped.push({ type: 'L', x: res.p2.x, y: res.p2.y });
          pendingMove = null;
        } else {
          pendingMove = nextPoint;
        }
        curPoint = nextPoint;
      } else if (cmd.type === 'A') {
        const inClip = (cmd.x >= clip.minX - 5 && cmd.x <= clip.maxX + 5 &&
                        cmd.y >= clip.minY - 5 && cmd.y <= clip.maxY + 5 &&
                        curPoint && curPoint.x >= clip.minX - 5 && curPoint.x <= clip.maxX + 5 &&
                        curPoint.y >= clip.minY - 5 && curPoint.y <= clip.maxY + 5);
        if (inClip) {
          if (pendingMove) {
            clipped.push({ type: 'M', x: pendingMove.x, y: pendingMove.y });
            pendingMove = null;
          }
          clipped.push(cmd);
        } else {
          pendingMove = null;
        }
        curPoint = { x: cmd.x, y: cmd.y };
      } else if (cmd.type === 'Z') {
        if (clipped.length > 2) {
          clipped.push({ type: 'Z' });
        }
        pendingMove = null;
      }
    }
    return clipped;
  }

  clip() {
    if (this.currentPath && this.currentPath.length >= 3) {
      const xs = this.currentPath.filter(p => p.x !== undefined).map(p => p.x);
      const ys = this.currentPath.filter(p => p.y !== undefined).map(p => p.y);
      if (xs.length > 0 && ys.length > 0) {
        const newClip = {
          minX: Math.min(...xs),
          maxX: Math.max(...xs),
          minY: Math.min(...ys),
          maxY: Math.max(...ys)
        };
        if (this.currentClip) {
          this.currentClip = {
            minX: Math.max(this.currentClip.minX, newClip.minX),
            maxX: Math.min(this.currentClip.maxX, newClip.maxX),
            minY: Math.max(this.currentClip.minY, newClip.minY),
            maxY: Math.min(this.currentClip.maxY, newClip.maxY)
          };
        } else {
          this.currentClip = newClip;
        }
      }
    }
  }

  stroke() {
    if (this.currentPath.length === 0) return;
    let pathArr = this.currentPath;
    if (this.currentClip) {
      pathArr = this.clipPath(pathArr, this.currentClip);
      if (pathArr.length === 0) return;
    }
    const xs = pathArr.filter(p => p.x !== undefined).map(p => p.x);
    const ys = pathArr.filter(p => p.y !== undefined).map(p => p.y);
    if (xs.length > 0 && ys.length > 0) {
      if (Math.max(...xs) < -20 || Math.min(...xs) > this.width + 20 ||
          Math.max(...ys) < -20 || Math.min(...ys) > this.height + 20) {
        return;
      }
    }
    const d = this.pathToD(pathArr);
    if (!d || !d.trim()) return;

    let color = this.strokeStyle;
    let lw = this.lineWidth;

    if (this.isMonochrome) {
      if (lw >= 2.0 || color.includes('#dc2626') || color.includes('#0284c7')) {
        lw = 1.417; // 0.50mm rebar
        color = '#000000';
      } else if (lw >= 1.0) {
        lw = 0.850; // 0.30mm concrete
        color = '#000000';
      } else {
        lw = 0.283; // 0.10mm dim/leader
        color = '#1f2937';
      }
    }

    let dashAttr = '';
    if (this.lineDash.length > 0) {
      dashAttr = ` stroke-dasharray="${this.lineDash.join(',')}"`;
    }

    this.elements.push(
      `<path d="${d}" fill="none" stroke="${color}" stroke-width="${lw.toFixed(3)}"${dashAttr} stroke-linecap="${this.lineCap}" stroke-linejoin="${this.lineJoin}"/>`
    );
  }

  fill() {
    if (this.currentPath.length === 0) return;
    let pathArr = this.currentPath;
    if (this.currentClip) {
      const xs = pathArr.filter(p => p.x !== undefined).map(p => p.x);
      const ys = pathArr.filter(p => p.y !== undefined).map(p => p.y);
      if (xs.length > 0 && ys.length > 0) {
        if (Math.max(...xs) < this.currentClip.minX - 2 || Math.min(...xs) > this.currentClip.maxX + 2 ||
            Math.max(...ys) < this.currentClip.minY - 2 || Math.min(...ys) > this.currentClip.maxY + 2) {
          return;
        }
      }
    }
    const d = this.pathToD(pathArr);
    if (!d || !d.trim()) return;

    let color = this.fillStyle;
    if (this.isMonochrome) {
      if (color === '#ffffff' || color === 'white') {
        color = '#ffffff';
      } else if (typeof color === 'string' && color.startsWith('rgba') && (color.includes(', 0.') || color.includes(',0.'))) {
        return; // Skip translucent UI highlight fills in monochrome CAD export
      } else {
        color = '#000000';
      }
    }
    this.elements.push(
      `<path d="${d}" fill="${color}" stroke="none"/>`
    );
  }

  strokeRect(x, y, w, h) {
    this.beginPath();
    this.rect(x, y, w, h);
    this.stroke();
  }

  fillRect(x, y, w, h) {
    if (this.fillStyle === 'rgba(0,0,0,0)' || this.fillStyle === 'transparent') return;
    if (this.isMonochrome && typeof this.fillStyle === 'string' && this.fillStyle.startsWith('rgba') && (this.fillStyle.includes(', 0.') || this.fillStyle.includes(',0.'))) return;
    this.beginPath();
    this.rect(x, y, w, h);
    this.fill();
  }

  clearRect(x, y, w, h) {}

  fillText(text, x, y) {
    if (!text && text !== 0) return;
    const str = String(text);
    if (!str.trim()) return;

    const [tx, ty] = this.transformPoint(x, y);
    if (this.currentClip) {
      if (tx < this.currentClip.minX - 5 || tx > this.currentClip.maxX + 5 ||
          ty < this.currentClip.minY - 5 || ty > this.currentClip.maxY + 5) {
        return;
      }
    }
    if (tx < -20 || tx > this.width + 20 || ty < -20 || ty > this.height + 20) {
      return;
    }

    const scale = Math.hypot(this.matrix[0], this.matrix[1]);

    let fSize = 10;
    const sizeMatch = (this.font || '').match(/(\d+(?:\.\d+)?)\s*px/i);
    if (sizeMatch) {
      fSize = parseFloat(sizeMatch[1]);
    }
    const scaledSize = Math.max(7, fSize * scale);
    const isBold = (this.font || '').includes('bold');

    let anchor = 'start';
    if (this.textAlign === 'center') anchor = 'middle';
    else if (this.textAlign === 'right' || this.textAlign === 'end') anchor = 'end';

    const angleRad = Math.atan2(this.matrix[1], this.matrix[0]);
    const angleDeg = Math.round((angleRad * 180) / Math.PI);

    let dyOffset = 0;
    let domBaseline = '';
    let rotAttr = '';

    if (Math.abs(angleDeg) > 0.1) {
      rotAttr = ` transform="rotate(${angleDeg} ${tx.toFixed(2)} ${ty.toFixed(2)})"`;
      if (this.textBaseline === 'middle') {
        domBaseline = ' dominant-baseline="central"';
      }
    } else {
      if (this.textBaseline === 'middle') dyOffset = scaledSize * 0.35;
      else if (this.textBaseline === 'bottom') dyOffset = 0;
      else if (this.textBaseline === 'top') dyOffset = scaledSize * 0.85;
    }

    const color = this.isMonochrome ? '#000000' : this.fillStyle;
    const escaped = str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

    this.elements.push(
      `<text x="${tx.toFixed(2)}" y="${(ty + dyOffset).toFixed(2)}" font-family="Tahoma, Arial, sans-serif" font-size="${scaledSize.toFixed(2)}px"${isBold ? ' font-weight="bold"' : ''}${domBaseline} fill="${color}" text-anchor="${anchor}"${rotAttr}>${escaped}</text>`
    );
  }

  measureText(text) {
    const str = String(text || '');
    let fSize = 10;
    const sizeMatch = (this.font || '').match(/(\d+(?:\.\d+)?)\s*px/i);
    if (sizeMatch) fSize = parseFloat(sizeMatch[1]);
    return { width: str.length * fSize * 0.58 };
  }

  pathToD(pathArr) {
    const parts = [];
    for (const cmd of pathArr) {
      if (cmd.type === 'M') parts.push(`M ${cmd.x.toFixed(2)} ${cmd.y.toFixed(2)}`);
      else if (cmd.type === 'L') parts.push(`L ${cmd.x.toFixed(2)} ${cmd.y.toFixed(2)}`);
      else if (cmd.type === 'A') parts.push(`A ${cmd.rx.toFixed(2)} ${cmd.ry.toFixed(2)} ${cmd.xRot} ${cmd.largeArc} ${cmd.sweep} ${cmd.x.toFixed(2)} ${cmd.y.toFixed(2)}`);
      else if (cmd.type === 'Z') parts.push('Z');
    }
    return parts.join(' ');
  }

  getSvgString() {
    return [
      `<?xml version="1.0" encoding="UTF-8"?>`,
      `<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 ${this.width} ${this.height}">`,
      `  <rect width="${this.width}" height="${this.height}" fill="#ffffff"/>`,
      `  <g id="drawing_layer">`,
      ...this.elements.map(e => `    ${e}`),
      `  </g>`,
      `</svg>`
    ].join('\n');
  }
}

function generateBeamCadSvg(currentBeam, chainInfo, options = {}) {
  const scaleCAD = 0.08;
  const sheetW = (typeof brmLayoutState !== 'undefined' && brmLayoutState.sheetW) ? brmLayoutState.sheetW : (420 * ((typeof brmLayoutState !== 'undefined' && brmLayoutState.scale) ? brmLayoutState.scale : 50));
  const sheetH = Math.round(sheetW * (297 / 420));
  const sheetW_cad = Math.round(sheetW * scaleCAD);
  const sheetH_cad = Math.round(sheetH * scaleCAD);

  const svgCtx = new Canvas2Svg(sheetW_cad, sheetH_cad, { isMonochrome: true, ...options });
  drawChainCadDrawing(svgCtx, sheetW_cad, sheetH_cad, currentBeam, chainInfo);
  return svgCtx.getSvgString();
}

function drawChainCadDrawing(ctx, width, height, currentBeam, chainInfo) {
  const chain = chainInfo.chain;
  const numSpans = chain.length;
  let totalLength = 0;
  chain.forEach(b => totalLength += b.length);
  if (totalLength <= 0) totalLength = 10000;

  const sheetX = 14;
  const sheetY = 6;

  // Tỉ lệ chuẩn CAD 1:1 (True Isometric Scale: 1mm thực tế = 0.08px trên bản vẽ)
  const scaleCAD = 0.08; 
  const scaleX = scaleCAD;
  const scaleY = scaleCAD;

  const colW = Math.round(400 * scaleCAD); // Cột 400mm đúng tỉ lệ = 32px
  const marginX = (brmLayoutState.marginX !== undefined) ? brmLayoutState.marginX : 500;
  const marginY = (brmLayoutState.marginY !== undefined) ? brmLayoutState.marginY : 400;
  const marginX_cad = Math.round(marginX * scaleCAD);
  const marginY_cad = Math.round(marginY * scaleCAD);

  // Kích thước trang in chuẩn A3 theo tỉ lệ
  const sheetW = brmLayoutState.sheetW || (420 * (brmLayoutState.scale || 50));
  const sheetH = Math.round(sheetW * (297 / 420));
  const sheetW_cad = Math.round(sheetW * scaleCAD);
  const sheetH_cad = Math.round(sheetH * scaleCAD);

  // Giới hạn chiều rộng khả dụng: Khung bản vẽ - 2 * marginX theo đúng yêu cầu người dùng
  const maxUsableW_cad = Math.max(200, sheetW_cad - (marginX_cad * 2));

  const isX = chainInfo.isX;

  // Kiểm tra gối nào thực sự có cột trong mô hình
  const hasCol = [];
  for (let i = 0; i <= numSpans; i++) {
    hasCol.push(checkColumnAtSupport(chain, i, isX));
  }

  // leftMargin tính theo sheetX + marginX_cad + (hasCol[0] ? colW/2 : 0)
  const leftMargin = sheetX + marginX_cad + (hasCol[0] ? Math.round(colW / 2) : 0);

  // Đọc các thông số bố cục từ Panel Layout
  const effDimSpace1 = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimSpace1 !== undefined) ? brmLayoutState.dimSpace1 : 350;
  const effDimSpace2 = (typeof brmLayoutState !== 'undefined' && brmLayoutState.dimSpace2 !== undefined) ? brmLayoutState.dimSpace2 : 260;
  const effLeaderDist = (typeof brmLayoutState !== 'undefined' && brmLayoutState.leaderDist !== undefined) ? brmLayoutState.leaderDist : 60;
  const effLeaderLen = (typeof brmLayoutState !== 'undefined' && brmLayoutState.leaderLen !== undefined) ? brmLayoutState.leaderLen : 160;

  const dSpace1_cad = Math.round(effDimSpace1 * scaleCAD);
  const dSpace2_cad = Math.round(effDimSpace2 * scaleCAD);

  // Cao độ mặt trên dầm cố định (Align Top), di chuyển theo marginY toàn trang
  // Base yChain = 125 để khi trục và dấu index đẩy lên không bị chạm mép trên khung bản vẽ A3
  const yChain = 125 + (marginY_cad - 32);

  const yDimTop = yChain - Math.max(46, Math.round(dSpace1_cad * 1.35));
  const yGridTop = yDimTop - Math.max(34, Math.round(dSpace2_cad * 1.35)); // Đẩy tên trục và index mặt cắt lên
  const greenDim = '#059669';

  chainInteractiveBoxes = [];

  // Đọc dropdown lựa chọn Bố trí thép dầm của nhịp đang chọn
  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const selL = document.getElementById('brmSelLeft');
  const selM = document.getElementById('brmSelMid');
  const selH = document.getElementById('brmSelHanger');
  const selR = document.getElementById('brmSelRight');
  const selSt = document.getElementById('brmSelStirrup');

  // Pre-calculate span geometry and rebar specs
  const spanLayouts = [];
  let currentAccumLen = 0;
  let activeSpanLayout = null;

  for (let i = 0; i < numSpans; i++) {
    const b = chain[i];
    const xStart = leftMargin + currentAccumLen * scaleX;
    const spanW = b.length * scaleX;
    const xEnd = xStart + spanW;
    const isActive = (b.label === currentBeam.label);

    let bDepth = b.depth || 400;
    let bWidth = b.width || 200;
    if (b.section) {
      const sm = b.section.match(/(\d+)\s*[xX]\s*(\d+)/);
      if (sm) {
        bWidth = parseInt(sm[1], 10);
        bDepth = parseInt(sm[2], 10);
      }
    }

    const hSpan = Math.round(bDepth * scaleY);
    const yBot = yChain + hSpan - 3;
    const yBotSupport = yBot - 3.2;

    const defCount = (bWidth >= 300) ? 3 : 2;
    const rebarMainTop = (selMainTop && selMainTop.selectedIndex >= 0) ? parseRebarSpec(selMainTop.options[selMainTop.selectedIndex].value, defCount, 18) : parseRebarSpec(b.rebar_main_top || `${defCount}D18`, defCount, 18);
    const rebarMainBot = (selMainBot && selMainBot.selectedIndex >= 0) ? parseRebarSpec(selMainBot.options[selMainBot.selectedIndex].value, defCount, 18) : parseRebarSpec(b.rebar_main_bot || `${defCount}D18`, defCount, 18);

    const extraTopLStr = (selL && selL.selectedIndex >= 0) ? selL.options[selL.selectedIndex].value : (b.extra_top_left || '0');
    const extraBotMStr = (selM && selM.selectedIndex >= 0) ? selM.options[selM.selectedIndex].value : (b.extra_bot_mid || '0');
    const extraTopRStr = (selR && selR.selectedIndex >= 0) ? selR.options[selR.selectedIndex].value : (b.extra_top_right || '0');
    const extraTopL = parseRebarSpec(extraTopLStr, 0, 18);
    const extraBotM = parseRebarSpec(extraBotMStr, 0, 18);
    const extraTopR = parseRebarSpec(extraTopRStr, 0, 18);

    const rebarTopL = (selL && selL.selectedIndex >= 0) ? parseRebarSpec(selL.options[selL.selectedIndex].value, defCount, 18) : parseRebarSpec(b.rebar_top_left, defCount, 18);
    const rebarBotM = (selM && selM.selectedIndex >= 0) ? parseRebarSpec(selM.options[selM.selectedIndex].value, defCount, 18) : parseRebarSpec(b.rebar_bot_mid, defCount, 18);
    const rebarTopR = (selR && selR.selectedIndex >= 0) ? parseRebarSpec(selR.options[selR.selectedIndex].value, defCount, 18) : parseRebarSpec(b.rebar_top_right, defCount, 18);
    const rebarHanger = (selH && selH.selectedIndex >= 0) ? parseRebarSpec(selH.options[selH.selectedIndex].value, defCount, 16) : parseRebarSpec(b.rebar_hanger || `${defCount}D16 (4.02cm²)`, defCount, 16);
    if (bWidth >= 300) {
      rebarHanger.count = Math.max(3, rebarHanger.count || 3);
      rebarHanger.label = `${rebarHanger.count}Φ${rebarHanger.diam}`;
      rebarMainTop.count = Math.max(3, rebarMainTop.count || 3);
      rebarMainTop.label = `${rebarMainTop.count}Φ${rebarMainTop.diam}`;
      rebarMainBot.count = Math.max(3, rebarMainBot.count || 3);
      rebarMainBot.label = `${rebarMainBot.count}Φ${rebarMainBot.diam}`;
    }
    const stSpec = (selSt && selSt.selectedIndex >= 0) ? parseStirrupSpec(selSt.options[selSt.selectedIndex].value) : parseStirrupSpec(b.stirrup);

    const xInnerL = xStart + (hasCol[i] ? colW / 2 : 0);
    const xInnerR = xEnd - (hasCol[i + 1] ? colW / 2 : 0);
    const innerSpan = Math.max(10, xInnerR - xInnerL);

    const layout = {
      beam: b,
      spanIndex: i,
      xStart,
      spanW,
      xEnd,
      xInnerL,
      xInnerR,
      innerSpan,
      isActive,
      bDepth,
      bWidth,
      hSpan,
      yBot,
      yBotSupport,
      isDeepBeam: (bDepth >= 700),
      rebarMainTop,
      rebarMainBot,
      extraTopL,
      extraBotM,
      extraTopR,
      rebarTopL,
      rebarBotM,
      rebarTopR,
      rebarHanger,
      stSpec
    };
    spanLayouts.push(layout);
    if (isActive) activeSpanLayout = layout;

    currentAccumLen += b.length;
  }
  if (!activeSpanLayout && spanLayouts.length > 0) activeSpanLayout = spanLayouts[0];

  // Khởi tạo các dấu mặt cắt: 1 mặt cắt cho nhịp < 2000, 3 mặt cắt cho nhịp >= 2000
  let cutCounter = 1;
  spanLayouts.forEach(span => {
    if (span.beam.length < 2000) {
      const cutIdx = `${cutCounter++}`;
      span.cuts = [
        { x: span.xInnerL + span.innerSpan * 0.50, label: cutIdx }
      ];
    } else {
      const idx1 = `${cutCounter++}`;
      const idx2 = `${cutCounter++}`;
      const idx3 = `${cutCounter++}`;
      span.cuts = [
        { x: span.xInnerL + span.innerSpan * 0.12, label: idx1 },
        { x: span.xInnerL + span.innerSpan * 0.50, label: idx2 },
        { x: span.xInnerR - span.innerSpan * 0.12, label: idx3 }
      ];
    }
  });

  const totalChainW = totalLength * scaleX;
  const maxChainH = Math.max(...spanLayouts.map(s => s.hSpan));

  // TÍNH TOÁN CẮT PHẦN THỪA (KHUNG BẢN VẼ - 2 * MARGINX) VÀ ĐUA XUỐNG BÊN DƯỚI
  const tierBeamMaxW = Math.max(100, maxUsableW_cad - colW);
  const numTiers = (totalChainW > maxUsableW_cad) ? Math.ceil(totalChainW / tierBeamMaxW) : 1;
  const tierSpacing = maxChainH + dSpace1_cad + (dSpace2_cad * 3) + Math.max(140, Math.round(marginY_cad * 0.7)); // Khoảng cách giữa các hàng dầm đua xuống tránh va chạm trục và index

  for (let t = 0; t < numTiers; t++) {
    const isFirstTier = (t === 0);
    const isLastTier = (t === numTiers - 1);
    const xTierCutStart = t * tierBeamMaxW;
    const xTierCutEnd = Math.min(totalChainW, (t + 1) * tierBeamMaxW);
    const tierDrawW = xTierCutEnd - xTierCutStart;

    const curYChain = yChain + t * tierSpacing;
    const curYDimTop = curYChain - Math.max(46, Math.round(dSpace1_cad * 1.35));
    const curYGridTop = curYDimTop - Math.max(34, Math.round(dSpace2_cad * 1.35));
    const curYGridBot = curYChain + maxChainH + dSpace1_cad + (numTiers > 1 ? dSpace2_cad : (dSpace2_cad * 2)) + Math.round(dSpace2_cad * 1.35);

    ctx.save();
    // Vùng clip giới hạn nghiêm ngặt trong khung (khung bản vẽ - 2 * marginX)
    ctx.beginPath();
    const clipLeft = isFirstTier ? (sheetX) : (leftMargin - 1);
    const clipRight = isLastTier ? (sheetX + sheetW_cad) : (leftMargin + tierDrawW + 1);
    ctx.rect(clipLeft, curYGridTop - 25, clipRight - clipLeft, (curYGridBot - curYGridTop) + 50);
    ctx.clip();

    // Dịch chuyển phần dầm tương ứng vào vị trí hiển thị của tier
    ctx.translate(-xTierCutStart, t * tierSpacing);

    drawFullBeamCadContent(ctx, spanLayouts, numSpans, leftMargin, yChain, colW, isX, chain, totalLength, totalChainW, maxChainH, greenDim, yDimTop, yGridTop, numTiers, hasCol);

    ctx.restore();

    // Vẽ nét cắt gián đoạn ziczac tại các mép cắt dầm
    if (!isLastTier) {
      drawCadVerticalBreakLine(ctx, leftMargin + tierDrawW, curYChain - 8, curYChain + maxChainH + 8, 8, 14);
    }
    if (!isFirstTier) {
      drawCadVerticalBreakLine(ctx, leftMargin, curYChain - 8, curYChain + maxChainH + 8, 8, 14);
    }

    // Interactive boxes cho từng nhịp trong tier hiện tại
    spanLayouts.forEach(span => {
      const sX1 = span.xStart - xTierCutStart;
      const sX2 = span.xEnd - xTierCutStart;
      if (sX2 > leftMargin && sX1 < leftMargin + tierDrawW) {
        chainInteractiveBoxes.push({
          beam: span.beam,
          x1: Math.max(leftMargin, sX1),
          y1: curYChain - 25,
          x2: Math.min(leftMargin + tierDrawW, sX2),
          y2: curYChain + span.hSpan + 50
        });
      }
    });
  }

  // 12. Divider Line: Bỏ nét vẽ đường ngăn giữa trang theo yêu cầu người dùng
  const lastYGridBot = yChain + (numTiers - 1) * tierSpacing + maxChainH + dSpace1_cad + (numTiers > 1 ? dSpace2_cad : (dSpace2_cad * 2)) + Math.round(dSpace2_cad * 1.35);
  const yDivider = lastYGridBot + 25;

  // 13. Detailed Cross Sections: XẾP LIÊN TIẾP NHAU ĐẾN KHI HẾT CHIỀU RỘNG TRANG MỚI XUỐNG HÀNG
  const allCrossSections = [];
  spanLayouts.forEach((span, i) => {
    const minMain = (span.bWidth >= 300) ? 3 : 2;
    const topMainCount = Math.max(minMain, (span.rebarMainTop && span.rebarMainTop.count) ? span.rebarMainTop.count : minMain);
    const topMainDiam = (span.rebarMainTop && span.rebarMainTop.diam) ? span.rebarMainTop.diam : 18;
    const topMainLabel = `${topMainCount}Φ${topMainDiam}`;

    const botMainCount = Math.max(minMain, (span.rebarMainBot && span.rebarMainBot.count) ? span.rebarMainBot.count : minMain);
    const botMainDiam = (span.rebarMainBot && span.rebarMainBot.diam) ? span.rebarMainBot.diam : 18;
    const botMainLabel = `${botMainCount}Φ${botMainDiam}`;

    const extraTopL = (span.extraTopL && span.extraTopL.count > 0) ? span.extraTopL.count : 0;
    const topLDiam = (span.extraTopL && span.extraTopL.diam) ? span.extraTopL.diam : topMainDiam;

    const extraTopR = (span.extraTopR && span.extraTopR.count > 0) ? span.extraTopR.count : 0;
    const topRDiam = (span.extraTopR && span.extraTopR.diam) ? span.extraTopR.diam : topMainDiam;

    const extraBotM = (span.extraBotM && span.extraBotM.count > 0) ? span.extraBotM.count : 0;
    const botExtraDiam = (span.extraBotM && span.extraBotM.diam) ? span.extraBotM.diam : botMainDiam;

    if (span.beam.length < 2000) {
      // (1) Nhịp < 2000: Chỉ tạo đúng 1 mặt cắt cross section chính giữa nhịp
      const cutIdx = span.cuts[0].label;
      allCrossSections.push({
        spanIndex: i,
        beam: span.beam,
        isActive: span.isActive,
        title: `${cutIdx}-${cutIdx}`,
        topMainCount: topMainCount,
        topMainDiam: topMainDiam,
        topMainLabel: topMainLabel,
        topExtraCount: extraTopL,
        topExtraDiam: topLDiam,
        topExtraLabel: (extraTopL > 0) ? `${extraTopL}Φ${topLDiam}` : '',
        botMainCount: botMainCount,
        botMainDiam: botMainDiam,
        botMainLabel: botMainLabel,
        botExtraCount: 0,
        botExtraDiam: botMainDiam,
        botExtraLabel: '',
        stirrupText: span.stSpec.shortDense,
        note: `${span.bWidth}x${span.bDepth}`
      });
    } else {
      const idx1 = span.cuts[0].label;
      const idx2 = span.cuts[1].label;
      const idx3 = span.cuts[2].label;

      allCrossSections.push(
        {
          spanIndex: i,
          beam: span.beam,
          isActive: span.isActive,
          title: `${idx1}-${idx1}`,
          topMainCount: topMainCount,
          topMainDiam: topMainDiam,
          topMainLabel: topMainLabel,
          topExtraCount: extraTopL,
          topExtraDiam: topLDiam,
          topExtraLabel: (extraTopL > 0) ? `${extraTopL}Φ${topLDiam}` : '',
          botMainCount: botMainCount,
          botMainDiam: botMainDiam,
          botMainLabel: botMainLabel,
          botExtraCount: 0,
          botExtraDiam: botMainDiam,
          botExtraLabel: '',
          stirrupText: span.stSpec.shortDense,
          note: `${span.bWidth}x${span.bDepth}`
        },
        {
          spanIndex: i,
          beam: span.beam,
          isActive: span.isActive,
          title: `${idx2}-${idx2}`,
          topMainCount: topMainCount,
          topMainDiam: topMainDiam,
          topMainLabel: topMainLabel,
          topExtraCount: 0,
          topExtraDiam: topMainDiam,
          topExtraLabel: '',
          botMainCount: botMainCount,
          botMainDiam: botMainDiam,
          botMainLabel: botMainLabel,
          botExtraCount: extraBotM,
          botExtraDiam: botExtraDiam,
          botExtraLabel: (extraBotM > 0) ? `${extraBotM}Φ${botExtraDiam}` : '',
          stirrupText: span.stSpec.shortMid,
          note: `${span.bWidth}x${span.bDepth}`
        },
        {
          spanIndex: i,
          beam: span.beam,
          isActive: span.isActive,
          title: `${idx3}-${idx3}`,
          topMainCount: topMainCount,
          topMainDiam: topMainDiam,
          topMainLabel: topMainLabel,
          topExtraCount: extraTopR,
          topExtraDiam: topRDiam,
          topExtraLabel: (extraTopR > 0) ? `${extraTopR}Φ${topRDiam}` : '',
          botMainCount: botMainCount,
          botMainDiam: botMainDiam,
          botMainLabel: botMainLabel,
          botExtraCount: 0,
          botExtraDiam: botMainDiam,
          botExtraLabel: '',
          stirrupText: span.stSpec.shortDense,
          note: `${span.bWidth}x${span.bDepth}`
        }
      );
    }
  });

  // ----------------------------------------------------------------------------
  // ĐƯỜNG BAO LAYOUT TRANG IN & DỒN MẶT CẮT VỪA TRANG IN (A3 LANDSCAPE)
  // ----------------------------------------------------------------------------
  // 1. Đường bao Layout ngay trên canvas 2D
  ctx.save();
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1.8;
  ctx.strokeRect(sheetX, sheetY, sheetW_cad, sheetH_cad);

  // Viền trong margin khung bản vẽ (8px)
  const borderMargin = 8;
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 1.0;
  ctx.strokeRect(sheetX + borderMargin, sheetY + borderMargin, sheetW_cad - borderMargin * 2, sheetH_cad - borderMargin * 2);

  // Tiêu đề bản vẽ dầm trên trang in (Align Bottom theo yêu cầu người dùng)
  ctx.save();
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 15px "Segoe UI", Roboto, Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  const storyStr = formatStoryLabel(currentBeam.story);
  const axisPart = chainInfo.axisName ? ` • TRỤC ${chainInfo.axisName.replace('Trục ', '').toUpperCase()}` : '';
  const sheetTitleText = `BẢN VẼ CHI TIẾT DẦM: ${currentBeam.longBeamId || currentBeam.label} • ${storyStr}${axisPart} (${numSpans} NHỊP • ${currentBeam.section || ''})`;
  const titleY = sheetY + sheetH_cad - borderMargin - 12;
  ctx.fillText(sheetTitleText, sheetX + sheetW_cad / 2, titleY);
  ctx.restore();

  // Bỏ text số đo chiều ngang và dọc trang theo yêu cầu người dùng
  ctx.restore();

  // 2. DỒN CÁC CROSS SECTION VỪA TRANG IN VỚI GAP X VÀ GAP Y
  const csRatio = (brmLayoutState.csRatio !== undefined) ? parseFloat(brmLayoutState.csRatio) : 2.0;
  const scaleCS = scaleCAD * csRatio;
  const gapX_cad = Math.round((brmLayoutState.gapX !== undefined ? brmLayoutState.gapX : -100) * scaleCAD);
  const gapY_cad = Math.round((brmLayoutState.gapY !== undefined ? brmLayoutState.gapY : -100) * scaleCAD);

  // Chiều rộng & chiều cao lớn nhất của các mặt cắt theo scaleCS
  let maxSecW = 200;
  let maxSecH = 400;
  allCrossSections.forEach(s => {
    const w = s.beam?.width || 200;
    const h = s.beam?.depth || 400;
    if (w > maxSecW) maxSecW = w;
    if (h > maxSecH) maxSecH = h;
  });
  const maxWPx = Math.round(maxSecW * scaleCS);
  const maxHPx = Math.round(maxSecH * scaleCS);

  const csShelfLen = Math.max(20, Math.round(effLeaderLen * scaleCS));
  const csSlantDist = Math.max(10, Math.round(effLeaderDist * scaleCS));
  const csDimOffsetBot = Math.max(24, Math.round(effDimSpace1 * 0.65 * scaleCS));

  // Chiều rộng 1 slot mặt cắt (thân mặt cắt + 2 bên leader dóng chữ + gapX_cad)
  const secColWidth = Math.max(140, maxWPx + csShelfLen + csSlantDist + 35 + gapX_cad);
  const rowHeight = Math.max(120, maxHPx + csDimOffsetBot + 60 + gapY_cad);
  const usableWidth = Math.max(secColWidth, sheetW_cad - (marginX_cad * 2));
  const colsPerRow = Math.max(1, Math.floor(usableWidth / secColWidth));

  allCrossSections.forEach((sec, k) => {
    const col = k % colsPerRow;
    const row = Math.floor(k / colsPerRow);

    const xCenter = sheetX + marginX_cad + (secColWidth / 2) + col * secColWidth;
    const ySec = yDivider + 18 + row * rowHeight;

    const secDef = {
      ...sec,
      xCenter,
      ySec
    };

    // Vẽ mặt cắt với leader góc 135°, không có sàn, không có w= h=
    drawSingleCrossSection(ctx, secDef, sec.beam);

    // Interactive box: Click vào mặt cắt để chọn nhịp tương ứng
    chainInteractiveBoxes.push({
      beam: sec.beam,
      x1: xCenter - Math.round(secColWidth / 2),
      y1: ySec - 15,
      x2: xCenter + Math.round(secColWidth / 2),
      y2: ySec + rowHeight
    });
  });
}

// ==============================================================================
// BEAM REBAR CAD CANVAS ZOOM & PAN STATE
// ==============================================================================
const brmCadView = {
  scale: 1.0,
  offsetX: 0,
  offsetY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  hasDragged: false
};

function zoomBeamCad(factor) {
  brmCadView.scale = Math.max(0.3, Math.min(6.0, brmCadView.scale * factor));
  renderBeamDrawings();
}

function focusActiveSpanCad() {
  const canvas = document.getElementById('brmDrawingCanvas');
  if (!canvas || !selectedBeamForRebar) return;
  const canvasW = canvas.clientWidth || 800;
  const chainInfo = findContinuousBeamChain(selectedBeamForRebar);
  const chain = chainInfo.chain || [selectedBeamForRebar];
  const scaleCAD = 0.08;
  const leftMargin = 70;

  let currentAccumLen = 0;
  let activeMidX = leftMargin + 200;

  for (let i = 0; i < chain.length; i++) {
    const b = chain[i];
    const spanW = b.length * scaleCAD;
    if (b.label === selectedBeamForRebar.label) {
      activeMidX = leftMargin + currentAccumLen * scaleCAD + spanW / 2;
      break;
    }
    currentAccumLen += b.length;
  }

  // Focus zoom 1:1 on active span
  brmCadView.scale = 1.0;
  brmCadView.offsetX = (canvasW / 2) - activeMidX;
  brmCadView.offsetY = 15;
  brmCadView.isDragging = false;
  brmCadView.hasDragged = false;
  renderBeamDrawings();
}

function resetBeamCadView() {
  const canvas = document.getElementById('brmDrawingCanvas');
  const canvasW = canvas ? (canvas.clientWidth || 800) : 800;
  const canvasH = canvas ? (canvas.clientHeight || 580) : 580;
  const chainInfo = selectedBeamForRebar ? findContinuousBeamChain(selectedBeamForRebar) : null;
  const chain = chainInfo && chainInfo.chain ? chainInfo.chain : [selectedBeamForRebar];
  
  if (beamDrawingMode === 'chain' && chain && chain.length >= 1) {
    let totalLen = 0;
    chain.forEach(b => totalLen += b.length);
    const scaleCAD = 0.08;

    const sheetW = brmLayoutState.sheetW || 24000;
    const sheetH = Math.round(sheetW * (297 / 420));
    const sheetW_cad = Math.round(sheetW * scaleCAD);
    const sheetH_cad = Math.round(sheetH * scaleCAD);

    const totalDrawW = sheetW_cad + 40;
    const totalDrawH = Math.max(sheetH_cad + 40, 600);
    
    // Fit toàn bộ đường bao Layout trang in và chi tiết vào khung nhìn (chừa khoảng đệm dưới toolbar nổi)
    const topPad = 48;
    const fitScaleX = (canvasW - 40) / totalDrawW;
    const fitScaleY = (canvasH - 40 - topPad) / totalDrawH;
    const fitScale = Math.min(1.0, fitScaleX, fitScaleY);

    brmCadView.scale = Math.max(0.22, fitScale);
    brmCadView.offsetX = Math.max(10, (canvasW - totalDrawW * brmCadView.scale) / 2);
    brmCadView.offsetY = Math.max(topPad + 6, (canvasH - totalDrawH * brmCadView.scale) / 2 + topPad / 2);
  } else {
    brmCadView.scale = 1.0;
    brmCadView.offsetX = 0;
    brmCadView.offsetY = 0;
  }
  brmCadView.isDragging = false;
  brmCadView.hasDragged = false;
  renderBeamDrawings();
}

window.focusActiveSpanCad = focusActiveSpanCad;

function renderBeamDrawings() {
  const canvas = document.getElementById('brmDrawingCanvas');
  if (!canvas || !selectedBeamForRebar) return;

  try {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const parentW = canvas.parentElement ? canvas.parentElement.clientWidth : 0;
    const parentH = canvas.parentElement ? canvas.parentElement.clientHeight : 0;
    const width = Math.max(rect.width || 0, parentW || 0, 800);
    const height = Math.max(rect.height || 0, parentH || 0, 480);

    if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
    }
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';

    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    // Subtle CAD engineering grid pattern (before zoom/pan for crisp reference)
    ctx.strokeStyle = '#f8fafc';
    ctx.lineWidth = 1;
    const gridStep = 20;
    ctx.beginPath();
    for (let x = 0; x <= width; x += gridStep) {
      ctx.moveTo(x, 0); ctx.lineTo(x, height);
    }
    for (let y = 0; y <= height; y += gridStep) {
      ctx.moveTo(0, y); ctx.lineTo(width, y);
    }
    ctx.stroke();

    // Apply Zoom & Pan Transform
    ctx.save();
    ctx.translate(brmCadView.offsetX, brmCadView.offsetY);
    ctx.scale(brmCadView.scale, brmCadView.scale);

    // Active beam & rebar selections
    const b = selectedBeamForRebar;
    const selL = document.getElementById('brmSelLeft');
    const selM = document.getElementById('brmSelMid');
    const selR = document.getElementById('brmSelRight');
    const selSt = document.getElementById('brmSelStirrup');

    const bDefCount = ((b.width || 200) >= 300) ? 3 : 2;
    const rebarTopL = selL && selL.selectedIndex >= 0 ? parseRebarSpec(selL.options[selL.selectedIndex].value, bDefCount, 18) : parseRebarSpec(b.rebar_top_left, bDefCount, 18);
    const rebarBotM = selM && selM.selectedIndex >= 0 ? parseRebarSpec(selM.options[selM.selectedIndex].value, bDefCount, 18) : parseRebarSpec(b.rebar_bot_mid, bDefCount, 18);
    const rebarTopR = selR && selR.selectedIndex >= 0 ? parseRebarSpec(selR.options[selR.selectedIndex].value, bDefCount, 18) : parseRebarSpec(b.rebar_top_right, bDefCount, 18);
    const stirrupSpec = selSt && selSt.selectedIndex >= 0 ? parseStirrupSpec(selSt.options[selSt.selectedIndex].value) : parseStirrupSpec(b.stirrup);

    const chainInfo = findContinuousBeamChain(b);

    if (beamDrawingMode === 'span') {
      drawSpanCadDrawing(ctx, width, height, b, chainInfo, rebarTopL, rebarBotM, rebarTopR, stirrupSpec);
    } else {
      drawChainCadDrawing(ctx, width, height, b, chainInfo);
    }

    try {
      const activeSvg = generateBeamCadSvg(b, chainInfo);
      window.activeBeamCadSvg = activeSvg;
      const svgContainer = document.getElementById('brmCadSvgContainer');
      if (svgContainer) {
        svgContainer.innerHTML = activeSvg;
      }
    } catch (eSvg) {
      console.warn('[SVG] Failed to generate live SVG:', eSvg);
    }

    ctx.restore(); // Restore Zoom & Pan
    ctx.restore(); // Restore DPR
    console.log(`[CAD] renderBeamDrawings: rendered ${b.label} in ${beamDrawingMode} mode (${width}x${height}, zoom=${brmCadView.scale.toFixed(2)})`);
  } catch (err) {
    console.error('[CAD Error] renderBeamDrawings failed:', err);
  }
}

// ------------------------------------------------------------------------------
// (5B) 3D REBAR SIMULATION ENGINE (PARAMETRIC & rebar.obj COMPATIBLE)
// ------------------------------------------------------------------------------
let brm3DScene = null;
let brm3DCamera = null;
let brm3DRenderer = null;
let brm3DControls = null;
let brm3DGroup = null;
let brm3DConcreteMesh = null;
let brm3DSourceMode = 'parametric'; // 'parametric' | 'obj'
let brm3DConcreteMode = 'translucent'; // 'translucent' | 'solid' | 'hidden'
let brm3DObjModel = null;
let brm3DIsLoadingObj = false;

function initBrm3D() {
  const container = document.getElementById('brm3DCanvas');
  if (!container || brm3DRenderer) return;

  const width = Math.max(container.clientWidth || 0, 700);
  const height = Math.max(container.clientHeight || 0, 480);

  brm3DScene = new THREE.Scene();
  brm3DScene.background = new THREE.Color(0xaaaaaa); // User requested gray #AAA

  // Lighting
  const ambLight = new THREE.AmbientLight(0xffffff, 0.75);
  brm3DScene.add(ambLight);

  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.85);
  dirLight1.position.set(5000, 10000, 7000);
  brm3DScene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.45);
  dirLight2.position.set(-5000, -6000, -5000);
  brm3DScene.add(dirLight2);

  // Camera
  brm3DCamera = new THREE.PerspectiveCamera(40, width / height, 10, 100000);
  brm3DCamera.position.set(1500, 2000, 5500);

  // WebGL Renderer
  brm3DRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
  brm3DRenderer.setPixelRatio(window.devicePixelRatio || 1);
  brm3DRenderer.setSize(width, height);
  container.innerHTML = '';
  container.appendChild(brm3DRenderer.domElement);

  // OrbitControls
  if (typeof THREE.OrbitControls === 'function') {
    brm3DControls = new THREE.OrbitControls(brm3DCamera, brm3DRenderer.domElement);
    brm3DControls.enableDamping = true;
    brm3DControls.dampingFactor = 0.08;
    brm3DControls.screenSpacePanning = true;
    brm3DControls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN
    };
    brm3DControls.target.set(0, 0, 0);
  }

  function animate() {
    requestAnimationFrame(animate);
    if (brm3DControls) brm3DControls.update();
    if (brm3DRenderer && brm3DScene && brm3DCamera) {
      brm3DRenderer.render(brm3DScene, brm3DCamera);
    }
  }
  animate();

  window.addEventListener('resize', () => {
    if (!brm3DCamera || !brm3DRenderer || !container) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w > 50 && h > 50) {
      brm3DCamera.aspect = w / h;
      brm3DCamera.updateProjectionMatrix();
      brm3DRenderer.setSize(w, h);
    }
  });
}

function createCylinderBetweenPoints(p1, p2, radius, material) {
  const v1 = new THREE.Vector3(p1.x, p1.y, p1.z);
  const v2 = new THREE.Vector3(p2.x, p2.y, p2.z);
  const distance = v1.distanceTo(v2);
  if (distance < 0.1) return null;

  const geom = new THREE.CylinderGeometry(radius, radius, distance, 12);
  const mesh = new THREE.Mesh(geom, material);

  // Midpoint
  mesh.position.addVectors(v1, v2).multiplyScalar(0.5);

  // Orient to vector
  const direction = new THREE.Vector3().subVectors(v2, v1).normalize();
  const up = new THREE.Vector3(0, 1, 0);
  mesh.quaternion.setFromUnitVectors(up, direction);

  return mesh;
}

function buildBeamRebar3D(beam) {
  if (!brm3DScene || !beam) return;

  // Clean previous parametric group
  if (brm3DGroup) {
    brm3DScene.remove(brm3DGroup);
    brm3DGroup.traverse(child => {
      if (child.isMesh) {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
          if (Array.isArray(child.material)) child.material.forEach(m => m.dispose());
          else child.material.dispose();
        }
      }
    });
    brm3DGroup = null;
  }

  brm3DGroup = new THREE.Group();
  brm3DScene.add(brm3DGroup);

  // 1. Trace Continuous Beam Chain (Mô phỏng 3D hết toàn bộ tuyến dầm dài liên tục)
  const chainInfo = findContinuousBeamChain(beam);
  const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [beam];
  const numSpans = chain.length;

  let currentAccumX = 0;
  const spansInfo = chain.map((b, idx) => {
    let bDepth = b.depth || 400;
    let bWidth = b.width || 200;
    if (b.section) {
      const sm = b.section.match(/(\d+)\s*[xX]\s*(\d+)/);
      if (sm) {
        bWidth = parseInt(sm[1], 10);
        bDepth = parseInt(sm[2], 10);
      }
    }
    let bLen = Math.round(b.length || 3000);
    const xStart = currentAccumX;
    const xEnd = xStart + bLen;
    currentAccumX = xEnd;
    return {
      beam: b,
      index: idx,
      length: bLen,
      width: bWidth,
      height: bDepth,
      xStart: xStart,
      xEnd: xEnd
    };
  });

  const TOTAL_L = currentAccumX;
  const BEAM_H = Math.max(...spansInfo.map(s => s.height));
  const BEAM_B = Math.max(...spansInfo.map(s => s.width));
  const COVER = 25; // Lớp bê tông bảo vệ chuẩn 25mm

  // Active beam selections from UI modal
  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const selL = document.getElementById('brmSelLeft');
  const selM = document.getElementById('brmSelMid');
  const selR = document.getElementById('brmSelRight');
  const selH = document.getElementById('brmSelHanger');
  const selSt = document.getElementById('brmSelStirrup');

  const defCount3D = (BEAM_B >= 300) ? 3 : 2;
  const rebarMainTop = selMainTop && selMainTop.selectedIndex >= 0 ? parseRebarSpec(selMainTop.options[selMainTop.selectedIndex].value, defCount3D, 18) : parseRebarSpec(beam.rebar_main_top || `${defCount3D}D18`, defCount3D, 18);
  const rebarMainBot = selMainBot && selMainBot.selectedIndex >= 0 ? parseRebarSpec(selMainBot.options[selMainBot.selectedIndex].value, defCount3D, 18) : parseRebarSpec(beam.rebar_main_bot || `${defCount3D}D18`, defCount3D, 18);
  const rebarTopL = selL && selL.selectedIndex >= 0 ? parseRebarSpec(selL.options[selL.selectedIndex].value, defCount3D, 18) : parseRebarSpec(beam.rebar_top_left, defCount3D, 18);
  const rebarBotM = selM && selM.selectedIndex >= 0 ? parseRebarSpec(selM.options[selM.selectedIndex].value, defCount3D, 18) : parseRebarSpec(beam.rebar_bot_mid, defCount3D, 18);
  const rebarTopR = selR && selR.selectedIndex >= 0 ? parseRebarSpec(selR.options[selR.selectedIndex].value, defCount3D, 18) : parseRebarSpec(beam.rebar_top_right, defCount3D, 18);
  const rebarHanger = selH && selH.selectedIndex >= 0 ? parseRebarSpec(selH.options[selH.selectedIndex].value, defCount3D, 16) : parseRebarSpec(beam.rebar_hanger || `${defCount3D}D16 (4.02cm²)`, defCount3D, 16);
  const stirrupSpec = selSt && selSt.selectedIndex >= 0 ? parseStirrupSpec(selSt.options[selSt.selectedIndex].value) : parseStirrupSpec(beam.stirrup || 'Φ6a100/a200');

  let STIRRUP_D = (typeof window !== 'undefined' && window.currentStirrupDiam) ? window.currentStirrupDiam : 6;
  const stMatch = (stirrupSpec.label || '').match(/(\d+)/);
  if (stMatch) STIRRUP_D = parseInt(stMatch[1], 10);

  // Offset to center entire continuous model at (0, 0, 0)
  const x_off = TOTAL_L / 2.0;
  const y_off = BEAM_H / 2.0;
  const z_off = BEAM_B / 2.0;

  function to3D(x, yWidth, zHeight) {
    return new THREE.Vector3(x - x_off, zHeight - y_off, yWidth - z_off);
  }

  // Bán kính uốn fillet giảm 50% (25mm -> 12.5mm)
  const FILLET_R = 12.5;

  function addFilletArc(xc, y, zc, rFillet, startAngle, endAngle, barRadius, material) {
    const sphereGeom = new THREE.SphereGeometry(barRadius, 8, 8);
    const segments = 8;
    for (let k = 0; k < segments; k++) {
      const a1 = startAngle + (endAngle - startAngle) * (k / segments);
      const a2 = startAngle + (endAngle - startAngle) * ((k + 1) / segments);
      const p1 = to3D(xc + rFillet * Math.cos(a1), y, zc + rFillet * Math.sin(a1));
      const p2 = to3D(xc + rFillet * Math.cos(a2), y, zc + rFillet * Math.sin(a2));

      const cyl = createCylinderBetweenPoints(p1, p2, barRadius, material);
      if (cyl) brm3DGroup.add(cyl);

      const sph = new THREE.Mesh(sphereGeom, material);
      sph.position.copy(p1);
      brm3DGroup.add(sph);
    }
    const pEnd = to3D(xc + rFillet * Math.cos(endAngle), y, zc + rFillet * Math.sin(endAngle));
    const sphEnd = new THREE.Mesh(sphereGeom, material);
    sphEnd.position.copy(pEnd);
    brm3DGroup.add(sphEnd);
  }

  // Materials - Màu sắc đồng bộ 100% với 2D CAD
  const matMainBot = new THREE.MeshPhongMaterial({
    color: 0x06b6d4, // Cyan - Thép chủ dưới chạy suốt
    specular: 0x888888,
    shininess: 45
  });

  const matHanger = new THREE.MeshPhongMaterial({
    color: 0x0284c7, // Blue/Cyan - Thép chủ/giá trên
    specular: 0x999999,
    shininess: 50
  });

  const matTopSupport = new THREE.MeshPhongMaterial({
    color: 0xc026d3, // Magenta - Thép tăng cường gối trên
    specular: 0x888888,
    shininess: 45
  });

  const matBotSupport = new THREE.MeshPhongMaterial({
    color: 0xc026d3, // Magenta - Thép tăng cường bụng dưới
    specular: 0x888888,
    shininess: 45
  });

  const matStirrup = new THREE.MeshPhongMaterial({
    color: 0x2864dc,
    specular: 0x888888,
    shininess: 45
  });

  const colBoxMat = new THREE.MeshPhongMaterial({
    color: 0x94a3b8,
    transparent: true,
    opacity: 0.5,
    depthWrite: false,
    side: THREE.DoubleSide
  });

  const colEdgesMat = new THREE.LineBasicMaterial({
    color: 0x334155,
    transparent: true,
    opacity: 0.65
  });

  const colBoxW = 400;
  const colBoxH = BEAM_H + 400;
  const colBoxD = Math.max(BEAM_B + 100, 400);

  const isX = chainInfo.isX;
  const hasCol = [];
  for (let idx = 0; idx <= numSpans; idx++) {
    hasCol.push(checkColumnAtSupport(chain, idx, isX));
  }

  // A. Concrete Spans for the Entire Continuous Beam (Chỉ phủ ra cạnh ngoài cột khi gối đó thực sự có cột)
  spansInfo.forEach((span, idx) => {
    const isActive = (span.beam.label === beam.label);
    let xSpanStart = span.xStart;
    let xSpanEnd = span.xEnd;
    if (idx === 0 && hasCol[0]) xSpanStart -= colBoxW / 2.0; // Phủ ra cạnh ngoài cột trái
    if (idx === numSpans - 1 && hasCol[numSpans]) xSpanEnd += colBoxW / 2.0; // Phủ ra cạnh ngoài cột phải
    const spanLen = xSpanEnd - xSpanStart;

    const boxGeom = new THREE.BoxGeometry(spanLen, span.height, span.width);
    const concreteMat = new THREE.MeshPhongMaterial({
      color: isActive ? (brm3DConcreteMode === 'translucent' ? 0xbaa898 : 0xdfd4c5) : 0xa5a5a0,
      transparent: (brm3DConcreteMode === 'translucent'),
      opacity: (brm3DConcreteMode === 'translucent' ? (isActive ? 0.40 : 0.22) : 1.0),
      depthWrite: (brm3DConcreteMode === 'solid'),
      side: THREE.DoubleSide
    });
    const spanMesh = new THREE.Mesh(boxGeom, concreteMat);
    const xMid = (xSpanStart + xSpanEnd) / 2.0;
    // Align Top: Mặt trên dầm phẳng bằng với sàn (cao độ BEAM_H)
    const zMid = BEAM_H - span.height / 2.0;
    spanMesh.position.set(xMid - x_off, zMid - y_off, (span.width / 2.0) - z_off);
    spanMesh.visible = (brm3DConcreteMode !== 'hidden');
    brm3DGroup.add(spanMesh);

    const edgesLine = new THREE.LineSegments(
      new THREE.EdgesGeometry(boxGeom),
      new THREE.LineBasicMaterial({
        color: isActive ? 0xd97706 : 0x475569, // Viền vàng nổi bật nhịp đang chọn
        transparent: true,
        opacity: isActive ? 0.95 : 0.45
      })
    );
    spanMesh.add(edgesLine);
  });

  // A2. Support Columns at All Joints & 3D Grid Axes with Grid Bubbles
  const colPositions = [spansInfo[0].xStart];
  spansInfo.forEach(s => colPositions.push(s.xEnd));

  colPositions.forEach((colX, idx) => {
    if (!hasCol[idx]) return; // BỎ QUA NẾU VỊ TRÍ NÀY KHÔNG CÓ CỘT

    const colGeom = new THREE.BoxGeometry(colBoxW, colBoxH, colBoxD);
    const colMesh = new THREE.Mesh(colGeom, colBoxMat);
    colMesh.position.set(colX - x_off, 0, (BEAM_B / 2.0) - z_off);
    brm3DGroup.add(colMesh);
    colMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(colGeom), colEdgesMat));

    // (1) 3D Grid Axis & Grid Bubble above column
    let gridLabel;
    if (idx < numSpans) {
      const coord = isX ? Math.min(chain[idx].p1[0], chain[idx].p2[0]) : Math.min(chain[idx].p1[1], chain[idx].p2[1]);
      gridLabel = getGridBubbleLabel(coord, isX) || (idx + 1);
    } else {
      const coord = isX ? Math.max(chain[numSpans - 1].p1[0], chain[numSpans - 1].p2[0]) : Math.max(chain[numSpans - 1].p1[1], chain[numSpans - 1].p2[1]);
      gridLabel = getGridBubbleLabel(coord, isX) || (numSpans + 1);
    }

    // Vertical dashed grid guideline through column axis
    const pBot = to3D(colX, BEAM_B / 2.0, -400);
    const pTop = to3D(colX, BEAM_B / 2.0, BEAM_H + 820);
    const vertGeom = new THREE.BufferGeometry().setFromPoints([pBot, pTop]);
    const vertLine = new THREE.Line(
      vertGeom,
      new THREE.LineDashedMaterial({ color: 0x0284c7, dashSize: 50, gapSize: 25, transparent: true, opacity: 0.70 })
    );
    vertLine.computeLineDistances();
    brm3DGroup.add(vertLine);

    // Horizontal transverse grid line across beam width
    const pTrans1 = to3D(colX, -500, BEAM_H + 200);
    const pTrans2 = to3D(colX, BEAM_B + 500, BEAM_H + 200);
    const transGeom = new THREE.BufferGeometry().setFromPoints([pTrans1, pTrans2]);
    const transLine = new THREE.Line(
      transGeom,
      new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.60 })
    );
    brm3DGroup.add(transLine);

    // 3D Billboard Grid Bubble Sprite (luôn hướng về camera, move Y 300mm lên cao)
    const bubble = createTextBubbleSprite(String(gridLabel), 'transparent', '#0f172a', '#0284c7');
    bubble.scale.set(450, 450, 1);
    bubble.position.copy(to3D(colX, BEAM_B / 2.0, BEAM_H + 820));
    brm3DGroup.add(bubble);
  });

  // B. Continuous Bottom Longitudinal Main Rebar: Chia thành các segment chung nhau các đỉnh liên tiếp
  // Vị trí các đỉnh là giao điểm thanh thép với 2 cạnh dầm theo mặt cắt dọc,
  // khi chiều cao dầm thay đổi qua các trục thì thép chủ dưới tự động đổi cao độ tương xứng với tiết diện dầm
  const MAIN_BOT_D = rebarMainBot.diam || 18;
  const N_BOT = (BEAM_B >= 300) ? Math.max(3, rebarMainBot.count || 3) : Math.max(1, rebarMainBot.count || 2);
  const hookH = Math.min(260, BEAM_H - COVER * 2 - STIRRUP_D * 2);

  // Mở rộng thép chủ dưới về mỗi bên 50mm nếu có cột ngoài cùng
  const x1_base = (hasCol[0] ? -colBoxW / 2.0 : 0) + COVER + STIRRUP_D + MAIN_BOT_D / 2.0;
  const x2_base = TOTAL_L + (hasCol[numSpans] ? colBoxW / 2.0 : 0) - (COVER + STIRRUP_D + MAIN_BOT_D / 2.0);
  const x1_bot = x1_base + (hasCol[0] ? 50 : 0);
  const x2_bot = x2_base - (hasCol[numSpans] ? 50 : 0);

  // Cao độ đáy thép chủ dưới theo tiết diện từng nhịp dầm (Align Top tại BEAM_H)
  const zBotSpans = spansInfo.map(s => (BEAM_H - s.height) + COVER + STIRRUP_D + MAIN_BOT_D / 2.0);

  const botYPos = [];
  const yMinBot = COVER + STIRRUP_D + MAIN_BOT_D / 2.0;
  const yMaxBot = BEAM_B - COVER - STIRRUP_D - MAIN_BOT_D / 2.0;
  if (N_BOT === 1) {
    botYPos.push(BEAM_B / 2.0);
  } else {
    const stepY = (yMaxBot - yMinBot) / (N_BOT - 1);
    for (let i = 0; i < N_BOT; i++) {
      botYPos.push(yMinBot + i * stepY);
    }
  }

  const barR_bot = MAIN_BOT_D / 2.0;
  botYPos.forEach(y => {
    // Xây dựng danh sách các đỉnh (vertices) liên tiếp của thanh thép dọc đáy
    const vertices = [];
    const zBot0 = zBotSpans[0];
    vertices.push({ x: x1_bot + FILLET_R, z: zBot0 });

    for (let i = 0; i < numSpans; i++) {
      const curSpan = spansInfo[i];
      const zBotCur = zBotSpans[i];
      const xLeft = (i === 0) ? (x1_bot + FILLET_R) : (curSpan.xStart + colBoxW / 4.0);
      const xRight = (i === numSpans - 1) ? (x2_bot - FILLET_R) : (curSpan.xEnd - colBoxW / 4.0);

      if (i > 0) {
        vertices.push({ x: xLeft, z: zBotCur });
      }
      vertices.push({ x: xRight, z: zBotCur });
    }

    // Vẽ các segment hình trụ nối tiếp nhau giữa các đỉnh chung
    for (let v = 0; v < vertices.length - 1; v++) {
      const pA = to3D(vertices[v].x, y, vertices[v].z);
      const pB = to3D(vertices[v + 1].x, y, vertices[v + 1].z);
      const segMesh = createCylinderBetweenPoints(pA, pB, barR_bot, matMainBot);
      if (segMesh) brm3DGroup.add(segMesh);

      const jointSph = new THREE.Mesh(new THREE.SphereGeometry(barR_bot, 8, 8), matMainBot);
      jointSph.position.copy(pB);
      brm3DGroup.add(jointSph);
    }

    // Móc neo 90° đầu trái ngoài cùng
    addFilletArc(x1_bot + FILLET_R, y, zBot0 + FILLET_R, FILLET_R, Math.PI, 1.5 * Math.PI, barR_bot, matMainBot);
    const hookL = createCylinderBetweenPoints(
      to3D(x1_bot, y, zBot0 + FILLET_R),
      to3D(x1_bot, y, zBot0 + hookH),
      barR_bot,
      matMainBot
    );
    if (hookL) brm3DGroup.add(hookL);
    const tipBotL = createCylinderBetweenPoints(
      to3D(x1_bot, y, zBot0 + hookH),
      to3D(x1_bot + 22, y, zBot0 + hookH - 22),
      barR_bot,
      matMainBot
    );
    if (tipBotL) brm3DGroup.add(tipBotL);

    // Móc neo 90° đầu phải ngoài cùng
    const zBotLast = zBotSpans[numSpans - 1];
    addFilletArc(x2_bot - FILLET_R, y, zBotLast + FILLET_R, FILLET_R, 1.5 * Math.PI, 2 * Math.PI, barR_bot, matMainBot);
    const hookR = createCylinderBetweenPoints(
      to3D(x2_bot, y, zBotLast + FILLET_R),
      to3D(x2_bot, y, zBotLast + hookH),
      barR_bot,
      matMainBot
    );
    if (hookR) brm3DGroup.add(hookR);
    const tipBotR = createCylinderBetweenPoints(
      to3D(x2_bot, y, zBotLast + hookH),
      to3D(x2_bot - 22, y, zBotLast + hookH - 22),
      barR_bot,
      matMainBot
    );
    if (tipBotR) brm3DGroup.add(tipBotR);
  });

  // C. Top Main Rebar Running Across Entire Continuous Chain
  const TOP_MAIN_D = rebarMainTop.diam || 18;
  const topZ = BEAM_H - COVER - STIRRUP_D - TOP_MAIN_D / 2.0;
  const yH1 = COVER + STIRRUP_D + TOP_MAIN_D / 2.0;
  const yH2 = BEAM_B - COVER - STIRRUP_D - TOP_MAIN_D / 2.0;
  const numTopMain = (BEAM_B >= 300) ? Math.max(3, rebarMainTop.count || 3) : (rebarMainTop.count || 2);
  const hangerYPos = [];
  if (numTopMain === 1) {
    hangerYPos.push(BEAM_B / 2.0);
  } else {
    const stepY = (yH2 - yH1) / (numTopMain - 1);
    for (let i = 0; i < numTopMain; i++) {
      hangerYPos.push(yH1 + i * stepY);
    }
  }
  const barR_top = TOP_MAIN_D / 2.0;

  const x1_top = (hasCol[0] ? -colBoxW / 2.0 : 0) + COVER + STIRRUP_D + TOP_MAIN_D / 2.0;
  const x2_top = TOTAL_L + (hasCol[numSpans] ? colBoxW / 2.0 : 0) - (COVER + STIRRUP_D + TOP_MAIN_D / 2.0);

  hangerYPos.forEach(y => {
    // 1. Thanh chạy suốt ngang qua toàn bộ chuỗi dầm
    const hangerMesh = createCylinderBetweenPoints(
      to3D(x1_top + FILLET_R, y, topZ),
      to3D(x2_top - FILLET_R, y, topZ),
      barR_top,
      matHanger
    );
    if (hangerMesh) brm3DGroup.add(hangerMesh);

    // 2. Góc fillet bên trái ngoài cùng
    addFilletArc(x1_top + FILLET_R, y, topZ - FILLET_R, FILLET_R, Math.PI, 0.5 * Math.PI, barR_top, matHanger);

    // 3. Móc neo thẳng đứng cắm xuống bên trái
    const hookL = createCylinderBetweenPoints(
      to3D(x1_top, y, topZ - hookH),
      to3D(x1_top, y, topZ - FILLET_R),
      barR_top,
      matHanger
    );
    if (hookL) brm3DGroup.add(hookL);

    // Mỏ vát 45° bẻ vào trong (22mm)
    const tipTopL = createCylinderBetweenPoints(
      to3D(x1_top, y, topZ - hookH),
      to3D(x1_top + 22, y, topZ - hookH + 22),
      barR_top,
      matHanger
    );
    if (tipTopL) brm3DGroup.add(tipTopL);

    // 4. Góc fillet bên phải ngoài cùng
    addFilletArc(x2_top - FILLET_R, y, topZ - FILLET_R, FILLET_R, 0.5 * Math.PI, 0, barR_top, matHanger);

    // 5. Móc neo thẳng đứng cắm xuống bên phải
    const hookR = createCylinderBetweenPoints(
      to3D(x2_top, y, topZ - FILLET_R),
      to3D(x2_top, y, topZ - hookH),
      barR_top,
      matHanger
    );
    if (hookR) brm3DGroup.add(hookR);

    // Mỏ vát 45° bẻ vào trong (22mm)
    const tipTopR = createCylinderBetweenPoints(
      to3D(x2_top, y, topZ - hookH),
      to3D(x2_top - 22, y, topZ - hookH + 22),
      barR_top,
      matHanger
    );
    if (tipTopR) brm3DGroup.add(tipTopR);
  });

  // D. Top Support Rebars (Thép gối trên - Moment âm: 2 thanh ở Lớp 2 nhích xuống)
  const topZ_supp = topZ - (HANGER_D + 8);
  const topSuppYPos = [COVER + STIRRUP_D + 10, BEAM_B - COVER - STIRRUP_D - 10];

  topSuppYPos.forEach(yTopSupp => {
    // D1. Gối trái ngoài cùng (Cột 0): Nếu nhịp đầu < 2000 thì đi suốt luôn không ngắt nhỏ
    const span0IsShort = (spansInfo[0].length < 2000);
    const lQuarter0 = span0IsShort ? spansInfo[0].length : spansInfo[0].length * 0.25;
    const rebarTop0 = (spansInfo[0].beam.label === beam.label && selL && selL.selectedIndex >= 0) ? parseRebarSpec(selL.options[selL.selectedIndex].value, defCount3D, 18) : parseRebarSpec(spansInfo[0].beam.rebar_top_left, defCount3D, 18);
    const extraTop0 = Math.max(2, rebarTop0.count || 2);

    if (span0IsShort || extraTop0 > 0) {
      const topL_D = rebarTop0.diam || 18;
      const barR_suppL = topL_D / 2.0;
      const barL = createCylinderBetweenPoints(
        to3D(x1_top + FILLET_R, yTopSupp, topZ_supp),
        to3D(x1_top + lQuarter0, yTopSupp, topZ_supp),
        barR_suppL,
        matTopSupport
      );
      if (barL) brm3DGroup.add(barL);

      addFilletArc(x1_top + FILLET_R, yTopSupp, topZ_supp - FILLET_R, FILLET_R, Math.PI, 0.5 * Math.PI, barR_suppL, matTopSupport);

      const hookColL = createCylinderBetweenPoints(
        to3D(x1_top, yTopSupp, topZ_supp - hookH * 0.8),
        to3D(x1_top, yTopSupp, topZ_supp - FILLET_R),
        barR_suppL,
        matTopSupport
      );
      if (hookColL) brm3DGroup.add(hookColL);

      if (!span0IsShort) {
        // Mỏ vát xiên 45° chúc xuống bẻ vào trong (35mm)
        const slantL = createCylinderBetweenPoints(
          to3D(x1_top + lQuarter0, yTopSupp, topZ_supp),
          to3D(x1_top + lQuarter0 - 35, yTopSupp, topZ_supp - 35),
          barR_suppL,
          matTopSupport
        );
        if (slantL) brm3DGroup.add(slantL);
      }
    }

    // D2. Các gối giữa (Intermediate Supports k = 1 to numSpans - 1):
    // Nếu nhịp k hoặc nhịp k-1 < 2000, thép tăng cường lưng đi suốt không ngắt
    for (let k = 1; k < numSpans; k++) {
      const colX = spansInfo[k].xStart;
      const prevSpan = spansInfo[k - 1];
      const nextSpan = spansInfo[k];
      const prevIsShort = (prevSpan.length < 2000);
      const nextIsShort = (nextSpan.length < 2000);

      const xMidSuppL = prevIsShort ? (prevSpan.xStart + (hasCol[k - 1] ? 0 : (COVER + STIRRUP_D))) : (colX - prevSpan.length * 0.25);
      const xMidSuppR = nextIsShort ? (nextSpan.xEnd - (hasCol[k + 1] ? 0 : (COVER + STIRRUP_D))) : (colX + nextSpan.length * 0.25);
      const suppDiam = 18;
      const suppR = suppDiam / 2.0;

      // Thanh nằm ngang chạy qua gối
      const barMid = createCylinderBetweenPoints(
        to3D(xMidSuppL, yTopSupp, topZ_supp),
        to3D(xMidSuppR, yTopSupp, topZ_supp),
        suppR,
        matTopSupport
      );
      if (barMid) brm3DGroup.add(barMid);

      if (!prevIsShort) {
        // Mỏ vát xiên 45° chúc xuống đầu trái bẻ vào trong (35mm)
        const slantMidL = createCylinderBetweenPoints(
          to3D(xMidSuppL, yTopSupp, topZ_supp),
          to3D(xMidSuppL + 35, yTopSupp, topZ_supp - 35),
          suppR,
          matTopSupport
        );
        if (slantMidL) brm3DGroup.add(slantMidL);
      }

      if (!nextIsShort) {
        // Mỏ vát xiên 45° chúc xuống đầu phải bẻ vào trong (35mm)
        const slantMidR = createCylinderBetweenPoints(
          to3D(xMidSuppR, yTopSupp, topZ_supp),
          to3D(xMidSuppR - 35, yTopSupp, topZ_supp - 35),
          suppR,
          matTopSupport
        );
        if (slantMidR) brm3DGroup.add(slantMidR);
      } else if (k === numSpans - 1 && !hasCol[numSpans]) {
        // Cắm móc neo xuống tại đầu dầm console nhịp ngắn ngoài cùng
        const hookTip = createCylinderBetweenPoints(
          to3D(xMidSuppR, yTopSupp, topZ_supp - hookH * 0.8),
          to3D(xMidSuppR, yTopSupp, topZ_supp),
          suppR,
          matTopSupport
        );
        if (hookTip) brm3DGroup.add(hookTip);
      }
    }

    // D3. Gối phải ngoài cùng (Cột N): Chỉ vẽ khi nhịp cuối >= 2000 (nếu < 2000 thì D2 đã phủ suốt nhịp)
    const spanLastIsShort = (spansInfo[numSpans - 1].length < 2000);
    const rebarTopLast = (spansInfo[numSpans - 1].beam.label === beam.label && selR && selR.selectedIndex >= 0) ? parseRebarSpec(selR.options[selR.selectedIndex].value, defCount3D, 18) : parseRebarSpec(spansInfo[numSpans - 1].beam.rebar_top_right, defCount3D, 18);
    const extraTopLast = Math.max(2, rebarTopLast.count || 2);

    if (!spanLastIsShort && extraTopLast > 0) {
      const lQuarterLast = spansInfo[numSpans - 1].length * 0.25;
      const topR_D = rebarTopLast.diam || 18;
      const barR_suppR = topR_D / 2.0;
      const barR = createCylinderBetweenPoints(
        to3D(x2_top - lQuarterLast, yTopSupp, topZ_supp),
        to3D(x2_top - FILLET_R, yTopSupp, topZ_supp),
        barR_suppR,
        matTopSupport
      );
      if (barR) brm3DGroup.add(barR);

      addFilletArc(x2_top - FILLET_R, yTopSupp, topZ_supp - FILLET_R, FILLET_R, 0.5 * Math.PI, 0, barR_suppR, matTopSupport);

      const hookColR = createCylinderBetweenPoints(
        to3D(x2_top, yTopSupp, topZ_supp - FILLET_R),
        to3D(x2_top, yTopSupp, topZ_supp - hookH * 0.8),
        barR_suppR,
        matTopSupport
      );
      if (hookColR) brm3DGroup.add(hookColR);

      // Mỏ vát xiên 45° chúc xuống bẻ vào trong (35mm)
      const slantR = createCylinderBetweenPoints(
        to3D(x2_top - lQuarterLast, yTopSupp, topZ_supp),
        to3D(x2_top - lQuarterLast + 35, yTopSupp, topZ_supp - 35),
        barR_suppR,
        matTopSupport
      );
      if (slantR) brm3DGroup.add(slantR);
    }
  });

  // E. Bottom Support Rebars (Thép bụng dưới: 2 thanh ở Lớp 2 nhích lên)
  // (1) Với đoạn dầm < 2000 thì không đặt thép tăng cường bụng!
  // (2) Thép tăng cường bụng luôn có 2 thanh, màu hồng #c026d3
  const botSuppYPos = [COVER + STIRRUP_D + 10, BEAM_B - COVER - STIRRUP_D - 10];
  spansInfo.forEach((span, sIdx) => {
    if (span.length < 2000) return; // BỎ QUA HOÀN TOÀN KHI NHỊP < 2000
    const isActive = (span.beam.label === beam.label);
    const rebarBot = (isActive && selM && selM.selectedIndex >= 0) ? parseRebarSpec(selM.options[selM.selectedIndex].value, defCount3D, 18) : parseRebarSpec(span.beam.rebar_bot_mid, defCount3D, 18);
    const minMainB = (span.width >= 300) ? 3 : 2;
    const extraBotCount = Math.max(2, rebarBot.count || 2);
    if (extraBotCount <= 0) return; // BỎ QUA NẾU KHÔNG CÓ THÉP TĂNG CƯỜNG BỤNG!

    const botExtraDiam3D = rebarBot.diam || 18;
    const zBotSupp = zBotSpans[sIdx] + MAIN_BOT_D + 10;
    const xBotSpan1 = span.xStart + span.length * 0.15;
    const xBotSpan2 = span.xEnd - span.length * 0.15;

    botSuppYPos.forEach(yBotSupp => {
      const barBotSupp = createCylinderBetweenPoints(
        to3D(xBotSpan1, yBotSupp, zBotSupp),
        to3D(xBotSpan2, yBotSupp, zBotSupp),
        botExtraDiam3D / 2.0,
        matBotSupport
      );
      if (barBotSupp) brm3DGroup.add(barBotSupp);

      // Mỏ vát 45° chúc lên bẻ vào trong đầu trái (30mm)
      const slantBotL = createCylinderBetweenPoints(
        to3D(xBotSpan1, yBotSupp, zBotSupp),
        to3D(xBotSpan1 + 30, yBotSupp, zBotSupp + 30),
        botExtraDiam3D / 2.0,
        matBotSupport
      );
      if (slantBotL) brm3DGroup.add(slantBotL);

      // Mỏ vát 45° chúc lên bẻ vào trong đầu phải (30mm)
      const slantBotR = createCylinderBetweenPoints(
        to3D(xBotSpan2, yBotSupp, zBotSupp),
        to3D(xBotSpan2 - 30, yBotSupp, zBotSupp + 30),
        botExtraDiam3D / 2.0,
        matBotSupport
      );
      if (slantBotR) brm3DGroup.add(slantBotR);
    });
  });

  // F. Skin Rebar when H >= 700 cho các nhịp dầm cao
  spansInfo.forEach(span => {
    if (span.height >= 700) {
      const matSkin = new THREE.MeshPhongMaterial({
        color: 0xa21caf,
        specular: 0x888888,
        shininess: 45
      });
      const zMid = BEAM_H - span.height / 2.0;
      const ySkin1 = COVER + STIRRUP_D / 2.0 + 6;
      const ySkin2 = span.width - COVER - STIRRUP_D / 2.0 - 6;

      [ySkin1, ySkin2].forEach(yS => {
        const skinBar = createCylinderBetweenPoints(
          to3D(span.xStart + 30, yS, zMid),
          to3D(span.xEnd - 30, yS, zMid),
          6,
          matSkin
        );
        if (skinBar) brm3DGroup.add(skinBar);

        const skinHookL = createCylinderBetweenPoints(
          to3D(span.xStart + 30, yS, zMid),
          to3D(span.xStart + 30 + 40, yS, zMid + 40),
          6,
          matSkin
        );
        if (skinHookL) brm3DGroup.add(skinHookL);

        const skinHookR = createCylinderBetweenPoints(
          to3D(span.xEnd - 30, yS, zMid),
          to3D(span.xEnd - 30 - 40, yS, zMid + 40),
          6,
          matSkin
        );
        if (skinHookR) brm3DGroup.add(skinHookR);
      });
    }
  });

  // G. Closed Rectangular Stirrups for Each Span (Ôm khít chiều cao từng nhịp)
  const HOOK_L = 100;
  const z2_st = BEAM_H - COVER - STIRRUP_D / 2.0; // Align Top

  spansInfo.forEach((span, sIdx) => {
    const z1_st = (BEAM_H - span.height) + COVER + STIRRUP_D / 2.0;
    const y1_st = (BEAM_B - span.width) / 2.0 + COVER + STIRRUP_D / 2.0;
    const y2_st = (BEAM_B + span.width) / 2.0 - COVER - STIRRUP_D / 2.0;

    const endZone = Math.min(1200, span.length * 0.25);
    const startX = span.xStart + COVER + STIRRUP_D / 2.0 + 10;
    const maxX = span.xEnd - COVER - STIRRUP_D / 2.0 - 10;
    let currX = startX;

    while (currX <= maxX) {
      const p1 = to3D(currX, y1_st, z1_st);
      const p2 = to3D(currX, y2_st, z1_st);
      const p3 = to3D(currX, y2_st, z2_st);
      const p4 = to3D(currX, y1_st, z2_st);

      const legBot = createCylinderBetweenPoints(p1, p2, STIRRUP_D / 2.0, matStirrup);
      const legRight = createCylinderBetweenPoints(p2, p3, STIRRUP_D / 2.0, matStirrup);
      const legTop = createCylinderBetweenPoints(p3, p4, STIRRUP_D / 2.0, matStirrup);
      const legLeft = createCylinderBetweenPoints(p4, p1, STIRRUP_D / 2.0, matStirrup);

      if (legBot) brm3DGroup.add(legBot);
      if (legRight) brm3DGroup.add(legRight);
      if (legTop) brm3DGroup.add(legTop);
      if (legLeft) brm3DGroup.add(legLeft);

      // 2 móc bẻ xéo 135° NẰM CÙNG 1 BÊN - TẤT CẢ Ở BÊN TRÁI
      const dx1 = -STIRRUP_D * 0.45;
      const dx2 =  STIRRUP_D * 0.45;
      const hStart1 = to3D(currX + dx1, y1_st, z2_st);
      const hEnd1   = to3D(currX + dx1, y1_st + HOOK_L * 0.707, z2_st - HOOK_L * 0.707);
      const hStart2 = to3D(currX + dx2, y1_st, z2_st);
      const hEnd2   = to3D(currX + dx2, y1_st + HOOK_L * 0.707, z2_st - HOOK_L * 0.707);

      const hook1 = createCylinderBetweenPoints(hStart1, hEnd1, STIRRUP_D / 2.0, matStirrup);
      const hook2 = createCylinderBetweenPoints(hStart2, hEnd2, STIRRUP_D / 2.0, matStirrup);

      if (hook1) brm3DGroup.add(hook1);
      if (hook2) brm3DGroup.add(hook2);

      // Bước đai: vùng dày a100 gần 2 gối, vùng giữa a200
      if ((currX - span.xStart) < endZone || (span.xEnd - currX) < endZone) {
        currX += 100;
      } else {
        currX += 200;
      }
    }
  });

  // Fit camera framing to entire continuous chain
  if (brm3DCamera && brm3DControls) {
    brm3DCamera.position.set(TOTAL_L * 0.12, BEAM_H * 2.5 + 400, TOTAL_L * 0.70);
    brm3DControls.target.set(0, 0, 0);
    brm3DControls.update();
  }
}

function loadOriginalObjModel() {
  if (brm3DIsLoadingObj) return;
  brm3DIsLoadingObj = true;

  const labelEl = document.getElementById('brmSourceLabel');
  if (labelEl) labelEl.textContent = '⏳ Đang nạp rebar.obj...';

  function onObjLoaded(obj) {
    brm3DObjModel = obj;
    brm3DObjModel.traverse(child => {
      if (child.isMesh && child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        mats.forEach(m => {
          if (m.name && m.name.includes('Be_tong')) {
            m.transparent = (brm3DConcreteMode === 'translucent');
            m.opacity = (brm3DConcreteMode === 'translucent' ? 0.35 : 1.0);
            m.depthWrite = (brm3DConcreteMode === 'solid');
            m.side = THREE.DoubleSide;
            if (brm3DConcreteMode === 'hidden') child.visible = false;
          }
        });
      }
    });

    const box = new THREE.Box3().setFromObject(brm3DObjModel);
    const center = box.getCenter(new THREE.Vector3());
    brm3DObjModel.position.sub(center);

    brm3DScene.add(brm3DObjModel);
    brm3DIsLoadingObj = false;

    if (brm3DSourceMode === 'obj') {
      if (brm3DGroup) brm3DGroup.visible = false;
      brm3DObjModel.visible = true;
      if (labelEl) labelEl.textContent = '⬅ Về Dầm Đang Chọn';
      if (brm3DCamera && brm3DControls) {
        brm3DCamera.position.set(1200, 1800, 6000);
        brm3DControls.target.set(0, 0, 0);
        brm3DControls.update();
      }
    }
  }

  if (typeof THREE.MTLLoader === 'function' && typeof THREE.OBJLoader === 'function') {
    const mtlLoader = new THREE.MTLLoader();
    mtlLoader.load('/rebar.mtl', materials => {
      materials.preload();
      const objLoader = new THREE.OBJLoader();
      objLoader.setMaterials(materials);
      objLoader.load('/rebar.obj', onObjLoaded, undefined, err => {
        console.error('[3D Rebar] Error loading rebar.obj:', err);
        brm3DIsLoadingObj = false;
        if (labelEl) labelEl.textContent = 'Lỗi nạp OBJ';
      });
    }, undefined, err => {
      console.warn('[3D Rebar] MTLLoader error, falling back to basic OBJLoader:', err);
      const objLoader = new THREE.OBJLoader();
      objLoader.load('/rebar.obj', onObjLoaded, undefined, err2 => {
        console.error('[3D Rebar] OBJLoader fallback error:', err2);
        brm3DIsLoadingObj = false;
        if (labelEl) labelEl.textContent = 'Lỗi nạp OBJ';
      });
    });
  } else {
    console.error('[3D Rebar] MTLLoader or OBJLoader is not available on window.THREE');
    brm3DIsLoadingObj = false;
    if (labelEl) labelEl.textContent = 'Thiếu OBJLoader';
  }
}

function toggleBrm3DSource() {
  const labelEl = document.getElementById('brmSourceLabel');
  if (brm3DSourceMode === 'parametric') {
    brm3DSourceMode = 'obj';
    if (brm3DGroup) brm3DGroup.visible = false;
    if (brm3DObjModel) {
      brm3DObjModel.visible = true;
      if (labelEl) labelEl.textContent = '⬅ Về Dầm Đang Chọn';
      if (brm3DCamera && brm3DControls) {
        brm3DCamera.position.set(1200, 1800, 6000);
        brm3DControls.target.set(0, 0, 0);
        brm3DControls.update();
      }
    } else {
      loadOriginalObjModel();
    }
  } else {
    brm3DSourceMode = 'parametric';
    if (labelEl) labelEl.textContent = 'Xem rebar.obj (300x700)';
    if (brm3DObjModel) brm3DObjModel.visible = false;
    if (brm3DGroup) brm3DGroup.visible = true;
    resetBrm3DCamera();
  }
}

function toggleBrm3DConcrete() {
  const btn = document.getElementById('btnBrmConcreteToggle');
  if (brm3DConcreteMode === 'translucent') {
    brm3DConcreteMode = 'solid';
    if (btn) btn.textContent = 'Bê tông: Đặc (Solid)';
  } else if (brm3DConcreteMode === 'solid') {
    brm3DConcreteMode = 'hidden';
    if (btn) btn.textContent = 'Bê tông: Ẩn (Chỉ cốt thép)';
  } else {
    brm3DConcreteMode = 'translucent';
    if (btn) btn.textContent = 'Bê tông: Bán trong suốt';
  }

  if (brm3DConcreteMesh) {
    if (brm3DConcreteMode === 'hidden') {
      brm3DConcreteMesh.visible = false;
    } else {
      brm3DConcreteMesh.visible = true;
      brm3DConcreteMesh.material.transparent = (brm3DConcreteMode === 'translucent');
      brm3DConcreteMesh.material.opacity = (brm3DConcreteMode === 'translucent' ? 0.35 : 1.0);
      brm3DConcreteMesh.material.depthWrite = (brm3DConcreteMode === 'solid');
      brm3DConcreteMesh.material.needsUpdate = true;
    }
  }

  if (brm3DObjModel) {
    brm3DObjModel.traverse(child => {
      if (child.isMesh && child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        mats.forEach(m => {
          if (m.name && m.name.includes('Be_tong')) {
            if (brm3DConcreteMode === 'hidden') {
              child.visible = false;
            } else {
              child.visible = true;
              m.transparent = (brm3DConcreteMode === 'translucent');
              m.opacity = (brm3DConcreteMode === 'translucent' ? 0.35 : 1.0);
              m.depthWrite = (brm3DConcreteMode === 'solid');
              m.needsUpdate = true;
            }
          }
        });
      }
    });
  }
}

function resetBrm3DCamera() {
  if (!brm3DCamera || !brm3DControls) return;
  const b = selectedBeamForRebar;
  let len = 8400;
  let h = 700;
  if (brm3DSourceMode === 'parametric' && b) {
    const chainInfo = findContinuousBeamChain(b);
    const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [b];
    len = chain.reduce((sum, item) => sum + Math.max(1000, item.length || 4000), 0);
    const sm = (b.section || '').match(/(\d+)\s*[xX]\s*(\d+)/);
    if (sm) h = parseInt(sm[2], 10);
  }
  brm3DCamera.position.set(len * 0.12, h * 2.5 + 400, len * 0.70);
  brm3DControls.target.set(0, 0, 0);
  brm3DControls.update();
}

function renderBeam3DRebar() {
  if (!selectedBeamForRebar) return;
  initBrm3D();
  if (brm3DRenderer && brm3DCamera) {
    const container = document.getElementById('brm3DCanvas');
    if (container) {
      const w = Math.max(container.clientWidth || 0, 700);
      const h = Math.max(container.clientHeight || 0, 480);
      brm3DCamera.aspect = w / h;
      brm3DCamera.updateProjectionMatrix();
      brm3DRenderer.setSize(w, h);
    }
  }

  if (brm3DSourceMode === 'parametric') {
    if (brm3DObjModel) brm3DObjModel.visible = false;
    buildBeamRebar3D(selectedBeamForRebar);
  } else {
    if (brm3DGroup) brm3DGroup.visible = false;
    if (brm3DObjModel) {
      brm3DObjModel.visible = true;
    } else {
      loadOriginalObjModel();
    }
  }
}

function openBeamRebarModal(b) {
  selectedBeamForRebar = b;
  const modal = document.getElementById('beamRebarModal');
  if (!modal) return;

  // Reset zoom & pan to fresh fit view on beam switch
  brmCadView.scale = 1.0;
  brmCadView.offsetX = 0;
  brmCadView.offsetY = 0;
  brmCadView.isDragging = false;
  brmCadView.hasDragged = false;
  updateDbStatusBadges();

  const { mLeft, mMid, mRight } = calculateBeamMoments(b);

  // Trace continuous beam chain
  const chainInfo = findContinuousBeamChain(b);
  const chain = chainInfo.chain || [b];

  const axisBadge = document.getElementById('brmGridAxisText');
  if (axisBadge) axisBadge.textContent = chainInfo.axisName;

  const chainBadge = document.getElementById('brmChainCountBadge');
  if (chainBadge) chainBadge.textContent = `${chain.length} nhịp`;

  // Set Info
  const spanStr = b.spanIndex ? ` (Nhịp ${b.spanIndex}/${b.spanCount || chain.length})` : '';
  document.getElementById('brmBeamName').textContent = `${b.longBeamId || b.label}${spanStr}`;
  document.getElementById('brmStory').textContent = formatStoryLabel(b.story);
  document.getElementById('brmSection').textContent = b.section;
  document.getElementById('brmLength').textContent = `${(b.length/1000).toFixed(2)} m`;

  // Populate Continuous Breadcrumbs Bar
  const breadcrumbContainer = document.getElementById('brmChainBreadcrumbs');
  if (breadcrumbContainer) {
    breadcrumbContainer.innerHTML = '';
    
    // Axis indicator
    const axisPill = document.createElement('span');
    axisPill.className = 'px-2 py-0.5 rounded-lg bg-amber-100 text-amber-900 font-extrabold text-[11px] border border-amber-300 mr-1 flex items-center gap-1 shrink-0';
    axisPill.innerHTML = `📍 Dầm dài ${b.longBeamId || b.label} (${chainInfo.axisName} - ${chain.length} nhịp)`;
    breadcrumbContainer.appendChild(axisPill);

    chain.forEach((cb, idx) => {
      const isSelected = (cb.label === b.label);
      const btn = document.createElement('button');
      btn.type = 'button';
      const cbSpanLabel = `Nhịp ${cb.spanIndex || (idx + 1)}`;

      // Check if this specific span fails
      const cbL = getRebarArea(cb.rebar_top_left);
      const cbM = getRebarArea(cb.rebar_bot_mid);
      const cbR = getRebarArea(cb.rebar_top_right);
      const reqL = cb.as_top_left_cm2 || 0;
      const reqM = cb.as_bot_mid_cm2 || 0;
      const reqR = cb.as_top_right_cm2 || 0;
      const isSpanFail = (reqL > 0 && cbL < reqL) || (reqM > 0 && cbM < reqM) || (reqR > 0 && cbR < reqR);
      const spanFailBadge = isSpanFail ? `<span class="text-[9px] bg-rose-500 text-white px-1.5 py-0.2 rounded-full font-extrabold animate-pulse ml-0.5" title="Nhịp này chưa đạt yêu cầu diện tích As!">⚠ Chưa đạt</span>` : '';

      if (isSelected) {
        btn.className = `px-2.5 py-1 rounded-xl ${isSpanFail ? 'bg-rose-700 ring-2 ring-rose-400' : 'bg-indigo-600'} text-white font-bold text-xs shadow-xs flex items-center gap-1.5 shrink-0 cursor-default`;
        btn.innerHTML = `<span>${cbSpanLabel}: ${cb.longBeamId || cb.label}</span><span class="text-[9px] bg-white/20 px-1 rounded">${(cb.length/1000).toFixed(2)}m</span><span class="text-[9px] bg-amber-400 text-slate-900 px-1 rounded font-extrabold">Đang chọn</span>${spanFailBadge}`;
      } else {
        btn.className = `px-2.5 py-1 rounded-xl ${isSpanFail ? 'bg-rose-50 text-rose-800 border-rose-300 font-bold' : 'bg-slate-100 text-slate-700 border-slate-200 font-semibold'} hover:bg-indigo-50 hover:text-indigo-700 text-xs border transition cursor-pointer flex items-center gap-1 shrink-0`;
        btn.innerHTML = `<span>${cbSpanLabel}: ${cb.longBeamId || cb.label}</span><span class="text-[9px] text-slate-500 font-normal">(${(cb.length/1000).toFixed(2)}m)</span>${spanFailBadge}`;
        btn.onclick = () => {
          const target = etabsData.beams.find(x => x.label === cb.label && x.story === b.story);
          if (target) openBeamRebarModal(target);
        };
      }
      breadcrumbContainer.appendChild(btn);

      if (idx < chain.length - 1) {
        const arrow = document.createElement('span');
        arrow.className = 'text-slate-400 text-xs font-bold shrink-0';
        arrow.textContent = '➔';
        breadcrumbContainer.appendChild(arrow);
      }
    });
  }

  // Moments & Req As: Lấy giá trị lớn nhất (bất lợi nhất) của tất cả các đoạn dầm cho toàn bộ dầm
  const maxAsTopL = Math.max(...chain.map(x => x.as_top_left_cm2 || 0));
  const maxAsBotMid = Math.max(...chain.map(x => x.as_bot_mid_cm2 || 0));
  const maxAsTopR = Math.max(...chain.map(x => x.as_top_right_cm2 || 0));
  const maxAsShear = Math.max(...chain.map(x => x.as_shear_cm2_m || 0));

  const chainMoments = chain.map(x => calculateBeamMoments(x));
  const minMLeft = Math.min(...chainMoments.map(x => x.mLeft));
  const maxMMid = Math.max(...chainMoments.map(x => x.mMid));
  const minMRight = Math.min(...chainMoments.map(x => x.mRight));

  document.getElementById('brmMLeft').textContent = `${minMLeft} kNm`;
  document.getElementById('brmAsLeftReq').textContent = `${maxAsTopL.toFixed(2)} cm²`;

  document.getElementById('brmMMid').textContent = `+${maxMMid} kNm`;
  document.getElementById('brmAsMidReq').textContent = `${maxAsBotMid.toFixed(2)} cm²`;

  document.getElementById('brmMRight').textContent = `${minMRight} kNm`;
  document.getElementById('brmAsRightReq').textContent = `${maxAsTopR.toFixed(2)} cm²`;

  document.getElementById('brmShearReq').textContent = `${maxAsShear.toFixed(2)} cm²/m`;

  const maxB = Math.max(...chain.map(x => x.width || 200));
  const minBars = (maxB >= 300) ? 3 : 2;

  // Khởi tạo hoặc phân bổ Thép Chủ (Suốt Dầm) và Thép Tăng Cường
  if (!b.rebar_main_top) {
    const m = (b.rebar_top_left || '').match(/^([1-4]D\d+)/i);
    b.rebar_main_top = m ? `${m[1]} (${(getRebarArea(m[1])).toFixed(2)}cm²)` : '2D18 (5.09cm²)';
  }
  if (!b.rebar_main_bot) {
    const m = (b.rebar_bot_mid || '').match(/^([1-4]D\d+)/i);
    b.rebar_main_bot = m ? `${m[1]} (${(getRebarArea(m[1])).toFixed(2)}cm²)` : '2D18 (5.09cm²)';
  }

  if (!b.extra_top_left || b.extra_top_left === '0 (Không TC)') {
    b.extra_top_left = (b.rebar_top_left && b.rebar_top_left.includes('+')) ? b.rebar_top_left.split('+')[1].replace(/\s*\(.*?\)/, '').trim() : '2D14';
  }
  if (!b.extra_bot_mid || b.extra_bot_mid === '0 (Không TC)') {
    b.extra_bot_mid = (b.rebar_bot_mid && b.rebar_bot_mid.includes('+')) ? b.rebar_bot_mid.split('+')[1].replace(/\s*\(.*?\)/, '').trim() : ((b.length < 2000) ? '0 (Không TC)' : '2D14');
  }
  if (!b.extra_top_right || b.extra_top_right === '0 (Không TC)') {
    b.extra_top_right = (b.rebar_top_right && b.rebar_top_right.includes('+')) ? b.rebar_top_right.split('+')[1].replace(/\s*\(.*?\)/, '').trim() : '2D14';
  }

  // Populate Dropdowns: Thép Chủ & Thép Tăng Cường
  populateRebarSelect('brmSelMainTop', MAIN_REBAR_CATALOG, b.rebar_main_top, minBars);
  populateRebarSelect('brmSelMainBot', MAIN_REBAR_CATALOG, b.rebar_main_bot, minBars);
  populateRebarSelect('brmSelLeft', EXTRA_REBAR_CATALOG, b.extra_top_left, 0);
  populateRebarSelect('brmSelMid', EXTRA_REBAR_CATALOG, b.extra_bot_mid, 0);
  populateRebarSelect('brmSelRight', EXTRA_REBAR_CATALOG, b.extra_top_right, 0);

  // Thép Support / Giá (Treo Đai Nhịp)
  const hangerSel = document.getElementById('brmSelHanger');
  if (hangerSel) {
    if (b.rebar_hanger) {
      let matched = false;
      for (let i = 0; i < hangerSel.options.length; i++) {
        if (hangerSel.options[i].value.includes(b.rebar_hanger) || b.rebar_hanger.includes(hangerSel.options[i].value)) {
          hangerSel.selectedIndex = i;
          matched = true;
          break;
        }
      }
      if (!matched) hangerSel.selectedIndex = (maxB >= 300) ? 3 : 1;
    } else {
      hangerSel.selectedIndex = (maxB >= 300) ? 3 : 1; // Default: 3D16 khi B >= 300
    }
  }

  // Stirrups: Mặc định luôn là phi 6 (f6a100/a200) theo yêu cầu quy chuẩn f6
  window.currentBeamInModal = b;
  let stirrupDiam = 6;
  if (chain.some(x => x._stirrupUserModified && x.stirrup)) {
    const customSpan = chain.find(x => x._stirrupUserModified && x.stirrup);
    const dm = customSpan.stirrup.match(/[dDΦØøϕ]?\s*(\d+)\s*a/i);
    if (dm) stirrupDiam = parseInt(dm[1], 10);
  } else {
    stirrupDiam = 6;
    if (!b.stirrup || !b.stirrup.startsWith('d6')) {
      b.stirrup = 'd6a100/a200';
    }
  }
  window.currentStirrupDiam = stirrupDiam;
  chain.forEach(spanBeam => {
    if (!spanBeam._stirrupUserModified) {
      spanBeam.stirrup = (stirrupDiam === 8) ? 'd8a100/a200' : 'd6a100/a200';
    }
  });

  const radio6 = document.querySelector('input[name="brmStirrupDiam"][value="6"]');
  const radio8 = document.querySelector('input[name="brmStirrupDiam"][value="8"]');
  if (stirrupDiam === 8) {
    if (radio8) radio8.checked = true;
  } else {
    if (radio6) radio6.checked = true;
  }
  populateStirrupDropdown(stirrupDiam, b.stirrup);

  // Show modal first so layout dimensions are non-zero
  modal.classList.remove('hidden');

  // Update live safety badges cho TOÀN BỘ dầm dài (nếu 1 nhịp không đạt thì tất cả không đạt)
  updateMainRebarStatusBadges(chain);
  updateContinuousRebarRatio('brmSelLeft', 'top_left', 'brmStatusLeft', chain);
  updateContinuousRebarRatio('brmSelMid', 'bot_mid', 'brmStatusMid', chain);
  updateContinuousRebarRatio('brmSelRight', 'top_right', 'brmStatusRight', chain);
  updateModalHeaderSafetyAlert();
  updateExportScopeUI();

  loadBrmLayoutState();
  initBrmLayoutSheetControls();
  updateBrmLayoutSheetControls();
  const vsTitle = document.getElementById('brmVsPropTitle');
  if (vsTitle) vsTitle.textContent = `Dầm dài ${b.longBeamId || b.label} - ${formatStoryLabel(b.story)} (${chain.length} nhịp • ${b.section || ''})`;

  // Update Beam Quick Navigation Dropdown
  const navSel = document.getElementById('brmBeamNavSelect');
  if (navSel) {
    if (!navSel.options.length || !window._sortedNavBeams || window._sortedNavBeams.length !== (etabsData?.beams?.length || 0)) {
      populateBeamNavSelect(b);
    } else {
      navSel.value = `${b.story}::${b.label}`;
    }
  }
  if (window.lucide) {
    lucide.createIcons();
  }

  // Mặc định hiển thị hết dầm dài liên tục ('chain') và fit vừa khung
  setBeamDrawingMode('chain');
  setTimeout(resetBeamCadView, 50);
}

function populateRebarSelect(selectId, catalog, currentValue, minBars = 2) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  sel.innerHTML = '';

  const cleanCurrent = (currentValue || '').replace(/\s*\(.*?\)/g, '').trim().toUpperCase();

  // Find exact match first, then partial match
  let matchIdx = catalog.findIndex(item => item.label.toUpperCase() === cleanCurrent);
  if (matchIdx < 0) {
    matchIdx = catalog.findIndex(item => currentValue && currentValue.toUpperCase().includes(item.label.toUpperCase()));
  }

  catalog.forEach((item, idx) => {
    const opt = document.createElement('option');
    opt.value = item.label;
    opt.dataset.area = item.area;
    opt.textContent = `${item.label} (${item.area.toFixed(2)} cm²)`;
    if (idx === matchIdx) {
      opt.selected = true;
    }
    sel.appendChild(opt);
  });

  if (matchIdx < 0 && catalog.length > 0) {
    if (minBars >= 3) {
      const idx3 = catalog.findIndex(item => {
        const m = item.label.match(/^(\d+)D/i);
        return m && parseInt(m[1], 10) >= 3;
      });
      sel.selectedIndex = (idx3 >= 0) ? idx3 : 2;
    } else {
      sel.selectedIndex = (catalog === EXTRA_REBAR_CATALOG) ? 0 : 1; // Extra rebar default: Không TC (0)
    }
  }
}

function onRebarSelectChange() {
  if (!selectedBeamForRebar) return;
  const b = selectedBeamForRebar;
  const chainInfo = findContinuousBeamChain(b);
  const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [b];

  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const selL = document.getElementById('brmSelLeft');
  const selM = document.getElementById('brmSelMid');
  const selH = document.getElementById('brmSelHanger');
  const selR = document.getElementById('brmSelRight');
  const selSt = document.getElementById('brmSelStirrup');

  const optMainTop = selMainTop && selMainTop.selectedIndex >= 0 ? selMainTop.options[selMainTop.selectedIndex] : null;
  const optMainBot = selMainBot && selMainBot.selectedIndex >= 0 ? selMainBot.options[selMainBot.selectedIndex] : null;
  const optL = selL && selL.selectedIndex >= 0 ? selL.options[selL.selectedIndex] : null;
  const optM = selM && selM.selectedIndex >= 0 ? selM.options[selM.selectedIndex] : null;
  const optR = selR && selR.selectedIndex >= 0 ? selR.options[selR.selectedIndex] : null;

  const valMainTop = optMainTop ? optMainTop.value : '2D18';
  const areaMainTop = optMainTop ? parseFloat(optMainTop.dataset.area) : 5.09;
  const valMainBot = optMainBot ? optMainBot.value : '2D18';
  const areaMainBot = optMainBot ? parseFloat(optMainBot.dataset.area) : 5.09;

  const valExtraL = optL ? optL.value : '0 (Không TC)';
  const areaExtraL = optL ? parseFloat(optL.dataset.area) : 0;
  const valExtraM = optM ? optM.value : '0 (Không TC)';
  const areaExtraM = optM ? parseFloat(optM.dataset.area) : 0;
  const valExtraR = optR ? optR.value : '0 (Không TC)';
  const areaExtraR = optR ? parseFloat(optR.dataset.area) : 0;

  const valH = selH ? selH.value : '';
  const valSt = selSt ? selSt.value : '';

  const totAreaL = areaMainTop + areaExtraL;
  const combinedL = (areaExtraL > 0) ? `${valMainTop}+${valExtraL} (${totAreaL.toFixed(2)}cm²)` : `${valMainTop} (${totAreaL.toFixed(2)}cm²)`;

  const totAreaM = areaMainBot + areaExtraM;
  const combinedM = (areaExtraM > 0) ? `${valMainBot}+${valExtraM} (${totAreaM.toFixed(2)}cm²)` : `${valMainBot} (${totAreaM.toFixed(2)}cm²)`;

  const totAreaR = areaMainTop + areaExtraR;
  const combinedR = (areaExtraR > 0) ? `${valMainTop}+${valExtraR} (${totAreaR.toFixed(2)}cm²)` : `${valMainTop} (${totAreaR.toFixed(2)}cm²)`;

  // Đồng bộ lựa chọn cốt thép cho TOÀN BỘ các đoạn dầm trong dầm dài liên tục
  chain.forEach(span => {
    span.rebar_main_top = `${valMainTop} (${areaMainTop.toFixed(2)}cm²)`;
    span.rebar_main_bot = `${valMainBot} (${areaMainBot.toFixed(2)}cm²)`;
    span.extra_top_left = valExtraL;
    span.extra_bot_mid = valExtraM;
    span.extra_top_right = valExtraR;
    span.rebar_top_left = combinedL;
    span.rebar_bot_mid = combinedM;
    span.rebar_top_right = combinedR;
    if (valH) span.rebar_hanger = valH;
    if (valSt) span.stirrup = valSt;
    span._rebarUserModified = true;
  });

  // Cập nhật nhãn trạng thái và tỉ lệ đạt của Thép Chủ
  updateMainRebarStatusBadges(chain);

  // Đánh giá đạt/không đạt cho TOÀN BỘ dầm dài: nếu 1 nhịp không đạt thì tất cả không đạt
  updateContinuousRebarRatio('brmSelLeft', 'top_left', 'brmStatusLeft', chain);
  updateContinuousRebarRatio('brmSelMid', 'bot_mid', 'brmStatusMid', chain);
  updateContinuousRebarRatio('brmSelRight', 'top_right', 'brmStatusRight', chain);
  updateModalHeaderSafetyAlert();

  // Vẽ lại 2D CAD và Rebuild 3D simulation lập tức khi thuộc tính thay đổi
  renderBeamDrawings();
  if (typeof buildBeamRebar3D === 'function') {
    buildBeamRebar3D(b);
  }
  if (beamDrawingMode === '3d' && typeof renderBeam3DRebar === 'function') {
    renderBeam3DRebar();
  }
}

function updateRebarRatio(selectId, reqArea, statusBadgeId) {
  if (selectedBeamForRebar) {
    const chainInfo = findContinuousBeamChain(selectedBeamForRebar);
    const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [selectedBeamForRebar];
    let posKey = 'top_left';
    if (selectId === 'brmSelMid') posKey = 'bot_mid';
    else if (selectId === 'brmSelRight') posKey = 'top_right';
    updateContinuousRebarRatio(selectId, posKey, statusBadgeId, chain);
    return;
  }

  const sel = document.getElementById(selectId);
  const badge = document.getElementById(statusBadgeId);
  if (!sel || !badge) return;

  const chosenOpt = sel.options[sel.selectedIndex];
  const chosenArea = chosenOpt ? parseFloat(chosenOpt.dataset.area) : 0;
  const req = reqArea || 0.1;
  const ratio = Math.round((chosenArea / req) * 100);

  if (ratio >= 100) {
    badge.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 whitespace-nowrap shrink-0';
    if (req <= 0.8) {
      badge.innerHTML = '🟢 Đạt (Cấu tạo)';
    } else if (ratio > 200) {
      const k = (chosenArea / req).toFixed(1);
      badge.innerHTML = `🟢 Đạt (K=${k})`;
    } else {
      badge.innerHTML = `🟢 Đạt ${ratio}%`;
    }
  } else {
    const lack = Math.round(((req - chosenArea) / req) * 100);
    badge.className = 'text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1 whitespace-nowrap shrink-0';
    badge.innerHTML = `🔴 Thiếu ${lack}%`;
  }
  badge.title = `As chọn: ${chosenArea.toFixed(2)} cm² / As yêu cầu: ${req.toFixed(2)} cm²`;
}

function saveBeamRebarSelection() {
  if (!selectedBeamForRebar) return;
  const b = selectedBeamForRebar;
  const chainInfo = findContinuousBeamChain(b);
  const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [b];

  const selMainTop = document.getElementById('brmSelMainTop');
  const selMainBot = document.getElementById('brmSelMainBot');
  const selL = document.getElementById('brmSelLeft');
  const selM = document.getElementById('brmSelMid');
  const selR = document.getElementById('brmSelRight');
  const selH = document.getElementById('brmSelHanger');
  const selSt = document.getElementById('brmSelStirrup');

  const optMainTop = selMainTop && selMainTop.selectedIndex >= 0 ? selMainTop.options[selMainTop.selectedIndex] : null;
  const optMainBot = selMainBot && selMainBot.selectedIndex >= 0 ? selMainBot.options[selMainBot.selectedIndex] : null;
  const optL = selL && selL.selectedIndex >= 0 ? selL.options[selL.selectedIndex] : null;
  const optM = selM && selM.selectedIndex >= 0 ? selM.options[selM.selectedIndex] : null;
  const optR = selR && selR.selectedIndex >= 0 ? selR.options[selR.selectedIndex] : null;

  const valMainTop = optMainTop ? optMainTop.value : '2D18';
  const areaMainTop = optMainTop ? parseFloat(optMainTop.dataset.area) : 5.09;
  const valMainBot = optMainBot ? optMainBot.value : '2D18';
  const areaMainBot = optMainBot ? parseFloat(optMainBot.dataset.area) : 5.09;

  const valExtraL = optL ? optL.value : '0 (Không TC)';
  const areaExtraL = optL ? parseFloat(optL.dataset.area) : 0;
  const valExtraM = optM ? optM.value : '0 (Không TC)';
  const areaExtraM = optM ? parseFloat(optM.dataset.area) : 0;
  const valExtraR = optR ? optR.value : '0 (Không TC)';
  const areaExtraR = optR ? parseFloat(optR.dataset.area) : 0;

  const valH = selH ? selH.value : (b.rebar_hanger || '');
  const valSt = selSt ? selSt.value : (b.stirrup || '');

  const totAreaL = areaMainTop + areaExtraL;
  const combinedL = (areaExtraL > 0) ? `${valMainTop}+${valExtraL} (${totAreaL.toFixed(2)}cm²)` : `${valMainTop} (${totAreaL.toFixed(2)}cm²)`;

  const totAreaM = areaMainBot + areaExtraM;
  const combinedM = (areaExtraM > 0) ? `${valMainBot}+${valExtraM} (${totAreaM.toFixed(2)}cm²)` : `${valMainBot} (${totAreaM.toFixed(2)}cm²)`;

  const totAreaR = areaMainTop + areaExtraR;
  const combinedR = (areaExtraR > 0) ? `${valMainTop}+${valExtraR} (${totAreaR.toFixed(2)}cm²)` : `${valMainTop} (${totAreaR.toFixed(2)}cm²)`;

  chain.forEach(span => {
    span.rebar_main_top = `${valMainTop} (${areaMainTop.toFixed(2)}cm²)`;
    span.rebar_main_bot = `${valMainBot} (${areaMainBot.toFixed(2)}cm²)`;
    span.extra_top_left = valExtraL;
    span.extra_bot_mid = valExtraM;
    span.extra_top_right = valExtraR;
    span.rebar_top_left = combinedL;
    span.rebar_bot_mid = combinedM;
    span.rebar_top_right = combinedR;
    if (valH) span.rebar_hanger = valH;
    if (valSt) span.stirrup = valSt;
    span._rebarUserModified = true;
    span._stirrupUserModified = true;
  });

  const chainSafety = evaluateChainSafety(chain);

  // Refresh tables and 2D canvas
  populateRebarTable('rebarTableBody', 'rebarFilterStory', 'rebarSearchInput');
  populateRebarTable('modalRebarTableBody', null, null);
  renderEtabs2DPlan();

  closeBeamRebarModal();
  const statusMsg = chainSafety.isSafe ? '🟢 Toàn dầm ĐẠT chuẩn TCVN 5574' : `🔴 Chú ý: ${chainSafety.reason}`;

  // Lưu bền vững vào cơ sở dữ liệu backend (PostgreSQL / SQLite fallback)
  const dbPayload = {
    project_name: 'CAI_TAO_PHUONG_AN_B',
    story: b.story || 'T1',
    long_beam_id: b.longBeamId || b.label,
    section: b.section || '',
    span_count: chain.length,
    total_length_mm: chain.reduce((sum, s) => sum + (s.length || 0), 0),
    rebar_main_top: `${valMainTop} (${areaMainTop.toFixed(2)}cm²)`,
    rebar_main_bot: `${valMainBot} (${areaMainBot.toFixed(2)}cm²)`,
    extra_top_left: valExtraL,
    extra_bot_mid: valExtraM,
    extra_top_right: valExtraR,
    rebar_top_left: combinedL,
    rebar_bot_mid: combinedM,
    rebar_top_right: combinedR,
    rebar_hanger: valH,
    stirrup: valSt,
    is_safe: chainSafety.isSafe,
    safety_status: chainSafety.isSafe ? 'Toàn dầm Đạt' : chainSafety.reason,
    spans_data: chain.map(s => ({
      label: s.label,
      story: s.story,
      length: s.length,
      section: s.section,
      width: s.width,
      depth: s.depth,
      as_top_left_cm2: s.as_top_left_cm2,
      as_bot_mid_cm2: s.as_bot_mid_cm2,
      as_top_right_cm2: s.as_top_right_cm2,
      as_shear_cm2_m: s.as_shear_cm2_m
    })),
    layout_settings: readCurrentPanelLayoutSettings()
  };

  fetch('/api/rebar/db/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dbPayload)
  }).then(r => r.json()).then(res => {
    console.log('[DB] Lưu dầm thành công:', res);
    updateDbStatusBadges();
  }).catch(err => {
    console.warn('[DB] Lỗi lưu CSDL:', err);
  });

  const storyStr = formatStoryLabel(b.story);
  alert(`✅ Đã lưu cấu hình cốt thép cho TOÀN BỘ dầm dài ${b.longBeamId || b.label} (${storyStr} • ${chain.length} nhịp • ${b.section}) thành công!\nTrạng thái: ${statusMsg}`);
}

function closeBeamRebarModal() {
  const modal = document.getElementById('beamRebarModal');
  if (modal) modal.classList.add('hidden');
  selectedBeamForRebar = null;
}

// ------------------------------------------------------------------------------
// CÁC HÀM XUẤT BẢN VẼ PDF / DXF & LƯU TRỮ CSDL POSTGRESQL / SQLITE
// ------------------------------------------------------------------------------

function readCurrentPanelLayoutSettings() {
  const getNum = (id, def) => {
    const el = document.getElementById(id);
    return el ? (parseFloat(el.value) || def) : def;
  };
  return {
    scale: getNum('brmSelScale', 50),
    csZoom: getNum('brmSelCsZoom', 2),
    marginX: getNum('brmInputMarginX', 500),
    marginY: getNum('brmInputMarginY', 400),
    gapX: getNum('brmInputGapX', -100),
    gapY: getNum('brmInputGapY', -100),
    leaderLen: getNum('brmInputLeaderLen', 160),
    leaderDist: getNum('brmInputLeaderDist', 60),
    dimSpace1: getNum('brmInputDimSpace1', 350),
    dimSpace2: getNum('brmInputDimSpace2', 260),
    dimScale: getNum('brmSelDimScale', 1.0)
  };
}

function downloadExportFile(url, payload, defaultFilename) {
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(resp => {
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const disposition = resp.headers.get('Content-Disposition');
    let filename = defaultFilename;
    if (disposition && disposition.indexOf('filename=') !== -1) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];
    }
    return resp.blob().then(blob => ({ blob, filename }));
  })
  .then(({ blob, filename }) => {
    const a = document.createElement('a');
    a.href = window.URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(a.href);
  })
  .catch(err => {
    alert(`Lỗi xuất file: ${err.message}`);
  });
}

function getActualExtraRebarsForChain(chain) {
  if (!chain || chain.length === 0) return [];
  const numSpans = chain.length;
  const colW = 300; // Chiều rộng cột tiêu chuẩn 300mm
  const rebars = [];

  let curX = 0;
  const spansMeta = chain.map((b, idx) => {
    const L = b.length || 0;
    const h = b.height || b.depth || 400;
    const sStart = curX;
    const sEnd = curX + L;
    curX += L;
    const extraL = b.extra_top_left;
    const extraR = b.extra_top_right;
    const extraM = b.extra_bot_mid;
    return {
      beam: b,
      index: idx,
      L,
      h,
      sStart,
      sEnd,
      extraL,
      extraR,
      extraM,
      hasL: (extraL && !extraL.startsWith('0') && extraL !== '0 (Không TC)'),
      hasR: (extraR && !extraR.startsWith('0') && extraR !== '0 (Không TC)'),
      hasM: (extraM && !extraM.startsWith('0') && extraM !== '0 (Không TC)')
    };
  });

  // A. Thép tăng cường gối trên (Top Extra Rebars) - Mô phỏng 100% chính xác drawFullBeamCadContent
  const rawIntervals = [];
  for (let k = 0; k <= numSpans; k++) {
    let xL, xR;
    let hookL = 0, hookR = 0;
    let spec = '2D14';

    if (k === 0) {
      if (spansMeta[0].hasL) {
        spec = spansMeta[0].extraL;
        hookL = Math.max(0, spansMeta[0].h - 25);
        xL = spansMeta[0].sStart - colW / 2;
        if (spansMeta[0].L < 2000) {
          xR = (numSpans === 1) ? (spansMeta[0].sEnd + colW / 2) : spansMeta[0].sEnd;
        } else {
          xR = spansMeta[0].sStart + colW / 2 + (spansMeta[0].L - colW) * 0.25;
        }
        rawIntervals.push({ x1: xL, x2: xR, hookL, hookR: 0, spec, desc: `Thanh gối biên trái (${spansMeta[0].beam.label})` });
      }
    } else if (k === numSpans) {
      const last = spansMeta[numSpans - 1];
      if (last.hasR) {
        spec = last.extraR;
        hookR = Math.max(0, last.h - 25);
        xR = last.sEnd + colW / 2;
        if (last.L < 2000) {
          xL = (numSpans === 1) ? (last.sStart - colW / 2) : last.sStart;
        } else {
          xL = last.sEnd - colW / 2 - (last.L - colW) * 0.25;
        }
        rawIntervals.push({ x1: xL, x2: xR, hookL: 0, hookR, spec, desc: `Thanh gối biên phải (${last.beam.label})` });
      }
    } else {
      const prev = spansMeta[k - 1];
      const next = spansMeta[k];
      if (prev.hasR || next.hasL) {
        spec = next.hasL ? next.extraL : prev.extraR;
        if (prev.L < 2000) {
          xL = (k - 1 === 0) ? (prev.sStart - colW / 2) : prev.sStart;
        } else {
          xL = prev.sEnd - colW / 2 - (prev.L - colW) * 0.25;
        }
        if (next.L < 2000) {
          xR = (k === numSpans - 1) ? (next.sEnd + colW / 2) : next.sEnd;
        } else {
          xR = next.sStart + colW / 2 + (next.L - colW) * 0.25;
        }
        rawIntervals.push({ x1: xL, x2: xR, hookL: 0, hookR: 0, spec, desc: `Thanh gối giữa (${prev.beam.label}-${next.beam.label})` });
      }
    }
  }

  // Merge các khoảng thép gối giao nhau / chạy qua nhịp ngắn
  rawIntervals.sort((a, b) => a.x1 - b.x1);
  const merged = [];
  rawIntervals.forEach(curr => {
    if (merged.length === 0) {
      merged.push({ ...curr });
    } else {
      const prev = merged[merged.length - 1];
      if (curr.x1 <= prev.x2 + 50) {
        prev.x2 = Math.max(prev.x2, curr.x2);
        prev.hookR = Math.max(prev.hookR, curr.hookR);
        prev.desc += ` + ${curr.desc}`;
      } else {
        merged.push({ ...curr });
      }
    }
  });

  merged.forEach(m => {
    const totalLen = Math.round((m.x2 - m.x1) + m.hookL + m.hookR);
    rebars.push({
      type: 'gối',
      spec: m.spec,
      desc: m.desc,
      length: totalLen
    });
  });

  // B. Thép tăng cường bụng dưới (Bottom Extra Rebars)
  // Chỉ đặt cho nhịp >= 2000mm (nhịp < 2000 bỏ qua hoàn toàn theo chuẩn TCVN)
  spansMeta.forEach(s => {
    if (s.L >= 2000 && s.hasM) {
      const effSpan = Math.max(0, s.L - colW);
      const botLen = Math.round(effSpan * 0.70);
      rebars.push({
        type: 'bụng',
        spec: s.extraM,
        desc: `Thanh bụng nhịp ${s.beam.label}`,
        length: botLen
      });
    }
  });

  return rebars;
}
window.getActualExtraRebarsForChain = getActualExtraRebarsForChain;

function updateModalHeaderSafetyAlert() {
  const groups = getAllLongBeamGroups();
  const total = groups.length;
  if (total === 0) return;

  let passCount = 0;
  let failCount = 0;
  let currentGroupSafety = null;

  const currentBeam = selectedBeamForRebar;
  const currentKey = currentBeam ? `${currentBeam.story}::${currentBeam.longBeamId || currentBeam.label}` : '';

  const failingGroups = [];
  const tcLungGroups = [];
  const tcBungGroups = [];
  const shortRebarGroups = [];

  // Lấy ngưỡng từ localStorage nếu có, fallback 600
  let threshold = 600;
  try {
    const savedThresh = localStorage.getItem('brmShortRebarThreshold');
    if (savedThresh) {
      const p = parseFloat(savedThresh);
      if (!isNaN(p) && p > 0) threshold = p;
    }
  } catch (e) {}
  if (typeof window._shortRebarThreshold !== 'undefined') {
    threshold = window._shortRebarThreshold;
  }
  window._shortRebarThreshold = threshold;

  groups.forEach(g => {
    const safety = evaluateChainSafety(g.beams);
    if (safety.isSafe) {
      passCount++;
    } else {
      failCount++;
      failingGroups.push({ group: g, safety });
    }
    const key = `${g.story}::${g.long_beam_id}`;
    if (key === currentKey) {
      currentGroupSafety = safety;
    }

    // 1. Kiểm tra thép tăng cường Lưng, Bụng
    let hasTcLung = false;
    let hasTcBung = false;
    let tcLungDetail = '';
    let tcBungDetail = '';

    g.beams.forEach(b => {
      const extraL = b.extra_top_left;
      const extraR = b.extra_top_right;
      const extraM = b.extra_bot_mid;
      const hasL = (extraL && !extraL.startsWith('0') && extraL !== '0 (Không TC)');
      const hasR = (extraR && !extraR.startsWith('0') && extraR !== '0 (Không TC)');
      const hasM = (extraM && !extraM.startsWith('0') && extraM !== '0 (Không TC)');

      if (hasL || hasR) {
        hasTcLung = true;
        const lStr = hasL ? `Gối T: ${extraL}` : '';
        const rStr = hasR ? `Gối P: ${extraR}` : '';
        tcLungDetail = [lStr, rStr].filter(Boolean).join(' • ');
      }
      if (hasM) {
        hasTcBung = true;
        tcBungDetail = `Bụng: ${extraM}`;
      }
    });

    if (hasTcLung) tcLungGroups.push({ group: g, detail: tcLungDetail });
    if (hasTcBung) tcBungGroups.push({ group: g, detail: tcBungDetail });

    // 2. Tính toán CHIỀU DÀI THỰC TẾ CỦA TỪNG THANH THÉP TĂNG CƯỜNG TRÊN BẢN VẼ
    // Đồng bộ 100% với hàm vẽ drawFullBeamCadContent (vươn qua cột + merge nhịp ngắn)
    const actualRebars = getActualExtraRebarsForChain(g.beams);
    const shortBars = actualRebars.filter(b => b.length < threshold);

    if (shortBars.length > 0) {
      const details = shortBars.map(b => `${b.desc}: L=${b.length}mm (${b.spec})`);
      shortRebarGroups.push({ group: g, details, shortBars });
    }
  });

  window._currentFailingGroups = failingGroups;
  window._currentTcLungGroups = tcLungGroups;
  window._currentTcBungGroups = tcBungGroups;
  window._currentShortRebarGroups = shortRebarGroups;

  // Update header summary on trigger button
  const summaryEl = document.getElementById('brmHeaderSummaryPass');
  if (summaryEl) summaryEl.textContent = `${passCount}/${total} Đạt`;

  // Update vertical dropdown panel badges
  const passEl = document.getElementById('brmHeaderPassCount');
  if (passEl) passEl.textContent = `${passCount}/${total}`;

  const failEl = document.getElementById('brmHeaderFailCount');
  if (failEl) failEl.textContent = `${failCount}/${total}`;

  const tcLungEl = document.getElementById('brmHeaderTcLungCount');
  if (tcLungEl) tcLungEl.textContent = `${tcLungGroups.length}/${total}`;

  const tcBungEl = document.getElementById('brmHeaderTcBungCount');
  if (tcBungEl) tcBungEl.textContent = `${tcBungGroups.length}/${total}`;

  const shortRebarCountEl = document.getElementById('brmShortRebarCount');
  if (shortRebarCountEl) shortRebarCountEl.textContent = `${shortRebarGroups.length}/${total}`;

  const thresholdInput = document.getElementById('brmShortRebarThreshold');
  if (thresholdInput && document.activeElement !== thresholdInput) {
    thresholdInput.value = threshold;
  }
  const threshLabel = document.getElementById('brmShortRebarThresholdLabel');
  if (threshLabel) threshLabel.textContent = `${threshold}`;

  populateTcLungDropdown(tcLungGroups);
  populateTcBungDropdown(tcBungGroups);
  populateShortRebarDropdown(shortRebarGroups);

  const failBadge = document.getElementById('brmHeaderFailBadge');
  const jumpHint = document.getElementById('brmHeaderFailJumpHint');
  const menuBtn = document.getElementById('btnToggleFailingBeamsMenu');
  const menuCount = document.getElementById('brmFailingMenuCount');
  const tableFailBadge = document.getElementById('tableFailCountBadge');
  if (tableFailBadge) tableFailBadge.textContent = `${failCount}`;

  if (failCount > 0) {
    if (failBadge) {
      failBadge.className = 'px-2 py-0.5 rounded-xl bg-rose-100 hover:bg-rose-200 text-rose-950 border border-rose-400 text-xs font-bold flex items-center gap-1 shadow-xs cursor-pointer active:scale-95 transition ring-2 ring-rose-400/30';
      failBadge.title = `Bấm để chuyển nhanh tới dầm không đạt tiếp theo (${failCount} dầm)`;
    }
    if (jumpHint) {
      jumpHint.classList.remove('hidden');
      jumpHint.classList.add('flex');
    }
    if (menuBtn) {
      menuBtn.classList.remove('hidden');
    }
    if (menuCount) {
      menuCount.textContent = `${failCount}`;
    }
    populateFailingBeamsDropdown(failingGroups);
  } else {
    if (failBadge) {
      failBadge.className = 'px-2 py-0.5 rounded-xl bg-slate-100 text-slate-500 border border-slate-300 text-xs font-bold flex items-center gap-1 shadow-2xs cursor-default';
      failBadge.title = 'Toàn bộ 60 dầm trong dự án đều đạt chuẩn TCVN 5574-2012!';
    }
    if (jumpHint) {
      jumpHint.classList.add('hidden');
      jumpHint.classList.remove('flex');
    }
    if (menuBtn) {
      menuBtn.classList.add('hidden');
    }
    closeFailingBeamsMenu();
  }

  // Update current beam status badge
  const currBadge = document.getElementById('brmHeaderCurrentBeamBadge');
  if (currBadge && currentBeam) {
    const bName = currentBeam.longBeamId || currentBeam.label;
    const storyStr = formatStoryLabel(currentBeam.story);
    if (currentGroupSafety && currentGroupSafety.isSafe) {
      currBadge.className = 'px-2.5 py-1 rounded-2xl text-xs font-extrabold flex items-center gap-1 shadow-2xs bg-emerald-100 text-emerald-800 border border-emerald-300 cursor-default';
      currBadge.removeAttribute('onclick');
      currBadge.title = `Dầm ${bName} • ${storyStr} bố trí cốt thép đạt chuẩn TCVN 5574`;
      currBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>Dầm ${bName} • ${storyStr}: ĐẠT</span>`;
    } else {
      const shortMsg = (currentGroupSafety && currentGroupSafety.shortReason) ? currentGroupSafety.shortReason : 'CHƯA ĐẠT';
      currBadge.className = 'px-2.5 py-1 rounded-2xl text-xs font-extrabold flex items-center gap-1.5 shadow-2xs bg-rose-100 hover:bg-rose-200 text-rose-950 border border-rose-400 animate-pulse cursor-pointer transition active:scale-95';
      currBadge.title = `Bấm để phóng to và định vị đúng nhịp chưa đạt này (${currentGroupSafety ? currentGroupSafety.reason : ''})`;
      currBadge.setAttribute('onclick', 'focusFailingSpanOfCurrentBeam()');
      currBadge.innerHTML = `
        <span class="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
        <span>Dầm ${bName} • ${storyStr}: ${shortMsg}</span>
        <span class="ml-1 text-[10px] px-1.5 py-0.2 bg-rose-200 text-rose-950 rounded-md font-bold flex items-center gap-0.5">
          <span>Phóng to</span>
          <svg class="w-3 h-3 text-rose-800" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
      `;
    }
  }
}

function populateFailingBeamsDropdown(failingGroups) {
  const listEl = document.getElementById('brmFailingBeamsList');
  if (!listEl) return;
  listEl.innerHTML = '';
  failingGroups.forEach((fg) => {
    const item = document.createElement('div');
    item.className = 'p-2 rounded-xl hover:bg-rose-50 cursor-pointer transition flex items-center justify-between gap-2 border border-transparent hover:border-rose-200 group';
    item.onclick = (e) => {
      e.stopPropagation();
      jumpToFailingBeam(fg.group.story, fg.group.long_beam_id);
    };

    const axis = fg.group.beams && fg.group.beams[0] && fg.group.beams[0].axisName ? ` [${fg.group.beams[0].axisName}]` : '';
    item.innerHTML = `
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span class="font-mono font-bold text-rose-900 bg-rose-100 px-1.5 py-0.2 rounded">${fg.group.long_beam_id}</span>
          <span class="text-[10px] font-semibold text-slate-600">${formatStoryLabel(fg.group.story)}${axis}</span>
          <span class="text-[10px] text-slate-400">(${fg.group.beams.length} nhịp)</span>
        </div>
        <div class="text-[11px] text-rose-700 font-medium truncate mt-0.5" title="${fg.safety.reason}">
          ⚠ ${fg.safety.reason}
        </div>
      </div>
      <span class="text-xs font-bold text-rose-600 group-hover:text-rose-900 flex items-center gap-0.5 shrink-0">
        <span>Sửa</span> ➔
      </span>
    `;
    listEl.appendChild(item);
  });
}

function populateTcLungDropdown(tcLungGroups) {
  const listEl = document.getElementById('brmTcLungList');
  const countEl = document.getElementById('brmTcLungMenuCount');
  if (countEl) countEl.textContent = `${tcLungGroups.length}`;
  if (!listEl) return;
  listEl.innerHTML = '';
  if (tcLungGroups.length === 0) {
    listEl.innerHTML = '<div class="p-2 text-center text-slate-400">Không có dầm nào cần thép tăng cường lưng</div>';
    return;
  }
  tcLungGroups.forEach(item => {
    const div = document.createElement('div');
    div.className = 'p-2 rounded-xl hover:bg-purple-50 cursor-pointer transition flex items-center justify-between gap-2 border border-transparent hover:border-purple-200 group';
    div.onclick = (e) => {
      e.stopPropagation();
      closeTcLungMenu();
      jumpToBeamFromStats(item.group.story, item.group.long_beam_id);
    };
    const axis = item.group.beams && item.group.beams[0] && item.group.beams[0].axisName ? ` [${item.group.beams[0].axisName}]` : '';
    div.innerHTML = `
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span class="font-mono font-bold text-purple-900 bg-purple-100 px-1.5 py-0.2 rounded">${item.group.long_beam_id}</span>
          <span class="text-[10px] font-semibold text-slate-600">${formatStoryLabel(item.group.story)}${axis}</span>
          <span class="text-[10px] text-slate-400">(${item.group.beams.length} nhịp)</span>
        </div>
        <div class="text-[11px] text-purple-700 font-medium truncate mt-0.5">
          ⚡ ${item.detail || 'Có thép tăng cường lưng'}
        </div>
      </div>
      <span class="text-xs font-bold text-purple-600 group-hover:text-purple-900 shrink-0">➔</span>
    `;
    listEl.appendChild(div);
  });
}

function populateTcBungDropdown(tcBungGroups) {
  const listEl = document.getElementById('brmTcBungList');
  const countEl = document.getElementById('brmTcBungMenuCount');
  if (countEl) countEl.textContent = `${tcBungGroups.length}`;
  if (!listEl) return;
  listEl.innerHTML = '';
  if (tcBungGroups.length === 0) {
    listEl.innerHTML = '<div class="p-2 text-center text-slate-400">Không có dầm nào cần thép tăng cường bụng</div>';
    return;
  }
  tcBungGroups.forEach(item => {
    const div = document.createElement('div');
    div.className = 'p-2 rounded-xl hover:bg-amber-50 cursor-pointer transition flex items-center justify-between gap-2 border border-transparent hover:border-amber-200 group';
    div.onclick = (e) => {
      e.stopPropagation();
      closeTcBungMenu();
      jumpToBeamFromStats(item.group.story, item.group.long_beam_id);
    };
    const axis = item.group.beams && item.group.beams[0] && item.group.beams[0].axisName ? ` [${item.group.beams[0].axisName}]` : '';
    div.innerHTML = `
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span class="font-mono font-bold text-amber-900 bg-amber-100 px-1.5 py-0.2 rounded">${item.group.long_beam_id}</span>
          <span class="text-[10px] font-semibold text-slate-600">${formatStoryLabel(item.group.story)}${axis}</span>
          <span class="text-[10px] text-slate-400">(${item.group.beams.length} nhịp)</span>
        </div>
        <div class="text-[11px] text-amber-700 font-medium truncate mt-0.5">
          ⚡ ${item.detail || 'Có thép tăng cường bụng'}
        </div>
      </div>
      <span class="text-xs font-bold text-amber-600 group-hover:text-amber-900 shrink-0">➔</span>
    `;
    listEl.appendChild(div);
  });
}

function populateShortRebarDropdown(shortRebarGroups) {
  const listEl = document.getElementById('brmShortRebarList');
  if (!listEl) return;
  listEl.innerHTML = '';
  const threshold = (typeof window._shortRebarThreshold !== 'undefined') ? window._shortRebarThreshold : 600;
  if (!shortRebarGroups || shortRebarGroups.length === 0) {
    listEl.innerHTML = `
      <div class="p-2.5 text-center text-slate-500 font-medium bg-emerald-50/50 rounded-xl border border-emerald-100">
        <div class="text-xs text-emerald-700 font-bold flex items-center justify-center gap-1">
          <svg class="w-3.5 h-3.5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Không có thanh thép tăng cường nào &lt; ${threshold}mm</span>
        </div>
        <p class="text-[10px] text-slate-500 mt-0.5">Tất cả thanh thép trên bản vẽ đều có chiều dài thực tế đạt chuẩn.</p>
      </div>`;
    return;
  }
  shortRebarGroups.forEach(item => {
    const div = document.createElement('div');
    div.className = 'p-1.5 rounded-lg hover:bg-indigo-50 cursor-pointer transition flex items-center justify-between gap-1 border border-transparent hover:border-indigo-200 group';
    div.onclick = (e) => {
      e.stopPropagation();
      jumpToBeamFromStats(item.group.story, item.group.long_beam_id);
    };
    const axis = item.group.beams && item.group.beams[0] && item.group.beams[0].axisName ? ` [${item.group.beams[0].axisName}]` : '';
    const detailsHtml = (item.details || []).map(d => `<div class="text-[10px] text-indigo-700 truncate">⚡ ${d}</div>`).join('');
    div.innerHTML = `
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span class="font-mono font-bold text-indigo-900 bg-indigo-100 px-1.5 py-0.2 rounded text-[10px]">${item.group.long_beam_id}</span>
          <span class="text-[10px] font-semibold text-slate-600">${formatStoryLabel(item.group.story)}${axis}</span>
          <span class="text-[10px] text-slate-400">(${item.group.beams.length} nhịp)</span>
        </div>
        ${detailsHtml}
      </div>
      <span class="text-[10px] font-bold text-indigo-600 group-hover:text-indigo-900 shrink-0">➔</span>
    `;
    listEl.appendChild(div);
  });
}
window.populateShortRebarDropdown = populateShortRebarDropdown;

function onShortRebarThresholdChange(val) {
  const num = parseFloat(val);
  if (!isNaN(num) && num > 0) {
    window._shortRebarThreshold = num;
    try {
      localStorage.setItem('brmShortRebarThreshold', num.toString());
    } catch (e) {
      console.warn('Lỗi lưu brmShortRebarThreshold vào localStorage:', e);
    }
    updateModalHeaderSafetyAlert();
  }
}
window.onShortRebarThresholdChange = onShortRebarThresholdChange;

function toggleTcLungAccordion() {
  const c = document.getElementById('brmTcLungListContainer');
  const arr = document.getElementById('brmTcLungArrow');
  if (!c) return;
  const isHidden = c.classList.toggle('hidden');
  if (arr) arr.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
}
function toggleTcBungAccordion() {
  const c = document.getElementById('brmTcBungListContainer');
  const arr = document.getElementById('brmTcBungArrow');
  if (!c) return;
  const isHidden = c.classList.toggle('hidden');
  if (arr) arr.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
}
function toggleFailAccordion() {
  const c = document.getElementById('brmFailListContainer');
  const arr = document.getElementById('brmFailArrow');
  if (!c) return;
  const isHidden = c.classList.toggle('hidden');
  if (arr) arr.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
}
function toggleShortRebarAccordion() {
  const c = document.getElementById('brmShortRebarListContainer');
  const arr = document.getElementById('brmShortRebarArrow');
  if (!c) return;
  const isHidden = c.classList.toggle('hidden');
  if (arr) arr.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
}
window.toggleTcLungAccordion = toggleTcLungAccordion;
window.toggleTcBungAccordion = toggleTcBungAccordion;
window.toggleFailAccordion = toggleFailAccordion;
window.toggleShortRebarAccordion = toggleShortRebarAccordion;

function jumpToBeamFromStats(story, longBeamId) {
  const beams = (etabsData && etabsData.beams) ? etabsData.beams : [];
  const match = beams.find(b => (b.story === story) && (b.longBeamId === longBeamId || b.label === longBeamId));
  if (match) {
    openBeamRebarModal(match);
    setTimeout(() => {
      if (typeof focusActiveSpanCad === 'function') focusActiveSpanCad();
      showToastNotification(`📍 Đã mở chi tiết dầm ${longBeamId} (${formatStoryLabel(story)})!`, 'info');
    }, 100);
  }
}
window.jumpToBeamFromStats = jumpToBeamFromStats;

function toggleTcLungMenu(e) {
  if (e) e.stopPropagation();
  closeTcBungMenu();
  closeFailingBeamsMenu();
  const m = document.getElementById('brmTcLungDropdown');
  if (m) m.classList.toggle('hidden');
}
window.toggleTcLungMenu = toggleTcLungMenu;

function closeTcLungMenu() {
  const m = document.getElementById('brmTcLungDropdown');
  if (m) m.classList.add('hidden');
}
window.closeTcLungMenu = closeTcLungMenu;

function toggleTcBungMenu(e) {
  if (e) e.stopPropagation();
  closeTcLungMenu();
  closeFailingBeamsMenu();
  const m = document.getElementById('brmTcBungDropdown');
  if (m) m.classList.toggle('hidden');
}
window.toggleTcBungMenu = toggleTcBungMenu;

function closeTcBungMenu() {
  const m = document.getElementById('brmTcBungDropdown');
  if (m) m.classList.add('hidden');
}
window.closeTcBungMenu = closeTcBungMenu;

function toggleFailingBeamsMenu(e) {
  if (e) e.stopPropagation();
  closeTcLungMenu();
  closeTcBungMenu();
  const menu = document.getElementById('brmFailingBeamsDropdown');
  if (menu) {
    menu.classList.toggle('hidden');
  }
}

function closeFailingBeamsMenu() {
  const menu = document.getElementById('brmFailingBeamsDropdown');
  if (menu) menu.classList.add('hidden');
}

if (!window._brmDocClickListenerAdded) {
  window._brmDocClickListenerAdded = true;
  document.addEventListener('click', (e) => {
    const menu = document.getElementById('brmFailingBeamsDropdown');
    const btn = document.getElementById('btnToggleFailingBeamsMenu');
    if (menu && !menu.classList.contains('hidden')) {
      if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {
        closeFailingBeamsMenu();
      }
    }
    const menuLung = document.getElementById('brmTcLungDropdown');
    const btnLung = document.getElementById('brmHeaderTcLungBadge');
    if (menuLung && !menuLung.classList.contains('hidden')) {
      if (!menuLung.contains(e.target) && (!btnLung || !btnLung.contains(e.target))) {
        closeTcLungMenu();
      }
    }
    const menuBung = document.getElementById('brmTcBungDropdown');
    const btnBung = document.getElementById('brmHeaderTcBungBadge');
    if (menuBung && !menuBung.classList.contains('hidden')) {
      if (!menuBung.contains(e.target) && (!btnBung || !btnBung.contains(e.target))) {
        closeTcBungMenu();
      }
    }
  });
}

function jumpToNextFailingBeam() {
  closeFailingBeamsMenu();
  let failingGroups = window._currentFailingGroups;
  if (!failingGroups || failingGroups.length === 0) {
    updateModalHeaderSafetyAlert();
    failingGroups = window._currentFailingGroups || [];
  }

  if (failingGroups.length === 0) {
    showToastNotification('🎉 Toàn bộ các dầm đều đạt chuẩn TCVN 5574-2012!', 'success');
    return;
  }

  const currentBeam = selectedBeamForRebar;
  const currentKey = currentBeam ? `${currentBeam.story}::${currentBeam.longBeamId || currentBeam.label}` : '';

  let currIdx = failingGroups.findIndex(fg => `${fg.group.story}::${fg.group.long_beam_id}` === currentKey);
  let nextIdx = (currIdx === -1) ? 0 : (currIdx + 1) % failingGroups.length;

  const target = failingGroups[nextIdx];
  if (target && target.group && target.group.beams && target.group.beams.length > 0) {
    const targetSpan = target.safety.worstSpan || target.group.beams[0];
    const fullTarget = (etabsData && etabsData.beams) 
      ? (etabsData.beams.find(x => x.label === targetSpan.label && x.story === target.group.story) || targetSpan)
      : targetSpan;

    openBeamRebarModal(fullTarget);

    setTimeout(() => {
      focusActiveSpanCad();
      const failNum = `${nextIdx + 1}/${failingGroups.length}`;
      showToastNotification(`⚡ Đã chuyển tới dầm chưa đạt (${failNum}): Dầm ${target.group.long_beam_id} (${target.group.story}) • ${target.safety.reason}`, 'warning');
      highlightFailingPropField(target.safety.worstPosition || 'bot_mid');
    }, 120);
  }
}

function jumpToFailingBeam(story, longBeamId) {
  closeFailingBeamsMenu();
  const groups = getAllLongBeamGroups();
  const g = groups.find(x => x.story === story && x.long_beam_id === longBeamId);
  if (!g || !g.beams || g.beams.length === 0) return;

  const safety = evaluateChainSafety(g.beams);
  const targetSpan = (safety && safety.worstSpan) ? safety.worstSpan : g.beams[0];
  const fullTarget = (etabsData && etabsData.beams) 
    ? (etabsData.beams.find(x => x.label === targetSpan.label && x.story === story) || targetSpan)
    : targetSpan;

  openBeamRebarModal(fullTarget);
  setTimeout(() => {
    focusActiveSpanCad();
    showToastNotification(`⚡ Đã chuyển tới: Dầm ${g.long_beam_id} (${story}) • ${safety ? safety.reason : ''}`, 'warning');
    if (safety && safety.worstPosition) highlightFailingPropField(safety.worstPosition);
  }, 120);
}

function focusFailingSpanOfCurrentBeam() {
  if (!selectedBeamForRebar) return;
  const chainInfo = findContinuousBeamChain(selectedBeamForRebar);
  const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [selectedBeamForRebar];
  const safety = evaluateChainSafety(chain);
  if (safety && safety.worstSpan) {
    const target = etabsData.beams.find(x => x.label === safety.worstSpan.label && x.story === selectedBeamForRebar.story);
    if (target && target.label !== selectedBeamForRebar.label) {
      openBeamRebarModal(target);
    }
    setTimeout(() => {
      focusActiveSpanCad();
      showToastNotification(`🔍 Đã định vị nhịp chưa đạt: ${safety.reason}`, 'warning');
      highlightFailingPropField(safety.worstPosition || 'bot_mid');
    }, 100);
  }
}

function highlightFailingPropField(pos) {
  let elId = 'brmSelMid';
  if (pos === 'top_left') elId = 'brmSelLeft';
  else if (pos === 'top_right') elId = 'brmSelRight';

  const el = document.getElementById(elId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    el.classList.add('ring-4', 'ring-rose-500', 'bg-rose-50');
    setTimeout(() => {
      el.classList.remove('ring-4', 'ring-rose-500', 'bg-rose-50');
    }, 2000);
  }
}

function showToastNotification(message, type = 'info') {
  let toast = document.getElementById('brmToastNotification');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'brmToastNotification';
    const modal = document.getElementById('beamRebarModal');
    if (modal) modal.appendChild(toast);
  }
  if (!toast) return;

  const bgClasses = {
    warning: 'bg-amber-900/95 text-amber-50 border border-amber-400/80 shadow-2xl ring-2 ring-amber-400/20',
    error: 'bg-rose-900/95 text-rose-50 border border-rose-400/80 shadow-2xl ring-2 ring-rose-400/20',
    success: 'bg-emerald-900/95 text-emerald-50 border border-emerald-400/80 shadow-2xl ring-2 ring-emerald-400/20',
    info: 'bg-indigo-900/95 text-indigo-50 border border-indigo-400/80 shadow-2xl ring-2 ring-indigo-400/20'
  };

  toast.className = `absolute top-16 left-1/2 -translate-x-1/2 z-50 pointer-events-none transition-all duration-300 opacity-100 translate-y-0 flex items-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs ${bgClasses[type] || bgClasses.info}`;
  toast.innerHTML = `<span>${message}</span>`;

  if (window._brmToastTimer) clearTimeout(window._brmToastTimer);
  window._brmToastTimer = setTimeout(() => {
    toast.className = `absolute top-16 left-1/2 -translate-x-1/2 z-50 pointer-events-none transition-all duration-300 opacity-0 -translate-y-2 flex items-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs ${bgClasses[type] || bgClasses.info}`;
  }, 3500);
}

function getClientPagesInfo() {
  const groups = getAllLongBeamGroups();
  const combineShort = document.getElementById('brmCheckCombineShort') ? document.getElementById('brmCheckCombineShort').checked : true;
  
  function isShort(bg) {
    const numSpans = (bg.beams || []).length;
    const totLen = bg.total_length_mm || (bg.beams || []).reduce((s, b) => s + (b.length || 0), 0);
    return (numSpans <= 2 && totLen <= 12000) || (numSpans === 1 && totLen <= 15000);
  }

  const pages = [];
  if (combineShort) {
    let i = 0;
    while (i < groups.length) {
      const bg1 = groups[i];
      if (isShort(bg1) && (i + 1 < groups.length) && isShort(groups[i + 1])) {
        pages.push({ type: 'combined', beams: [bg1, groups[i + 1]] });
        i += 2;
      } else {
        pages.push({ type: 'single', beams: [bg1] });
        i += 1;
      }
    }
  } else {
    groups.forEach(g => pages.push({ type: 'single', beams: [g] }));
  }

  let currentBeamPageIndex = 1;
  if (selectedBeamForRebar) {
    const targetKey = `${selectedBeamForRebar.story}::${selectedBeamForRebar.longBeamId || selectedBeamForRebar.label}`;
    for (let pIdx = 0; pIdx < pages.length; pIdx++) {
      const p = pages[pIdx];
      const hasBeam = p.beams.some(bg => `${bg.story}::${bg.long_beam_id}` === targetKey);
      if (hasBeam) {
        currentBeamPageIndex = pIdx + 1;
        break;
      }
    }
  }

  return {
    groups,
    pages,
    totalPages: pages.length || 1,
    currentBeamPageIndex
  };
}

function onExportScopeChange() {
  const scopeSel = document.getElementById('brmExportPageScope');
  const scope = scopeSel ? scopeSel.value : 'current';
  const rangeBox = document.getElementById('brmExportRangeBox');
  const rangeInput = document.getElementById('brmExportPageRangeInput');
  const rangeHint = document.getElementById('brmExportRangeHint');

  const { totalPages, currentBeamPageIndex } = getClientPagesInfo();

  if (scope === 'range') {
    if (rangeBox) {
      rangeBox.classList.remove('hidden');
      rangeBox.classList.add('flex');
    }
    if (rangeHint) rangeHint.textContent = `(1 - ${totalPages})`;
    if (rangeInput && !rangeInput.value) {
      rangeInput.value = (currentBeamPageIndex > 0) ? `${currentBeamPageIndex}` : '1';
    }
  } else {
    if (rangeBox) {
      rangeBox.classList.add('hidden');
      rangeBox.classList.remove('flex');
    }
  }

  const pdfLabel = document.getElementById('brmBtnExportPdfLabel');
  const dxfLabel = document.getElementById('brmBtnExportDxfLabel');
  if (scope === 'current') {
    if (pdfLabel) pdfLabel.textContent = `Xuất PDF (Trang ${currentBeamPageIndex}/${totalPages})`;
    if (dxfLabel) dxfLabel.textContent = `Xuất DXF (Trang ${currentBeamPageIndex}/${totalPages})`;
  } else if (scope === 'all') {
    if (pdfLabel) pdfLabel.textContent = `Xuất PDF (Tất cả ${totalPages} trang)`;
    if (dxfLabel) dxfLabel.textContent = `Xuất DXF (Tất cả ${totalPages} trang)`;
  } else {
    if (pdfLabel) pdfLabel.textContent = 'Xuất PDF (Khoảng trang)';
    if (dxfLabel) dxfLabel.textContent = 'Xuất DXF (Khoảng trang)';
  }
}

function updateExportScopeUI() {
  onExportScopeChange();
}

function parseClientPageRange(rangeStr, maxPages) {
  if (!rangeStr || String(rangeStr).trim().toLowerCase() === 'all') {
    return Array.from({ length: maxPages }, (_, i) => i + 1);
  }
  const pages = new Set();
  const parts = String(rangeStr).split(',').map(s => s.trim()).filter(Boolean);
  parts.forEach(p => {
    if (p.includes('-')) {
      const [s, e] = p.split('-').map(x => parseInt(x.trim(), 10));
      if (!isNaN(s) && !isNaN(e)) {
        const start = Math.min(s, e);
        const end = Math.max(s, e);
        for (let k = start; k <= end; k++) {
          if (k >= 1 && k <= maxPages) pages.add(k);
        }
      }
    } else {
      const num = parseInt(p, 10);
      if (!isNaN(num) && num >= 1 && num <= maxPages) pages.add(num);
    }
  });
  return pages.size > 0 ? Array.from(pages).sort((a, b) => a - b) : Array.from({ length: maxPages }, (_, i) => i + 1);
}

function exportBeamWithScope(format, overrideScope) {
  const info = getClientPagesInfo();
  const scopeSel = document.getElementById('brmExportPageScope');
  const scope = overrideScope || (scopeSel ? scopeSel.value : 'current');
  const rangeInput = document.getElementById('brmExportPageRangeInput');
  const rangeVal = rangeInput ? rangeInput.value.trim() : '';

  const b = selectedBeamForRebar;
  let filename = (format === 'pdf') ? 'BanVe_Dam_ETABS.pdf' : 'BanVe_Dam_ETABS.dxf';

  if (scope === 'current') {
    if (b) {
      filename = `Dam_${b.story || 'T1'}_${b.longBeamId || b.label}_Trang_${info.currentBeamPageIndex}.${format}`;
    } else {
      filename = `Dam_Trang_${info.currentBeamPageIndex}.${format}`;
    }
    // XUẤT TRỰC TIẾP TỪ SVG ĐANG HIỂN THỊ TRÊN MÀN HÌNH (100% 1:1, KHÔNG VẼ LẠI)
    let currentSvg = window.activeBeamCadSvg;
    if (!currentSvg && b) {
      const chainInfo = findContinuousBeamChain(b);
      currentSvg = generateBeamCadSvg(b, chainInfo);
    }
    const endpoint = (format === 'pdf') ? '/api/export-svg-to-pdf' : '/api/export-svg-to-dxf';
    const payload = { svg: currentSvg, filename: filename, scope: 'current' };
    if (format === 'dxf') {
      payload.custom_layers = getCadLayerConfig();
    }
    downloadExportFile(endpoint, payload, filename);
    return;
  }

  // Multi-page export (All or Range)
  if (scope === 'range') {
    const safeR = (rangeVal || '1').replace(/\s+/g, '').replace(/,/g, '_');
    filename = `BanVe_Dam_ETABS_Trang_${safeR}.${format}`;
  } else {
    filename = `ToanBo_BanVe_Dam_ETABS_AllPages.${format}`;
  }

  const pages = info.pages || [];
  let targetPages = pages;
  if (scope === 'range') {
    const targetIdxs = parseClientPageRange(rangeVal, pages.length);
    targetPages = targetIdxs.map(idx => pages[idx - 1]).filter(Boolean);
  }

  // Tự động sinh SVG cho từng trang theo đúng thông số hiển thị
  const svgPages = [];
  targetPages.forEach(p => {
    const bg = p.beams[0];
    const targetBeam = (bg.beams && bg.beams.length > 0) ? bg.beams[0] : bg;
    const chainInfo = findContinuousBeamChain(targetBeam);
    const svgStr = generateBeamCadSvg(targetBeam, chainInfo);
    svgPages.push(svgStr);
  });

  const payload = {
    svg_pages: svgPages,
    filename: filename,
    scope: scope
  };
  if (format === 'dxf') {
    payload.custom_layers = getCadLayerConfig();
  }

  const endpoint = (format === 'pdf') ? '/api/export-svg-to-pdf' : '/api/export-svg-to-dxf';
  downloadExportFile(endpoint, payload, filename);
}

function exportCurrentBeamPdf() {
  exportBeamWithScope('pdf');
}

function exportCurrentBeamDxf() {
  exportBeamWithScope('dxf');
}

function getAllLongBeamGroups() {
  const beams = (etabsData && etabsData.beams) ? etabsData.beams : [];
  if (beams.length === 0) return [];
  const groups = {};
  beams.forEach(b => {
    const st = b.story || 'T1';
    const lId = b.longBeamId || b.label;
    const key = `${st}::${lId}`;
    if (!groups[key]) {
      groups[key] = {
        story: st,
        long_beam_id: lId,
        commonSection: b.section || '200x400',
        total_length_mm: 0,
        rebar_top_left: b.rebar_top_left,
        rebar_bot_mid: b.rebar_bot_mid,
        rebar_top_right: b.rebar_top_right,
        rebar_hanger: b.rebar_hanger,
        stirrup: b.stirrup,
        beams: []
      };
    }
    groups[key].beams.push(b);
  });
  const res = Object.values(groups);
  res.forEach(g => {
    g.beams.sort((a, b) => (a.spanIndex || 0) - (b.spanIndex || 0));
    g.total_length_mm = g.beams.reduce((sum, b) => sum + (b.length || 0), 0);
  });
  res.sort((a, b) => a.story.localeCompare(b.story) || a.long_beam_id.localeCompare(b.long_beam_id));
  return res;
}

function exportAllBeamsPdf() {
  exportBeamWithScope('pdf', 'all');
}

function exportAllBeamsDxf() {
  exportBeamWithScope('dxf', 'all');
}

function saveAllBeamsToDb() {
  const groups = getAllLongBeamGroups();
  if (groups.length === 0) {
    alert('Không có dữ liệu dầm để lưu!');
    return;
  }
  const designs = groups.map(g => {
    const chainSafety = evaluateChainSafety(g.beams);
    return {
      project_name: 'CAI_TAO_PHUONG_AN_B',
      story: g.story,
      long_beam_id: g.long_beam_id,
      section: g.commonSection,
      span_count: g.beams.length,
      total_length_mm: g.total_length_mm,
      rebar_top_left: g.rebar_top_left,
      rebar_bot_mid: g.rebar_bot_mid,
      rebar_top_right: g.rebar_top_right,
      rebar_hanger: g.rebar_hanger,
      stirrup: g.stirrup,
      is_safe: chainSafety.isSafe,
      safety_status: chainSafety.isSafe ? 'Toàn dầm Đạt' : chainSafety.reason,
      spans_data: g.beams.map(s => ({
        label: s.label,
        story: s.story,
        length: s.length,
        section: s.section,
        width: s.width,
        depth: s.depth
      }))
    };
  });

  fetch('/api/rebar/db/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ designs })
  })
  .then(r => r.json())
  .then(res => {
    alert(`✅ ${res.message || 'Đã lưu toàn bộ thiết kế dầm vào cơ sở dữ liệu thành công!'}`);
    updateDbStatusBadges();
  })
  .catch(err => {
    alert(`Lỗi lưu CSDL: ${err.message}`);
  });
}

function updateDbStatusBadges() {
  fetch('/api/rebar/db/status')
    .then(r => r.json())
    .then(data => {
      const engineName = (data.current_engine === 'postgresql') ? 'PostgreSQL' : 'SQLite';
      const count = (data.current_engine === 'postgresql') ? data.postgresql_count : data.sqlite_count;
      const text = `DB: ${engineName} (${count} dầm)`;
      const brmEl = document.getElementById('brmDbText');
      if (brmEl) brmEl.textContent = text;
      const tblEl = document.getElementById('tableDbText');
      if (tblEl) tblEl.textContent = text;
    })
    .catch(() => {});
}

function loadSavedDesignsFromDb() {
  fetch('/api/rebar/db/load?project_name=CAI_TAO_PHUONG_AN_B')
    .then(r => r.json())
    .then(data => {
      if (data.success && data.designs && data.designs.length > 0) {
        console.log(`[DB] Đã nạp ${data.designs.length} dầm từ CSDL (${data.engine}):`, data.designs);
        const map = {};
        data.designs.forEach(d => {
          map[`${d.story}::${d.long_beam_id}`] = d;
        });
        const beams = (etabsData && etabsData.beams) ? etabsData.beams : [];
        if (beams.length > 0) {
          beams.forEach(b => {
            const key = `${b.story}::${b.longBeamId || b.label}`;
            if (map[key]) {
              const d = map[key];
              b.rebar_top_left = d.rebar_top_left;
              b.rebar_bot_mid = d.rebar_bot_mid;
              b.rebar_top_right = d.rebar_top_right;
              if (d.rebar_hanger) b.rebar_hanger = d.rebar_hanger;
              if (d.stirrup) b.stirrup = d.stirrup;
              b._rebarUserModified = true;
              b._stirrupUserModified = true;
            }
          });
          populateRebarTable('rebarTableBody', 'rebarFilterStory', 'rebarSearchInput');
          renderEtabs2DPlan();
        }
      }
      updateDbStatusBadges();
    })
    .catch(err => console.warn('[DB] Không thể nạp thiết kế từ DB:', err));
}

// ------------------------------------------------------------------------------
// TOP-RIGHT 3D TOOLBAR ACTIONS (WIRE, GRIDS, MOMENTS, RESET, DEPLOY)
// ------------------------------------------------------------------------------

function toggle3DWireframe() {
  is3DWireframe = !is3DWireframe;
  threeMeshes.forEach(m => {
    if (m.material) m.material.wireframe = is3DWireframe;
  });
  modalThreeMeshes.forEach(m => {
    if (m.material) m.material.wireframe = is3DWireframe;
  });

  const btns = [document.getElementById('btn3DWireframe'), document.getElementById('btnModalWireframe')].filter(Boolean);
  btns.forEach(btn => {
    btn.classList.toggle('bg-indigo-600', is3DWireframe);
    btn.classList.toggle('text-white', is3DWireframe);
    btn.classList.toggle('bg-slate-100', !is3DWireframe);
    btn.classList.toggle('text-slate-700', !is3DWireframe);
  });
}

function toggle3DGrids() {
  show3DGrids = !show3DGrids;
  if (threeGridsGroup) threeGridsGroup.visible = show3DGrids;
  if (modalThreeGridsGroup) modalThreeGridsGroup.visible = show3DGrids;

  const btn = document.getElementById('btn3DGrids');
  if (btn) {
    btn.classList.toggle('bg-emerald-600', show3DGrids);
    btn.classList.toggle('text-white', show3DGrids);
    btn.classList.toggle('bg-slate-100', !show3DGrids);
    btn.classList.toggle('text-slate-700', !show3DGrids);
  }
}

function toggle3DMoment() {
  show3DMoments = !show3DMoments;
  if (threeMomentsGroup) threeMomentsGroup.visible = show3DMoments;
  if (modalThreeMomentsGroup) modalThreeMomentsGroup.visible = show3DMoments;

  const btn = document.getElementById('btn3DMoment');
  if (btn) {
    btn.classList.toggle('bg-amber-600', show3DMoments);
    btn.classList.toggle('text-white', show3DMoments);
    btn.classList.toggle('bg-slate-100', !show3DMoments);
    btn.classList.toggle('text-slate-700', !show3DMoments);
  }
}

function toggle3DLegend() {
  const body = document.getElementById('body3DLegend');
  const ico = document.getElementById('ico3DLegendToggle');
  if (!body) return;
  const isHidden = body.classList.toggle('hidden');
  if (ico) {
    ico.style.transition = 'transform 0.2s ease-in-out';
    ico.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
  }
}
window.toggle3DLegend = toggle3DLegend;

function toggle2DLegend() {
  const body = document.getElementById('body2DLegend');
  const ico = document.getElementById('ico2DLegendToggle');
  if (!body) return;
  const isHidden = body.classList.toggle('hidden');
  if (ico) {
    ico.style.transition = 'transform 0.2s ease-in-out';
    ico.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
  }
}
window.toggle2DLegend = toggle2DLegend;

function reset3DCamera() {
  if (threeCamera && threeControls) {
    threeCamera.position.set(16500, 16000, 24000);
    threeControls.target.set(16500, 7600, -6000);
    threeControls.update();
  }
}

function resetModal3DCamera() {
  if (modalThreeCamera && modalThreeControls) {
    modalThreeCamera.position.set(16500, 16000, 24000);
    modalThreeControls.target.set(16500, 7600, -6000);
    modalThreeControls.update();
  }
}

function resizeThreeRenderer(containerId, renderer, camera) {
  const container = document.getElementById(containerId);
  if (!container || !renderer || !camera) return;
  const width = container.clientWidth;
  const height = container.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

// ------------------------------------------------------------------------------
// (4) ONE-CLICK DEPLOY TO https://mr.pkld.online (VPS SYNC)
// ------------------------------------------------------------------------------

async function deployToVps() {
  const ok = confirm('🚀 Bạn có chắc muốn Deploy toàn bộ Hồ Sơ Kết Cấu Dầm lên https://mr.pkld.online (VPS 103.163.219.87) không?');
  if (!ok) return;

  const btns = [document.getElementById('btnDeployVps'), document.getElementById('btnCardDeployVps')].filter(Boolean);
  btns.forEach(b => {
    b.disabled = true;
    b.dataset.oldHtml = b.innerHTML;
    b.innerHTML = '<span class="animate-spin inline-block mr-1">⏳</span> Deploying...';
  });

  try {
    const res = await fetch('/api/deploy-to-vps', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ etabsData: etabsData })
    });
    const result = await res.json();
    if (result.success) {
      alert(`🚀 Deploy thành công lên:\n${result.url || 'https://mr.pkld.online'}\n\nTrang web đã sẵn sàng phục vụ!`);
      window.open('https://mr.pkld.online', '_blank');
    } else {
      alert(`⚠️ Lỗi deploy: ${result.message || 'Không xác định'}`);
    }
  } catch (err) {
    alert(`Lỗi kết nối deploy: ${err.message}`);
  } finally {
    const btn1 = document.getElementById('btnDeployVps');
    if (btn1) {
      btn1.disabled = false;
      btn1.innerHTML = '<i data-lucide="send" class="w-3.5 h-3.5 text-amber-300"></i> Deploy mr.pkld.online';
    }
    const btn2 = document.getElementById('btnCardDeployVps');
    if (btn2) {
      btn2.disabled = false;
      btn2.innerHTML = '<i data-lucide="send" class="w-3.5 h-3.5 text-emerald-200"></i> Deploy';
    }
    if (window.lucide) lucide.createIcons();
  }
}

// ==============================================================================
// 4. REBAR CALCULATION & SELECTION TABLE
// ==============================================================================

function populateRebarTable(tbodyId, storyFilterId, searchInputId) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody || !etabsData || !etabsData.beams) return;

  const storyFilter = storyFilterId && document.getElementById(storyFilterId) ? document.getElementById(storyFilterId).value : 'ALL';
  const searchTerm = searchInputId && document.getElementById(searchInputId) ? document.getElementById(searchInputId).value.toLowerCase().trim() : '';

  let filtered = etabsData.beams;
  if (storyFilter !== 'ALL') {
    filtered = filtered.filter(b => b.story === storyFilter);
  }
  if (searchTerm) {
    filtered = filtered.filter(b => 
      (b.longBeamId && b.longBeamId.toLowerCase().includes(searchTerm)) ||
      (b.axisName && b.axisName.toLowerCase().includes(searchTerm)) ||
      b.label.toLowerCase().includes(searchTerm) || 
      b.section.toLowerCase().includes(searchTerm) ||
      b.story.toLowerCase().includes(searchTerm)
    );
  }
  if (window._filterOnlyFailingRebar) {
    filtered = filtered.filter(b => {
      const chainInfo = findContinuousBeamChain(b);
      const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [b];
      return !evaluateChainSafety(chain).isSafe;
    });
  }

  tbody.innerHTML = '';
  filtered.forEach((b, idx) => {
    const chainInfo = findContinuousBeamChain(b);
    const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [b];
    const safety = evaluateChainSafety(chain);

    const statusBadge = safety.isSafe
      ? `<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px] border border-emerald-300 whitespace-nowrap shadow-2xs" title="${safety.reason}">🟢 Toàn dầm Đạt</span>`
      : `<button type="button" onclick="event.stopPropagation(); openBeamRebarModal(etabsData.beams.find(x => x.label === '${b.label}' && x.story === '${b.story}'))" class="px-2 py-0.5 rounded-full bg-rose-100 hover:bg-rose-200 text-rose-900 font-bold text-[10px] border border-rose-300 whitespace-nowrap shadow-2xs cursor-pointer hover:scale-105 active:scale-95 transition flex items-center gap-1" title="${safety.reason} • Bấm để chuyển tới & sửa dầm này"><span>🔴 ${safety.shortReason}</span><span class="text-[9px] bg-rose-200 px-1 py-0.2 rounded font-extrabold">Sửa ➔</span></button>`;

    const tr = document.createElement('tr');
    tr.className = idx % 2 === 0 ? 'bg-white hover:bg-indigo-50/40 transition cursor-pointer' : 'bg-slate-50/60 hover:bg-indigo-50/40 transition cursor-pointer';
    tr.onclick = (e) => {
      // If clicking button/select ignore, otherwise open modal
      if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'SELECT') {
        openBeamRebarModal(b);
      }
    };

    tr.innerHTML = `
      <td class="p-2.5 text-center font-bold text-slate-700">${b.story}</td>
      <td class="p-2.5 font-bold text-indigo-700 flex items-center gap-2">
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="px-2 py-0.5 rounded-md font-mono text-xs font-extrabold bg-indigo-100 text-indigo-900 border border-indigo-300 shadow-2xs">${b.longBeamId || b.label}</span>
          <span class="text-[10px] text-slate-500 font-medium whitespace-nowrap">Nhịp ${b.spanIndex || 1}/${b.spanCount || 1}</span>
        </div>
        <button onclick="event.stopPropagation(); openBeamRebarModal(etabsData.beams.find(x => x.label === '${b.label}' && x.story === '${b.story}'))" class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-200 text-[10px] font-semibold cursor-pointer ml-auto whitespace-nowrap" title="Chọn cốt thép dầm">Chọn thép</button>
      </td>
      <td class="p-2.5 text-slate-800 font-semibold">${b.section}</td>
      <td class="p-2.5 text-right font-medium text-slate-600">${(b.length/1000).toFixed(2)}m</td>
      <td class="p-2.5 text-right font-bold text-amber-700 bg-amber-50/40">${(b.as_top_left_cm2 || 0).toFixed(2)}</td>
      <td class="p-2.5 text-right font-bold text-amber-700 bg-amber-50/40">${(b.as_bot_mid_cm2 || 0).toFixed(2)}</td>
      <td class="p-2.5 text-right font-bold text-amber-700 bg-amber-50/40">${(b.as_top_right_cm2 || 0).toFixed(2)}</td>
      <td class="p-2.5 text-right font-bold text-sky-700 bg-sky-50/40">${(b.as_shear_cm2_m || 0).toFixed(2)}</td>
      <td class="p-2.5 font-bold text-indigo-950 bg-indigo-50/30">
        <div class="flex items-center gap-1.5 flex-wrap">
          <span class="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-semibold text-[10px]" title="Thép gối trái">${b.rebar_top_left}</span>
          <span class="text-slate-400">/</span>
          <span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 font-bold text-[10px]" title="Thép bụng nhịp">${b.rebar_bot_mid}</span>
          <span class="text-slate-400">/</span>
          <span class="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-semibold text-[10px]" title="Thép gối phải">${b.rebar_top_right}</span>
        </div>
      </td>
      <td class="p-2.5 text-center font-bold text-sky-800 bg-sky-50/20">${b.stirrup}</td>
      <td class="p-2.5 text-center">
        ${statusBadge}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

window._filterOnlyFailingRebar = false;

function toggleFilterFailingRebar() {
  window._filterOnlyFailingRebar = !window._filterOnlyFailingRebar;
  const btn = document.getElementById('btnFilterFailingRebar');
  if (btn) {
    if (window._filterOnlyFailingRebar) {
      btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold border border-rose-500 bg-rose-600 text-white shadow-md transition flex items-center gap-1.5 cursor-pointer ring-2 ring-rose-400/30';
    } else {
      btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold border border-rose-300 bg-rose-50 text-rose-800 hover:bg-rose-100 transition flex items-center gap-1.5 cursor-pointer shadow-2xs';
    }
  }
  filterRebarTable();
}

function filterRebarTable() {
  populateRebarTable('rebarTableBody', 'rebarFilterStory', 'rebarSearchInput');
}

function exportRebarCSV() {
  if (!etabsData || !etabsData.beams) return;
  let csv = '\uFEFFStory,Long_Beam,Span,Spans_Total,Axis,ETABS_Label,Section,Width(mm),Depth(mm),Length(m),As_Top_Left(cm2),As_Bot_Mid(cm2),As_Top_Right(cm2),As_Shear(cm2/m),Rebar_Left,Rebar_Mid,Rebar_Right,Stirrup,Status\n';

  etabsData.beams.forEach(b => {
    const chainInfo = findContinuousBeamChain(b);
    const chain = (chainInfo && chainInfo.chain && chainInfo.chain.length > 0) ? chainInfo.chain : [b];
    const safety = evaluateChainSafety(chain);
    const statusText = safety.isSafe ? 'Toan dam Dat (TCVN 5574)' : `Khong dat (${safety.shortReason})`;

    csv += `"${b.story}","${b.longBeamId || ''}",${b.spanIndex || 1},${b.spanCount || 1},"${b.axisName || ''}","${b.label}","${b.section}",${b.width},${b.depth},${(b.length/1000).toFixed(2)},${b.as_top_left_cm2},${b.as_bot_mid_cm2},${b.as_top_right_cm2},${b.as_shear_cm2_m},"${b.rebar_top_left}","${b.rebar_bot_mid}","${b.rebar_top_right}","${b.stirrup}","${statusText}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Bang_Thong_Ke_Thep_Dam_ETABS_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function printRebarTable() {
  window.print();
}

function setupBeamCanvasEvents() {
  const canvas = document.getElementById('brmDrawingCanvas');
  if (!canvas) return;

  // Mouse Down: Start Pan Dragging
  canvas.addEventListener('mousedown', (e) => {
    brmCadView.isDragging = true;
    brmCadView.hasDragged = false;
    brmCadView.dragStartX = e.clientX - brmCadView.offsetX;
    brmCadView.dragStartY = e.clientY - brmCadView.offsetY;
    canvas.style.cursor = 'grabbing';
  });

  // Window Mouse Move: Pan or Hover detection
  window.addEventListener('mousemove', (e) => {
    if (brmCadView.isDragging) {
      const newX = e.clientX - brmCadView.dragStartX;
      const newY = e.clientY - brmCadView.dragStartY;
      if (Math.hypot(newX - brmCadView.offsetX, newY - brmCadView.offsetY) > 4) {
        brmCadView.hasDragged = true;
      }
      brmCadView.offsetX = newX;
      brmCadView.offsetY = newY;
      renderBeamDrawings();
      return;
    }

    if (e.target !== canvas) return;

    if (beamDrawingMode !== 'chain') {
      canvas.style.cursor = 'grab';
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - brmCadView.offsetX) / brmCadView.scale;
    const y = (e.clientY - rect.top - brmCadView.offsetY) / brmCadView.scale;

    let hovering = false;
    for (const box of chainInteractiveBoxes) {
      if (x >= box.x1 && x <= box.x2 && y >= box.y1 && y <= box.y2) {
        hovering = true;
        break;
      }
    }
    canvas.style.cursor = hovering ? 'pointer' : 'grab';
  });

  // Window Mouse Up: End Pan Dragging
  window.addEventListener('mouseup', () => {
    if (brmCadView.isDragging) {
      brmCadView.isDragging = false;
      canvas.style.cursor = 'grab';
    }
  });

  // Mouse Wheel: Zoom centered at cursor
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    brmCadView.offsetX = mouseX - (mouseX - brmCadView.offsetX) * zoomFactor;
    brmCadView.offsetY = mouseY - (mouseY - brmCadView.offsetY) * zoomFactor;
    brmCadView.scale = Math.max(0.3, Math.min(6.0, brmCadView.scale * zoomFactor));
    renderBeamDrawings();
  }, { passive: false });

  // Canvas Click: Only trigger selection if not dragged
  canvas.addEventListener('click', (e) => {
    if (brmCadView.hasDragged) return; // Ignore drag clicks
    if (beamDrawingMode !== 'chain') return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - brmCadView.offsetX) / brmCadView.scale;
    const y = (e.clientY - rect.top - brmCadView.offsetY) / brmCadView.scale;

    for (const box of chainInteractiveBoxes) {
      if (x >= box.x1 && x <= box.x2 && y >= box.y1 && y <= box.y2) {
        if (box.beam && box.beam.label !== selectedBeamForRebar?.label) {
          openBeamRebarModal(box.beam);
        }
        break;
      }
    }
  });

  window.addEventListener('resize', () => {
    const modal = document.getElementById('beamRebarModal');
    if (modal && !modal.classList.contains('hidden') && selectedBeamForRebar) {
      if (beamDrawingMode === '3d') {
        renderBeam3DRebar();
      } else {
        renderBeamDrawings();
      }
    }
  });
}

// Quick Beam Navigation in Modal (Prev, Next, Dropdown) - Chỉ hiển thị dầm dài (Long Beams)
function populateBeamNavSelect(activeBeam) {
  const sel = document.getElementById('brmBeamNavSelect');
  if (!sel || !etabsData || !etabsData.beams) return;

  const longBeams = getLongBeamsList();
  window._sortedLongBeams = longBeams;

  sel.innerHTML = '';
  longBeams.forEach(lb => {
    const opt = document.createElement('option');
    opt.value = lb.key;
    const axisText = lb.axisName ? ` [${lb.axisName}]` : '';
    const safety = evaluateChainSafety(lb.beams || (lb.firstBeam ? findContinuousBeamChain(lb.firstBeam).chain : []));
    const failPrefix = safety.isSafe ? '' : '⚠️ [CHƯA ĐẠT] ';
    opt.textContent = `${failPrefix}${lb.longBeamId} (${lb.numSpans} nhịp) • ${lb.commonSection} • L=${(lb.totalLength/1000).toFixed(2)}m • ${lb.story}${axisText}`;
    if (!safety.isSafe) {
      opt.style.color = '#b91c1c';
      opt.style.fontWeight = 'bold';
    }
    if (activeBeam) {
      const activeLongId = activeBeam.longBeamId || activeBeam.label;
      if (lb.story === activeBeam.story && lb.longBeamId === activeLongId) {
        opt.selected = true;
      }
    }
    sel.appendChild(opt);
  });
}

function navigateBeamRebarModal(delta) {
  if (!window._sortedLongBeams || window._sortedLongBeams.length === 0) {
    populateBeamNavSelect(selectedBeamForRebar);
  }
  const longBeams = window._sortedLongBeams || [];
  if (!longBeams.length || !selectedBeamForRebar) return;

  const curLongId = selectedBeamForRebar.longBeamId || selectedBeamForRebar.label;
  const curStory = selectedBeamForRebar.story;
  const curIdx = longBeams.findIndex(x => x.longBeamId === curLongId && x.story === curStory);
  let nextIdx = (curIdx === -1) ? 0 : curIdx + delta;
  if (nextIdx < 0) nextIdx = longBeams.length - 1;
  if (nextIdx >= longBeams.length) nextIdx = 0;

  const targetLb = longBeams[nextIdx];
  if (targetLb && targetLb.firstBeam) {
    openBeamRebarModal(targetLb.firstBeam);
  }
}

function onBeamNavSelectChange(val) {
  if (!val || !etabsData || !etabsData.beams) return;
  const longBeams = window._sortedLongBeams || getLongBeamsList();
  const targetLb = longBeams.find(x => x.key === val);
  if (targetLb && targetLb.firstBeam) {
    openBeamRebarModal(targetLb.firstBeam);
  }
}

// Global window exports for modal controls
window.setBeamDrawingMode = setBeamDrawingMode;
window.toggleBrm3DSource = toggleBrm3DSource;
window.toggleBrm3DConcrete = toggleBrm3DConcrete;
window.resetBrm3DCamera = resetBrm3DCamera;
window.renderBeam3DRebar = renderBeam3DRebar;
window.openBeamRebarModal = openBeamRebarModal;
window.closeBeamRebarModal = closeBeamRebarModal;
window.saveBeamRebarSelection = saveBeamRebarSelection;
window.onRebarSelectChange = onRebarSelectChange;
window.findContinuousBeamChain = findContinuousBeamChain;
window.populateBeamNavSelect = populateBeamNavSelect;
window.navigateBeamRebarModal = navigateBeamRebarModal;
window.onBeamNavSelectChange = onBeamNavSelectChange;
window.exportCurrentBeamPdf = exportCurrentBeamPdf;
window.exportCurrentBeamDxf = exportCurrentBeamDxf;
window.exportAllBeamsPdf = exportAllBeamsPdf;
window.exportAllBeamsDxf = exportAllBeamsDxf;
window.saveAllBeamsToDb = saveAllBeamsToDb;
window.updateDbStatusBadges = updateDbStatusBadges;
window.updateModalHeaderSafetyAlert = updateModalHeaderSafetyAlert;
window.onExportScopeChange = onExportScopeChange;
window.updateExportScopeUI = updateExportScopeUI;
window.exportBeamWithScope = exportBeamWithScope;
window.jumpToNextFailingBeam = jumpToNextFailingBeam;
window.jumpToFailingBeam = jumpToFailingBeam;
window.focusFailingSpanOfCurrentBeam = focusFailingSpanOfCurrentBeam;
window.toggleFailingBeamsMenu = toggleFailingBeamsMenu;
window.closeFailingBeamsMenu = closeFailingBeamsMenu;
window.toggleFilterFailingRebar = toggleFilterFailingRebar;
window.showToastNotification = showToastNotification;

// ==============================================================================
// BẢNG CHI TIẾT TIẾT DIỆN CỘT TOÀN NHÀ (GRID 18 CỘT × 4 TẦNG)
// ==============================================================================

let columnMatrixData = null;

const colModalViewState = { zoom: 1.0, panX: 0, panY: 0, isDragging: false, dragStartX: 0, dragStartY: 0, hoveredCell: null };
const colTabViewState = { zoom: 1.0, panX: 0, panY: 0, isDragging: false, dragStartX: 0, dragStartY: 0, hoveredCell: null };
const colEtabsModalViewState = { zoom: 1.0, panX: 0, panY: 0, isDragging: false, dragStartX: 0, dragStartY: 0, hoveredCell: null };

const COL_SHEET = {
  sheetW: 2800,
  sheetH: 1750,
  marginLeft: 160,
  marginRight: 60,
  marginTop: 120,
  marginBottom: 60,
  storyColW: 160,
  colHeaderH: 90
};

async function loadColumnMatrixData() {
  if (columnMatrixData) return columnMatrixData;
  try {
    const res = await fetch('/api/column-matrix');
    const json = await res.json();
    if (json.success && json.data) {
      columnMatrixData = json.data;
      return columnMatrixData;
    }
  } catch (e) {
    console.warn('Lỗi nạp /api/column-matrix, thử /column_matrix.json:', e);
  }
  try {
    const res2 = await fetch('/column_matrix.json');
    const json2 = await res2.json();
    if (json2.success && json2.data) {
      columnMatrixData = json2.data;
      return columnMatrixData;
    }
  } catch (e2) {
    console.error('Lỗi nạp column matrix data:', e2);
  }
  return null;
}

function drawColumnSheetOnCanvas(canvasId, viewState, badgeId, textId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  const dpr = window.devicePixelRatio || 1;
  const targetW = Math.round(rect.width * dpr);
  const targetH = Math.round(rect.height * dpr);
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
  }

  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.scale(dpr, dpr);

  // Background workspace
  ctx.fillStyle = '#f1f5f9';
  ctx.fillRect(0, 0, rect.width, rect.height);

  // Apply Pan & Zoom
  ctx.translate(viewState.panX, viewState.panY);
  ctx.scale(viewState.zoom, viewState.zoom);

  const { sheetW, sheetH, marginLeft, marginRight, marginTop, marginBottom, storyColW, colHeaderH } = COL_SHEET;

  // 1. Paper sheet with drop shadow
  ctx.save();
  ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
  ctx.shadowBlur = 15;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 6;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, sheetW, sheetH);
  ctx.restore();

  // 2. Outer Border (CAD standard double line)
  ctx.strokeStyle = '#0f172a';
  ctx.lineWidth = 2.5;
  ctx.strokeRect(marginLeft * 0.4, 25, sheetW - marginLeft * 0.4 - 25, sheetH - 50);

  ctx.lineWidth = 1.0;
  ctx.strokeRect(marginLeft * 0.4 + 6, 31, sheetW - marginLeft * 0.4 - 37, sheetH - 62);

  // 3. Sheet Title & Header
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 30px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('BẢNG CHI TIẾT TIẾT DIỆN CỘT QUA CÁC TẦNG (GRID 15 CỘT × 4 TẦNG)', marginLeft, 45);

  ctx.fillStyle = '#475569';
  ctx.font = '500 15px sans-serif';
  const modelName = (columnMatrixData && columnMatrixData.model_name) || 'CAI_TAO_PHUONG_AN_B.EDB';
  ctx.fillText(`DỰ ÁN: ${modelName}  •  TCVN 5574:2018  •  TỈ LỆ 1/25  •  BÊ TÔNG B22.5 (M300)  •  THÉP DỌC CB400-V, ĐAI CB240-T`, marginLeft, 85);

  // 4. Ghi chú kỹ thuật ở chân bản vẽ (Không khung tên title block)
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 13px sans-serif';
  ctx.fillText('GHI CHÚ THI CÔNG:', marginLeft, sheetH - 40);
  ctx.fillStyle = '#475569';
  ctx.font = '12px sans-serif';
  ctx.fillText('1. Bê tông B22.5 (M300), c = 25mm. Đoạn nối chồng cốt thép dọc L_nối >= 35d (>= 700mm).  •  2. Thép đai f6a100 ở 2 đầu cột (500mm tính từ mặt dầm/sàn), vùng giữa cột bố trí f6a200.', marginLeft + 140, sheetH - 40);

  // 6. Grid Table Matrix
  const gridX = marginLeft;
  const gridY = marginTop;
  const gridW = sheetW - marginLeft - marginRight;
  const gridH = sheetH - marginTop - marginBottom;

  const columnLabels = (columnMatrixData && columnMatrixData.column_labels) || Array.from({ length: 15 }, (_, i) => `C${i + 1}`);
  const colsW = gridW - storyColW;
  const cellW = colsW / Math.max(1, columnLabels.length);
  const rowsH = gridH - colHeaderH;
  const cellH = rowsH / 4.0;

  // Outer grid table box
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 2.0;
  ctx.strokeRect(gridX, gridY, gridW, gridH);

  // Column header background
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(gridX, gridY, gridW, colHeaderH);

  // Story header background
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(gridX, gridY + colHeaderH, storyColW, rowsH);

  // Corner cell
  ctx.fillStyle = '#f1f5f9';
  ctx.fillRect(gridX, gridY, storyColW, colHeaderH);
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 1.0;
  ctx.beginPath();
  ctx.moveTo(gridX, gridY);
  ctx.lineTo(gridX + storyColW, gridY + colHeaderH);
  ctx.stroke();

  ctx.fillStyle = '#1e293b';
  ctx.font = 'bold 13px sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText('MÃ CỘT', gridX + storyColW - 12, gridY + 16);
  ctx.textAlign = 'left';
  ctx.fillText('TẦNG', gridX + 14, gridY + colHeaderH - 28);

  // Column Headers (C1 to C15)
  const colMeta = (columnMatrixData && columnMatrixData.column_meta) || {};
  const stories = (columnMatrixData && columnMatrixData.stories) || [
    { id: 'T4', name: 'TẦNG 4', elevation: '+10.800' },
    { id: 'T3', name: 'TẦNG 3', elevation: '+7.200' },
    { id: 'T2', name: 'TẦNG 2', elevation: '+3.600' },
    { id: 'T1', name: 'TẦNG 1', elevation: '±0.000' }
  ];
  const cells = (columnMatrixData && columnMatrixData.cells) || {};

  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 1.0;
  columnLabels.forEach((lbl, colIdx) => {
    const cx = gridX + storyColW + colIdx * cellW;
    ctx.beginPath();
    ctx.moveTo(cx, gridY);
    ctx.lineTo(cx, gridY + gridH);
    ctx.stroke();

    const meta = colMeta[lbl] || { grid: '---' };
    const axisStr = (meta.grid && meta.grid !== '---') ? `Trục ${meta.grid}` : '---';

    ctx.textAlign = 'center';
    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 18px monospace';
    ctx.fillText(lbl, cx + cellW / 2.0, gridY + 18);

    ctx.fillStyle = '#64748b';
    ctx.font = '12px sans-serif';
    ctx.fillText(axisStr, cx + cellW / 2.0, gridY + 52);
  });

  // Story Headers & Cell rendering
  stories.forEach((stInfo, rowIdx) => {
    const cy = gridY + colHeaderH + rowIdx * cellH;

    // Horizontal grid divider
    ctx.beginPath();
    ctx.moveTo(gridX, cy);
    ctx.lineTo(gridX + gridW, cy);
    ctx.stroke();

    // Story Header on the left
    ctx.textAlign = 'center';
    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 16px sans-serif';
    ctx.fillText(stInfo.name, gridX + storyColW / 2.0, cy + cellH * 0.42);

    ctx.fillStyle = '#64748b';
    ctx.font = '13px sans-serif';
    ctx.fillText(`Cốt: ${stInfo.elevation}`, gridX + storyColW / 2.0, cy + cellH * 0.58);

    // Render cells in this row
    columnLabels.forEach((lbl, colIdx) => {
      const cellX = gridX + storyColW + colIdx * cellW;
      const cellY = cy;

      const cellKey = `${stInfo.id}_${lbl}`;
      const cellData = cells[cellKey];

      const isHovered = viewState.hoveredCell && viewState.hoveredCell.story === stInfo.id && viewState.hoveredCell.label === lbl;

      if (isHovered) {
        ctx.fillStyle = 'rgba(245, 158, 11, 0.12)';
        ctx.fillRect(cellX + 1, cellY + 1, cellW - 2, cellH - 2);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(cellX + 1, cellY + 1, cellW - 2, cellH - 2);
      }

      if (!cellData || !cellData.exists) {
        // Empty cell
        ctx.save();
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1.0;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(cellX + 10, cellY + 10); ctx.lineTo(cellX + cellW - 10, cellY + cellH - 10);
        ctx.moveTo(cellX + 10, cellY + cellH - 10); ctx.lineTo(cellX + cellW - 10, cellY + 10);
        ctx.stroke();
        ctx.restore();

        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('— KHÔNG CÓ CỘT —', cellX + cellW / 2.0, cellY + cellH / 2.0);
        return;
      }

      // Draw cross section in cell
      const bW = cellData.width || 250;
      const bH = cellData.depth || 300;
      const rebarStr = cellData.rebar_str || '4Φ18';
      const stirrupStr = cellData.stirrup_str || 'd6a100/200';
      const hasCrosstie = cellData.has_crosstie || (bH >= 500);

      // Isometric scale inside cell
      const maxDrawW = cellW * 0.44;
      const maxDrawH = cellH * 0.48;
      const scaleCS = Math.min(maxDrawW / bW, maxDrawH / bH);

      const drawW = bW * scaleCS;
      const drawH = bH * scaleCS;

      const cxCenter = cellX + cellW / 2.0;
      const cyCenter = cellY + cellH * 0.50;

      const rectX = cxCenter - drawW / 2.0;
      const rectY = cyCenter - drawH / 2.0;

      // 1. Concrete contour
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 2.0;
      ctx.fillRect(rectX, rectY, drawW, drawH);
      ctx.strokeRect(rectX, rectY, drawW, drawH);

      // 2. Stirrup with 25mm cover
      const cover = Math.max(3.5, 25.0 * scaleCS);
      const stX = rectX + cover;
      const stY = rectY + cover;
      const stW = Math.max(4.0, drawW - cover * 2.0);
      const stH = Math.max(4.0, drawH - cover * 2.0);

      ctx.strokeStyle = '#0284c7';
      ctx.lineWidth = 1.6;
      ctx.strokeRect(stX, stY, stW, stH);

      // 2 hooks at 135 deg in top-left
      const hk = Math.max(3.0, 28.0 * scaleCS);
      ctx.beginPath();
      ctx.moveTo(stX + 1, stY + 1); ctx.lineTo(stX + hk * 0.8, stY + hk * 0.8);
      ctx.moveTo(stX + 3, stY + 1); ctx.lineTo(stX + hk * 0.8 + 2, stY + hk * 0.8);
      ctx.stroke();

      // Crossties if 8 bars
      if (hasCrosstie && stH > 30) {
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 1.3;
        const yTie1 = stY + stH / 3.0;
        const yTie2 = stY + 2.0 * stH / 3.0;
        ctx.beginPath();
        ctx.moveTo(stX, yTie1); ctx.lineTo(stX + stW, yTie1);
        ctx.moveTo(stX, yTie2); ctx.lineTo(stX + stW, yTie2);
        ctx.moveTo(stX, yTie1); ctx.lineTo(stX + 3, yTie1 - 3);
        ctx.moveTo(stX + stW, yTie1); ctx.lineTo(stX + stW - 3, yTie1 - 3);
        ctx.moveTo(stX, yTie2); ctx.lineTo(stX + 3, yTie2 - 3);
        ctx.moveTo(stX + stW, yTie2); ctx.lineTo(stX + stW - 3, yTie2 - 3);
        ctx.stroke();
      }

      // 3. Rebar dots (Red 0.50 mm)
      const dotR = Math.max(2.4, Math.min(4.2, 10.0 * scaleCS));
      const inset = Math.max(dotR + 1.2, cover + dotR * 0.6);
      const rxL = rectX + inset;
      const rxR = rectX + drawW - inset;
      const ryT = rectY + inset;
      const ryB = rectY + drawH - inset;

      const dots = [
        [rxL, ryT], [rxR, ryT],
        [rxL, ryB], [rxR, ryB]
      ];

      if (hasCrosstie || rebarStr.startsWith('8') || bH >= 500) {
        const yM1 = ryT + (ryB - ryT) / 3.0;
        const yM2 = ryT + 2.0 * (ryB - ryT) / 3.0;
        dots.push([rxL, yM1], [rxR, yM1], [rxL, yM2], [rxR, yM2]);
      }

      ctx.fillStyle = '#dc2626';
      ctx.strokeStyle = '#7f1d1d';
      ctx.lineWidth = 1.0;
      dots.forEach(([dx, dy]) => {
        ctx.beginPath();
        ctx.arc(dx, dy, dotR, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      });

      // 4. CAD Dimensions
      const dimDistB = Math.max(14, drawH * 0.16);
      drawCadDimension(ctx, rectX, rectY + drawH, rectX + drawW, rectY + drawH, `${Math.round(bW)}`, dimDistB, false, '#16a34a');

      const dimDistH = -Math.max(14, drawW * 0.20);
      drawCadDimension(ctx, rectX, rectY, rectX, rectY + drawH, `${Math.round(bH)}`, dimDistH, true, '#16a34a');

      // 5. Rebar Leader
      ctx.fillStyle = '#dc2626';
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 1.3;
      ctx.font = 'bold 12px monospace';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'bottom';

      const rebElbowX = rxR + Math.max(8, drawW * 0.18);
      const rebElbowY = ryT - Math.max(8, drawH * 0.16);
      const rebTextW = ctx.measureText(rebarStr).width;
      const rebShelfEnd = rebElbowX + Math.max(28, rebTextW + 8);

      ctx.beginPath();
      ctx.moveTo(rxR, ryT);
      ctx.lineTo(rebElbowX, rebElbowY);
      ctx.lineTo(rebShelfEnd, rebElbowY);
      ctx.stroke();
      ctx.fillText(rebarStr, rebElbowX + 3, rebElbowY - 2);

      // 6. Stirrup Leader
      ctx.fillStyle = '#0284c7';
      ctx.strokeStyle = '#0284c7';
      ctx.lineWidth = 1.2;
      ctx.font = 'bold 11px monospace';

      const stElbowX = stX - Math.max(8, drawW * 0.16);
      const stElbowY = cyCenter - Math.max(8, drawH * 0.14);
      const stTextW = ctx.measureText(stirrupStr).width;
      const stShelfEnd = stElbowX - Math.max(26, stTextW + 8);

      ctx.beginPath();
      ctx.arc(stX, cyCenter, 2.0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(stX, cyCenter);
      ctx.lineTo(stElbowX, stElbowY);
      ctx.lineTo(stShelfEnd, stElbowY);
      ctx.stroke();
      ctx.fillText(stirrupStr, stShelfEnd + 3, stElbowY - 2);

      // 7. Title Below
      ctx.fillStyle = '#0f172a';
      ctx.font = 'bold 13px monospace';
      ctx.textAlign = 'center';
      const cleanSec = (cellData.section_name || `${bW}x${bH}`).replace('C1 ', '').replace('C2 ', '').replace('C3 ', '');
      ctx.fillText(`${lbl} (${cleanSec})`, cxCenter, cellY + cellH - 12);
    });
  });

  ctx.restore();
}

function setupColumnCanvasEvents(canvasId, viewState, renderFunc, badgeId, textId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  function getVirtualCoord(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const sx = (mx - viewState.panX) / viewState.zoom;
    const sy = (my - viewState.panY) / viewState.zoom;
    return { sx, sy };
  }

  function getCellAt(sx, sy) {
    const { sheetW, sheetH, marginLeft, marginRight, marginTop, marginBottom, storyColW, colHeaderH } = COL_SHEET;
    const gridX = marginLeft;
    const gridY = marginTop;
    const gridW = sheetW - marginLeft - marginRight;
    const gridH = sheetH - marginTop - marginBottom;
    const columnLabels = (columnMatrixData && columnMatrixData.column_labels) || Array.from({ length: 15 }, (_, i) => `C${i + 1}`);
    const colsW = gridW - storyColW;
    const cellW = colsW / Math.max(1, columnLabels.length);
    const rowsH = gridH - colHeaderH;
    const cellH = rowsH / 4.0;

    if (sx < gridX + storyColW || sx > gridX + gridW || sy < gridY + colHeaderH || sy > gridY + gridH) {
      return null;
    }

    const colIdx = Math.floor((sx - (gridX + storyColW)) / cellW);
    const rowIdx = Math.floor((sy - (gridY + colHeaderH)) / cellH);

    if (colIdx < 0 || colIdx >= columnLabels.length || rowIdx < 0 || rowIdx >= 4) return null;
    const stories = (columnMatrixData && columnMatrixData.stories) || [
      { id: 'T4', name: 'TẦNG 4', elevation: '+10.800' },
      { id: 'T3', name: 'TẦNG 3', elevation: '+7.200' },
      { id: 'T2', name: 'TẦNG 2', elevation: '+3.600' },
      { id: 'T1', name: 'TẦNG 1', elevation: '±0.000' }
    ];

    const lbl = columnLabels[colIdx];
    const st = stories[rowIdx];
    const cellKey = `${st.id}_${lbl}`;
    const cellData = (columnMatrixData && columnMatrixData.cells && columnMatrixData.cells[cellKey]) || null;

    return { colIdx, rowIdx, label: lbl, story: st.id, storyName: st.name, elevation: st.elevation, data: cellData };
  }

  canvas.addEventListener('mousedown', (e) => {
    viewState.isDragging = true;
    viewState.dragStartX = e.clientX - viewState.panX;
    viewState.dragStartY = e.clientY - viewState.panY;
    canvas.style.cursor = 'grabbing';
  });

  window.addEventListener('mouseup', () => {
    if (viewState.isDragging) {
      viewState.isDragging = false;
      canvas.style.cursor = 'grab';
    }
  });

  canvas.addEventListener('mousemove', (e) => {
    if (viewState.isDragging) {
      viewState.panX = e.clientX - viewState.dragStartX;
      viewState.panY = e.clientY - viewState.dragStartY;
      renderFunc();
      return;
    }

    const { sx, sy } = getVirtualCoord(e);
    const cell = getCellAt(sx, sy);
    const prevCell = viewState.hoveredCell;

    const changed = (!prevCell && cell) || (prevCell && !cell) || (prevCell && cell && (prevCell.label !== cell.label || prevCell.story !== cell.story));

    if (changed) {
      viewState.hoveredCell = cell;
      renderFunc();

      const textEl = document.getElementById(textId);
      if (textEl) {
        if (cell && cell.data && cell.data.exists) {
          const d = cell.data;
          const cleanSec = (d.section_name || `${d.width}x${d.depth}`).replace('C1 ', '').replace('C2 ', '').replace('C3 ', '');
          textEl.textContent = `🏛️ Cột ${cell.label} • ${cell.storyName} (${cell.elevation}) • Tiết diện: ${cleanSec} mm • Thép dọc: ${d.rebar_str} • Đai: ${d.stirrup_str} • Trục: ${d.grid}`;
        } else if (cell) {
          textEl.textContent = `🏛️ Cột ${cell.label} • ${cell.storyName} (${cell.elevation}) • [Không có cột tại vị trí này]`;
        } else {
          textEl.textContent = 'Rê chuột vào tiết diện cột để xem chi tiết';
        }
      }
    }
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    const newZoom = Math.max(0.15, Math.min(6.0, viewState.zoom * zoomFactor));

    viewState.panX = mx - (mx - viewState.panX) * (newZoom / viewState.zoom);
    viewState.panY = my - (my - viewState.panY) * (newZoom / viewState.zoom);
    viewState.zoom = newZoom;

    renderFunc();
  }, { passive: false });
}

function fitColumnCadToContainer(canvasId, viewState, renderFunc) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  const { sheetW, sheetH } = COL_SHEET;
  const scaleX = (rect.width - 24) / sheetW;
  const scaleY = (rect.height - 24) / sheetH;
  const fitZoom = Math.min(scaleX, scaleY);

  viewState.zoom = fitZoom;
  viewState.panX = Math.round((rect.width - sheetW * fitZoom) / 2);
  viewState.panY = Math.round((rect.height - sheetH * fitZoom) / 2);

  renderFunc();
}

// 1. Full Modal Controls
function renderModalColumnCadFull() {
  drawColumnSheetOnCanvas('columnCadCanvas', colModalViewState, 'columnCadHoverBadge', 'columnCadHoverText');
}
function fitColumnCadView() {
  fitColumnCadToContainer('columnCadCanvas', colModalViewState, renderModalColumnCadFull);
}
function zoomColumnCad(factor) {
  colModalViewState.zoom = Math.max(0.15, Math.min(6.0, colModalViewState.zoom * factor));
  renderModalColumnCadFull();
}
function resetColumnCadView() {
  colModalViewState.zoom = 1.0;
  colModalViewState.panX = 0;
  colModalViewState.panY = 0;
  renderModalColumnCadFull();
}
async function openColumnDrawingModal() {
  const modal = document.getElementById('columnDrawingModal');
  if (modal) {
    modal.classList.remove('hidden');
    await loadColumnMatrixData();
    setTimeout(() => {
      fitColumnCadView();
    }, 100);
  }
}
function closeColumnDrawingModal() {
  const modal = document.getElementById('columnDrawingModal');
  if (modal) modal.classList.add('hidden');
}

// 2. Tab Pane Controls
function renderTabColumnCad() {
  drawColumnSheetOnCanvas('tabColumnCadCanvas', colTabViewState, 'tabColumnCadHoverBadge', 'tabColumnCadHoverText');
}
function fitTabColumnCadView() {
  fitColumnCadToContainer('tabColumnCadCanvas', colTabViewState, renderTabColumnCad);
}
function zoomTabColumnCad(factor) {
  colTabViewState.zoom = Math.max(0.15, Math.min(6.0, colTabViewState.zoom * factor));
  renderTabColumnCad();
}
function resetTabColumnCadView() {
  colTabViewState.zoom = 1.0;
  colTabViewState.panX = 0;
  colTabViewState.panY = 0;
  renderTabColumnCad();
}

// 3. Etabs Modal Pane Controls
function renderModalColumnCad() {
  drawColumnSheetOnCanvas('modalColumnCadCanvas', colEtabsModalViewState, 'modalColumnCadHoverBadge', 'modalColumnCadHoverText');
}
function fitModalColumnCadView() {
  fitColumnCadToContainer('modalColumnCadCanvas', colEtabsModalViewState, renderModalColumnCad);
}
function zoomModalColumnCad(factor) {
  colEtabsModalViewState.zoom = Math.max(0.15, Math.min(6.0, colEtabsModalViewState.zoom * factor));
  renderModalColumnCad();
}

// 4. Export Handlers
async function exportColumnSheetPdf() {
  if (typeof showToastNotification === 'function') {
    showToastNotification('⚡ Đang chuẩn bị tải file PDF Bản Vẽ Cột (Grid 15×4)...', 'info');
  }
  window.location.href = '/api/export-column-pdf';
}
async function exportColumnSheetDxf() {
  if (typeof showToastNotification === 'function') {
    showToastNotification('⚡ Đang chuẩn bị tải file DXF Bản Vẽ Cột (AutoCAD R2010)...', 'info');
  }
  window.location.href = '/api/export-column-dxf';
}

// Global window exports
window.openColumnDrawingModal = openColumnDrawingModal;
window.closeColumnDrawingModal = closeColumnDrawingModal;
window.fitColumnCadView = fitColumnCadView;
window.zoomColumnCad = zoomColumnCad;
window.resetColumnCadView = resetColumnCadView;
window.renderTabColumnCad = renderTabColumnCad;
window.fitTabColumnCadView = fitTabColumnCadView;
window.zoomTabColumnCad = zoomTabColumnCad;
window.resetTabColumnCadView = resetTabColumnCadView;
window.renderModalColumnCad = renderModalColumnCad;
window.fitModalColumnCadView = fitModalColumnCadView;
window.zoomModalColumnCad = zoomModalColumnCad;
window.exportColumnSheetPdf = exportColumnSheetPdf;
window.exportColumnSheetDxf = exportColumnSheetDxf;

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  setup2DCanvasEvents('etabs2DCanvas', view2D, renderEtabs2DPlan);
  setup2DCanvasEvents('modal2DCanvas', modalView2D, renderModal2DPlan);
  setupBeamCanvasEvents();
  initBrmLayoutSheetControls();
  updateBrmLayoutSheetControls();

  // Setup Column Sheet Canvas Events
  setupColumnCanvasEvents('columnCadCanvas', colModalViewState, renderModalColumnCadFull, 'columnCadHoverBadge', 'columnCadHoverText');
  setupColumnCanvasEvents('tabColumnCadCanvas', colTabViewState, renderTabColumnCad, 'tabColumnCadHoverBadge', 'tabColumnCadHoverText');
  setupColumnCanvasEvents('modalColumnCadCanvas', colEtabsModalViewState, renderModalColumnCad, 'modalColumnCadHoverBadge', 'modalColumnCadHoverText');
  
  // Pre-load data in background and update DB badge
  setTimeout(() => {
    loadEtabsData();
    loadColumnMatrixData();
    loadTieBeamData();
    updateDbStatusBadges();
  }, 400);

  // Setup Tie Beam Sheet Canvas Events
  setupTieBeamCanvasEvents('tabTieBeamCadCanvas', tieBeamTabViewState, renderTabTieBeamCad, 'tabTieBeamCadHoverBadge', 'tabTieBeamCadHoverText');
  setupTieBeamCanvasEvents('tieBeamCadCanvas', tieBeamModalViewState, renderModalTieBeamCad, 'tieBeamCadHoverBadge', 'tieBeamCadHoverText');
});


// ============================================================================
// (8) BẢN VẼ CHI TIẾT ĐÀ KIỀNG TRỤC A, B, C (CHỊU PHẢN LỰC ĐẤT NỀN ĐẨY LÊN)
// ============================================================================

let tieBeamData = null;
let tieBeamTabViewState = { zoom: 0.48, panX: 45, panY: 35, isDragging: false, startX: 0, startY: 0, hoveredSpan: null };
let tieBeamModalViewState = { zoom: 0.58, panX: 60, panY: 45, isDragging: false, startX: 0, startY: 0, hoveredSpan: null };
let tieBeamInteractiveBoxes = [];

const TIE_SHEET = {
  sheetW: 2384,
  sheetH: 1684,
  marginLeft: 65,
  marginRight: 40,
  marginTop: 40,
  marginBottom: 40
};

async function loadTieBeamData() {
  if (tieBeamData) return tieBeamData;
  try {
    const res = await fetch('/api/tie-beam-data');
    const json = await res.json();
    if (json.success && json.data) {
      tieBeamData = json.data;
      return tieBeamData;
    }
  } catch (e) {
    console.warn('Lỗi nạp /api/tie-beam-data, thử tải /tie_beam_data.json:', e);
  }
  try {
    const res2 = await fetch('/tie_beam_data.json');
    const json2 = await res2.json();
    if (json2.success && json2.data) {
      tieBeamData = json2.data;
      return tieBeamData;
    }
  } catch (e2) {
    console.error('Lỗi nạp tie beam data:', e2);
  }
  return null;
}

function drawTieBeamSheetOnCanvas(canvasId, viewState, badgeId, textId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  const dpr = window.devicePixelRatio || 1;
  const targetW = Math.round(rect.width * dpr);
  const targetH = Math.round(rect.height * dpr);
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
  }

  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.scale(dpr, dpr);

  // Background workspace
  ctx.fillStyle = '#f1f5f9';
  ctx.fillRect(0, 0, rect.width, rect.height);

  // Apply Pan & Zoom
  ctx.translate(viewState.panX, viewState.panY);
  ctx.scale(viewState.zoom, viewState.zoom);

  const { sheetW, sheetH, marginLeft, marginRight, marginTop, marginBottom } = TIE_SHEET;

  // 1. Paper sheet with drop shadow
  ctx.save();
  ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
  ctx.shadowBlur = 15;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 6;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, sheetW, sheetH);
  ctx.restore();

  // 2. Outer Border (CAD standard double line)
  ctx.strokeStyle = '#0f172a';
  ctx.lineWidth = 2.5;
  ctx.strokeRect(marginLeft, marginTop, sheetW - marginLeft - marginRight, sheetH - marginTop - marginBottom);

  ctx.lineWidth = 1.0;
  ctx.strokeRect(marginLeft + 6, marginTop + 6, sheetW - marginLeft - marginRight - 12, sheetH - marginTop - marginBottom - 12);

  // 3. Main Sheet Title Banner
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 24px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('BẢN VẼ CHI TIẾT ĐÀ KIỀNG DỌC THEO TRỤC A, B, C (TẦNG 1 / MÓNG)', marginLeft + 20, marginTop + 18);

  ctx.fillStyle = '#475569';
  ctx.font = '13px sans-serif';
  ctx.fillText('DỰ ÁN: CẢI TẠO PHƯƠNG ÁN B • TCVN 5574:2018 • BỐ TRÍ THÉP XÉT ĐẾN TÁC ĐỘNG CỦA PHẢN LỰC ĐẤT NỀN ĐẨY LÊN', marginLeft + 20, marginTop + 48);

  // Clear collision boxes for this frame
  tieBeamInteractiveBoxes = [];

  const axes = tieBeamData && tieBeamData.axes ? tieBeamData.axes : getDefaultTieBeamAxes();

  // Content area: 3 rows for Axis A, Axis B, Axis C
  const bottomH = 110;
  const contentY = marginTop + 75;
  const contentH = sheetH - marginTop - marginBottom - bottomH - 75;
  const rowH = contentH / 3.0;

  axes.forEach((axis, axIdx) => {
    const rowY = contentY + axIdx * rowH;
    drawCanvasTieBeamAxis(ctx, axis, marginLeft + 15, rowY, sheetW - marginLeft - marginRight - 30, rowH, viewState);

    // Divider line between axes
    if (axIdx < 2) {
      ctx.save();
      ctx.strokeStyle = '#cbd5e1';
      ctx.setLineDash([5, 5]);
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.moveTo(marginLeft + 20, rowY + rowH);
      ctx.lineTo(sheetW - marginRight - 20, rowY + rowH);
      ctx.stroke();
      ctx.restore();
    }
  });

  // 4. Bottom Section: Technical Notes (Toàn chiều rộng - Không khung tên)
  const bottomY = sheetH - marginBottom - bottomH - 10;
  const notesW = (sheetW - marginLeft - marginRight) - 30;

  // Notes Box
  ctx.save();
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(marginLeft + 15, bottomY, notesW, bottomH);
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 1.0;
  ctx.strokeRect(marginLeft + 15, bottomY, notesW, bottomH);

  ctx.fillStyle = '#b91c1c';
  ctx.font = 'bold 13px sans-serif';
  ctx.fillText('★ GHI CHÚ NGUYÊN LÝ BỐ TRÍ THÉP ĐÀ KIỀNG CHỊU PHẢN LỰC ĐẤT NỀN ĐẨY LÊN:', marginLeft + 25, bottomY + 16);

  ctx.fillStyle = '#1e293b';
  ctx.font = '11.5px sans-serif';
  const notesCol1 = [
    '1. NGUYÊN LÝ PHẢN LỰC ĐẤT (q_đất > 0): Đà kiềng tựa trên nền đất chịu áp lực phản lực đất tác dụng từ dưới lên.',
    '2. Do phản lực đẩy từ dưới lên, mô-men uốn tại GIỮA NHỊP gây căng thớ TRÊN, tại VỊ TRÍ GỐI gây căng thớ DƯỚI.',
    '3. Cốt thép tăng cường NHỊP bố trí ở LỚP TRÊN (LƯNG DẦM), cắt thép 0.65L. Cốt thép tăng cường GỐI bố trí ở LỚP DƯỚI, neo 0.25L.'
  ];
  const notesCol2 = [
    '4. Thép chủ trên và dưới chạy suốt liên tục đối xứng chống lún lệch, chống xoắn và tăng cứng giằng móng.',
    '5. Bê tông B22.5 (M300), Thép chủ CB400-V, Đai CB240-T. Lớp bê tông bảo vệ c = 35mm.',
    '6. Toàn bộ thép đai đà kiềng quy chuẩn về f6 (d6a100/200).'
  ];
  const colHalfW = notesW * 0.5;
  notesCol1.forEach((line, li) => {
    ctx.fillText(line, marginLeft + 25, bottomY + 38 + li * 22);
  });
  notesCol2.forEach((line, li) => {
    ctx.fillText(line, marginLeft + 25 + colHalfW, bottomY + 38 + li * 22);
  });
  ctx.restore();

  ctx.restore();
}

function drawCanvasTieBeamAxis(ctx, axis, bx, by, bw, bh, viewState) {
  const spans = axis.spans || [];
  const totalLen = axis.total_len_mm || 15000;

  // Title
  ctx.save();
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 15px sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText(`${axis.axis_title} • L = ${(totalLen/1000).toFixed(2)}m • ${spans.length} NHỊP (TCVN 5574:2018 - CHỊU PHẢN LỰC ĐẤT)`, bx + 15, by + 10);
  ctx.restore();

  const elevW = bw * 0.73;
  const csW = bw - elevW - 20;
  const csX = bx + elevW + 15;

  const marginX = 40.0;
  const drawableW = elevW - marginX * 2;
  const scaleX = drawableW / totalLen;

  const beamDrawH = 34.0;
  const beamTopY = by + bh * 0.52;
  const beamBotY = beamTopY + beamDrawH;

  // Track coordinates
  let curX = bx + marginX;
  const spanCoords = [];
  const supportXs = [curX];

  spans.forEach(sp => {
    const spanW = sp.length * scaleX;
    spanCoords.push({
      span: sp,
      x1: curX,
      x2: curX + spanW,
      w: spanW,
      len: sp.length,
      width: sp.width,
      depth: sp.depth
    });

    // Record interactive box for hover tooltip
    tieBeamInteractiveBoxes.push({
      axisId: axis.axis_id,
      axisTitle: axis.axis_title,
      span: sp,
      box: { x: curX, y: beamTopY - 10, w: spanW, h: beamDrawH + 50 }
    });

    curX += spanW;
    supportXs.push(curX);
  });

  // A. Cổ móng / đài móng tại các gối
  const colW = 24.0;
  const colH = 26.0;
  const footingW = 44.0;
  const footingH = 16.0;

  ctx.save();
  ctx.fillStyle = '#e2e8f0';
  ctx.strokeStyle = '#475569';
  ctx.lineWidth = 1.2;

  supportXs.forEach(sx => {
    ctx.fillRect(sx - colW / 2.0, beamBotY, colW, colH);
    ctx.strokeRect(sx - colW / 2.0, beamBotY, colW, colH);
    ctx.fillRect(sx - footingW / 2.0, beamBotY + colH, footingW, footingH);
    ctx.strokeRect(sx - footingW / 2.0, beamBotY + colH, footingW, footingH);
  });
  ctx.restore();

  // B. Khung bê tông dầm
  ctx.save();
  ctx.fillStyle = '#f8fafc';
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1.4;

  spanCoords.forEach(sc => {
    const isHov = viewState.hoveredSpan && viewState.hoveredSpan.id === sc.span.id;
    if (isHov) {
      ctx.fillStyle = '#fef3c7';
    } else {
      ctx.fillStyle = '#f8fafc';
    }
    ctx.fillRect(sc.x1, beamTopY, sc.w, beamDrawH);
    ctx.strokeRect(sc.x1, beamTopY, sc.w, beamDrawH);
  });
  ctx.restore();

  // C. Mũi tên biểu diễn phản lực đất đẩy lên (q_đất > 0)
  ctx.save();
  ctx.strokeStyle = '#d97706';
  ctx.fillStyle = '#d97706';
  ctx.lineWidth = 1.2;

  spanCoords.forEach(sc => {
    const arrowCount = Math.max(3, Math.floor(sc.w / 40.0));
    const dx = sc.w / (arrowCount + 1);
    for (let ai = 1; ai <= arrowCount; ai++) {
      const ax = sc.x1 + ai * dx;
      const ayBot = beamBotY + 20;
      const ayTop = beamBotY + 3;

      ctx.beginPath();
      ctx.moveTo(ax, ayBot);
      ctx.lineTo(ax, ayTop);
      ctx.stroke();

      // Arrow head pointing UP
      ctx.beginPath();
      ctx.moveTo(ax, ayTop);
      ctx.lineTo(ax - 3.5, ayTop + 6);
      ctx.lineTo(ax + 3.5, ayTop + 6);
      ctx.closePath();
      ctx.fill();
    }
  });

  ctx.font = 'bold 9.5px sans-serif';
  ctx.fillText('▲▲▲ PHẢN LỰC ĐẤT NỀN ĐẨY LÊN (q_đất > 0) ▲▲▲', spanCoords[0].x1 + 10, beamBotY + 32);
  ctx.restore();

  // D. Cốt đai (Stirrups) - Cyan
  ctx.save();
  ctx.strokeStyle = '#0284c7';
  ctx.lineWidth = 1.0;

  spanCoords.forEach(sc => {
    const stX1 = sc.x1 + 4;
    const stX2 = sc.x2 - 4;
    const qLen = sc.w * 0.25;
    const stepDense = Math.max(3.5, qLen / 8.0);
    let cx = stX1;

    ctx.beginPath();
    while (cx <= stX1 + qLen) {
      ctx.moveTo(cx, beamTopY + 3);
      ctx.lineTo(cx, beamBotY - 3);
      cx += stepDense;
    }
    const stepMid = stepDense * 2.0;
    while (cx <= stX2 - qLen) {
      ctx.moveTo(cx, beamTopY + 3);
      ctx.lineTo(cx, beamBotY - 3);
      cx += stepMid;
    }
    while (cx <= stX2) {
      ctx.moveTo(cx, beamTopY + 3);
      ctx.lineTo(cx, beamBotY - 3);
      cx += stepDense;
    }
    ctx.stroke();
  });
  ctx.restore();

  // E. CỐT THÉP DỌC CHỊU LỰC (ĐẬM NÉT 0.50 MM - MÀU ĐỎ)
  // Quy luật phản lực đất:
  // - Thép tăng cường NHỊP: LỚP TRÊN (LƯNG DẦM)
  // - Thép tăng cường GỐI: LỚP DƯỚI (BỤNG DẦM)
  ctx.save();
  ctx.strokeStyle = '#dc2626';
  ctx.lineWidth = 2.4; // 0.50 mm

  const startX = spanCoords[0].x1 + 3;
  const endX = spanCoords[spanCoords.length - 1].x2 - 3;
  const mainTopY = beamTopY + 5;
  const mainBotY = beamBotY - 5;

  // 1. Thép chủ trên chạy suốt
  ctx.beginPath();
  ctx.moveTo(startX, mainTopY + 14);
  ctx.lineTo(startX, mainTopY);
  ctx.lineTo(endX, mainTopY);
  ctx.lineTo(endX, mainTopY + 14);
  ctx.stroke();

  // 2. Thép chủ dưới chạy suốt
  ctx.beginPath();
  ctx.moveTo(startX, mainBotY - 14);
  ctx.lineTo(startX, mainBotY);
  ctx.lineTo(endX, mainBotY);
  ctx.lineTo(endX, mainBotY - 14);
  ctx.stroke();

  // 3. THÉP TĂNG CƯỜNG NHỊP: LỚP TRÊN (LƯNG DẦM)
  const extraTopY = mainTopY + 5;
  ctx.beginPath();
  spanCoords.forEach(sc => {
    if (sc.span.extra_top_mid) {
      const cutL = sc.w * 0.18;
      const cutR = sc.w * 0.82;
      const xl = sc.x1 + cutL;
      const xr = sc.x1 + cutR;
      ctx.moveTo(xl, extraTopY + 5);
      ctx.lineTo(xl, extraTopY);
      ctx.lineTo(xr, extraTopY);
      ctx.lineTo(xr, extraTopY + 5);
    }
  });
  ctx.stroke();

  // 4. THÉP TĂNG CƯỜNG GỐI: LỚP DƯỚI (BỤNG DẦM)
  const extraBotY = mainBotY - 5;
  ctx.beginPath();
  spanCoords.forEach((sc, i) => {
    const lQuarter = sc.w * 0.25;
    if (i === 0 && sc.span.extra_bot_support) {
      ctx.moveTo(sc.x1 + 3, extraBotY - 10);
      ctx.lineTo(sc.x1 + 3, extraBotY);
      ctx.lineTo(sc.x1 + lQuarter, extraBotY);
      ctx.lineTo(sc.x1 + lQuarter - 4, extraBotY - 4);
    }
    if (i < spanCoords.length - 1) {
      const nextQ = spanCoords[i + 1].w * 0.25;
      ctx.moveTo(sc.x2 - lQuarter, extraBotY);
      ctx.lineTo(sc.x2 + nextQ, extraBotY);
      ctx.lineTo(sc.x2 + nextQ - 4, extraBotY - 4);
      ctx.moveTo(sc.x2 - lQuarter, extraBotY);
      ctx.lineTo(sc.x2 - lQuarter + 4, extraBotY - 4);
    } else {
      if (sc.span.extra_bot_support) {
        ctx.moveTo(sc.x2 - lQuarter, extraBotY);
        ctx.lineTo(sc.x2 - 3, extraBotY);
        ctx.lineTo(sc.x2 - 3, extraBotY - 10);
        ctx.moveTo(sc.x2 - lQuarter, extraBotY);
        ctx.lineTo(sc.x2 - lQuarter + 4, extraBotY - 4);
      }
    }
  });
  ctx.stroke();
  ctx.restore();

  // F. ĐƯỜNG DIM KÍCH THƯỚC (Nét 0.09 mm - Xanh lá)
  // 1. Dim nhịp dầm phía trên
  const dimTopY = beamTopY - 15;
  spanCoords.forEach(sc => {
    drawCanvasDimLine(ctx, sc.x1, dimTopY, sc.x2, dimTopY, `${Math.round(sc.len)}`);
  });

  // 2. Dim chi tiết cắt thép tăng cường nhịp
  const dimExtraTopY = dimTopY - 14;
  spanCoords.forEach(sc => {
    if (sc.span.extra_top_mid) {
      const l1 = Math.round(sc.len * 0.18);
      const l2 = Math.round(sc.len * 0.64);
      const l3 = Math.round(sc.len) - l1 - l2;
      const xa = sc.x1;
      const xb = sc.x1 + sc.w * 0.18;
      const xc = sc.x1 + sc.w * 0.82;
      const xd = sc.x2;
      drawCanvasDimLine(ctx, xa, dimExtraTopY, xb, dimExtraTopY, `${l1}`);
      drawCanvasDimLine(ctx, xb, dimExtraTopY, xc, dimExtraTopY, `${l2} (TC Nhịp)`, true);
      drawCanvasDimLine(ctx, xc, dimExtraTopY, xd, dimExtraTopY, `${l3}`);
    }
  });

  // 3. Dim nhịp thông thủy bên dưới
  const dimSpanY = beamBotY + 52;
  spanCoords.forEach(sc => {
    drawCanvasDimLine(ctx, sc.x1, dimSpanY, sc.x2, dimSpanY, `${Math.round(sc.len)}`);
  });

  // 4. Dim tổng bên dưới ngang hàng lưới trục
  const dimTotalY = dimSpanY + 16;
  drawCanvasDimLine(ctx, spanCoords[0].x1, dimTotalY, spanCoords[spanCoords.length - 1].x2, dimTotalY, `${Math.round(totalLen)}`, true);

  // G. Vòng tròn trục kiến trúc
  const bubbleY = dimTotalY + 18;
  const supportGrids = axis.support_grids || [];
  ctx.save();
  ctx.lineWidth = 1.2;
  ctx.strokeStyle = '#475569';
  ctx.font = 'bold 10px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  supportXs.forEach((sx, gi) => {
    const lbl = supportGrids[gi] || `${gi + 1}`;
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(sx, bubbleY, 9.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#0f172a';
    ctx.fillText(lbl, sx, bubbleY);
  });
  ctx.restore();

  // H. VẼ 2 MẶT CẮT NGANG ĐIỂN HÌNH BÊN PHẢI (1-1 Giữa nhịp & 2-2 Gối tựa)
  const secSp = spans.length > 1 ? spans[1] : spans[0];
  drawCanvasTieBeamCrossSections(ctx, csX, by + 10, csW, bh - 25, secSp, axis.axis_id);
}

function drawCanvasDimLine(ctx, x1, y1, x2, y2, text, isBold = false) {
  ctx.save();
  ctx.strokeStyle = '#15803d';
  ctx.lineWidth = 0.8;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  // Ticks 45 độ
  const t = 3.5;
  ctx.moveTo(x1 - t, y1 - t); ctx.lineTo(x1 + t, y1 + t);
  ctx.moveTo(x2 - t, y2 - t); ctx.lineTo(x2 + t, y2 + t);
  ctx.stroke();

  // Dim text
  ctx.fillStyle = '#166534';
  ctx.font = isBold ? 'bold 9px sans-serif' : '8.5px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText(text, (x1 + x2) / 2.0, y1 - 2);
  ctx.restore();
}

function drawCanvasTieBeamCrossSections(ctx, csX, csY, csW, csH, secData, axisId) {
  const bW = secData.width || 200;
  const bH = secData.depth || 400;
  const halfH = csH / 2.0;

  // 1. Mặt cắt 1-1: Giữa nhịp
  drawSingleCanvasCS(
    ctx, csX, csY + 5, csW, halfH - 10,
    `MẶT CẮT 1-1 (GIỮA NHỊP ${axisId})`,
    '[CĂNG THỚ TRÊN DO PHẢN LỰC ĐẤT]',
    bW, bH,
    `${secData.main_top} + ${secData.extra_top_mid || ''}`.replace(/\s*\+\s*$/, ''),
    secData.main_bot,
    secData.stirrup,
    true
  );

  // 2. Mặt cắt 2-2: Gối cột
  drawSingleCanvasCS(
    ctx, csX, csY + halfH + 5, csW, halfH - 10,
    `MẶT CẮT 2-2 (GỐI CỘT ${axisId})`,
    '[CĂNG THỚ DƯỚI DO CỘT TỰA ĐÈ XUỐNG]',
    bW, bH,
    secData.main_top,
    `${secData.main_bot} + ${secData.extra_bot_support || ''}`.replace(/\s*\+\s*$/, ''),
    secData.stirrup,
    false
  );
}

function drawSingleCanvasCS(ctx, x, y, w, h, title, subTitle, bW, bH, topRebar, botRebar, stirrup, isMidSpan) {
  ctx.save();

  // Title
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 11px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText(title, x + w / 2.0, y);

  ctx.fillStyle = isMidSpan ? '#b45309' : '#047857';
  ctx.font = 'bold 9px sans-serif';
  ctx.fillText(subTitle, x + w / 2.0, y + 14);

  // Box scaling
  const maxBoxH = h - 45;
  const maxBoxW = w * 0.42;
  const sc = Math.min(maxBoxW / bW, maxBoxH / bH);
  const drawW = bW * sc;
  const drawH = bH * sc;
  const bx = x + w * 0.32 - drawW / 2.0;
  const by = y + 36;

  // Concrete outline
  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1.4;
  ctx.fillRect(bx, by, drawW, drawH);
  ctx.strokeRect(bx, by, drawW, drawH);

  // Stirrup: 35mm cover
  const cover = 35.0 * sc;
  const stX = bx + cover;
  const stY = by + cover;
  const stW = drawW - cover * 2;
  const stH = drawH - cover * 2;

  ctx.strokeStyle = '#0284c7';
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(stX, stY, stW, stH, 3);
  } else {
    ctx.strokeRect(stX, stY, stW, stH);
  }
  ctx.stroke();

  // Hooks 135 deg at top-left
  ctx.beginPath();
  ctx.moveTo(stX + 4, stY + 1); ctx.lineTo(stX + 8, stY + 5);
  ctx.moveTo(stX + 1, stY + 4); ctx.lineTo(stX + 5, stY + 8);
  ctx.stroke();

  // Parse counts
  function getCount(s) {
    let tot = 0;
    const matches = s.matchAll(/(\d+)\s*[ΦdD]/g);
    for (const m of matches) tot += parseInt(m[1], 10);
    return tot > 0 ? tot : 2;
  }

  const topCount = getCount(topRebar);
  const botCount = getCount(botRebar);
  const dotR = 3.6;

  ctx.fillStyle = '#dc2626';
  ctx.strokeStyle = '#991b1b';
  ctx.lineWidth = 0.8;

  // Top Rebar dots
  let topXs = [];
  if (topCount === 2) {
    topXs = [stX + 4, stX + stW - 4];
  } else if (topCount === 3) {
    topXs = [stX + 4, stX + stW / 2.0, stX + stW - 4];
  } else {
    const dx = (stW - 8) / (topCount - 1);
    for (let i = 0; i < topCount; i++) topXs.push(stX + 4 + i * dx);
  }

  topXs.forEach(tx => {
    ctx.beginPath();
    ctx.arc(tx, stY + 4, dotR, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  });

  // Bot Rebar dots
  let botXs = [];
  if (botCount === 2) {
    botXs = [stX + 4, stX + stW - 4];
  } else if (botCount === 3) {
    botXs = [stX + 4, stX + stW / 2.0, stX + stW - 4];
  } else {
    const dx = (stW - 8) / (botCount - 1);
    for (let i = 0; i < botCount; i++) botXs.push(stX + 4 + i * dx);
  }

  botXs.forEach(bxPos => {
    ctx.beginPath();
    ctx.arc(bxPos, stY + stH - 4, dotR, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  });

  // Dimensions
  drawCanvasDimLine(ctx, bx, by + drawH + 10, bx + drawW, by + drawH + 10, `${bW}`);

  // Leader Top
  const leadX = bx + drawW + 12;
  const leadTopY = stY + 4;
  ctx.strokeStyle = '#475569';
  ctx.lineWidth = 0.9;
  ctx.beginPath();
  ctx.moveTo(topXs[topXs.length - 1], stY + 4);
  ctx.lineTo(leadX, leadTopY);
  ctx.lineTo(leadX + 50, leadTopY);
  ctx.stroke();

  ctx.fillStyle = '#dc2626';
  ctx.font = 'bold 9.5px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';
  ctx.fillText(topRebar, leadX + 2, leadTopY);
  if (isMidSpan) {
    ctx.fillStyle = '#b45309';
    ctx.font = '8px sans-serif';
    ctx.fillText('(TC Lưng Nhịp)', leadX + 2, leadTopY + 10);
  }

  // Leader Bot
  const leadBotY = stY + stH - 4;
  ctx.beginPath();
  ctx.moveTo(botXs[botXs.length - 1], stY + stH - 4);
  ctx.lineTo(leadX, leadBotY);
  ctx.lineTo(leadX + 50, leadBotY);
  ctx.stroke();

  ctx.fillStyle = '#dc2626';
  ctx.font = 'bold 9.5px sans-serif';
  ctx.fillText(botRebar, leadX + 2, leadBotY);
  if (!isMidSpan) {
    ctx.fillStyle = '#047857';
    ctx.font = '8px sans-serif';
    ctx.fillText('(TC Bụng Gối)', leadX + 2, leadBotY + 10);
  }

  ctx.restore();
}

function getDefaultTieBeamAxes() {
  return [
    {
      axis_id: 'A',
      axis_title: 'ĐÀ KIỀNG TRỤC A (DK-A)',
      total_len_mm: 14700.0,
      support_grids: ['4', '5', '6', '7'],
      spans: [
        { id: 'DK-A1', beam_label: 'B16', grid_from: '4', grid_to: '5', length: 3600, width: 200, depth: 400, main_top: '2Φ18', main_bot: '2Φ18', extra_top_mid: '1Φ18', extra_bot_support: '1Φ18', stirrup: 'd6a100/200' },
        { id: 'DK-A2', beam_label: 'B9', grid_from: '5', grid_to: '6', length: 5600, width: 200, depth: 400, main_top: '2Φ18', main_bot: '2Φ18', extra_top_mid: '1Φ18', extra_bot_support: '1Φ18', stirrup: 'd6a100/200' },
        { id: 'DK-A3', beam_label: 'B10', grid_from: '6', grid_to: '7', length: 5500, width: 200, depth: 400, main_top: '2Φ18', main_bot: '2Φ18', extra_top_mid: '1Φ18', extra_bot_support: '1Φ18', stirrup: 'd6a100/200' }
      ]
    },
    {
      axis_id: 'B',
      axis_title: 'ĐÀ KIỀNG TRỤC B (DK-B)',
      total_len_mm: 32950.0,
      support_grids: ['1', '2', '3', '5', '6', '7'],
      spans: [
        { id: 'DK-B1', beam_label: 'B8', grid_from: '1', grid_to: '2', length: 5900, width: 200, depth: 400, main_top: '2Φ20', main_bot: '2Φ20', extra_top_mid: '1Φ20', extra_bot_support: '1Φ20', stirrup: 'd6a100/200' },
        { id: 'DK-B2', beam_label: 'B19', grid_from: '2', grid_to: '3', length: 7350, width: 300, depth: 500, main_top: '3Φ20', main_bot: '3Φ20', extra_top_mid: '2Φ20', extra_bot_support: '2Φ20', stirrup: 'd8a100/200' },
        { id: 'DK-B3', beam_label: 'B21', grid_from: '3', grid_to: '5', length: 8600, width: 300, depth: 500, main_top: '3Φ20', main_bot: '3Φ20', extra_top_mid: '2Φ22', extra_bot_support: '2Φ22', stirrup: 'd8a100/200' },
        { id: 'DK-B4', beam_label: 'B13', grid_from: '5', grid_to: '6', length: 5600, width: 200, depth: 400, main_top: '2Φ20', main_bot: '2Φ20', extra_top_mid: '1Φ20', extra_bot_support: '1Φ20', stirrup: 'd6a100/200' },
        { id: 'DK-B5', beam_label: 'B12', grid_from: '6', grid_to: '7', length: 5500, width: 200, depth: 400, main_top: '2Φ20', main_bot: '2Φ20', extra_top_mid: '1Φ20', extra_bot_support: '1Φ20', stirrup: 'd6a100/200' }
      ]
    },
    {
      axis_id: 'C',
      axis_title: 'ĐÀ KIỀNG TRỤC C (DK-C)',
      total_len_mm: 21850.0,
      support_grids: ['1', '2', '3', '4*', '5'],
      spans: [
        { id: 'DK-C1', beam_label: 'B2', grid_from: '1', grid_to: '2', length: 5900, width: 200, depth: 400, main_top: '2Φ18', main_bot: '2Φ18', extra_top_mid: '1Φ18', extra_bot_support: '1Φ18', stirrup: 'd6a100/200' },
        { id: 'DK-C2', beam_label: 'B20', grid_from: '2', grid_to: '3', length: 7350, width: 300, depth: 500, main_top: '3Φ20', main_bot: '3Φ20', extra_top_mid: '2Φ20', extra_bot_support: '2Φ20', stirrup: 'd8a100/200' },
        { id: 'DK-C3', beam_label: 'B22', grid_from: '3', grid_to: '4*', length: 3500, width: 200, depth: 400, main_top: '2Φ18', main_bot: '2Φ18', extra_top_mid: '', extra_bot_support: '1Φ18', stirrup: 'd6a100/200' },
        { id: 'DK-C4', beam_label: 'B23', grid_from: '4*', grid_to: '5', length: 5100, width: 200, depth: 400, main_top: '2Φ18', main_bot: '2Φ18', extra_top_mid: '1Φ18', extra_bot_support: '1Φ18', stirrup: 'd6a100/200' }
      ]
    }
  ];
}

function setupTieBeamCanvasEvents(canvasId, viewState, renderFn, badgeId, textId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  canvas.addEventListener('mousedown', (e) => {
    if (e.button === 0) {
      viewState.isDragging = true;
      viewState.startX = e.clientX - viewState.panX;
      viewState.startY = e.clientY - viewState.panY;
      canvas.classList.add('cursor-grabbing');
    }
  });

  window.addEventListener('mouseup', () => {
    if (viewState.isDragging) {
      viewState.isDragging = false;
      canvas.classList.remove('cursor-grabbing');
    }
  });

  canvas.addEventListener('mousemove', (e) => {
    if (viewState.isDragging) {
      viewState.panX = e.clientX - viewState.startX;
      viewState.panY = e.clientY - viewState.startY;
      renderFn();
      return;
    }

    // Hover detection over tie beam spans
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const sheetX = (mouseX - viewState.panX) / viewState.zoom;
    const sheetY = (mouseY - viewState.panY) / viewState.zoom;

    let hit = null;
    for (const item of tieBeamInteractiveBoxes) {
      const b = item.box;
      if (sheetX >= b.x && sheetX <= b.x + b.w && sheetY >= b.y && sheetY <= b.y + b.h) {
        hit = item;
        break;
      }
    }

    const badge = document.getElementById(badgeId);
    const textSpan = document.getElementById(textId);

    if (hit) {
      canvas.style.cursor = 'pointer';
      viewState.hoveredSpan = hit.span;
      if (textSpan) {
        const sp = hit.span;
        textSpan.innerHTML = `🏗️ <strong>${hit.axisTitle}</strong> • Nhịp <strong>${sp.grid_from}-${sp.grid_to}</strong> (dầm <strong>${sp.beam_label}</strong>): ${sp.width}×${sp.depth}mm • L=${(sp.length/1000).toFixed(2)}m • Thép chủ: <strong>${sp.main_top}+${sp.main_bot}</strong> • <em>TC Nhịp (Lưng):</em> <strong>${sp.extra_top_mid || 'Đủ'}</strong> • <em>TC Gối (Bụng):</em> <strong>${sp.extra_bot_support || 'Đủ'}</strong> • Đai: ${sp.stirrup}`;
      }
      renderFn();
    } else {
      canvas.style.cursor = 'grab';
      if (viewState.hoveredSpan) {
        viewState.hoveredSpan = null;
        if (textSpan) {
          textSpan.innerHTML = 'Rê chuột vào nhịp đà kiềng để xem chi tiết quy cách thép &amp; phản lực';
        }
        renderFn();
      }
    }
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    const newZoom = Math.max(0.1, Math.min(3.5, viewState.zoom * zoomFactor));

    viewState.panX = mouseX - (mouseX - viewState.panX) * (newZoom / viewState.zoom);
    viewState.panY = mouseY - (mouseY - viewState.panY) * (newZoom / viewState.zoom);
    viewState.zoom = newZoom;

    renderFn();
  }, { passive: false });
}

// Tab & Modal View Controllers
function renderTabTieBeamCad() {
  drawTieBeamSheetOnCanvas('tabTieBeamCadCanvas', tieBeamTabViewState, 'tabTieBeamCadHoverBadge', 'tabTieBeamCadHoverText');
}
function fitTabTieBeamCadView() {
  const canvas = document.getElementById('tabTieBeamCadCanvas');
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return;
  const zoomW = (rect.width - 40) / TIE_SHEET.sheetW;
  const zoomH = (rect.height - 40) / TIE_SHEET.sheetH;
  tieBeamTabViewState.zoom = Math.min(zoomW, zoomH);
  tieBeamTabViewState.panX = Math.round((rect.width - TIE_SHEET.sheetW * tieBeamTabViewState.zoom) / 2.0);
  tieBeamTabViewState.panY = Math.round((rect.height - TIE_SHEET.sheetH * tieBeamTabViewState.zoom) / 2.0);
  renderTabTieBeamCad();
}
function zoomTabTieBeamCad(factor) {
  tieBeamTabViewState.zoom = Math.max(0.1, Math.min(3.5, tieBeamTabViewState.zoom * factor));
  renderTabTieBeamCad();
}
function resetTabTieBeamCadView() {
  tieBeamTabViewState.zoom = 1.0;
  tieBeamTabViewState.panX = 40;
  tieBeamTabViewState.panY = 30;
  renderTabTieBeamCad();
}

function renderModalTieBeamCad() {
  drawTieBeamSheetOnCanvas('tieBeamCadCanvas', tieBeamModalViewState, 'tieBeamCadHoverBadge', 'tieBeamCadHoverText');
}
function openTieBeamDrawingModal() {
  const modal = document.getElementById('tieBeamDrawingModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  loadTieBeamData().then(() => {
    setTimeout(() => {
      fitTieBeamCadView();
      renderModalTieBeamCad();
    }, 80);
  });
}
function closeTieBeamDrawingModal() {
  const modal = document.getElementById('tieBeamDrawingModal');
  if (!modal) return;
  modal.classList.add('hidden');
  document.body.style.overflow = '';
}
function fitTieBeamCadView() {
  const canvas = document.getElementById('tieBeamCadCanvas');
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return;
  const zoomW = (rect.width - 40) / TIE_SHEET.sheetW;
  const zoomH = (rect.height - 40) / TIE_SHEET.sheetH;
  tieBeamModalViewState.zoom = Math.min(zoomW, zoomH);
  tieBeamModalViewState.panX = Math.round((rect.width - TIE_SHEET.sheetW * tieBeamModalViewState.zoom) / 2.0);
  tieBeamModalViewState.panY = Math.round((rect.height - TIE_SHEET.sheetH * tieBeamModalViewState.zoom) / 2.0);
  renderModalTieBeamCad();
}
function zoomTieBeamCad(factor) {
  tieBeamModalViewState.zoom = Math.max(0.1, Math.min(3.5, tieBeamModalViewState.zoom * factor));
  renderModalTieBeamCad();
}
function resetTieBeamCadView() {
  tieBeamModalViewState.zoom = 1.0;
  tieBeamModalViewState.panX = 60;
  tieBeamModalViewState.panY = 40;
  renderModalTieBeamCad();
}

async function exportTieBeamSheetPdf() {
  if (typeof showToastNotification === 'function') {
    showToastNotification('⚡ Đang chuẩn bị tải file PDF Bản Vẽ Đà Kiềng (Trục A, B, C)...', 'info');
  }
  const a = document.createElement('a');
  a.href = '/api/export-tie-beam-pdf';
  a.download = 'Bang_Chi_Tiet_Da_Kieng_Truc_ABC.pdf';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

async function exportTieBeamSheetDxf() {
  if (typeof showToastNotification === 'function') {
    showToastNotification('⚡ Đang chuẩn bị tải file DXF Bản Vẽ Đà Kiềng (AutoCAD R2010)...', 'info');
  }
  const a = document.createElement('a');
  a.href = '/api/export-tie-beam-dxf';
  a.download = 'Bang_Chi_Tiet_Da_Kieng_Truc_ABC.dxf';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// Global window exports
window.openTieBeamDrawingModal = openTieBeamDrawingModal;
window.closeTieBeamDrawingModal = closeTieBeamDrawingModal;
window.fitTieBeamCadView = fitTieBeamCadView;
window.zoomTieBeamCad = zoomTieBeamCad;
window.resetTieBeamCadView = resetTieBeamCadView;
window.renderTabTieBeamCad = renderTabTieBeamCad;
window.fitTabTieBeamCadView = fitTabTieBeamCadView;
window.zoomTabTieBeamCad = zoomTabTieBeamCad;
window.resetTabTieBeamCadView = resetTabTieBeamCadView;
window.renderModalTieBeamCad = renderModalTieBeamCad;
window.exportTieBeamSheetPdf = exportTieBeamSheetPdf;
window.exportTieBeamSheetDxf = exportTieBeamSheetDxf;

async function exportBeamPlanPdf() {
  const input = document.getElementById('etabs2DStorySelect');
  const story = (input && input.value) ? input.value : 'T3';
  if (typeof showToastNotification === 'function') {
    showToastNotification(`⚡ Đang chuẩn bị tải PDF Mặt Bằng (${story})...`, 'info');
  }
  const a = document.createElement('a');
  if (story === 'C') {
    a.href = '/api/export-column-plan-pdf';
    a.download = 'Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.pdf';
  } else {
    a.href = `/api/export-beam-plan-pdf?story=${encodeURIComponent(story)}`;
    a.download = `Mat_Bang_Ket_Cau_Dam_${story}.pdf`;
  }
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

async function exportBeamPlanDxf() {
  const input = document.getElementById('etabs2DStorySelect');
  const story = (input && input.value) ? input.value : 'T3';
  if (typeof showToastNotification === 'function') {
    showToastNotification(`⚡ Đang chuẩn bị tải DXF Mặt Bằng (${story})...`, 'info');
  }
  const a = document.createElement('a');
  if (story === 'C') {
    a.href = '/api/export-column-plan-dxf';
    a.download = 'Mat_Bang_Dinh_Vi_Va_Bo_Tri_Cot.dxf';
  } else {
    a.href = `/api/export-beam-plan-dxf?story=${encodeURIComponent(story)}`;
    a.download = `Mat_Bang_Ket_Cau_Dam_${story}.dxf`;
  }
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

window.exportBeamPlanPdf = exportBeamPlanPdf;
window.exportBeamPlanDxf = exportBeamPlanDxf;



// ==============================================================================
// CAD LAYER SETTINGS & LOCAL STORAGE MANAGEMENT (AUTOCAD DXF TCVN)
// ==============================================================================

const DEFAULT_CAD_LAYERS = {
  THEP_CHU: {
    name: 'THEP_CHU',
    desc: 'Thép chủ dọc dầm (lớp trên, lớp dưới)',
    color: 1, // Red
    linetype: 'Continuous',
    lineweight: 50 // 0.50 mm
  },
  THEP_TANG_CUONG: {
    name: 'THEP_TANG_CUONG',
    desc: 'Thép tăng cường (gối, bụng, móc thép)',
    color: 6, // Magenta
    linetype: 'Continuous',
    lineweight: 50 // 0.50 mm
  },
  COT_DAI: {
    name: 'COT_DAI',
    desc: 'Cốt đai, móc đai, nhánh đai, thép giá dầm',
    color: 4, // Cyan
    linetype: 'Continuous',
    lineweight: 15 // 0.15 mm
  },
  BE_TONG: {
    name: 'BE_TONG',
    desc: 'Đường bao bê tông (thân dầm, mép cột, mặt cắt)',
    color: 7, // White/Black
    linetype: 'Continuous',
    lineweight: 35 // 0.35 mm
  },
  DIM: {
    name: 'DIM',
    desc: 'Đường gióng, đường kích thước, text dim, mũi tên',
    color: 3, // Green
    linetype: 'Continuous',
    lineweight: 9 // 0.09 mm
  },
  TRUC: {
    name: 'TRUC',
    desc: 'Trục định vị dầm/cột, đường tim trục, bong bóng trục',
    color: 8, // Dark Gray
    linetype: 'CENTER',
    lineweight: 15 // 0.15 mm
  },
  TEXT: {
    name: 'TEXT',
    desc: 'Chữ ghi chú, tên dầm, cao độ, quy cách thép',
    color: 7, // White/Black
    linetype: 'Continuous',
    lineweight: 15 // 0.15 mm
  },
  KHUNG_TEN: {
    name: 'KHUNG_TEN',
    desc: 'Đường viền khung bản vẽ, khung tên, tiêu đề bảng',
    color: 7, // White/Black
    linetype: 'Continuous',
    lineweight: 50 // 0.50 mm
  }
};

const STANDARD_LINEWEIGHTS = [
  { val: 0, label: '0.00 mm (Default)' },
  { val: 5, label: '0.05 mm' },
  { val: 9, label: '0.09 mm' },
  { val: 13, label: '0.13 mm' },
  { val: 15, label: '0.15 mm' },
  { val: 18, label: '0.18 mm' },
  { val: 20, label: '0.20 mm' },
  { val: 25, label: '0.25 mm' },
  { val: 30, label: '0.30 mm' },
  { val: 35, label: '0.35 mm' },
  { val: 40, label: '0.40 mm' },
  { val: 50, label: '0.50 mm' },
  { val: 60, label: '0.60 mm' },
  { val: 70, label: '0.70 mm' },
  { val: 80, label: '0.80 mm' },
  { val: 100, label: '1.00 mm' }
];

const STANDARD_LINETYPES = [
  { val: 'Continuous', label: 'Continuous (Nét liền)' },
  { val: 'CENTER', label: 'CENTER (Nét gạch chấm tâm)' },
  { val: 'DASHED', label: 'DASHED (Nét đứt nét dài)' },
  { val: 'HIDDEN', label: 'HIDDEN (Nét đứt nét ngắn)' },
  { val: 'PHANTOM', label: 'PHANTOM (Nét hai chấm gạch)' }
];

function getAciColorHex(aci) {
  const aciMap = {
    1: '#EF4444', // Red
    2: '#EAB308', // Yellow
    3: '#22C55E', // Green
    4: '#06B6D4', // Cyan
    5: '#3B82F6', // Blue
    6: '#EC4899', // Magenta
    7: '#1E293B', // Dark Slate for AutoCAD Color 7
    8: '#64748B', // Gray
    9: '#94A3B8', // Light Gray
  };
  const num = parseInt(aci, 10);
  if (aciMap[num]) return aciMap[num];
  if (num >= 10 && num <= 255) {
    const hue = Math.round(((num - 10) / 245) * 360);
    return `hsl(${hue}, 75%, 45%)`;
  }
  return '#64748B';
}

function getCadLayerConfig() {
  try {
    const saved = localStorage.getItem('brmCadLayerConfig');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && typeof parsed === 'object') {
        const result = {};
        for (const k in DEFAULT_CAD_LAYERS) {
          result[k] = Object.assign({}, DEFAULT_CAD_LAYERS[k], parsed[k] || {});
        }
        return result;
      }
    }
  } catch (e) {
    console.warn('Error reading brmCadLayerConfig:', e);
  }
  return JSON.parse(JSON.stringify(DEFAULT_CAD_LAYERS));
}

function openCadLayerSettingsModal() {
  const modal = document.getElementById('cadLayerSettingsModal');
  if (!modal) return;
  const tbody = document.getElementById('cadLayerTableBody');
  if (!tbody) return;

  const currentCfg = getCadLayerConfig();
  let html = '';

  for (const [key, cfg] of Object.entries(currentCfg)) {
    const hex = getAciColorHex(cfg.color);
    
    // Linetype options
    let ltOptions = '';
    STANDARD_LINETYPES.forEach(lt => {
      const sel = (lt.val.toUpperCase() === (cfg.linetype || 'Continuous').toUpperCase()) ? 'selected' : '';
      ltOptions += `<option value="${lt.val}" ${sel}>${lt.label}</option>`;
    });

    // Lineweight options
    let lwOptions = '';
    STANDARD_LINEWEIGHTS.forEach(lw => {
      const sel = (parseInt(lw.val, 10) === parseInt(cfg.lineweight, 10)) ? 'selected' : '';
      lwOptions += `<option value="${lw.val}" ${sel}>${lw.label}</option>`;
    });

    html += `
      <tr class="hover:bg-slate-50 transition border-b border-slate-100" data-layer="${key}">
        <td class="p-2.5 whitespace-nowrap">
          <span class="font-mono font-bold text-slate-800 text-xs px-2 py-0.5 rounded bg-slate-100 border border-slate-300 shadow-2xs">${key}</span>
        </td>
        <td class="p-2.5">
          <span class="text-slate-700 font-medium text-xs">${cfg.desc || DEFAULT_CAD_LAYERS[key]?.desc || ''}</span>
        </td>
        <td class="p-2.5 whitespace-nowrap">
          <div class="flex items-center gap-2">
            <span id="layerSwatch_${key}" class="w-6 h-6 rounded-md border border-slate-300 shrink-0 shadow-2xs transition-colors" style="background-color: ${hex};" title="Màu hiển thị"></span>
            <input type="number" id="layerColor_${key}" min="1" max="255" value="${cfg.color}" 
                   oninput="updateLayerSwatch('${key}', this.value)" 
                   class="w-16 px-2 py-1 text-center font-bold font-mono text-xs border border-slate-300 rounded-lg focus:outline-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white" 
                   title="Nhập mã màu AutoCAD ACI (1-255)">
            <span id="layerColorName_${key}" class="text-[11px] text-slate-500 font-medium w-16 truncate"></span>
          </div>
        </td>
        <td class="p-2.5 whitespace-nowrap">
          <select id="layerLinetype_${key}" class="w-full px-2 py-1 text-xs border border-slate-300 rounded-lg focus:outline-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white font-medium text-slate-700">
            ${ltOptions}
          </select>
        </td>
        <td class="p-2.5 whitespace-nowrap">
          <select id="layerLineweight_${key}" class="w-full px-2 py-1 text-xs border border-slate-300 rounded-lg focus:outline-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-white font-medium text-slate-700">
            ${lwOptions}
          </select>
        </td>
      </tr>
    `;
  }

  tbody.innerHTML = html;

  // Update color names
  for (const [key, cfg] of Object.entries(currentCfg)) {
    updateLayerSwatch(key, cfg.color);
  }

  modal.classList.remove('hidden');
}

function closeCadLayerSettingsModal() {
  const modal = document.getElementById('cadLayerSettingsModal');
  if (modal) modal.classList.add('hidden');
}

function updateLayerSwatch(layerKey, aciVal) {
  const swatch = document.getElementById(`layerSwatch_${layerKey}`);
  const nameEl = document.getElementById(`layerColorName_${layerKey}`);
  const val = parseInt(aciVal, 10);
  if (isNaN(val) || val < 1 || val > 255) return;
  const hex = getAciColorHex(val);
  if (swatch) swatch.style.backgroundColor = hex;

  const names = {
    1: '1 - Red',
    2: '2 - Yellow',
    3: '3 - Green',
    4: '4 - Cyan',
    5: '5 - Blue',
    6: '6 - Magenta',
    7: '7 - White',
    8: '8 - Gray',
    9: '9 - Lt Gray'
  };
  if (nameEl) {
    nameEl.textContent = names[val] || `ACI ${val}`;
  }
}

function saveCadLayerConfigFromUI() {
  const config = {};
  for (const key of Object.keys(DEFAULT_CAD_LAYERS)) {
    const colInput = document.getElementById(`layerColor_${key}`);
    const ltSelect = document.getElementById(`layerLinetype_${key}`);
    const lwSelect = document.getElementById(`layerLineweight_${key}`);

    let color = colInput ? parseInt(colInput.value, 10) : DEFAULT_CAD_LAYERS[key].color;
    if (isNaN(color) || color < 1) color = 1;
    if (color > 255) color = 255;

    const linetype = ltSelect ? ltSelect.value : DEFAULT_CAD_LAYERS[key].linetype;
    let lineweight = lwSelect ? parseInt(lwSelect.value, 10) : DEFAULT_CAD_LAYERS[key].lineweight;
    if (isNaN(lineweight)) lineweight = 15;

    config[key] = {
      name: key,
      desc: DEFAULT_CAD_LAYERS[key].desc,
      color: color,
      linetype: linetype,
      lineweight: lineweight
    };
  }

  try {
    localStorage.setItem('brmCadLayerConfig', JSON.stringify(config));
    if (typeof showToastNotification === 'function') {
      showToastNotification('✅ Đã lưu cấu hình Layer CAD vào LocalStorage thành công!', 'success');
    } else {
      alert('Đã lưu cấu hình Layer CAD thành công!');
    }
  } catch (e) {
    console.error('Failed to save to localStorage:', e);
    alert('Lỗi lưu LocalStorage: ' + e.message);
  }

  closeCadLayerSettingsModal();
}

function resetCadLayerConfigToDefault() {
  if (!confirm('Bạn có chắc muốn khôi phục toàn bộ Layer về cấu hình chuẩn TCVN mặc định?')) return;
  try {
    localStorage.removeItem('brmCadLayerConfig');
  } catch (e) {}
  openCadLayerSettingsModal();
  if (typeof showToastNotification === 'function') {
    showToastNotification('🔄 Đã khôi phục cài đặt Layer chuẩn mặc định.', 'info');
  }
}

window.DEFAULT_CAD_LAYERS = DEFAULT_CAD_LAYERS;
window.getCadLayerConfig = getCadLayerConfig;
window.openCadLayerSettingsModal = openCadLayerSettingsModal;
window.closeCadLayerSettingsModal = closeCadLayerSettingsModal;
window.updateLayerSwatch = updateLayerSwatch;
window.saveCadLayerConfigFromUI = saveCadLayerConfigFromUI;
window.resetCadLayerConfigToDefault = resetCadLayerConfigToDefault;


// ==============================================================================
// (6) AEC 3D STUDIO: WALL (LINE) & DOOR (BLOCK) WITH SNAP & ROUND 50/100
// ==============================================================================

let aecToolMode = 'select'; // 'select' | 'wall' | 'door'
let aecSnapRound = 100;     // 50 | 100 | 0 (none)
let aecSnapToGeometry = true;
let aecSelectedStory = 'T3';
let aecWallThickness = 100; // mm
let aecWallHeight = 3000;   // mm
let aecDoorWidth = 900;     // mm
let aecDoorHeight = 2200;   // mm
let aecDoorAngle = 0;       // degrees (0, 90, 180, 270)

let aecElements = [];       // array of user-drawn wall & door data objects
let aecThreeGroup = null;    // THREE.Group containing all AEC meshes in threeScene
let modalAecThreeGroup = null;
let aecWallStartPoint = null;// THREE.Vector3 for P1 while drawing wall
let aecCurrentSnappedPoint = null;

const aecStoryElevations = {
  'T1': 0,
  'T2': 7600,
  'T3': 11800,
  'T4': 15600,
  'TM': 18400
};

function getAecActiveElevation() {
  if (etabsData && etabsData.stories) {
    const st = etabsData.stories.find(s => s.name === aecSelectedStory);
    if (st && st.elevation !== undefined) {
      return st.elevation;
    }
  }
  return aecStoryElevations[aecSelectedStory] || 11800;
}

function initAecStudio() {
  loadAecElementsFromStorage();
  updateAecCountBadge();
}

function loadAecElementsFromStorage() {
  try {
    const raw = localStorage.getItem('etabs_aec_elements_v1');
    if (raw) {
      aecElements = JSON.parse(raw);
    }
  } catch (e) {
    console.warn('Could not load AEC elements from localStorage:', e);
  }
}

function saveAecElementsToStorage() {
  try {
    localStorage.setItem('etabs_aec_elements_v1', JSON.stringify(aecElements));
  } catch (e) {
    console.warn('Could not save AEC elements to localStorage:', e);
  }
  updateAecCountBadge();
}

function updateAecCountBadge() {
  const badge = document.getElementById('aecBadgeCount');
  if (!badge) return;
  const walls = aecElements.filter(e => e.type === 'wall').length;
  const doors = aecElements.filter(e => e.type === 'door').length;
  badge.textContent = `${walls} Tường • ${doors} Cửa`;
}

function setAecToolMode(mode) {
  aecToolMode = mode;
  aecWallStartPoint = null;
  clearAecPreview();

  const modes = ['select', 'wall', 'door'];
  modes.forEach(m => {
    const btn = document.getElementById('aecBtnMode' + m.charAt(0).toUpperCase() + m.slice(1));
    if (btn) {
      if (m === mode) {
        btn.className = 'py-1 px-3 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-xs transition cursor-pointer flex items-center gap-1.5';
      } else {
        btn.className = 'py-1 px-3 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-white/80 transition cursor-pointer flex items-center gap-1.5';
      }
    }
  });

  const wallParams = document.getElementById('aecWallParams');
  const doorParams = document.getElementById('aecDoorParams');
  if (wallParams) wallParams.classList.toggle('hidden', mode !== 'wall');
  if (doorParams) doorParams.classList.toggle('hidden', mode !== 'door');

  if (threeControls) {
    if (mode === 'select') {
      threeControls.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
    } else {
      threeControls.mouseButtons.LEFT = null; // Disable rotate so left click draws/places!
    }
  }

  updateAecHUDHint();
}

function setAecSnapRound(val) {
  aecSnapRound = val;
  [50, 100, 0].forEach(v => {
    const id = v === 0 ? 'aecBtnSnapOff' : 'aecBtnSnap' + v;
    const btn = document.getElementById(id);
    if (btn) {
      if (v === val) {
        btn.className = 'py-1 px-2.5 rounded bg-indigo-600 text-white shadow-xs transition cursor-pointer font-bold';
      } else {
        btn.className = 'py-1 px-2.5 rounded text-slate-700 hover:bg-white/80 transition cursor-pointer font-semibold';
      }
    }
  });
  updateAecHUDHint();
}

function toggleAecSnapGeom(checked) {
  aecSnapToGeometry = checked;
}

function changeAecStory(val) {
  aecSelectedStory = val;
  aecWallStartPoint = null;
  clearAecPreview();
  updateAecHUDHint();
}

function setAecWallThickness(val) {
  aecWallThickness = val;
  [100, 200].forEach(v => {
    const btn = document.getElementById('aecBtnWall' + v);
    if (btn) {
      btn.className = (v === val) ? 'px-2 py-0.5 rounded bg-amber-600 text-white cursor-pointer' : 'px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer';
    }
  });
  updateAecHUDHint();
}

function setAecWallHeight(val) {
  aecWallHeight = val;
  [3000, 3800].forEach(v => {
    const btn = document.getElementById('aecBtnWallH' + v);
    if (btn) {
      btn.className = (v === val) ? 'px-2 py-0.5 rounded bg-amber-600 text-white cursor-pointer' : 'px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer';
    }
  });
  updateAecHUDHint();
}

function setAecDoorWidth(val) {
  aecDoorWidth = val;
  [800, 900, 1200].forEach(v => {
    const btn = document.getElementById('aecBtnDoor' + v);
    if (btn) {
      btn.className = (v === val) ? 'px-2 py-0.5 rounded bg-emerald-600 text-white cursor-pointer' : 'px-2 py-0.5 rounded text-slate-700 hover:bg-white/80 cursor-pointer';
    }
  });
  updateAecHUDHint();
}

function rotateAecDoor() {
  aecDoorAngle = (aecDoorAngle + 90) % 360;
  const lbl = document.getElementById('aecDoorAngleLabel');
  if (lbl) lbl.textContent = aecDoorAngle + '°';
  updateAecHUDHint();
}

function undoLastAecElement() {
  if (aecElements.length === 0) return;
  const removed = aecElements.pop();
  saveAecElementsToStorage();
  refreshAecScene();
  if (typeof showToastNotification === 'function') {
    showToastNotification(`↩️ Đã hoàn tác: ${removed.type === 'wall' ? 'Tường' : 'Cửa'}`, 'info');
  }
}

function clearAllAecElements() {
  if (aecElements.length === 0) return;
  if (!confirm('Bạn có chắc muốn xóa toàn bộ Tường và Cửa 3D đã vẽ không?')) return;
  aecElements = [];
  aecWallStartPoint = null;
  clearAecPreview();
  saveAecElementsToStorage();
  refreshAecScene();
  if (typeof showToastNotification === 'function') {
    showToastNotification('🗑️ Đã xóa sạch toàn bộ vật thể AEC 3D', 'warning');
  }
}

function refreshAecScene() {
  if (threeScene) {
    buildAecMeshes(threeScene, false);
  }
  if (modalThreeScene) {
    buildAecMeshes(modalThreeScene, true);
  }
}

function buildAecMeshes(scene, isModal = false) {
  if (!scene) return null;

  // Remove previous AEC group
  const prevGrp = isModal ? modalAecThreeGroup : aecThreeGroup;
  if (prevGrp) {
    scene.remove(prevGrp);
  }

  const grp = new THREE.Group();
  grp.name = 'aecThreeGroup';

  const wallMat = new THREE.MeshStandardMaterial({
    color: 0x94a3b8, // Slate 400
    roughness: 0.5,
    metalness: 0.05
  });

  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x334155, // Dark slate frame
    roughness: 0.3,
    metalness: 0.2
  });

  const leafMat = new THREE.MeshStandardMaterial({
    color: 0xb45309, // Warm architectural wood
    roughness: 0.4,
    metalness: 0.1
  });

  const handleMat = new THREE.MeshStandardMaterial({
    color: 0xf59e0b, // Brass gold
    roughness: 0.2,
    metalness: 0.8
  });

  aecElements.forEach(elem => {
    if (elem.type === 'wall') {
      const p1 = elem.p1;
      const p2 = elem.p2;
      const dx = p2.x - p1.x;
      const dz = p2.z - p1.z;
      const len = Math.hypot(dx, dz);
      if (len < 10) return;

      const angle = Math.atan2(dz, dx);
      const thk = elem.thickness || 100;
      const h = elem.height || 3000;
      const elev = p1.y || 0;

      const geom = new THREE.BoxGeometry(len, h, thk);
      const mesh = new THREE.Mesh(geom, wallMat.clone());
      mesh.position.set((p1.x + p2.x) / 2, elev + h / 2, (p1.z + p2.z) / 2);
      mesh.rotation.y = -angle;

      const edges = new THREE.EdgesGeometry(geom);
      const edgeLine = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x1e293b, linewidth: 1.5 }));
      mesh.add(edgeLine);

      mesh.userData = { isAec: true, aecData: elem };
      grp.add(mesh);

    } else if (elem.type === 'door') {
      const pos = elem.pos;
      const w = elem.width || 900;
      const h = elem.height || 2200;
      const thk = elem.thickness || 100;
      const ang = (elem.angle || 0) * Math.PI / 180;
      const elev = pos.y || 0;

      const doorGrp = new THREE.Group();
      doorGrp.position.set(pos.x, elev, pos.z);
      doorGrp.rotation.y = -ang;

      // 1. Frame: Left jamb, right jamb, header
      const jambGeom = new THREE.BoxGeometry(50, h, thk + 20);
      const leftJamb = new THREE.Mesh(jambGeom, frameMat);
      leftJamb.position.set(-w / 2 + 25, h / 2, 0);
      doorGrp.add(leftJamb);

      const rightJamb = new THREE.Mesh(jambGeom, frameMat);
      rightJamb.position.set(w / 2 - 25, h / 2, 0);
      doorGrp.add(rightJamb);

      const headerGeom = new THREE.BoxGeometry(w, 50, thk + 20);
      const header = new THREE.Mesh(headerGeom, frameMat);
      header.position.set(0, h - 25, 0);
      doorGrp.add(header);

      // 2. Door Leaf (Panel) - open ~30 degrees
      const leafW = w - 80;
      const leafGeom = new THREE.BoxGeometry(leafW, h - 60, 40);
      const leafMesh = new THREE.Mesh(leafGeom, leafMat);
      const leafPivot = new THREE.Group();
      leafPivot.position.set(-w / 2 + 50, 0, 0);
      leafPivot.rotation.y = 0.52; // ~30 degrees open
      leafMesh.position.set(leafW / 2, (h - 60) / 2 + 10, 0);
      leafPivot.add(leafMesh);

      // 3. Handle
      const handleGeom = new THREE.CylinderGeometry(10, 10, 60, 8);
      const handleMesh = new THREE.Mesh(handleGeom, handleMat);
      handleMesh.rotation.z = Math.PI / 2;
      handleMesh.position.set(leafW - 50, 1000, 25);
      leafPivot.add(handleMesh);

      doorGrp.add(leafPivot);

      // 4. Floor Swing Arc
      const arcCurve = new THREE.EllipseCurve(
        -w / 2 + 50, 0,
        leafW, leafW,
        0, 0.52,
        false, 0
      );
      const arcPts = arcCurve.getPoints(16).map(p => new THREE.Vector3(p.x, 5, p.y));
      const arcGeom = new THREE.BufferGeometry().setFromPoints(arcPts);
      const arcLine = new THREE.Line(arcGeom, new THREE.LineBasicMaterial({ color: 0x0284c7, linewidth: 1 }));
      doorGrp.add(arcLine);

      doorGrp.userData = { isAec: true, aecData: elem };
      grp.add(doorGrp);
    }
  });

  scene.add(grp);
  if (isModal) modalAecThreeGroup = grp;
  else aecThreeGroup = grp;
  return grp;
}

function getAecCandidatePoints(currentY) {
  const pts = [];
  if (!etabsData) return pts;

  // Columns: centers & 4 corners
  (etabsData.columns || []).forEach(c => {
    const colY = (c.p1[2] + c.p2[2]) / 2.0;
    if (Math.abs(colY - currentY) < 4000) {
      const cx = c.p1[0];
      const cz = -c.p1[1];
      const w = (c.width || 300) / 2;
      const d = (c.depth || 300) / 2;
      pts.push({ x: cx, y: currentY, z: cz, label: `Cột ${c.label || ''}` });
      pts.push({ x: cx - w, y: currentY, z: cz - d, label: `Góc Cột` });
      pts.push({ x: cx + w, y: currentY, z: cz - d, label: `Góc Cột` });
      pts.push({ x: cx - w, y: currentY, z: cz + d, label: `Góc Cột` });
      pts.push({ x: cx + w, y: currentY, z: cz + d, label: `Góc Cột` });
    }
  });

  // Beams: start & end
  (etabsData.beams || []).forEach(b => {
    const bY = (b.p1[2] + b.p2[2]) / 2.0;
    if (Math.abs(bY - currentY) < 3000) {
      pts.push({ x: b.p1[0], y: currentY, z: -b.p1[1], label: `Đầu Dầm ${b.label || ''}` });
      pts.push({ x: b.p2[0], y: currentY, z: -b.p2[1], label: `Đầu Dầm ${b.label || ''}` });
    }
  });

  // Existing AEC Walls
  aecElements.forEach(elem => {
    if (elem.type === 'wall' && elem.p1 && elem.p2) {
      pts.push({ x: elem.p1.x, y: currentY, z: elem.p1.z, label: 'Đầu Tường' });
      pts.push({ x: elem.p2.x, y: currentY, z: elem.p2.z, label: 'Đầu Tường' });
    }
  });

  return pts;
}

function calculateAecSnap(rawPoint, candidates) {
  const currentY = rawPoint.y;
  let bestPt = null;
  let bestDist = Infinity;
  let snapLabel = '';

  // 1. Geometry snap
  if (aecSnapToGeometry && candidates && candidates.length > 0) {
    candidates.forEach(cand => {
      const d = Math.hypot(cand.x - rawPoint.x, cand.z - rawPoint.z);
      if (d < 450 && d < bestDist) {
        bestDist = d;
        bestPt = new THREE.Vector3(cand.x, currentY, cand.z);
        snapLabel = cand.label;
      }
    });
  }

  // 2. Fallback to Round 50 / 100
  if (!bestPt) {
    if (aecSnapRound > 0) {
      const rx = Math.round(rawPoint.x / aecSnapRound) * aecSnapRound;
      const rz = Math.round(rawPoint.z / aecSnapRound) * aecSnapRound;
      bestPt = new THREE.Vector3(rx, currentY, rz);
      snapLabel = `Lưới ${aecSnapRound}mm`;
    } else {
      bestPt = rawPoint.clone();
      snapLabel = 'Tự do';
    }
  }

  return { point: bestPt, label: snapLabel };
}

function distanceToSegment2D(px, pz, x1, z1, x2, z2) {
  const l2 = (x2 - x1) * (x2 - x1) + (z2 - z1) * (z2 - z1);
  if (l2 === 0) return { distance: Math.hypot(px - x1, pz - z1), nearest: { x: x1, z: z1 }, angle: 0 };
  let t = ((px - x1) * (x2 - x1) + (pz - z1) * (z2 - z1)) / l2;
  t = Math.max(0, Math.min(1, t));
  const nx = x1 + t * (x2 - x1);
  const nz = z1 + t * (z2 - z1);
  const angle = Math.atan2(z2 - z1, x2 - x1);
  return { distance: Math.hypot(px - nx, pz - nz), nearest: { x: nx, z: nz }, angle };
}

function setupAec3DInteraction(container, renderer, camera, scene, isModal = false) {
  if (!container || !renderer || !camera || !scene) return;

  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();

  let previewGroup = scene.getObjectByName('aecPreviewGroup');
  if (!previewGroup) {
    previewGroup = new THREE.Group();
    previewGroup.name = 'aecPreviewGroup';
    scene.add(previewGroup);
  }

  // Snap Marker Sphere & Cross
  const markerGeom = new THREE.SphereGeometry(60, 16, 16);
  const markerMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: true });
  const snapMarker = new THREE.Mesh(markerGeom, markerMat);
  snapMarker.visible = false;
  previewGroup.add(snapMarker);

  function getPlaneIntersection(e) {
    const rect = container.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const elev = getAecActiveElevation();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -elev);
    const target = new THREE.Vector3();
    const hit = raycaster.ray.intersectPlane(plane, target);
    return hit ? target : null;
  }

  container.addEventListener('mousemove', e => {
    if (aecToolMode === 'select') {
      snapMarker.visible = false;
      return;
    }

    const rawHit = getPlaneIntersection(e);
    if (!rawHit) {
      snapMarker.visible = false;
      return;
    }

    const candidates = getAecCandidatePoints(rawHit.y);
    const { point: snappedPt, label } = calculateAecSnap(rawHit, candidates);
    aecCurrentSnappedPoint = snappedPt;

    snapMarker.position.copy(snappedPt);
    snapMarker.position.y += 15;
    snapMarker.visible = true;

    const hudCoord = document.getElementById('aec3DHintCoord');

    // Remove old dynamic preview objects in previewGroup (except snapMarker)
    for (let i = previewGroup.children.length - 1; i >= 0; i--) {
      const child = previewGroup.children[i];
      if (child !== snapMarker) {
        previewGroup.remove(child);
      }
    }

    if (aecToolMode === 'wall') {
      if (aecWallStartPoint) {
        let p2 = snappedPt.clone();
        if (e.shiftKey) {
          const dx = Math.abs(p2.x - aecWallStartPoint.x);
          const dz = Math.abs(p2.z - aecWallStartPoint.z);
          if (dx > dz) p2.z = aecWallStartPoint.z;
          else p2.x = aecWallStartPoint.x;
        }

        const dx = p2.x - aecWallStartPoint.x;
        const dz = p2.z - aecWallStartPoint.z;
        const len = Math.hypot(dx, dz);
        const angle = Math.atan2(dz, dx);

        if (len >= 50) {
          const previewGeom = new THREE.BoxGeometry(len, aecWallHeight, aecWallThickness);
          const previewMat = new THREE.MeshBasicMaterial({
            color: 0xf59e0b,
            transparent: true,
            opacity: 0.55
          });
          const previewMesh = new THREE.Mesh(previewGeom, previewMat);
          previewMesh.position.set((aecWallStartPoint.x + p2.x) / 2, aecWallStartPoint.y + aecWallHeight / 2, (aecWallStartPoint.z + p2.z) / 2);
          previewMesh.rotation.y = -angle;

          const edges = new THREE.EdgesGeometry(previewGeom);
          const edgeLine = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xd97706, linewidth: 2 }));
          previewMesh.add(edgeLine);
          previewGroup.add(previewMesh);
        }

        if (hudCoord) {
          hudCoord.innerHTML = `L = <strong class="text-amber-400 font-mono text-sm">${Math.round(len).toLocaleString()} mm</strong> • [${label}] (Shift: Khóa trục • Esc: Hủy)`;
        }
      } else {
        if (hudCoord) {
          hudCoord.innerHTML = `Snap: <strong class="text-cyan-300 font-mono">${label}</strong> • X: ${Math.round(snappedPt.x)}, Z: ${Math.round(snappedPt.z)} • Bấm điểm đầu`;
        }
      }
    } else if (aecToolMode === 'door') {
      const w = aecDoorWidth;
      const h = aecDoorHeight;
      const thk = aecWallThickness;
      let ang = aecDoorAngle;

      // Auto-align door with closest wall if near
      let snapWall = null;
      let minWallDist = 400;
      aecElements.forEach(elem => {
        if (elem.type === 'wall' && elem.p1 && elem.p2) {
          const dist = distanceToSegment2D(snappedPt.x, snappedPt.z, elem.p1.x, elem.p1.z, elem.p2.x, elem.p2.z);
          if (dist.distance < minWallDist) {
            minWallDist = dist.distance;
            snapWall = { elem, nearestPt: dist.nearest, angle: dist.angle };
          }
        }
      });

      if (snapWall) {
        snappedPt.x = snapWall.nearestPt.x;
        snappedPt.z = snapWall.nearestPt.z;
        ang = snapWall.angle * 180 / Math.PI;
      }

      const doorPrevGrp = new THREE.Group();
      doorPrevGrp.position.set(snappedPt.x, snappedPt.y, snappedPt.z);
      doorPrevGrp.rotation.y = -ang * Math.PI / 180;

      const boxGeom = new THREE.BoxGeometry(w, h, thk + 20);
      const boxMat = new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.5 });
      const boxMesh = new THREE.Mesh(boxGeom, boxMat);
      boxMesh.position.set(0, h / 2, 0);
      doorPrevGrp.add(boxMesh);

      const edges = new THREE.EdgesGeometry(boxGeom);
      const edgeLine = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x059669, linewidth: 2 }));
      boxMesh.add(edgeLine);

      previewGroup.add(doorPrevGrp);

      if (hudCoord) {
        hudCoord.innerHTML = `Snap: <strong class="text-emerald-400 font-mono">${label}</strong> • Rộng ${w}mm • Góc ${Math.round(ang)}° (Space: Xoay • Bấm để đặt)`;
      }
    }
  });

  container.addEventListener('click', e => {
    if (e.button !== 0) return;
    if (aecToolMode === 'select') return;

    const rawHit = getPlaneIntersection(e);
    if (!rawHit) return;

    const candidates = getAecCandidatePoints(rawHit.y);
    const { point: snappedPt } = calculateAecSnap(rawHit, candidates);

    if (aecToolMode === 'wall') {
      if (!aecWallStartPoint) {
        aecWallStartPoint = snappedPt.clone();
        if (typeof showToastNotification === 'function') {
          showToastNotification('📍 Đã chọn điểm đầu tường, hãy rê chuột và bấm điểm kết thúc', 'info');
        }
      } else {
        let p2 = snappedPt.clone();
        if (e.shiftKey) {
          const dx = Math.abs(p2.x - aecWallStartPoint.x);
          const dz = Math.abs(p2.z - aecWallStartPoint.z);
          if (dx > dz) p2.z = aecWallStartPoint.z;
          else p2.x = aecWallStartPoint.x;
        }

        const len = Math.hypot(p2.x - aecWallStartPoint.x, p2.z - aecWallStartPoint.z);
        if (len >= 100) {
          aecElements.push({
            id: 'wall_' + Date.now(),
            type: 'wall',
            p1: { x: aecWallStartPoint.x, y: aecWallStartPoint.y, z: aecWallStartPoint.z },
            p2: { x: p2.x, y: p2.y, z: p2.z },
            thickness: aecWallThickness,
            height: aecWallHeight,
            story: aecSelectedStory
          });
          saveAecElementsToStorage();
          refreshAecScene();
          if (typeof showToastNotification === 'function') {
            showToastNotification(`🧱 Đã vẽ tường: L = ${Math.round(len).toLocaleString()} mm (Dày ${aecWallThickness}mm)`, 'success');
          }
          aecWallStartPoint = p2.clone();
        }
      }
    } else if (aecToolMode === 'door') {
      let ang = aecDoorAngle;
      aecElements.forEach(elem => {
        if (elem.type === 'wall' && elem.p1 && elem.p2) {
          const dist = distanceToSegment2D(snappedPt.x, snappedPt.z, elem.p1.x, elem.p1.z, elem.p2.x, elem.p2.z);
          if (dist.distance < 400) {
            snappedPt.x = dist.nearest.x;
            snappedPt.z = dist.nearest.z;
            ang = dist.angle * 180 / Math.PI;
          }
        }
      });

      aecElements.push({
        id: 'door_' + Date.now(),
        type: 'door',
        pos: { x: snappedPt.x, y: snappedPt.y, z: snappedPt.z },
        width: aecDoorWidth,
        height: aecDoorHeight,
        thickness: aecWallThickness,
        angle: ang,
        story: aecSelectedStory
      });
      saveAecElementsToStorage();
      refreshAecScene();
      if (typeof showToastNotification === 'function') {
        showToastNotification(`🚪 Đã đặt cửa block: ${aecDoorWidth} x ${aecDoorHeight} mm`, 'success');
      }
    }
  });

  container.addEventListener('contextmenu', e => {
    if (aecToolMode !== 'select') {
      e.preventDefault();
      if (aecWallStartPoint) {
        aecWallStartPoint = null;
        clearAecPreview();
        if (typeof showToastNotification === 'function') {
          showToastNotification('Đã dừng đường vẽ tường', 'info');
        }
      } else {
        setAecToolMode('select');
      }
    }
  });

  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      if (aecWallStartPoint) {
        aecWallStartPoint = null;
        clearAecPreview();
      } else if (aecToolMode !== 'select') {
        setAecToolMode('select');
      }
    } else if (e.code === 'Space' || e.key === 'r' || e.key === 'R') {
      if (aecToolMode === 'door') {
        e.preventDefault();
        rotateAecDoor();
      }
    } else if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      if (aecElements.length > 0) {
        e.preventDefault();
        undoLastAecElement();
      }
    }
  });
}

function clearAecPreview() {
  if (threeScene) {
    const grp = threeScene.getObjectByName('aecPreviewGroup');
    if (grp) {
      for (let i = grp.children.length - 1; i >= 0; i--) {
        const c = grp.children[i];
        if (c.geometry && c.geometry.type !== 'SphereGeometry') {
          grp.remove(c);
        }
      }
    }
  }
}

function updateAecHUDHint() {
  const hud = document.getElementById('aec3DHintHUD');
  const icon = document.getElementById('aec3DHintIcon');
  const text = document.getElementById('aec3DHintText');
  const coord = document.getElementById('aec3DHintCoord');
  if (!hud) return;

  if (aecToolMode === 'select') {
    hud.classList.add('hidden');
  } else if (aecToolMode === 'wall') {
    hud.classList.remove('hidden');
    if (icon) icon.textContent = '🧱';
    if (text) text.textContent = 'Vẽ Tường Line (Dày ' + aecWallThickness + 'mm • Cao ' + aecWallHeight + 'mm)';
    if (coord) coord.textContent = `Snap: ${aecSnapRound > 0 ? aecSnapRound + 'mm' : 'Tắt'} • Bấm điểm đầu`;
  } else if (aecToolMode === 'door') {
    hud.classList.remove('hidden');
    if (icon) icon.textContent = '🚪';
    if (text) text.textContent = 'Đặt Cửa Block (' + aecDoorWidth + 'x' + aecDoorHeight + 'mm)';
    if (coord) coord.textContent = `Snap: ${aecSnapRound > 0 ? aecSnapRound + 'mm' : 'Tắt'} • Rê chuột, Space xoay`;
  }
}


window.setAecToolMode = setAecToolMode;
window.setAecSnapRound = setAecSnapRound;
window.toggleAecSnapGeom = toggleAecSnapGeom;
window.changeAecStory = changeAecStory;
window.setAecWallThickness = setAecWallThickness;
window.setAecWallHeight = setAecWallHeight;
window.setAecDoorWidth = setAecDoorWidth;
window.rotateAecDoor = rotateAecDoor;
window.undoLastAecElement = undoLastAecElement;
window.clearAllAecElements = clearAllAecElements;
