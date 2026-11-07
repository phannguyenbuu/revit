"""Hot-load fit commands, Qwen normalizer and input handlers without resetting the dock."""
import ast
from pathlib import Path
import textwrap

from max_cli import request_json


def main():
    folder = Path(__file__).resolve().parent
    source = (folder / "max_bridge.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    names = {"create_fitted_primitive", "create_fitted_cylinder", "create_fitted_half_cylinder",
             "create_bbox_box", "_caps_mode", "_cap_faces_maxscript", "remove_selected_caps",
             "get_selection_handles", "perform_action", "handle_chat_prompt"}
    chunks = ["import sys, importlib", "sys.path.insert(0, " + repr(str(folder)) + ")",
              "import prompt_normalizer", "importlib.reload(prompt_normalizer)",
              "_PROMPT_WORKERS = globals().get('_PROMPT_WORKERS', set())"]
    chunks += [ast.get_source_segment(source, n) for n in tree.body
               if isinstance(n, ast.FunctionDef) and n.name in names]
    classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    chunks.append(textwrap.dedent(ast.get_source_segment(source, classes["PromptNormalizationWorker"])))
    chunks.append(textwrap.dedent(ast.get_source_segment(source, classes["LocalQwenStatusWorker"])))
    chunks.append(textwrap.dedent(ast.get_source_segment(source, classes["LocalQwenStartWorker"])))
    for class_name, method, new_name in (
            ("MaxBridgeRequestHandler", "do_POST", "_updated_do_POST"),
            ("MaxChatbotPanel", "_ensure_prompt_status", "_updated_ensure_prompt_status"),
            ("MaxChatbotPanel", "_ensure_qwen_status", "_updated_ensure_qwen_status"),
            ("MaxChatbotPanel", "_ensure_qwen_button", "_updated_ensure_qwen_button"),
            ("MaxChatbotPanel", "on_start_qwen", "_updated_on_start_qwen"),
            ("MaxChatbotPanel", "on_qwen_started", "_updated_on_qwen_started"),
            ("MaxChatbotPanel", "_refresh_qwen_status", "_updated_refresh_qwen_status"),
            ("MaxChatbotPanel", "_receive_qwen_status", "_updated_receive_qwen_status"),
            ("MaxChatbotPanel", "_tick_prompt_status", "_updated_tick_prompt_status"),
            ("MaxChatbotPanel", "_set_prompt_status", "_updated_set_prompt_status"),
            ("MaxChatbotPanel", "on_send_prompt", "_updated_send_prompt"),
            ("MaxChatbotPanel", "on_prompt_normalized", "_updated_normalized_prompt")):
        node = next(n for n in classes[class_name].body if isinstance(n, ast.FunctionDef) and n.name == method)
        chunks.append(textwrap.dedent(ast.get_source_segment(source, node)).replace("def " + method + "(", "def " + new_name + "(", 1))
    chunks.append('''
_BRIDGE_SERVER.RequestHandlerClass.do_POST = _updated_do_POST
if _CHATBOT_WINDOW and hasattr(_CHATBOT_WINDOW, 'panel'):
    _updated_panel = _CHATBOT_WINDOW.panel
    if getattr(_updated_panel, '_prompt_pending', False):
        raise RuntimeError('Wait for the pending prompt before reloading input handlers')
    _updated_panel.prompt_input.returnPressed.disconnect(_updated_panel.on_send_prompt)
    _updated_panel.send_btn.clicked.disconnect(_updated_panel.on_send_prompt)
    type(_updated_panel).on_send_prompt = _updated_send_prompt
    type(_updated_panel).on_prompt_normalized = _updated_normalized_prompt
    type(_updated_panel)._ensure_prompt_status = _updated_ensure_prompt_status
    type(_updated_panel)._tick_prompt_status = _updated_tick_prompt_status
    type(_updated_panel)._set_prompt_status = _updated_set_prompt_status
    type(_updated_panel)._ensure_qwen_status = _updated_ensure_qwen_status
    type(_updated_panel)._refresh_qwen_status = _updated_refresh_qwen_status
    type(_updated_panel)._receive_qwen_status = _updated_receive_qwen_status
    _updated_panel._ensure_qwen_status()
    type(_updated_panel)._ensure_qwen_button = _updated_ensure_qwen_button
    type(_updated_panel).on_start_qwen = _updated_on_start_qwen
    type(_updated_panel).on_qwen_started = _updated_on_qwen_started
    _updated_panel._ensure_qwen_button()
    _updated_panel._ensure_prompt_status()
    _updated_panel._prompt_status_timer.timeout.disconnect()
    _updated_panel._prompt_status_timer.timeout.connect(_updated_panel._tick_prompt_status)
    _updated_panel.prompt_input.returnPressed.connect(_updated_panel.on_send_prompt)
    _updated_panel.send_btn.clicked.connect(_updated_panel.on_send_prompt)
''')
    result = request_json("/api/execute", {"language": "python", "code": "exec(" + repr("\n\n".join(chunks)) + ", globals())"})
    if not result.get("success"):
        raise RuntimeError(result)
    print("Fit commands, Qwen normalization and dock input updated.")


if __name__ == "__main__":
    main()
