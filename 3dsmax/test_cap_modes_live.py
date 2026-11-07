"""Check individual cap removal and undo on temporary scene nodes."""
from test_fit_primitives_live import execute


def main():
    code = r'''
def _check_single_cap(shape, axis, mode):
    original = list(rt.selection)
    source_name = None
    result_name = None
    try:
        with pymxs.undo(False):
            src = rt.Box(name=rt.uniqueName('__SingleCapTest'), width=20, length=30,
                         height=40, pos=rt.Point3(200, 300, 400))
            source_name = str(src.name)
            rt.select(src)
        prompt = 'tao box tu bbox' if shape == 'box' else 'tao ' + shape.replace('_', ' ') + ' fit ' + axis
        prompt += ' khong nap ' + ('tren' if mode == 'top' else 'duoi')
        result = handle_chat_prompt(prompt)['data']
        assert result.get('success'), result
        result_name = result['name']
        try:
            def cap_count(which):
                return int(rt.execute('(local c=selection[1]; ' + _cap_faces_maxscript('c',3,True,which) + '; capFaces.numberSet)'))
            other = 'bottom' if mode == 'top' else 'top'
            assert cap_count(mode) == 0, 'Requested cap remains'
            assert cap_count(other) > 0, 'Opposite cap was also deleted'
            assert result['caps_removed'] == mode
            follow_up = 'khong nap ' + ('duoi' if other == 'bottom' else 'tren')
            removed = handle_chat_prompt(follow_up)['data']
            assert removed.get('success'), removed
            try:
                assert cap_count('both') == 0
                assert removed['removed_cap_faces'] > 0
            finally:
                rt.execute('max undo')
            assert cap_count(other) > 0, 'Undo failed to restore the remaining cap'
        finally:
            rt.execute('max undo')
        assert rt.getNodeByName(source_name) is not None
        assert rt.getNodeByName(result_name) is None
        return {'shape':shape, 'axis':axis, 'single_cap':mode, 'passed':True}
    finally:
        with pymxs.undo(False):
            for name in (source_name, result_name):
                node = rt.getNodeByName(name) if name else None
                if node is not None:
                    rt.delete(node)
            rt.select(original) if original else rt.clearSelection()
'''
    execute("exec(" + repr(code) + ", globals())")
    for case in (("cylinder", "X", "top"), ("half_cylinder", "Y", "bottom"), ("box", "Z", "top")):
        print(execute("_check_single_cap(" + ",".join(repr(v) for v in case) + ")")["result"], flush=True)


if __name__ == "__main__":
    main()
