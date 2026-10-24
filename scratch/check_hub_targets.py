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

# Check targets
print("target_init1:", target_init1 in code)
print("target_init2:", target_init2 in code)
print("target_build:", target_build in code)
print("target_ray1:", target_ray1 in code)
print("target_ray2:", target_ray2 in code)
