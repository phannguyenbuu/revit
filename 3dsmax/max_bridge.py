# -*- coding: utf-8 -*-
"""
3ds Max AI Copilot Bridge & Chatbot Server
Enables external AI agents, CLI tools, and the embedded Chatbot UI to inspect,
control, and automate Autodesk 3ds Max safely on the main Qt/Max thread.
"""

import sys
import os
import io
import json
import time
import queue
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# 3ds Max Python APIs
try:
    import pymxs
    from pymxs import runtime as rt
except ImportError:
    pymxs = None
    rt = None

# Qt Support (PySide2 for 3ds Max 2021-2023, PySide6 for 2024+)
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    QT_VERSION = 5
except ImportError:
    try:
        from PySide6 import QtCore, QtWidgets, QtGui
        QT_VERSION = 6
    except ImportError:
        QtCore = QtWidgets = QtGui = None
        QT_VERSION = 0

# Global singletons
_BRIDGE_SERVER = None
_CHATBOT_WINDOW = None
_TASK_QUEUE = queue.Queue()
_DISPATCHER_TIMER = None
_DEFAULT_PORT = 8096

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
PORT_FILE_REPO = os.path.join(REPO_DIR, "bridge_port.txt")
PORT_FILE_TEMP = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "max_bridge_port.txt")

# ==============================================================================
# Main Thread Task Dispatcher
# ==============================================================================

def _process_main_thread_tasks():
    """Processes queued tasks on 3ds Max's main thread via QTimer."""
    count = 0
    while not _TASK_QUEUE.empty() and count < 10:
        count += 1
        try:
            task = _TASK_QUEUE.get_nowait()
            func, args, kwargs, result_holder, done_event = task
            try:
                res = func(*args, **kwargs)
                result_holder['result'] = res
            except Exception as e:
                result_holder['error'] = str(e)
                result_holder['traceback'] = traceback.format_exc()
            finally:
                done_event.set()
        except queue.Empty:
            break

def run_on_main_thread(func, *args, **kwargs):
    """Enqueues a function to run on the 3ds Max main thread and waits for the result."""
    if threading.current_thread() is threading.main_thread():
        return func(*args, **kwargs)

    done_event = threading.Event()
    result_holder = {}
    _TASK_QUEUE.put((func, args, kwargs, result_holder, done_event))
    
    timeout_sec = kwargs.pop('_timeout', 45)
    success = done_event.wait(timeout=timeout_sec)
    
    if not success:
        return {"error": f"Execution timed out after {timeout_sec}s"}
    if "error" in result_holder:
        return {"error": result_holder["error"], "traceback": result_holder.get("traceback")}
    return result_holder.get("result")

# ==============================================================================
# 3ds Max Automation Core Logic
# ==============================================================================

def get_scene_status():
    """Returns general metadata about 3ds Max and the open scene."""
    if not rt:
        return {"status": "error", "message": "pymxs not loaded"}

    filepath = str(rt.maxFilePath) + str(rt.maxFileName)
    if not filepath.strip():
        filepath = "Untitled"

    renderer_class = "Unknown"
    try:
        renderer_class = str(rt.classof(rt.renderers.current))
    except Exception:
        pass

    viewport_type = "Unknown"
    try:
        viewport_type = str(rt.viewport.getType())
    except Exception:
        pass

    return {
        "status": "online",
        "app": "Autodesk 3ds Max",
        "max_version": str(rt.maxVersion()[0]),
        "file_path": filepath,
        "is_modified": bool(rt.getSaveRequired()),
        "objects_count": int(rt.objects.count),
        "selection_count": int(rt.selection.count),
        "renderer": renderer_class,
        "viewport": viewport_type,
        "system_unit": f"{rt.units.SystemScale} {rt.units.SystemType}",
        "time_range": {
            "start": float(rt.animationRange.start),
            "end": float(rt.animationRange.end),
            "current": float(rt.currentTime),
            "frame_rate": int(rt.frameRate)
        }
    }

def get_scene_summary(limit=100):
    """Lists objects in the scene with transforms, classes, and materials."""
    if not rt:
        return {"error": "pymxs not loaded"}

    status = get_scene_status()
    objects = []
    
    for i in range(min(int(rt.objects.count), limit)):
        try:
            node = rt.objects[i]
            pos = [round(float(node.pos.x), 2), round(float(node.pos.y), 2), round(float(node.pos.z), 2)]
            
            # Poly/Vertex count
            poly_count = 0
            vert_count = 0
            try:
                poly_count = int(rt.getNumFaces(node))
                vert_count = int(rt.getNumVerts(node))
            except Exception:
                pass

            mat_name = str(node.material.name) if node.material else None
            layer_name = str(node.layer.name) if node.layer else "0"

            objects.append({
                "name": str(node.name),
                "class": str(rt.classof(node)),
                "layer": layer_name,
                "material": mat_name,
                "position": pos,
                "polys": poly_count,
                "verts": vert_count,
                "is_selected": bool(node.isSelected),
                "is_hidden": bool(node.isHidden)
            })
        except Exception:
            continue

    selected_names = [str(node.name) for node in rt.selection]

    return {
        "status": status,
        "total_objects": int(rt.objects.count),
        "returned_objects": len(objects),
        "selected_objects": selected_names,
        "objects": objects
    }

def execute_maxscript(code):
    """Executes arbitrary MAXScript code and captures output."""
    if not rt:
        return {"error": "pymxs not loaded"}

    # Wrap in with undo label
    try:
        # Evaluate code
        val = rt.execute(code)
        val_str = str(val) if val is not None else "OK"
        return {"success": True, "result": val_str}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

def execute_python_code(code):
    """Executes arbitrary Python code in the 3ds Max environment."""
    loc = {"rt": rt, "pymxs": pymxs}
    try:
        # Try eval first for expressions
        try:
            res = eval(code, globals(), loc)
            return {"success": True, "result": str(res)}
        except SyntaxError:
            # Fallback to exec
            exec(code, globals(), loc)
            return {"success": True, "result": "Executed successfully"}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

def perform_action(action_name, params):
    """Handles structured high-level modeling, camera, lighting, and rendering tasks."""
    if not rt:
        return {"error": "pymxs not loaded"}

    action = action_name.lower()

    if action == "create_primitive":
        ptype = params.get("type", "Box").capitalize()
        pos = params.get("position", [0, 0, 0])
        name = params.get("name")
        p_dict = params.get("params", {})

        # Build MAXScript command
        param_parts = [f"pos:[{pos[0]},{pos[1]},{pos[2]}]"]
        if name:
            param_parts.append(f'name:"{name}"')
        for k, v in p_dict.items():
            if isinstance(v, str):
                param_parts.append(f'{k}:"{v}"')
            else:
                param_parts.append(f'{k}:{v}')

        cmd = f"{ptype} {(' '.join(param_parts))}"
        res = rt.execute(cmd)
        return {"success": True, "action": action, "node": str(res.name) if res else str(res)}

    elif action == "create_camera":
        pos = params.get("position", [0, -200, 150])
        target = params.get("target", [0, 0, 50])
        name = params.get("name", "AI_Camera")
        fov = params.get("fov", 45.0)

        cmd = f'Freecamera name:"{name}" pos:[{pos[0]},{pos[1]},{pos[2]}] fov:{fov}; targetCamera target:(targetObject pos:[{target[0]},{target[1]},{target[2]}])'
        res = rt.execute(cmd)
        return {"success": True, "camera": name}

    elif action == "create_light_setup":
        # 3-Point Lighting setup
        mxs = """
        (
            local keyLight = directionalLight name:"AI_KeyLight" pos:[150, -150, 200] target:(targetObject pos:[0,0,0]) multiplier:1.2
            local fillLight = omniLight name:"AI_FillLight" pos:[-180, -100, 120] multiplier:0.6
            local backLight = omniLight name:"AI_RimLight" pos:[0, 200, 160] multiplier:0.8
            #(keyLight.name, fillLight.name, backLight.name)
        )
        """
        res = rt.execute(mxs)
        return {"success": True, "lights": ["AI_KeyLight", "AI_FillLight", "AI_RimLight"]}

    elif action == "quick_render":
        out_path = params.get("output_path", os.path.join(REPO_DIR, "render_test.png"))
        width = params.get("width", 1280)
        height = params.get("height", 720)
        
        # Render active viewport
        mxs = f'render outputfile:@"{out_path}" outputwidth:{width} outputheight:{height} vfb:off'
        rt.execute(mxs)
        
        file_exists = os.path.exists(out_path)
        return {
            "success": file_exists,
            "output_path": out_path,
            "size_bytes": os.path.getsize(out_path) if file_exists else 0
        }

    elif action == "export_model":
        out_path = params.get("path")
        if not out_path:
            return {"error": "Missing 'path' parameter"}
        
        selected_only = bool(params.get("selected_only", False))
        sel_flag = "#noPrompt selectedOnly:true" if selected_only else "#noPrompt"
        
        mxs = f'exportFile @"{out_path}" {sel_flag}'
        res = rt.execute(mxs)
        return {"success": bool(res), "exported_file": out_path}

    elif action == "select":
        names = params.get("names", [])
        if params.get("all"):
            rt.execute("select $*")
            return {"success": True, "count": int(rt.selection.count)}
        elif params.get("none"):
            rt.execute("clearSelection()")
            return {"success": True, "count": 0}
        elif names:
            name_str = ", ".join([f'"{n}"' for n in names])
            mxs = f'select (for o in objects where findItem #({name_str}) o.name > 0 collect o)'
            rt.execute(mxs)
            return {"success": True, "count": int(rt.selection.count)}

    elif action == "delete":
        if params.get("selection"):
            cnt = int(rt.selection.count)
            rt.execute("delete $")
            return {"success": True, "deleted_count": cnt}
        names = params.get("names", [])
        if names:
            name_str = ", ".join([f'"{n}"' for n in names])
            mxs = f'delete (for o in objects where findItem #({name_str}) o.name > 0 collect o)'
            rt.execute(mxs)
            return {"success": True, "deleted": names}

    elif action == "clean_scene":
        mxs = """
        (
            local removedLayers = 0
            for i = (LayerManager.count - 1) to 1 by -1 do
            (
                local l = LayerManager.getLayer i
                local nodes = #()
                l.nodes &nodes
                if nodes.count == 0 do
                (
                    LayerManager.deleteLayerByName l.name
                    removedLayers += 1
                )
            )
            freeSceneBitmaps()
            gc light:true
            "Cleaned " + (removedLayers as string) + " empty layers."
        )
        """
        res = rt.execute(mxs)
        return {"success": True, "result": str(res)}

    elif action == "export_fbx":
        out_path = params.get("path")
        return export_selection_to_fbx(out_path)

    elif action in ("export_rectangles_fbx", "export_rect_fbx"):
        out_dir = params.get("dir", DEFAULT_FBX_DIR)
        return export_rectangles_batch(output_dir=out_dir)

    elif action in ("native_export", "max_export"):
        return native_max_export()

    elif action in ("native_import", "max_import"):
        return native_max_import()

    elif action == "create_toolbar":
        tb = create_ai_toolbar()
        return {"success": tb is not None}

    return {"error": f"Unknown action: {action_name}"}

DEFAULT_FBX_DIR = r"D:\Dropbox\3DLib\mesh\FBX"

def native_max_export():
    """Triggers native 3ds Max File Export command dialog."""
    if rt:
        try:
            rt.execute("max file export")
            return {"success": True, "message": "Đã gọi hộp thoại File Export của 3ds Max."}
        except Exception as e:
            err = str(e)
            if _CHATBOT_WINDOW:
                _CHATBOT_WINDOW.append_message("🤖 AI", f"❌ Lỗi mở Export: {err}", color="#e06c75")
            return {"error": err}
    return {"error": "pymxs not loaded"}

def native_max_import():
    """Triggers native 3ds Max File Import command dialog."""
    if rt:
        try:
            rt.execute("max file import")
            return {"success": True, "message": "Đã gọi hộp thoại File Import của 3ds Max."}
        except Exception as e:
            err = str(e)
            if _CHATBOT_WINDOW:
                _CHATBOT_WINDOW.append_message("🤖 AI", f"❌ Lỗi mở Import: {err}", color="#e06c75")
            return {"error": err}
    return {"error": "pymxs not loaded"}

def get_default_fbx_path():
    r"""Returns the default FBX export path: D:\Dropbox\3DLib\mesh\FBX\{maxfilename}.fbx"""
    max_file = str(rt.maxFileName).strip() if rt else ""
    if max_file:
        base_name = os.path.splitext(max_file)[0]
    elif rt and int(rt.selection.count) > 0:
        base_name = str(rt.selection[0].name).strip()
    else:
        base_name = "Untitled"

    os.makedirs(DEFAULT_FBX_DIR, exist_ok=True)
    return os.path.join(DEFAULT_FBX_DIR, f"{base_name}.fbx")

def export_rectangles_batch(rectangles=None, output_dir=None):
    """Batch exports objects bounded by each selected (or scene) Rectangle to FBX.
    For each rectangle:
      - Filters all objects whose XY bounding box falls within the rectangle.
      - Translates coordinates so rectangle position is (0, 0) (objects offset accordingly).
      - Exports to FBX named: {maxfilename}_{rectangle.name}.fbx in D:\\Dropbox\\3DLib\\mesh\\FBX
      - Restores original coordinates of objects immediately after export.
    """
    if not rt:
        return {"error": "pymxs not loaded"}

    if not output_dir:
        output_dir = DEFAULT_FBX_DIR
    os.makedirs(output_dir, exist_ok=True)

    # 1. Determine target rectangles
    if rectangles is None:
        sel = list(rt.selection)
        rect_candidates = [o for o in sel if rt.isKindOf(o, rt.Rectangle) or str(rt.classOf(o)).lower() == 'rectangle']
        if not rect_candidates:
            # If nothing in selection is a rectangle, search all shapes in scene
            rect_candidates = [o for o in rt.shapes if rt.isKindOf(o, rt.Rectangle) or str(rt.classOf(o)).lower() == 'rectangle']
        rectangles = rect_candidates

    if not rectangles:
        return {"error": "Không tìm thấy đối tượng Rectangle nào! Hãy tạo hoặc chọn ít nhất 1 Rectangle trong 3ds Max."}

    max_file = str(rt.maxFileName).strip()
    base_max_name = os.path.splitext(max_file)[0] if max_file else "Untitled"

    # Configure standard FBX export settings
    mxs_setup = """
    (
        FBXExporterSetParam "ResetExport"
        FBXExporterSetParam "SelectedOnly" true
        FBXExporterSetParam "ASCII" false
        FBXExporterSetParam "EmbedTextures" true
        FBXExporterSetParam "Cameras" false
        FBXExporterSetParam "Lights" false
        FBXExporterSetParam "Animation" false
        FBXExporterSetParam "Triangulate" false
        FBXExporterSetParam "ScaleFactor" 1.0
        FBXExporterSetParam "UpAxis" "Z"
    )
    """
    rt.execute(mxs_setup)

    orig_sel = list(rt.selection)
    all_rect_set = set(rectangles)
    results = []
    tol = 5.0  # 5mm tolerance for bounding box containment

    for r in rectangles:
        r_name = str(r.name).strip()
        r_min_x = min(float(r.min.x), float(r.max.x))
        r_max_x = max(float(r.min.x), float(r.max.x))
        r_min_y = min(float(r.min.y), float(r.max.y))
        r_max_y = max(float(r.min.y), float(r.max.y))

        inside_objs = []
        for o in rt.objects:
            if o in all_rect_set or rt.isKindOf(o, rt.Targetobject):
                continue
            try:
                o_min_x = min(float(o.min.x), float(o.max.x))
                o_max_x = max(float(o.min.x), float(o.max.x))
                o_min_y = min(float(o.min.y), float(o.max.y))
                o_max_y = max(float(o.min.y), float(o.max.y))

                if (o_min_x >= (r_min_x - tol) and o_max_x <= (r_max_x + tol) and
                    o_min_y >= (r_min_y - tol) and o_max_y <= (r_max_y + tol)):
                    inside_objs.append(o)
            except Exception:
                pass

        if not inside_objs:
            msg_skip = f"Rectangle '{r_name}' không chứa vật thể nào bên trong (bỏ qua)."
            if rt:
                rt.format(f"[MaxAI] {msg_skip}\\n")
            results.append({"rectangle": r_name, "count": 0, "status": "skipped", "message": msg_skip})
            continue

        # Find root objects to avoid double translation on children/groups
        inside_set = set(inside_objs)
        root_objs = [o for o in inside_objs if o.parent is None or o.parent not in inside_set]

        # Translation delta to move rectangle pos to (0,0) in X, Y
        delta = rt.Point3(-float(r.pos.x), -float(r.pos.y), 0.0)

        # Output file name: {maxfilename}_{rectangle.name}.fbx
        safe_r_name = "".join(c for c in r_name if c.isalnum() or c in (' ', '_', '-')).strip()
        out_filename = f"{base_max_name}_{safe_r_name}.fbx"
        out_path = os.path.join(output_dir, out_filename)

        export_ok = False
        try:
            # 1. Translate root objects to origin
            for ro in root_objs:
                if rt.isValidNode(ro):
                    rt.move(ro, delta)

            # 2. Select inside objects for export
            rt.select(inside_objs)

            # 3. Export to FBX
            ok = rt.exportFile(out_path, rt.Name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
            file_exists = os.path.exists(out_path)
            export_ok = bool(ok) and file_exists
            size_kb = round(os.path.getsize(out_path) / 1024, 1) if file_exists else 0

            if export_ok:
                res_info = {
                    "rectangle": r_name,
                    "filename": out_filename,
                    "path": out_path,
                    "count": len(inside_objs),
                    "size_kb": size_kb,
                    "status": "success"
                }
                results.append(res_info)
                if rt:
                    rt.format(f"[MaxAI] ✅ Đã xuất FBX: {out_filename} ({len(inside_objs)} đối tượng, {size_kb} KB)\\n")
            else:
                results.append({
                    "rectangle": r_name,
                    "filename": out_filename,
                    "status": "failed",
                    "error": "3ds Max exportFile trả về false"
                })
        except Exception as ex:
            results.append({
                "rectangle": r_name,
                "status": "error",
                "error": str(ex)
            })
        finally:
            # 4. ALWAYS restore original positions
            for ro in root_objs:
                if rt.isValidNode(ro):
                    rt.move(ro, -delta)

    # Restore initial selection
    if orig_sel:
        rt.select(orig_sel)
    else:
        rt.clearSelection()

    success_items = [item for item in results if item.get("status") == "success"]
    total_exported = len(success_items)

    summary_msg = f"Đã xuất FBX thành công cho {total_exported}/{len(rectangles)} Rectangle vào {output_dir}"
    if rt:
        rt.displayTempPrompt(summary_msg, 6000)
    if _CHATBOT_WINDOW:
        detail_lines = []
        for item in results:
            if item.get("status") == "success":
                detail_lines.append(f"• 📐 <b>{item['rectangle']}</b> ➔ <code>{item['filename']}</code> ({item['count']} objs, {item['size_kb']} KB)")
            elif item.get("status") == "skipped":
                detail_lines.append(f"• ⚠️ <b>{item['rectangle']}</b>: Không có vật thể bên trong")
            else:
                detail_lines.append(f"• ❌ <b>{item['rectangle']}</b>: Lỗi xuất")
        _CHATBOT_WINDOW.append_message("📦 Export FBX Rectangles", f"✅ {summary_msg}:<br/>" + "<br/>".join(detail_lines), color="#98c379")

    return {
        "success": total_exported > 0,
        "total_rectangles": len(rectangles),
        "exported_count": total_exported,
        "output_dir": output_dir,
        "results": results
    }

def export_selection_to_fbx(output_path=None, prompt_dialog=False):
    r"""Exports currently selected objects in 3ds Max to an FBX file.
    Default destination: D:\Dropbox\3DLib\mesh\FBX\{maxfilename}.fbx
    If selection consists entirely of Rectangle shapes, delegates to batch rectangle export.
    """
    if not rt:
        return {"error": "pymxs not loaded"}

    count = int(rt.selection.count)
    if count == 0:
        return {"error": "Chưa có đối tượng nào được chọn! Hãy chọn ít nhất 1 đối tượng trong 3ds Max."}

    # TÙY CHỌN BATCH RECTANGLE: Nếu toàn bộ đối tượng chọn là Rectangle -> Xuất FBX theo từng Rectangle
    sel = list(rt.selection)
    if len(sel) > 0 and all(rt.isKindOf(o, rt.Rectangle) or str(rt.classOf(o)).lower() == 'rectangle' for o in sel):
        return export_rectangles_batch(rectangles=sel, output_dir=DEFAULT_FBX_DIR)

    if not output_path:
        default_file = get_default_fbx_path()
        if prompt_dialog:
            # Open 3ds Max native Save File Dialog if requested or Shift held
            mxs_dialog = f'getSaveFileName caption:"Xuất FBX Cho Đối Tượng Đang Chọn" filename:@"{default_file}" types:"Autodesk FBX (*.fbx)|*.fbx|"'
            res = rt.execute(mxs_dialog)
            if not res:
                return {"cancelled": True, "message": "Người dùng đã hủy chọn file xuất."}
            output_path = str(res)
        else:
            output_path = default_file

    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    # Configure standard Architectural / BIM FBX settings (Z-Up, Textures Embedded, Selected Only)
    mxs_setup = """
    (
        FBXExporterSetParam "ResetExport"
        FBXExporterSetParam "SelectedOnly" true
        FBXExporterSetParam "ASCII" false
        FBXExporterSetParam "EmbedTextures" true
        FBXExporterSetParam "Cameras" false
        FBXExporterSetParam "Lights" false
        FBXExporterSetParam "Animation" false
        FBXExporterSetParam "Triangulate" false
        FBXExporterSetParam "ScaleFactor" 1.0
        FBXExporterSetParam "UpAxis" "Z"
    )
    """
    rt.execute(mxs_setup)

    export_cmd = f'exportFile @"{output_path}" #noPrompt selectedOnly:true using:FBXEXP'
    ok = rt.execute(export_cmd)

    if ok and os.path.exists(output_path):
        size_kb = round(os.path.getsize(output_path) / 1024, 1)
        filename = os.path.basename(output_path)
        msg = f"Đã xuất FBX thành công: {filename} ({size_kb} KB, {count} đối tượng)"
        try:
            if rt:
                rt.format(f"[MaxAI] {msg} -> {output_path}\n")
                rt.displayTempPrompt(f"Đã xuất FBX: {filename} ({size_kb} KB) vào D:\\Dropbox\\3DLib\\mesh\\FBX", 5000)
            if _CHATBOT_WINDOW:
                _CHATBOT_WINDOW.append_message("📦 Export FBX", f"✅ {msg}\n📁 Lưu tại: {output_path}", color="#98c379")
        except Exception:
            pass
        return {
            "success": True,
            "path": output_path,
            "filename": filename,
            "selected_count": count,
            "size_kb": size_kb
        }
    else:
        return {"error": f"3ds Max không thể xuất file FBX sang {output_path}"}

_AI_TOOLBAR = None

def create_ai_toolbar(main_wnd=None):
    """Creates a native QToolBar docked at the top of 3ds Max."""
    global _AI_TOOLBAR
    if not QtWidgets:
        return None

    if not main_wnd:
        app = QtWidgets.QApplication.instance()
        if app:
            for w in app.topLevelWidgets():
                if "autodesk 3ds max" in w.windowTitle().lower():
                    main_wnd = w
                    break

    if not main_wnd:
        return None

    # Remove existing toolbar if any
    for tb in main_wnd.findChildren(QtWidgets.QToolBar, "MaxAIToolBar"):
        try:
            main_wnd.removeToolBar(tb)
            tb.close()
            tb.deleteLater()
        except Exception:
            pass

    tb = QtWidgets.QToolBar("AI Tools", main_wnd)
    tb.setObjectName("MaxAIToolBar")
    tb.setStyleSheet("""
        QToolBar {
            background-color: #282c34;
            border: 1px solid #3e4451;
            spacing: 4px;
            padding: 2px 4px;
        }
        QToolButton {
            background-color: #21252b;
            color: #abb2bf;
            font-weight: bold;
            font-size: 11px;
            border: 1px solid #3e4451;
            border-radius: 4px;
            padding: 3px 8px;
        }
        QToolButton:hover {
            background-color: #3e4451;
            color: #61afef;
            border: 1px solid #61afef;
        }
    """)

    def _on_export_click():
        is_shift = False
        if QtWidgets and hasattr(QtWidgets, "QApplication"):
            app = QtWidgets.QApplication.instance()
            if app:
                is_shift = bool(app.keyboardModifiers() & QtCore.Qt.ShiftModifier)
        return export_selection_to_fbx(prompt_dialog=is_shift)

    act_native_export = tb.addAction("📤 Export ")
    act_native_export.setToolTip("Lệnh Export gốc của 3ds Max (File -> Export)")
    act_native_export.triggered.connect(lambda: run_on_main_thread(native_max_export))

    act_native_import = tb.addAction("📥 Import ")
    act_native_import.setToolTip("Lệnh Import gốc của 3ds Max (File -> Import)")
    act_native_import.triggered.connect(lambda: run_on_main_thread(native_max_import))

    act_fbx = tb.addAction("📦 Export FBX ")
    act_fbx.setToolTip("Xuất FBX vào D:\\Dropbox\\3DLib\\mesh\\FBX\\{maxfilename}.fbx (Tự động batch nếu chọn Rectangle; Giữ Shift để đổi nơi lưu)")
    act_fbx.triggered.connect(lambda: run_on_main_thread(_on_export_click))

    act_rect_fbx = tb.addAction("📐 FBX Rectangles ")
    act_rect_fbx.setToolTip("Xuất FBX theo từng Rectangle: lọc các vật thể lọt lòng XY, đưa về gốc (0,0) -> D:\\Dropbox\\3DLib\\mesh\\FBX\\{maxfilename}_{rect}.fbx")
    act_rect_fbx.triggered.connect(lambda: run_on_main_thread(export_rectangles_batch))

    act_copilot = tb.addAction("🤖 AI Copilot ")
    act_copilot.setToolTip("Hiện / Ẩn panel AI Copilot ở lề phải")
    act_copilot.triggered.connect(toggle_ui)

    main_wnd.addToolBar(QtCore.Qt.TopToolBarArea, tb)
    tb.show()
    _AI_TOOLBAR = tb
    return tb

# ==============================================================================
# HTTP Server & Request Handler
# ==============================================================================

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class MaxBridgeRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default console clutter

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json({"status": "ok"})

    def do_GET(self):
        path = self.path.lower()
        if path in ("/", "/api/status"):
            res = run_on_main_thread(get_scene_status)
            self._send_json(res)
        elif path == "/api/scene":
            res = run_on_main_thread(get_scene_summary)
            self._send_json(res)
        else:
            self._send_json({"error": f"Unknown endpoint: {self.path}"}, 404)

    def do_POST(self):
        path = self.path.lower()
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            body = json.loads(raw_body)
        except Exception as e:
            self._send_json({"error": f"Invalid JSON body: {e}"}, 400)
            return

        if path == "/api/execute":
            lang = body.get("language", "maxscript").lower()
            code = body.get("code", "")
            if lang == "python":
                res = run_on_main_thread(execute_python_code, code)
            else:
                res = run_on_main_thread(execute_maxscript, code)
            
            # Also log to Chatbot UI if open
            if _CHATBOT_WINDOW:
                run_on_main_thread(_CHATBOT_WINDOW.log_external_command, lang, code, res)
            self._send_json(res)

        elif path == "/api/action":
            action = body.get("action", "")
            params = body.get("params", body)
            res = run_on_main_thread(perform_action, action, params)
            if _CHATBOT_WINDOW:
                run_on_main_thread(_CHATBOT_WINDOW.log_external_command, "action", action, res)
            self._send_json(res)

        elif path == "/api/chat":
            prompt = body.get("prompt", "")
            # Process prompt through chatbot logic
            res = run_on_main_thread(handle_chat_prompt, prompt)
            self._send_json(res)

        elif path == "/mcp":
            # Model Context Protocol router
            method = body.get("method", "")
            if method == "tools/list":
                self._send_json({
                    "tools": [
                        {"name": "get_scene_status", "description": "Get current 3ds Max version, active file, units, and renderer."},
                        {"name": "get_scene_summary", "description": "List objects, polygons, layers, and materials."},
                        {"name": "execute_maxscript", "description": "Execute arbitrary MAXScript code in 3ds Max."},
                        {"name": "execute_python", "description": "Execute Python code in 3ds Max."},
                        {"name": "perform_action", "description": "Perform high-level actions: create_primitive, create_camera, create_light_setup, quick_render, export_model, clean_scene."}
                    ]
                })
            elif method == "tools/call":
                tool_name = body.get("params", {}).get("name", "")
                args = body.get("params", {}).get("arguments", {})
                if tool_name == "get_scene_status":
                    res = run_on_main_thread(get_scene_status)
                elif tool_name == "get_scene_summary":
                    res = run_on_main_thread(get_scene_summary, args.get("limit", 100))
                elif tool_name == "execute_maxscript":
                    res = run_on_main_thread(execute_maxscript, args.get("code", ""))
                elif tool_name == "execute_python":
                    res = run_on_main_thread(execute_python_code, args.get("code", ""))
                elif tool_name == "perform_action":
                    res = run_on_main_thread(perform_action, args.get("action", ""), args.get("params", {}))
                else:
                    res = {"error": f"Unknown tool: {tool_name}"}
                self._send_json({"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]})
            else:
                self._send_json({"jsonrpc": "2.0", "result": {"supported": True}})
        else:
            self._send_json({"error": f"Unknown endpoint: {self.path}"}, 404)

def handle_chat_prompt(prompt):
    """Interprets high-level chat prompts and executes actions or returns guidance."""
    p_lower = prompt.lower()
    
    # 0. Open FBX Folder
    if any(k in p_lower for k in ["mở thư mục", "open folder", "open fbx", "mở fbx"]):
        try:
            os.startfile(DEFAULT_FBX_DIR)
            return {"reply": f"📂 Đã mở thư mục lưu FBX: `{DEFAULT_FBX_DIR}`", "data": {"path": DEFAULT_FBX_DIR}}
        except Exception as e:
            return {"reply": f"❌ Không thể mở thư mục: {e}", "data": {}}

    # Rectangle Batch Export
    if any(k in p_lower for k in ["rectangle", "hcn", "hình chữ nhật", "batch fbx"]) and any(k in p_lower for k in ["xuất", "xuat", "lưu", "save", "export", "chạy"]):
        res = export_rectangles_batch()
        if res.get("success"):
            return {
                "reply": f"✅ Đã xuất FBX thành công cho {res.get('exported_count')}/{res.get('total_rectangles')} Rectangle vào `{res.get('output_dir')}`!",
                "data": res
            }
        else:
            return {
                "reply": f"⚠️ {res.get('error', 'Không tìm thấy Rectangle hoặc lỗi xuất file')}",
                "data": res
            }

    # 1. Toolbar & Export FBX
    if "fbx" in p_lower or any(k in p_lower for k in ["toolbar", "thanh công cụ", "3dlib", "mesh/fbx"]):
        # Always ensure the AI toolbar is created/visible on top
        create_ai_toolbar()
        
        # Check if user specifically asked about information/path/settings or asked to create/show button
        is_query_or_config = any(k in p_lower for k in ["ở đâu", "về đâu", "thư mục", "đường dẫn", "mặc định", "tạo nút", "thêm nút", "cấu hình", "cài đặt", "hướng dẫn"])
        
        # Check if user specifically requested to export FBX right away
        if not is_query_or_config and any(k in p_lower for k in ["xuất", "xuat", "chạy export", "lưu", "save", "export"]):
            res = export_selection_to_fbx()
            if res.get("success"):
                return {
                    "reply": f"✅ Đã xuất thành công FBX: {res.get('filename')} ({res.get('size_kb')} KB, {res.get('selected_count')} đối tượng)!\n• Đường dẫn lưu: `{res.get('path')}`\nĐồng thời thanh công cụ 'AI Tools' đã sẵn sàng trên Toolbar phía trên.",
                    "data": res
                }
            elif res.get("cancelled"):
                return {
                    "reply": f"ℹ️ Bạn đã hủy hộp thoại chọn file FBX. Nút '📦 Export FBX' đã hiển thị trên thanh công cụ phía trên.",
                    "data": res
                }
            elif res.get("error"):
                return {
                    "reply": f"⚠️ {res.get('error')}\nNút '📦 Export FBX' đã được ghim lên thanh công cụ Toolbar phía trên.",
                    "data": res
                }

        # Otherwise user asked to create/show button or asked about default path
        sel_count = int(rt.selection.count) if rt else 0
        default_target = get_default_fbx_path()
        return {
            "reply": f"✅ Nút '📦 Export FBX' được cấu hình lưu mặc định về:\n📁 `{default_target}`\n"
                     f"• Đang chọn: {sel_count} đối tượng.\n"
                     f"• Nhấn trực tiếp nút '📦 Export FBX' trên Toolbar hoặc nút '[📦 Xuất File FBX]' ở panel bên dưới để lưu 1 chạm (Giữ phím Shift nếu muốn chọn thư mục khác).",
            "data": {"toolbar": "MaxAIToolBar", "selected_count": sel_count, "default_path": default_target}
        }

    # 1. Inspect
    if any(k in p_lower for k in ["inspect", "thống kê", "kiểm tra", "summary", "status"]):
        status = get_scene_status()
        summary = get_scene_summary(limit=20)
        return {
            "reply": f"Mô hình đang mở: {status['file_path']}\nSố lượng đối tượng: {status['objects_count']}\nRenderer: {status['renderer']}\nĐang chọn: {len(summary['selected_objects'])} đối tượng.",
            "data": summary
        }

    # 2. Render
    elif any(k in p_lower for k in ["render", "chụp hình", "kết xuất"]):
        out = os.path.join(REPO_DIR, f"render_{int(time.time())}.png")
        res = perform_action("quick_render", {"output_path": out})
        return {
            "reply": f"Đã kết xuất hình ảnh thành công: {out}" if res.get("success") else f"Lỗi render: {res.get('error')}",
            "data": res
        }

    # 3. Clean
    elif any(k in p_lower for k in ["clean", "dọn dẹp", "xóa layer rác"]):
        res = perform_action("clean_scene", {})
        return {"reply": f"Đã dọn dẹp scene: {res.get('result')}", "data": res}

    # 4. Fallback: Evaluate as MAXScript directly if it looks like code
    elif any(p_lower.startswith(prefix) for prefix in ["box ", "sphere ", "cylinder ", "select ", "delete ", "$", "format "]):
        res = execute_maxscript(prompt)
        return {
            "reply": f"Kết quả MAXScript: {res.get('result', res.get('error'))}",
            "data": res
        }

    return {
        "reply": f"Đã nhận yêu cầu: '{prompt}'. Bạn có thể yêu cầu tôi: kiểm tra mô hình, tạo vật thể, thiết lập 3-point light, render nhanh hoặc chạy mã MAXScript/Python.",
        "prompt": prompt
    }

# ==============================================================================
# In-App Chatbot UI (PySide2 / PySide6 - Dockable Right Panel)
# ==============================================================================

if QtWidgets:
    class MaxChatbotPanel(QtWidgets.QWidget):
        """Inner UI widget for AI Copilot chat, logs, and prompt execution."""
        def __init__(self, parent=None, port=8096):
            super().__init__(parent)
            self.port = port
            self.init_ui()

        def init_ui(self):
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(4)

            # 1. Message Log Area
            self.chat_display = QtWidgets.QTextEdit()
            self.chat_display.setReadOnly(True)
            self.chat_display.setStyleSheet("""
                QTextEdit {
                    background-color: #1e2227;
                    color: #abb2bf;
                    border: 1px solid #3e4451;
                    border-radius: 4px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 11px;
                    padding: 4px;
                }
            """)
            layout.addWidget(self.chat_display, stretch=1)

            # Native 3ds Max File Actions (Export & Import) Row - Nằm chung 1 hàng ngang
            row_native_layout = QtWidgets.QHBoxLayout()
            row_native_layout.setSpacing(4)
            row_native_layout.setContentsMargins(0, 0, 0, 0)

            btn_export = QtWidgets.QPushButton("📤 Export")
            btn_export.setToolTip("Lệnh Export gốc của 3ds Max (File -> Export)")
            btn_export.setFixedHeight(26)
            btn_export.setStyleSheet("""
                QPushButton {
                    background-color: #21252b;
                    color: #e5c07b;
                    font-weight: bold;
                    border: 1px solid #e5c07b;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #e5c07b;
                    color: #1e2227;
                }
            """)
            btn_export.clicked.connect(self.on_quick_native_export)

            btn_import = QtWidgets.QPushButton("📥 Import")
            btn_import.setToolTip("Lệnh Import gốc của 3ds Max (File -> Import)")
            btn_import.setFixedHeight(26)
            btn_import.setStyleSheet("""
                QPushButton {
                    background-color: #21252b;
                    color: #d19a66;
                    font-weight: bold;
                    border: 1px solid #d19a66;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #d19a66;
                    color: #1e2227;
                }
            """)
            btn_import.clicked.connect(self.on_quick_native_import)

            row_native_layout.addWidget(btn_export)
            row_native_layout.addWidget(btn_import)
            layout.addLayout(row_native_layout)

            # Quick Action: Prominent Export FBX Button
            btn_fbx = QtWidgets.QPushButton("📦 Xuất File FBX  ")
            btn_fbx.setToolTip("Xuất selection vào D:\\Dropbox\\3DLib\\mesh\\FBX\\{maxfilename}.fbx (Tự động batch nếu chọn Rectangle; Giữ Shift để đổi nơi lưu)")
            btn_fbx.setFixedHeight(26)
            btn_fbx.setStyleSheet("""
                QPushButton {
                    background-color: #21252b;
                    color: #98c379;
                    font-weight: bold;
                    border: 1px solid #98c379;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #98c379;
                    color: #1e2227;
                }
            """)
            btn_fbx.clicked.connect(self.on_quick_export_fbx)
            layout.addWidget(btn_fbx)

            btn_fbx_rect = QtWidgets.QPushButton("📐 Xuất FBX theo Rectangle  ")
            btn_fbx_rect.setToolTip("Lọc vật thể lọt trong bbox XY của từng Rectangle, đưa về gốc (0,0) -> D:\\Dropbox\\3DLib\\mesh\\FBX\\{maxfilename}_{rect}.fbx")
            btn_fbx_rect.setFixedHeight(26)
            btn_fbx_rect.setStyleSheet("""
                QPushButton {
                    background-color: #21252b;
                    color: #61afef;
                    font-weight: bold;
                    border: 1px solid #61afef;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #61afef;
                    color: #1e2227;
                }
            """)
            btn_fbx_rect.clicked.connect(self.on_quick_export_rect_fbx)
            layout.addWidget(btn_fbx_rect)

            # Secondary Quick Actions Row
            row2_layout = QtWidgets.QHBoxLayout()
            row2_layout.setSpacing(4)
            row2_layout.setContentsMargins(0, 0, 0, 0)

            btn_inspect = QtWidgets.QPushButton("🔍 Kiểm Tra  ")
            btn_inspect.setToolTip("Xem thống kê scene và đối tượng đang chọn")
            btn_inspect.setFixedHeight(24)
            btn_inspect.setStyleSheet("""
                QPushButton {
                    background-color: #21252b;
                    color: #61afef;
                    border: 1px solid #3e4451;
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #3e4451;
                    color: #ffffff;
                }
            """)
            btn_inspect.clicked.connect(self.on_quick_inspect)
            row2_layout.addWidget(btn_inspect)

            btn_toolbar = QtWidgets.QPushButton("🛠️ Toolbar  ")
            btn_toolbar.setToolTip("Ghim thanh công cụ AI Tools lên trên cùng")
            btn_toolbar.setFixedHeight(24)
            btn_toolbar.setStyleSheet("""
                QPushButton {
                    background-color: #21252b;
                    color: #e5c07b;
                    border: 1px solid #3e4451;
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #3e4451;
                    color: #ffffff;
                }
            """)
            btn_toolbar.clicked.connect(self.on_quick_toolbar)
            row2_layout.addWidget(btn_toolbar)

            layout.addLayout(row2_layout)

            # 2. Compact Input Prompt Box
            input_layout = QtWidgets.QHBoxLayout()
            input_layout.setSpacing(4)

            self.prompt_input = QtWidgets.QLineEdit()
            self.prompt_input.setPlaceholderText("Nhập lệnh MAXScript hoặc prompt...")
            self.prompt_input.setFixedHeight(28)
            self.prompt_input.setStyleSheet("""
                QLineEdit {
                    background-color: #282c34;
                    color: #ffffff;
                    border: 1px solid #3e4451;
                    border-radius: 4px;
                    padding: 0 6px;
                    font-size: 11px;
                }
                QLineEdit:focus {
                    border: 1px solid #61afef;
                }
            """)
            self.prompt_input.returnPressed.connect(self.on_send_prompt)
            input_layout.addWidget(self.prompt_input, stretch=1)

            self.send_btn = QtWidgets.QPushButton("Gửi")
            self.send_btn.setFixedHeight(28)
            self.send_btn.setFixedWidth(45)
            self.send_btn.setStyleSheet("""
                QPushButton {
                    background-color: #61afef;
                    color: #1e2227;
                    font-weight: bold;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #528bff;
                }
            """)
            self.send_btn.clicked.connect(self.on_send_prompt)
            input_layout.addWidget(self.send_btn)

            layout.addLayout(input_layout)

            # Initial Welcome Message
            self.append_message("🤖 AI", f"Bridge online (Port {self.port}) — Đã gắn vào lề phải (Right Panel)")

        def append_message(self, sender, text, color="#61afef"):
            timestamp = time.strftime("%H:%M:%S")
            formatted = f"""
            <div style="margin-bottom: 4px; line-height: 1.3;">
                <span style="color: {color}; font-weight: bold;">[{timestamp}] {sender}:</span>
                <span style="color: #abb2bf; white-space: pre-wrap;">{text}</span>
            </div>
            """
            self.chat_display.append(formatted)
            sb = self.chat_display.verticalScrollBar()
            sb.setValue(sb.maximum())

        def on_send_prompt(self):
            text = self.prompt_input.text().strip()
            if not text:
                return
            self.prompt_input.clear()
            self.append_message("👤 Bạn", text, color="#e5c07b")
            
            res = handle_chat_prompt(text)
            self.append_message("🤖 AI", res.get("reply", str(res)))

        def on_quick_native_export(self):
            self.append_message("👤 Bạn", "📤 [Lệnh 3ds Max] Mở hộp thoại File Export", color="#e5c07b")
            res = native_max_export()
            if res.get("error"):
                self.append_message("🤖 AI", f"❌ {res.get('error')}", color="#e06c75")

        def on_quick_native_import(self):
            self.append_message("👤 Bạn", "📥 [Lệnh 3ds Max] Mở hộp thoại File Import", color="#d19a66")
            res = native_max_import()
            if res.get("error"):
                self.append_message("🤖 AI", f"❌ {res.get('error')}", color="#e06c75")

        def on_quick_export_fbx(self):
            is_shift = False
            if QtWidgets and hasattr(QtWidgets, "QApplication"):
                app = QtWidgets.QApplication.instance()
                if app:
                    is_shift = bool(app.keyboardModifiers() & QtCore.Qt.ShiftModifier)
            self.append_message("👤 Bạn", "📦 [Nút Nhanh] Xuất FBX cho Selection", color="#98c379")
            res = export_selection_to_fbx(prompt_dialog=is_shift)
            if res.get("success"):
                if res.get("exported_count"):
                    self.append_message("🤖 AI", f"✅ Đã xuất FBX thành công cho {res.get('exported_count')}/{res.get('total_rectangles')} Rectangle vào `{res.get('output_dir')}`!")
                else:
                    self.append_message("🤖 AI", f"✅ Đã xuất thành công FBX: {res.get('filename')} ({res.get('size_kb')} KB, {res.get('selected_count')} đối tượng)!\n• Đường dẫn: {res.get('path')}")
            elif res.get("cancelled"):
                self.append_message("🤖 AI", "ℹ️ Đã hủy xuất file.")
            else:
                self.append_message("🤖 AI", f"❌ {res.get('error', 'Lỗi không xác định')}", color="#e06c75")

        def on_quick_export_rect_fbx(self):
            self.append_message("👤 Bạn", "📐 [Nút Nhanh] Xuất FBX theo từng Rectangle lọt lòng về gốc (0,0)", color="#61afef")
            res = export_rectangles_batch()
            if res.get("success"):
                self.append_message("🤖 AI", f"✅ Đã xuất FBX thành công cho {res.get('exported_count')}/{res.get('total_rectangles')} Rectangle vào `{res.get('output_dir')}`!")
            else:
                self.append_message("🤖 AI", f"❌ {res.get('error', 'Không tìm thấy Rectangle hoặc lỗi xuất file')}", color="#e06c75")

        def on_quick_inspect(self):
            self.append_message("👤 Bạn", "🔍 [Nút Nhanh] Kiểm tra scene", color="#61afef")
            res = handle_chat_prompt("kiểm tra")
            self.append_message("🤖 AI", res.get("reply", str(res)))

        def on_quick_toolbar(self):
            self.append_message("👤 Bạn", "🛠️ [Nút Nhanh] Ghim AI Tools lên Toolbar", color="#e5c07b")
            tb = create_ai_toolbar()
            if tb:
                self.append_message("🤖 AI", "✅ Đã ghim thanh công cụ 'AI Tools' có nút '📦 Export FBX' lên Toolbar phía trên cùng của 3ds Max!")
            else:
                self.append_message("🤖 AI", "❌ Không thể tìm thấy cửa sổ chính của 3ds Max.", color="#e06c75")

        def log_external_command(self, cmd_type, code, result):
            res_str = result.get("result") if isinstance(result, dict) else str(result)
            err_str = result.get("error") if isinstance(result, dict) else None
            if err_str:
                self.append_message(f"⚡ [{cmd_type}]", f"{code}\n❌ {err_str}", color="#e06c75")
            else:
                self.append_message(f"⚡ [{cmd_type}]", f"{code}\n✅ {res_str}", color="#61afef")


    class MaxChatbotDock(QtWidgets.QDockWidget):
        """Dockable 3ds Max AI Copilot panel attached to the Right Dock Area alongside the Command Panel."""
        def __init__(self, parent=None, port=8096):
            super().__init__("AI Copilot", parent)
            self.setObjectName("MaxAICopilotDock")
            self.port = port
            self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
            self.panel = MaxChatbotPanel(self, port=port)
            self.setWidget(self.panel)

            # Styling for the dock widget matching 3ds Max dark theme
            self.setStyleSheet("""
                QDockWidget {
                    color: #abb2bf;
                    font-weight: bold;
                    font-size: 11px;
                }
                QDockWidget::title {
                    background-color: #282c34;
                    padding: 4px;
                    border: 1px solid #3e4451;
                    border-bottom: none;
                }
            """)
            self.setMinimumWidth(260)
            self.resize(300, 280)

        def append_message(self, sender, text, color="#61afef"):
            if hasattr(self, 'panel') and self.panel:
                self.panel.append_message(sender, text, color)

        def log_external_command(self, cmd_type, code, result):
            if hasattr(self, 'panel') and self.panel:
                self.panel.log_external_command(cmd_type, code, result)


    # Backwards compatibility alias
    MaxChatbotWindow = MaxChatbotDock

# ==============================================================================
# Server Startup & Lifecycle Management
# ==============================================================================

def toggle_ui():
    """Toggles visibility of the AI Copilot Dock on the right margin of 3ds Max."""
    global _CHATBOT_WINDOW
    if _CHATBOT_WINDOW and isinstance(_CHATBOT_WINDOW, QtWidgets.QDockWidget):
        if _CHATBOT_WINDOW.isVisible():
            _CHATBOT_WINDOW.hide()
        else:
            _CHATBOT_WINDOW.show()
            _CHATBOT_WINDOW.raise_()
    else:
        start_bridge_server(show_ui=True)

def start_bridge_server(port=_DEFAULT_PORT, show_ui=True):
    global _BRIDGE_SERVER, _CHATBOT_WINDOW, _DISPATCHER_TIMER

    # 1. Setup QTimer on Main Thread to dispatch queued tasks
    if QtCore and not _DISPATCHER_TIMER:
        _DISPATCHER_TIMER = QtCore.QTimer()
        _DISPATCHER_TIMER.timeout.connect(_process_main_thread_tasks)
        _DISPATCHER_TIMER.start(20)  # 20ms polling interval

    # 2. Start HTTP Server if not already running
    bound_port = None
    if not _BRIDGE_SERVER:
        candidate_ports = [port, 8098, 8099, 8097, 8094, 8096]
        server = None

        for p in candidate_ports:
            try:
                server = ThreadedHTTPServer(("127.0.0.1", p), MaxBridgeRequestHandler)
                bound_port = p
                break
            except Exception:
                continue

        if not server:
            print("[MaxAI Bridge] ERROR: Could not bind to any candidate ports.")
            return False

        _BRIDGE_SERVER = server
        t = threading.Thread(target=_BRIDGE_SERVER.serve_forever, daemon=True)
        t.start()

        # Save Port File
        try:
            with open(PORT_FILE_REPO, "w", encoding="utf-8") as f:
                f.write(str(bound_port))
            with open(PORT_FILE_TEMP, "w", encoding="utf-8") as f:
                f.write(str(bound_port))
        except Exception:
            pass

        print(f"[MaxAI Bridge] SUCCESS: Bridge server listening on http://127.0.0.1:{bound_port}")
    else:
        try:
            with open(PORT_FILE_REPO, "r", encoding="utf-8") as f:
                bound_port = int(f.read().strip())
        except Exception:
            bound_port = port

    # 3. Create or Show Chatbot Dock Widget docked to RightDockWidgetArea
    if show_ui and QtWidgets:
        try:
            main_wnd = None
            if hasattr(QtWidgets, "QApplication"):
                app = QtWidgets.QApplication.instance()
                for w in app.topLevelWidgets():
                    if "autodesk 3ds max" in w.windowTitle().lower():
                        main_wnd = w
                        break

            # Remove previous dialog or dock instances
            if _CHATBOT_WINDOW:
                try:
                    if main_wnd and isinstance(_CHATBOT_WINDOW, QtWidgets.QDockWidget):
                        main_wnd.removeDockWidget(_CHATBOT_WINDOW)
                    _CHATBOT_WINDOW.close()
                    _CHATBOT_WINDOW.deleteLater()
                except Exception:
                    pass
                _CHATBOT_WINDOW = None

            if main_wnd:
                for old in main_wnd.findChildren(QtWidgets.QDockWidget, "MaxAICopilotDock"):
                    try:
                        main_wnd.removeDockWidget(old)
                        old.close()
                        old.deleteLater()
                    except Exception:
                        pass

            current_port = bound_port or _DEFAULT_PORT
            _CHATBOT_WINDOW = MaxChatbotDock(parent=main_wnd, port=current_port)
            if main_wnd:
                main_wnd.addDockWidget(QtCore.Qt.RightDockWidgetArea, _CHATBOT_WINDOW)
                # Automatically create and dock AI Tools Toolbar on top
                create_ai_toolbar(main_wnd)
            _CHATBOT_WINDOW.show()
            _CHATBOT_WINDOW.raise_()
        except Exception as ex:
            print(f"[MaxAI Bridge] Warning: Could not show Chatbot UI: {ex}")

    return True

if __name__ == "__main__" or pymxs is not None:
    start_bridge_server()
