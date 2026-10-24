/**
 * ruby_3d_hub.js - Client-side Controller for SketchUp Ruby (.rb) to 3D OBJ & WebGL Viewer
 * Features:
 * 1. Interactive Three.js WebGL 3D Viewer with OrbitControls
 * 2. Isometric, Top, and Front camera presets + Wireframe toggle
 * 3. Ruby code editor with instant paste, file upload, and sample selection
 * 4. Model bounds, vertices, faces, file size stats & materials breakdown
 * 5. One-click OBJ/MTL download & Explorer folder opening
 */

let ruby3dScene, ruby3dCamera, ruby3dRenderer, ruby3dControls;
let ruby3dCurrentModel = null;
let ruby3dLoaded = false;
let ruby3dInitialized = false;
let rubyCurrentModelStats = null;
let rubyWireframeActive = false;

// Initialize when switching to tab-rb-obj
function initRuby3dDashboard() {
  if (!ruby3dInitialized) {
    initRuby3dThreeViewer();
    ruby3dInitialized = true;
    loadRubySamplesList();
    // Default load house_bim_model.rb on first visit
    loadRubySample('house_bim_model.rb');
  } else {
    setTimeout(onRuby3dResize, 100);
  }
}

// Initialize Three.js WebGL Viewer
function initRuby3dThreeViewer() {
  const container = document.getElementById('ruby3dCanvasContainer');
  if (!container) return;

  const w = container.clientWidth || 640;
  const h = container.clientHeight || 520;

  // 1. Scene
  ruby3dScene = new THREE.Scene();
  ruby3dScene.background = new THREE.Color(0x18181b); // zinc-900

  // 2. Camera
  ruby3dCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
  ruby3dCamera.position.set(20, 16, 25);

  // 3. Renderer
  ruby3dRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
  ruby3dRenderer.setSize(w, h);
  ruby3dRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  ruby3dRenderer.outputEncoding = THREE.sRGBEncoding;
  ruby3dRenderer.shadowMap.enabled = true;
  container.innerHTML = '';
  container.appendChild(ruby3dRenderer.domElement);

  // 4. OrbitControls
  if (typeof THREE.OrbitControls !== 'undefined') {
    ruby3dControls = new THREE.OrbitControls(ruby3dCamera, ruby3dRenderer.domElement);
    ruby3dControls.enableDamping = true;
    ruby3dControls.dampingFactor = 0.08;
    ruby3dControls.screenSpacePanning = true;
    ruby3dControls.minDistance = 1;
    ruby3dControls.maxDistance = 500;
    // Pan bằng nút cuộn chuột (Wheel / Middle button) chuẩn CAD, không ảnh hưởng thao tác click
    ruby3dControls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN
    };
  }

  // 5. Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
  ruby3dScene.add(ambientLight);

  const sunLight = new THREE.DirectionalLight(0xfffbeb, 0.9);
  sunLight.position.set(40, 70, 40);
  sunLight.castShadow = true;
  ruby3dScene.add(sunLight);

  const skyFill = new THREE.DirectionalLight(0x93c5fd, 0.45);
  skyFill.position.set(-40, -20, -40);
  ruby3dScene.add(skyFill);

  // 6. Ground Grid & Axes
  const gridHelper = new THREE.GridHelper(50, 50, 0xf43f5e, 0x334155);
  gridHelper.position.y = -0.01;
  gridHelper.name = "GridHelper";
  ruby3dScene.add(gridHelper);

  const axesHelper = new THREE.AxesHelper(4);
  axesHelper.name = "AxesHelper";
  ruby3dScene.add(axesHelper);

  // 7. Resize Listeners
  window.addEventListener('resize', onRuby3dResize);
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => onRuby3dResize());
    ro.observe(container);
  }

  // 8. Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    if (ruby3dControls) ruby3dControls.update();
    ruby3dRenderer.render(ruby3dScene, ruby3dCamera);
  }
  animate();
}

function onRuby3dResize() {
  const container = document.getElementById('ruby3dCanvasContainer');
  if (!container || !ruby3dRenderer || !ruby3dCamera) return;
  const w = container.clientWidth;
  const h = container.clientHeight || 520;
  if (w <= 0 || h <= 0) return;
  ruby3dCamera.aspect = w / h;
  ruby3dCamera.updateProjectionMatrix();
  ruby3dRenderer.setSize(w, h);
}

// Preset Views
function resetRuby3dCamera() {
  if (!ruby3dCurrentModel || !ruby3dCamera) return;
  const box = new THREE.Box3().setFromObject(ruby3dCurrentModel);
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = ruby3dCamera.fov * (Math.PI / 180);
  let camDist = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
  camDist = Math.max(camDist, 8);

  ruby3dCamera.position.set(camDist * 0.7, camDist * 0.55, camDist * 0.85);
  ruby3dCamera.lookAt(0, size.y / 3, 0);
  if (ruby3dControls) {
    ruby3dControls.target.set(0, size.y / 3, 0);
    ruby3dControls.update();
  }
}

function setRuby3dViewTop() {
  if (!ruby3dCurrentModel || !ruby3dCamera) return;
  const box = new THREE.Box3().setFromObject(ruby3dCurrentModel);
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.z);
  const fov = ruby3dCamera.fov * (Math.PI / 180);
  let camDist = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.4;

  ruby3dCamera.position.set(0, camDist, 0.001);
  ruby3dCamera.lookAt(0, 0, 0);
  if (ruby3dControls) {
    ruby3dControls.target.set(0, 0, 0);
    ruby3dControls.update();
  }
}

function setRuby3dViewFront() {
  if (!ruby3dCurrentModel || !ruby3dCamera) return;
  const box = new THREE.Box3().setFromObject(ruby3dCurrentModel);
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.y);
  const fov = ruby3dCamera.fov * (Math.PI / 180);
  let camDist = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.4;

  ruby3dCamera.position.set(0, size.y / 2, camDist);
  ruby3dCamera.lookAt(0, size.y / 2, 0);
  if (ruby3dControls) {
    ruby3dControls.target.set(0, size.y / 2, 0);
    ruby3dControls.update();
  }
}

function toggleRuby3dWireframe() {
  if (!ruby3dCurrentModel) return;
  rubyWireframeActive = !rubyWireframeActive;
  ruby3dCurrentModel.traverse(function(child) {
    if (child.isMesh && child.material) {
      if (Array.isArray(child.material)) {
        child.material.forEach(m => m.wireframe = rubyWireframeActive);
      } else {
        child.material.wireframe = rubyWireframeActive;
      }
    }
  });

  const btn = document.getElementById('btnRubyWireframe');
  if (btn) {
    if (rubyWireframeActive) {
      btn.classList.add('bg-rose-600', 'text-white');
      btn.classList.remove('bg-zinc-800', 'text-zinc-300');
    } else {
      btn.classList.remove('bg-rose-600', 'text-white');
      btn.classList.add('bg-zinc-800', 'text-zinc-300');
    }
  }
}

// Load OBJ & MTL into Three.js
function loadRuby3dObj(objUrl, mtlUrl, stats) {
  if (!ruby3dScene) return;

  const overlay = document.getElementById('ruby3dLoadingOverlay');
  if (overlay) overlay.classList.remove('hidden');

  // Remove existing model
  if (ruby3dCurrentModel) {
    ruby3dScene.remove(ruby3dCurrentModel);
    ruby3dCurrentModel = null;
  }

  const mtlLoader = new THREE.MTLLoader();
  const mtlDir = mtlUrl.substring(0, mtlUrl.lastIndexOf('/') + 1);
  const mtlFile = mtlUrl.substring(mtlUrl.lastIndexOf('/') + 1);

  mtlLoader.setPath(mtlDir);
  mtlLoader.load(mtlFile, function(materials) {
    materials.preload();

    const objLoader = new THREE.OBJLoader();
    objLoader.setMaterials(materials);

    const objDir = objUrl.substring(0, objUrl.lastIndexOf('/') + 1);
    const objFile = objUrl.substring(objUrl.lastIndexOf('/') + 1);
    objLoader.setPath(objDir);

    objLoader.load(objFile, function(object) {
      ruby3dCurrentModel = object;

      // Enable DoubleSide on materials & shadows
      object.traverse(function(child) {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          if (child.material) {
            if (Array.isArray(child.material)) {
              child.material.forEach(m => {
                m.side = THREE.DoubleSide;
                m.wireframe = rubyWireframeActive;
              });
            } else {
              child.material.side = THREE.DoubleSide;
              child.material.wireframe = rubyWireframeActive;
            }
          }
        }
      });

      // Center model on ground
      const box = new THREE.Box3().setFromObject(object);
      const size = new THREE.Vector3();
      box.getSize(size);
      const center = new THREE.Vector3();
      box.getCenter(center);

      object.position.x = -center.x;
      object.position.y = -box.min.y; // sit directly on y = 0 grid
      object.position.z = -center.z;

      ruby3dScene.add(object);
      ruby3dLoaded = true;

      if (overlay) overlay.classList.add('hidden');

      // Adjust camera
      resetRuby3dCamera();

      // Render model stats
      renderRubyStats(stats || {
        obj_filename: objFile,
        width_m: size.x,
        depth_m: size.z,
        height_m: size.y
      });
    }, function(xhr) {
      // Progress
    }, function(err) {
      console.error("Lỗi nạp OBJ:", err);
      if (overlay) overlay.classList.add('hidden');
      alert("Không thể nạp file 3D OBJ vào WebGL. Kiểm tra console.");
    });
  }, function(xhr) {}, function(err) {
    // If MTL fails, fallback to loading OBJ directly without materials
    console.warn("Không tìm thấy MTL, nạp OBJ đơn sắc:", err);
    const objLoader = new THREE.OBJLoader();
    objLoader.load(objUrl, function(object) {
      ruby3dCurrentModel = object;
      const box = new THREE.Box3().setFromObject(object);
      const center = new THREE.Vector3();
      box.getCenter(center);
      object.position.x = -center.x;
      object.position.y = -box.min.y;
      object.position.z = -center.z;
      ruby3dScene.add(object);
      if (overlay) overlay.classList.add('hidden');
      resetRuby3dCamera();
    });
  });
}

function renderRubyStats(stats) {
  rubyCurrentModelStats = stats;
  const titleEl = document.getElementById('ruby3dCurrentTitle');
  const dimEl = document.getElementById('ruby3dDimensions');
  const vertEl = document.getElementById('ruby3dVertices');
  const faceEl = document.getElementById('ruby3dFaces');
  const sizeEl = document.getElementById('ruby3dFileSize');
  const matEl = document.getElementById('ruby3dMaterialsCount');
  const matListEl = document.getElementById('rubyMaterialsList');

  if (titleEl) titleEl.innerText = stats.obj_filename || 'ruby_model.obj';
  if (dimEl) dimEl.innerText = `${stats.width_m || 0}m x ${stats.depth_m || 0}m • Cao ${stats.height_m || 0}m`;
  if (vertEl) vertEl.innerText = (stats.vertices || 0).toLocaleString();
  if (faceEl) faceEl.innerText = (stats.faces || 0).toLocaleString();
  if (sizeEl) sizeEl.innerText = `${stats.file_size_kb || 0} KB`;
  if (matEl) matEl.innerText = stats.materials_count || (stats.materials ? stats.materials.length : 0);

  if (matListEl && stats.materials) {
    matListEl.innerHTML = stats.materials.map(m => `
      <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-300 text-[11px] font-mono border border-zinc-700">
        <span class="w-2 h-2 rounded-full bg-rose-400"></span>
        <span class="truncate max-w-[120px]">${m}</span>
      </span>
    `).join('');
  }
}

// Convert Ruby code to 3D OBJ
async function runRubyConvert() {
  const codeEl = document.getElementById('rubySourceCode');
  const btn = document.getElementById('btnRunRubyConvert');
  const overlay = document.getElementById('ruby3dLoadingOverlay');
  const logEl = document.getElementById('rubyConsoleLog');

  if (!codeEl || !codeEl.value.trim()) {
    alert("Vui lòng dán mã Ruby hoặc chọn file mẫu trước khi chuyển đổi!");
    return;
  }

  const code = codeEl.value;
  let fileName = 'ruby_model';
  const sampleSelect = document.getElementById('rubySampleSelect');
  if (sampleSelect && sampleSelect.value) {
    fileName = sampleSelect.value.replace('.rb', '');
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="inline-block animate-spin mr-1">⌛</span> Đang Chuyển Đổi...`;
  }
  if (overlay) overlay.classList.remove('hidden');
  if (logEl) {
    logEl.innerText = `[${new Date().toLocaleTimeString()}] Bắt đầu thực thi mã SketchUp Ruby & trích xuất 3D OBJ...`;
  }

  try {
    const res = await fetch('/api/rb/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, fileName: fileName })
    });

    const data = await res.json();

    if (!data.success) {
      throw new Error(data.error || "Lỗi chuyển đổi mã Ruby sang OBJ");
    }

    if (logEl) {
      logEl.innerText = `[${new Date().toLocaleTimeString()}] Thành công!\n- File: ${data.stats.obj_filename}\n- Đỉnh (Vertices): ${data.stats.vertices}\n- Mặt (Faces): ${data.stats.faces}\n- Kích thước: ${data.stats.width_m}m x ${data.stats.depth_m}m x ${data.stats.height_m}m\n- Dung lượng OBJ: ${data.stats.file_size_kb} KB`;
    }

    // Load into Three.js
    loadRuby3dObj(data.stats.obj_url, data.stats.mtl_url, data.stats);

  } catch (err) {
    console.error("Lỗi chuyển đổi Ruby:", err);
    if (logEl) {
      logEl.innerText = `[${new Date().toLocaleTimeString()}] LỖI: ${err.message}`;
    }
    alert(`Không thể chuyển đổi mã Ruby sang 3D OBJ:\n${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i data-lucide="play" class="w-4 h-4 fill-white"></i> Chuyển Đổi sang 3D OBJ`;
      if (window.lucide) lucide.createIcons();
    }
    if (overlay) overlay.classList.add('hidden');
  }
}

// Load Sample Ruby Files
async function loadRubySamplesList() {
  const select = document.getElementById('rubySampleSelect');
  if (!select) return;

  try {
    const res = await fetch('/api/rb/samples');
    const data = await res.json();

    if (data.samples && data.samples.length > 0) {
      select.innerHTML = data.samples.map(s => `
        <option value="${s.name}">${s.name} (${s.size_kb} KB)</option>
      `).join('');
    }
  } catch (err) {
    console.warn("Lỗi tải danh sách mẫu Ruby:", err);
  }
}

// Load Sample Content into Editor
async function loadRubySample(sampleName) {
  const select = document.getElementById('rubySampleSelect');
  const targetFile = sampleName || (select ? select.value : 'house_bim_model.rb');

  try {
    const res = await fetch(`/api/rb/sample-code?file=${encodeURIComponent(targetFile)}`);
    const data = await res.json();

    if (data.code) {
      const codeEl = document.getElementById('rubySourceCode');
      if (codeEl) codeEl.value = data.code;
      if (select && sampleName) select.value = sampleName;
      // Trigger conversion
      runRubyConvert();
    }
  } catch (err) {
    console.error("Lỗi nạp mẫu Ruby:", err);
  }
}

// Handle Local .rb File Upload
function handleRubyFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    const codeEl = document.getElementById('rubySourceCode');
    if (codeEl) codeEl.value = e.target.result;
    const select = document.getElementById('rubySampleSelect');
    if (select) {
      const opt = document.createElement('option');
      opt.value = file.name;
      opt.text = `[Upload] ${file.name}`;
      opt.selected = true;
      select.appendChild(opt);
    }
    runRubyConvert();
  };
  reader.readAsText(file, 'utf-8');
}

// Download OBJ / MTL
function downloadRubyObj() {
  if (rubyCurrentModelStats && rubyCurrentModelStats.obj_url) {
    const a = document.createElement('a');
    a.href = rubyCurrentModelStats.obj_url;
    a.download = rubyCurrentModelStats.obj_filename || 'ruby_model.obj';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } else {
    alert("Chưa có mô hình OBJ nào được xuất!");
  }
}

function downloadRubyMtl() {
  if (rubyCurrentModelStats && rubyCurrentModelStats.mtl_url) {
    const a = document.createElement('a');
    a.href = rubyCurrentModelStats.mtl_url;
    a.download = rubyCurrentModelStats.mtl_filename || 'ruby_model.mtl';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } else {
    alert("Chưa có file vật liệu MTL!");
  }
}

async function openRubyFolder() {
  try {
    const res = await fetch('/api/rb/open-folder', { method: 'POST' });
    const data = await res.json();
    if (!data.success) {
      alert("Không thể mở thư mục: " + (data.message || ""));
    }
  } catch (err) {
    console.error("Lỗi mở thư mục export:", err);
  }
}

function clearRubyCodeEditor() {
  const codeEl = document.getElementById('rubySourceCode');
  if (codeEl) {
    codeEl.value = '';
    codeEl.focus();
  }
}

function copyRubyCodeEditor() {
  const codeEl = document.getElementById('rubySourceCode');
  if (codeEl && codeEl.value) {
    navigator.clipboard.writeText(codeEl.value);
    alert("Đã sao chép toàn bộ mã Ruby vào Clipboard!");
  }
}
