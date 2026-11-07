"""Live integration check: python 3dsmax/test_fit_primitives_live.py.

Uses temporary scene nodes, undoes each replacement, and restores selection.
Run while Max is idle with the bridge active. Also hot-loads the fit functions.
"""
import ast
import json
from pathlib import Path

from max_cli import request_json


def execute(code):
    result = request_json("/api/execute", {"language": "python", "code": code})
    if not result.get("success"):
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


def main():
    source = Path(__file__).with_name("max_bridge.py").read_text(encoding="utf-8-sig")
    names = {"create_fitted_primitive", "create_fitted_cylinder", "create_fitted_half_cylinder",
             "create_bbox_box", "_caps_mode", "_cap_faces_maxscript", "remove_selected_caps", "get_selection_handles",
             "perform_action", "handle_chat_prompt"}
    definitions = ["import re", "import sys", "sys.path.insert(0, " + repr(str(Path(__file__).parent)) + ")",
                   "import prompt_normalizer"] + [ast.get_source_segment(source, node)
        for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name in names]
    execute("exec(" + repr("\n\n".join(definitions)) + ", globals())")
    test_code = r'''
def _check_fit_replacements(cases_override=None, check_options=True):
    original = list(rt.selection)
    temporary_names = []
    reports = []
    shapes = [('cylinder', a) for a in 'XYZ'] + [('half_cylinder', a) for a in 'XYZ'] + [('box', 'Z')]
    cases = [(shape, axis, opened) for shape, axis in shapes for opened in (False, True)]
    if cases_override is not None:
        cases = cases_override
    try:
        for shape, axis, opened in cases:
            with pymxs.undo(False):
                src = rt.Box(name=rt.uniqueName('__FitPrimitiveTest'), width=20, length=30,
                             height=40, pos=rt.Point3(1000, 2000, 3000))
                temporary_names.append(str(src.name))
                src.scale = rt.Point3(-1.2, 0.8, 1.1)
                rt.rotate(src, rt.EulerAngles(17, 23, 31))
                src.material = rt.StandardMaterial(name='__FitTestMaterial')
                rt.select(src)
            source_name = str(src.name)
            bbox = rt.nodeGetBoundingBox(src, rt.Matrix3(1))
            mesh = rt.snapshotAsMesh(src)
            points = []
            for i in range(1, int(mesh.numverts) + 1):
                points.append(rt.getVert(mesh, i))
            prompt = 'box từ bbox' if shape == 'box' else shape.replace('_', ' ') + ' fit trục ' + axis
            if opened:
                prompt += ' bỏ nắp trên và dưới'
            res = handle_chat_prompt(prompt)['data']
            assert res.get('success'), res
            temporary_names.append(res['name'])
            dst = rt.getNodeByName(res['name'])
            try:
                assert rt.getNodeByName(source_name) is None, 'Source was not deleted'
                assert str(dst.material.name) == '__FitTestMaterial'
                assert str(rt.selection[0].name) == res['name']
                assert str(rt.classOf(dst)) == 'Editable_Poly'
                assert res['sides'] == 32
                assert int(rt.polyop.getOpenEdges(dst).numberSet) > 0 if opened else int(rt.polyop.getOpenEdges(dst).numberSet) == 0
                assert res['removed_cap_faces'] > 0 if opened else res['removed_cap_faces'] == 0
                if shape == 'box':
                    actual = rt.nodeGetBoundingBox(dst, rt.Matrix3(1))
                    for j in range(2):
                        for k in range(3):
                            assert abs(actual[j][k] - bbox[j][k]) < 0.002, 'BBox mismatch'
                else:
                    idx = {'X': 0, 'Y': 1, 'Z': 2}[axis]
                    assert abs(dst.dir[idx] - 1) < 0.0001, 'Wrong axis'
                    inverse = rt.inverse(dst.objectTransform)
                    for p in points:
                        local = p * inverse
                        assert -0.002 <= local.z <= res['height'] + 0.002, 'Height does not fit'
                        radial = (local.x**2 + local.y**2)**0.5
                        assert radial <= res['radius'] * rt.cos(180.0/res['sides']) + 0.002, 'Radius does not fit'
                        if shape == 'half_cylinder':
                            assert local.y >= -0.002, 'Source lies outside flat side'
                    if shape == 'half_cylinder':
                        outmesh = rt.snapshotAsMesh(dst)
                        max_y = 0.0
                        for i in range(1, int(outmesh.numverts) + 1):
                            p = rt.getVert(outmesh, i) * inverse
                            assert p.y >= -0.002, 'Half cylinder curves the wrong way'
                            max_y = max(max_y, float(p.y))
                        assert max_y > res['radius'] * 0.99
                if not opened:
                    face_count = int(rt.polyop.getNumFaces(dst))
                    opened_result = handle_chat_prompt('bỏ nắp trên và dưới')['data']
                    assert opened_result.get('success'), opened_result
                    try:
                        assert opened_result['removed_cap_faces'] > 0
                        assert int(rt.polyop.getNumFaces(dst)) == face_count - opened_result['removed_cap_faces']
                        assert int(rt.polyop.getOpenEdges(dst).numberSet) > 0
                    finally:
                        rt.execute('max undo')
                    assert int(rt.polyop.getNumFaces(dst)) == face_count
                    assert int(rt.polyop.getOpenEdges(dst).numberSet) == 0
                reports.append({'shape': shape, 'axis': axis, 'open_ends': opened, 'passed': True})
            finally:
                rt.execute('max undo')
                assert rt.getNodeByName(source_name) is not None, 'Undo did not restore source'
                assert rt.getNodeByName(res['name']) is None, 'Undo did not remove replacement'
                with pymxs.undo(False):
                    rt.delete(rt.getNodeByName(source_name))
        if not check_options:
            return reports
        with pymxs.undo(False):
            src = rt.Box(name=rt.uniqueName('__FitKeepSourceTest'), width=20, length=30, height=40)
            temporary_names.append(str(src.name))
            rt.select(src)
        source_name = str(src.name)
        keep = perform_action('fit_half_cylinder', {'axis': 'Y', 'sides': 127, 'delete_source': False})
        assert keep.get('success'), keep
        temporary_names.append(keep['name'])
        try:
            assert keep['sides'] == 128
            assert rt.getNodeByName(source_name) is not None
        finally:
            rt.execute('max undo')
        with pymxs.undo(False):
            rt.clearSelection()
        assert not create_bbox_box()['success']
        assert not create_fitted_half_cylinder('Q')['success']
        assert not create_fitted_cylinder('Z', 2)['success']
        assert not create_bbox_box('false')['success']
        assert not create_bbox_box(remove_caps='true')['success']
        assert not handle_chat_prompt('half cylinder X Y')['data']
        reports.append({'validation_and_keep_source': True})
        return reports
    finally:
        with pymxs.undo(False):
            for name in temporary_names:
                node = rt.getNodeByName(name)
                if node is not None:
                    rt.delete(node)
            valid = []
            for node in original:
                if rt.isValidNode(node):
                    valid.append(node)
            if valid:
                rt.select(valid)
            else:
                rt.clearSelection()
'''
    execute("exec(" + repr(test_code) + ", globals())")
    # Keep each HTTP/main-thread task short enough for the bridge's 45s timeout.
    cases = [(shape, axis, opened)
             for shape, axes in (("cylinder", "XYZ"), ("half_cylinder", "XYZ"), ("box", "Z"))
             for axis in axes for opened in (False, True)]
    for case in cases:
        print(execute("_check_fit_replacements(" + repr([case]) + ", False)")["result"], flush=True)
    print(execute("_check_fit_replacements([], True)")["result"], flush=True)


if __name__ == "__main__":
    main()
