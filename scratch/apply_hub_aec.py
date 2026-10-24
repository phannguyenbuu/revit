import sys

with open('etabs_hub.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update initThree3D
target_init1 = """  // Setup Raycaster Hover & Click for Beams
  setupThreeRaycaster(container, threeRenderer, threeCamera, threeBeamMeshes, 'etabs3DTooltip');"""

replacement_init1 = """  // Setup Raycaster Hover & Click for Beams
  setupThreeRaycaster(container, threeRenderer, threeCamera, threeBeamMeshes, 'etabs3DTooltip');

  // Setup AEC 3D Studio Interaction (Wall Line, Door Block, Snap & Round)
  initAecStudio();
  setupAec3DInteraction(container, threeRenderer, threeCamera, threeScene, false);"""

# 2. Update initModalThree3D
target_init2 = """  setupThreeRaycaster(container, modalThreeRenderer, modalThreeCamera, modalThreeBeamMeshes, 'etabs3DTooltip');"""

replacement_init2 = """  setupThreeRaycaster(container, modalThreeRenderer, modalThreeCamera, modalThreeBeamMeshes, 'etabs3DTooltip');

  // Setup Modal AEC 3D Interaction
  setupAec3DInteraction(container, modalThreeRenderer, modalThreeCamera, modalThreeScene, true);"""

# 3. Update build3DModel
target_build = """  // 6. (5) 3D Beam Labels
  const labelsGrp = build3DBeamLabels(scene);
  if (isModal) modalThreeLabelsGroup = labelsGrp;
  else threeLabelsGroup = labelsGrp;
}"""

replacement_build = """  // 6. (5) 3D Beam Labels
  const labelsGrp = build3DBeamLabels(scene);
  if (isModal) modalThreeLabelsGroup = labelsGrp;
  else threeLabelsGroup = labelsGrp;

  // 7. (6) AEC 3D Objects (Walls & Doors)
  const aecGrp = buildAecMeshes(scene, isModal);
  if (isModal) modalAecThreeGroup = aecGrp;
  else aecThreeGroup = aecGrp;
}"""

# 4. Update setupThreeRaycaster for no conflict
target_ray1 = """  container.addEventListener('mousemove', e => {
    const rect = container.getBoundingClientRect();"""

replacement_ray1 = """  container.addEventListener('mousemove', e => {
    if (typeof aecToolMode !== 'undefined' && aecToolMode !== 'select') return;
    const rect = container.getBoundingClientRect();"""

target_ray2 = """  container.addEventListener('click', e => {
    if (isDragging3D) {
      return; // Đã kéo chuột (xoay hoặc pan), không kích hoạt click mở modal
    }
    if (e.button !== 0) return; // Chỉ nhận click chuột trái"""

replacement_ray2 = """  container.addEventListener('click', e => {
    if (typeof aecToolMode !== 'undefined' && aecToolMode !== 'select') return;
    if (isDragging3D) {
      return; // Đã kéo chuột (xoay hoặc pan), không kích hoạt click mở modal
    }
    if (e.button !== 0) return; // Chỉ nhận click chuột trái"""

code = code.replace(target_init1, replacement_init1, 1)
code = code.replace(target_init2, replacement_init2, 1)
code = code.replace(target_build, replacement_build, 1)
code = code.replace(target_ray1, replacement_ray1, 1)
code = code.replace(target_ray2, replacement_ray2, 1)

# Now define AEC Studio functions module
aec_module = r"""
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
"""

# Append aec_module before the end of the file
window_exports = """
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
"""

code = code + "\n" + aec_module + "\n" + window_exports

with open('etabs_hub.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("SUCCESS: etabs_hub.js patched with AEC Studio module!")
