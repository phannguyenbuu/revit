/**
 * RevitAI Bridge Dashboard - General Structural Notes Hub (Bảng Ghi Chú Chung)
 * Source: C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Documents\plot\1020\Plot_20261020_082443_WIN_1016103_603241_1047778_627247.pdf
 */

let gnViewerState = {
  img: null,
  isLoaded: false,
  activeMode: 'hd'
};

const GN_IMAGE_URL = '/static/general_notes_page1.png';
const GN_PDF_URL = '/static/general_notes_drawing.pdf';

// Per-canvas viewport tracker (scale, panX, panY)
const canvasViewports = {};

function getNotesViewport(canvasId) {
  if (!canvasViewports[canvasId]) {
    canvasViewports[canvasId] = {
      scale: 1.0,
      panX: 0,
      panY: 0,
      minScale: 0.08,
      maxScale: 6.0
    };
  }
  return canvasViewports[canvasId];
}

// -----------------------------------------------------------------------------
// 0. SUBTAB DROPDOWN MENU CONTROLLER
// -----------------------------------------------------------------------------

function toggleNotesDropdown(e) {
  if (e) {
    e.stopPropagation();
  }
  const pane = document.getElementById('subpane-etabs-notes');
  const isNotesTabActive = pane && !pane.classList.contains('hidden');

  if (!isNotesTabActive && typeof switchEtabsSubTab === 'function') {
    switchEtabsSubTab('etabs-notes');
  }

  const menu = document.getElementById('notes-dropdown-menu');
  const chevron = document.getElementById('notes-dropdown-chevron');
  if (!menu) return;
  const isHidden = menu.classList.contains('hidden');
  if (isHidden) {
    menu.classList.remove('hidden');
    if (chevron) chevron.style.transform = 'rotate(180deg)';
  } else {
    menu.classList.add('hidden');
    if (chevron) chevron.style.transform = 'rotate(0deg)';
  }
}

function closeNotesDropdown() {
  const menu = document.getElementById('notes-dropdown-menu');
  const chevron = document.getElementById('notes-dropdown-chevron');
  if (menu && !menu.classList.contains('hidden')) {
    menu.classList.add('hidden');
    if (chevron) chevron.style.transform = 'rotate(0deg)';
  }
}

function selectNotesViewAndSwitch(mode) {
  closeNotesDropdown();
  if (typeof switchEtabsSubTab === 'function') {
    switchEtabsSubTab('etabs-notes');
  }
  if (typeof setNotesViewMode === 'function') {
    setNotesViewMode(mode, 'tab');
  }
}

// Global click outside listener
document.addEventListener('click', (e) => {
  const container = document.getElementById('dropdown-notes-container');
  if (container && !container.contains(e.target)) {
    closeNotesDropdown();
  }
});

// -----------------------------------------------------------------------------
// 1. MODAL OPEN / CLOSE & TAB SWITCHING
// -----------------------------------------------------------------------------

function openGeneralNotesModal(initialMode = 'hd') {
  const modal = document.getElementById('modalGeneralNotes');
  if (!modal) return;
  modal.classList.remove('hidden');

  setNotesViewMode(initialMode, 'modal');
  initNotesImage(() => {
    fitNotesCanvas('gnInteractiveCanvas');
  });

  if (window.lucide) {
    try { window.lucide.createIcons(); } catch (e) {}
  }
}

function closeGeneralNotesModal() {
  const modal = document.getElementById('modalGeneralNotes');
  if (modal) modal.classList.add('hidden');
}

function setNotesViewMode(mode, context = 'modal') {
  gnViewerState.activeMode = mode;
  let prefix = 'gnModal';
  let canvasId = 'gnInteractiveCanvas';

  if (context === 'tab') {
    prefix = 'gnTab';
    canvasId = 'tabGnInteractiveCanvas';
  } else if (context === 'etabsModal') {
    prefix = 'gnEtabsModal';
    canvasId = 'modalGnInteractiveCanvas';
  }

  const modes = ['hd', 'pdf', 'text'];
  modes.forEach(m => {
    const pane = document.getElementById(`${prefix}Pane_${m}`);
    const btn = document.getElementById(`${prefix}Btn_${m}`);
    if (pane) {
      if (m === mode) pane.classList.remove('hidden');
      else pane.classList.add('hidden');
    }
    if (btn) {
      if (m === mode) {
        btn.className = (context === 'etabsModal')
          ? 'py-1 px-2.5 rounded text-xs font-bold bg-amber-500 text-white transition'
          : 'py-1.5 px-3 rounded-lg text-xs font-bold bg-amber-500 text-white shadow-xs transition';
      } else {
        btn.className = (context === 'etabsModal')
          ? 'py-1 px-2.5 rounded text-xs font-semibold text-slate-600 hover:text-slate-900 transition'
          : 'py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition';
      }
    }
  });

  if (mode === 'hd') {
    setTimeout(() => {
      fitNotesCanvas(canvasId);
    }, 80);
  } else if (mode === 'pdf') {
    let iframeId = 'gnTabPdfIframe';
    if (context === 'modal') iframeId = 'gnModalPdfIframe';
    else if (context === 'etabsModal') iframeId = 'gnEtabsModalPdfIframe';
    const iframe = document.getElementById(iframeId);
    if (iframe && (!iframe.src || iframe.src === 'about:blank' || iframe.src.endsWith('about:blank'))) {
      iframe.src = iframe.dataset.src || (GN_PDF_URL + '#view=FitH');
    }
  }
}

// -----------------------------------------------------------------------------
// 2. CANVAS INTERACTIVE ENGINE (PAN, ZOOM, FIT)
// -----------------------------------------------------------------------------

function initNotesImage(callback) {
  if (gnViewerState.isLoaded && gnViewerState.img) {
    if (callback) callback();
    return;
  }
  const img = new Image();
  img.src = GN_IMAGE_URL + '?v=' + Date.now();
  img.onload = () => {
    gnViewerState.img = img;
    gnViewerState.isLoaded = true;
    setupCanvasListeners('gnInteractiveCanvas');
    setupCanvasListeners('tabGnInteractiveCanvas');
    setupCanvasListeners('modalGnInteractiveCanvas');
    if (callback) callback();
  };
}

function setupCanvasListeners(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || canvas.dataset.listenersAttached === 'true') return;
  canvas.dataset.listenersAttached = 'true';

  let isDown = false;
  let startX = 0, startY = 0;

  canvas.addEventListener('mousedown', (e) => {
    isDown = true;
    const vp = getNotesViewport(canvasId);
    startX = e.clientX - vp.panX;
    startY = e.clientY - vp.panY;
    canvas.style.cursor = 'grabbing';
  });

  window.addEventListener('mouseup', () => {
    if (isDown) {
      isDown = false;
      if (canvas) canvas.style.cursor = 'grab';
    }
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    const vp = getNotesViewport(canvasId);
    vp.panX = e.clientX - startX;
    vp.panY = e.clientY - startY;
    drawNotesCanvas(canvasId);
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    const vp = getNotesViewport(canvasId);
    const oldScale = vp.scale;
    let newScale = oldScale * zoomFactor;
    newScale = Math.max(vp.minScale, Math.min(vp.maxScale, newScale));

    // Zoom anchored at cursor position
    vp.panX = mouseX - (mouseX - vp.panX) * (newScale / oldScale);
    vp.panY = mouseY - (mouseY - vp.panY) * (newScale / oldScale);
    vp.scale = newScale;

    drawNotesCanvas(canvasId);
    updateZoomHud(canvasId);
  }, { passive: false });

  // Double click to fit view
  canvas.addEventListener('dblclick', () => {
    fitNotesCanvas(canvasId);
  });

  // Window resize observer
  const ro = new ResizeObserver(() => {
    if (canvas && canvas.offsetParent !== null) {
      drawNotesCanvas(canvasId);
    }
  });
  ro.observe(canvas);
}

function fitNotesCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !gnViewerState.img) return;
  setupCanvasListeners(canvasId);

  const rect = canvas.getBoundingClientRect();
  const cWidth = rect.width || canvas.clientWidth || 800;
  const cHeight = rect.height || canvas.clientHeight || 600;

  const imgW = gnViewerState.img.width;
  const imgH = gnViewerState.img.height;
  if (!imgW || !imgH) return;

  const scaleX = (cWidth - 32) / imgW;
  const scaleY = (cHeight - 32) / imgH;
  const vp = getNotesViewport(canvasId);
  vp.scale = Math.min(scaleX, scaleY);

  vp.panX = (cWidth - imgW * vp.scale) / 2;
  vp.panY = (cHeight - imgH * vp.scale) / 2;

  drawNotesCanvas(canvasId);
  updateZoomHud(canvasId);
}

function zoomNotesCanvas(factor, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !gnViewerState.img) return;
  setupCanvasListeners(canvasId);

  const rect = canvas.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const vp = getNotesViewport(canvasId);
  const oldScale = vp.scale;
  let newScale = oldScale * factor;
  newScale = Math.max(vp.minScale, Math.min(vp.maxScale, newScale));

  vp.panX = centerX - (centerX - vp.panX) * (newScale / oldScale);
  vp.panY = centerY - (centerY - vp.panY) * (newScale / oldScale);
  vp.scale = newScale;

  drawNotesCanvas(canvasId);
  updateZoomHud(canvasId);
}

function resetNotesCanvas100(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !gnViewerState.img) return;
  setupCanvasListeners(canvasId);

  const vp = getNotesViewport(canvasId);
  vp.scale = 1.0;
  const rect = canvas.getBoundingClientRect();
  vp.panX = (rect.width - gnViewerState.img.width) / 2;
  vp.panY = (rect.height - gnViewerState.img.height) / 2;

  drawNotesCanvas(canvasId);
  updateZoomHud(canvasId);
}

function drawNotesCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !gnViewerState.img) return;
  setupCanvasListeners(canvasId);

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;

  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (!w || !h) return;

  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }

  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);

  // Background grid
  ctx.fillStyle = '#1e293b';
  ctx.fillRect(0, 0, w, h);

  // Subtle grid lines
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 0.5;
  const gridSize = 40;
  for (let x = 0; x < w; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Draw CAD sheet with smooth shadow
  const vp = getNotesViewport(canvasId);
  const imgW = gnViewerState.img.width * vp.scale;
  const imgH = gnViewerState.img.height * vp.scale;
  const px = vp.panX;
  const py = vp.panY;

  ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
  ctx.shadowBlur = 18;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 6;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(px, py, imgW, imgH);

  ctx.shadowColor = 'transparent';
  ctx.drawImage(gnViewerState.img, px, py, imgW, imgH);

  // Sheet boundary border
  ctx.strokeStyle = '#0284c7';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(px, py, imgW, imgH);

  ctx.restore();
}

function updateZoomHud(canvasId) {
  const vp = getNotesViewport(canvasId);
  const pct = Math.round(vp.scale * 100);
  let hudId = 'gnModalZoomBadge';
  if (canvasId === 'tabGnInteractiveCanvas') hudId = 'gnTabZoomBadge';
  const el = document.getElementById(hudId);
  if (el) el.textContent = pct + '%';
}

// -----------------------------------------------------------------------------
// 3. UTILITY ACTIONS (OPEN FOLDER, PRINT, DOWNLOAD)
// -----------------------------------------------------------------------------

function openGeneralNotesFolder() {
  fetch('/api/general-notes/open-folder', { method: 'POST' })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        showToastNotification('Đã mở thư mục chứa bản vẽ trên Windows Explorer', 'success');
      } else {
        alert('Lỗi mở thư mục: ' + (res.error || 'Unknown'));
      }
    })
    .catch(e => alert('Lỗi kết nối API: ' + e));
}

function downloadGeneralNotesPdf() {
  const a = document.createElement('a');
  a.href = GN_PDF_URL;
  a.download = 'Plot_20261020_082443_Bang_Ghi_Chu_Chung_TCVN.pdf';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function printGeneralNotes() {
  const w = window.open(GN_PDF_URL, '_blank');
  if (w) {
    w.focus();
    setTimeout(() => {
      try { w.print(); } catch (e) {}
    }, 600);
  }
}

function copyNoteSection(elemId) {
  const el = document.getElementById(elemId);
  if (!el) return;
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    showToastNotification('Đã sao chép nội dung ghi chú vào Clipboard!', 'success');
  }).catch(() => {
    alert('Không thể tự động sao chép. Vui lòng chọn text thủ công.');
  });
}

function showToastNotification(msg, type = 'info') {
  let toast = document.getElementById('gnGlobalToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'gnGlobalToast';
    toast.className = 'fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-2xl shadow-xl font-bold text-xs flex items-center gap-2 transition-all duration-300 pointer-events-none opacity-0 translate-y-2';
    document.body.appendChild(toast);
  }

  if (type === 'success') {
    toast.className = 'fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-2xl shadow-xl font-bold text-xs flex items-center gap-2 transition-all duration-300 pointer-events-none bg-emerald-600 text-white shadow-emerald-500/30 opacity-100 translate-y-0';
    toast.innerHTML = `<span class="w-2 h-2 rounded-full bg-white"></span> ${msg}`;
  } else {
    toast.className = 'fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-2xl shadow-xl font-bold text-xs flex items-center gap-2 transition-all duration-300 pointer-events-none bg-slate-900 text-white shadow-slate-900/30 opacity-100 translate-y-0';
    toast.innerHTML = `<span>ℹ️</span> ${msg}`;
  }

  setTimeout(() => {
    toast.classList.remove('opacity-100', 'translate-y-0');
    toast.classList.add('opacity-0', 'translate-y-2');
  }, 2800);
}

// Auto-initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initNotesImage();
});
