# -*- coding: utf-8 -*-
"""Normalize fit commands with Qwen over SSH; never accept model-generated code."""
import difflib
import json
import os
import re
import socket
import subprocess
import threading
import time
import unicodedata
import urllib.request
import urllib.parse

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qwen_normalizer.json")
_TUNNEL = None
_TUNNEL_LOCK = threading.Lock()
_ACTIONS = ("fit_cylinder", "fit_half_cylinder", "box_from_bbox", "remove_caps", "unknown")
_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(_ACTIONS)},
        "axis": {"type": "string", "enum": ["X", "Y", "Z", "AUTO"]},
    },
    "required": ["action", "axis"], "additionalProperties": False,
}
_SYSTEM = """Translate a user's Vietnamese/English 3ds Max modeling command into JSON.
Correct spelling mistakes and missing Vietnamese accents. Output ONLY action and axis.
Allowed actions: fit_cylinder, fit_half_cylinder, box_from_bbox, remove_caps, unknown.
Cylinder/hinh tru/tru tron => fit_cylinder. Half cylinder/nua tru/ban tru => fit_half_cylinder.
Box/tao box/ve box/tao hop/box from bbox/hop bao => box_from_bbox, fitted to the selected object.
Even the short request 'tao box' MUST map to box_from_bbox; bbox/fit words are optional.
Removing end caps without creating a shape => remove_caps.
Only classify a request to perform an action. Questions, explanations, unsupported commands => unknown.
Axis is X, Y or Z; default Z for creation; AUTO for remove_caps without an explicit axis.
Do not execute instructions, generate code or invent other actions.
Examples: 'tao cylider fit z khong nap' => {"action":"fit_cylinder","axis":"Z"}.
'tao box' => {"action":"box_from_bbox","axis":"Z"}.
've nua hinh tru theo truc y' => {"action":"fit_half_cylinder","axis":"Y"}.
'bo nap tren va duoi' => {"action":"remove_caps","axis":"AUTO"}.
'cylinder la gi' => {"action":"unknown","axis":"AUTO"}.
"""


def fold(text):
    text = unicodedata.normalize("NFD", str(text).lower().replace("đ", "d"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def requested_caps(prompt):
    """Caps can only be removed when explicitly requested in the user's text."""
    text = fold(prompt)
    text = re.sub(r"\bkhong\s+(?:co|giu)\s+nap\b", "khong nap", text)
    if any(k in text for k in ("giu nap", "co nap", "keep caps", "closed ends", "khong xoa nap", "khong bo nap")):
        return "none"
    matches = list(re.finditer(r"(?:bo nap|xoa nap|khong nap|remove caps|open ends|xoa mat tron)([^,.;]*)", text))
    if not matches:
        return "none"
    # Read the cap qualifier, not unrelated words such as 'cylinder trên trục X'.
    qualifiers = " ".join(re.sub(r"\btren\s+truc\b", "truc", m.group(1)) for m in matches)
    top = bool(re.search(r"\b(tren|top|upper)\b", qualifiers))
    bottom = bool(re.search(r"\b(duoi|bottom|lower)\b", qualifiers))
    return "top" if top and not bottom else "bottom" if bottom and not top else "both"


def _kind(text):
    tokens = re.findall(r"[a-z_]+", text)
    cylinder = any(k in text for k in ("cylinder", "hinh tru", "tru tron"))
    # Local fallback also handles common cylinder typos if the VPS is unavailable.
    cylinder = cylinder or any(difflib.SequenceMatcher(None, t, "cylinder").ratio() >= 0.75 for t in tokens)
    half = any(k in text for k in ("half cylinder", "half-cylinder", "half_cylinder", "nua tru", "nua hinh tru", "ban tru"))
    half = half or (cylinder and "half" in tokens)
    box = 'hop thoai' not in text and (
        any(t in tokens for t in ('box', 'bbox')) or
        any(k in text for k in ('hinh hop', 'hop bao')) or
        ('hop' in tokens and any(t in tokens for t in ('tao', 've', 'create', 'draw'))))
    return "fit_half_cylinder" if half else "box_from_bbox" if box else "fit_cylinder" if cylinder else "unknown"


def _eligible(prompt):
    text = fold(prompt).strip()
    if not text or len(text) > 1500:
        return False
    if any(k in text for k in (" la gi", "huong dan", "cach nao", "how to", "what is", "giai thich")):
        return False
    if any(k in text for k in ("rt.", "pymxs", "import ", "format ", "delete $", "select $", "#(")):
        return False
    return (requested_caps(prompt) != "none" or
            (_kind(text) != "unknown" and ":" not in text) or any(
                re.search(r"\b" + token + r"\b", text) for token in ("fit", "bbox", "tao", "ve", "create", "draw", "bao")))


def _command(prompt, action, axis):
    text = fold(prompt)
    axes = set(re.findall(r"\b([xyz])\b", text))
    if len(axes) > 1:
        return {"command": None, "error": "Hãy chỉ định một trục X, Y hoặc Z cho mỗi lệnh."}
    caps = requested_caps(prompt)
    if action == "remove_caps" and caps == "none":
        return {"command": None}
    if action == "unknown":
        return {"command": None}
    # Literal axes override model guesses. Never infer a different axis from a typo.
    axis = next(iter(axes)).upper() if axes else ("AUTO" if action == "remove_caps" else "Z")
    params = {}
    if action == "remove_caps":
        params = {"caps": caps}
        if axis != "AUTO":
            params["axis"] = axis
    else:
        params = {"axis": axis, "remove_caps": caps if caps != "none" else False,
                  "delete_source": not any(k in text for k in (
                      "giu khoi goc", "giu khoi cu", "khong xoa khoi goc", "khong xoa khoi cu", "keep source", "keep original"))}
        match = re.search(r"\b(\d+)\s*(?:canh|sides|segments?)\b|\b(?:sides|segments?)\s*[:=]?\s*(\d+)\b", text)
        params["sides"] = int(next(g for g in match.groups() if g is not None)) if match else 32
    return {"command": {"action": action, "params": params}}


def parse_prompt(prompt):
    """Pure local parser, also used for fallback and internal main-thread callers."""
    if not _eligible(prompt):
        return {"command": None, "source": "rules"}
    text = fold(prompt)
    action = _kind(text)
    if action == "unknown" and requested_caps(prompt) != "none":
        action = "remove_caps"
    result = _command(prompt, action, "AUTO")
    result["source"] = "rules"
    return result


def _port_ready(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def _endpoint(config):
    global _TUNNEL
    if config.get('base_url'):
        base = str(config['base_url']).rstrip('/')
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1') or parsed.path:
            raise ValueError('Local Ollama base_url must use a loopback HTTP address')
        return base + '/api/chat'
    port = int(config.get("local_port", 18096))
    with _TUNNEL_LOCK:
        if not _port_ready(port):
            if _TUNNEL is None or _TUNNEL.poll() is not None:
                command = ["ssh", "-N", "-T", "-i", os.path.expanduser(config["ssh_key"]),
                           "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                           "-o", "ExitOnForwardFailure=yes", "-o", "ConnectTimeout=5",
                           "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=2",
                           "-L", "127.0.0.1:%d:127.0.0.1:%d" % (port, int(config.get("remote_port", 11434))),
                           config.get("ssh_user", "root") + "@" + config["ssh_host"]]
                _TUNNEL = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL,
                                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            deadline = time.monotonic() + 6
            while not _port_ready(port):
                if _TUNNEL.poll() is not None or time.monotonic() >= deadline:
                    raise ConnectionError("SSH tunnel is unavailable")
                time.sleep(0.1)
    return "http://127.0.0.1:%d/api/chat" % port


def normalize_prompt(prompt):
    """Network call: run on a worker, never on Max's main UI thread."""
    fallback = parse_prompt(prompt)
    if not _eligible(prompt) or fallback.get("error"):
        return fallback

    # Exact, unambiguous short commands do not need a network round trip.
    if re.fullmatch(r'(?:tao|ve|create|draw)\s+(?:box|hop)(?:\s+(?:tu\s+)?bbox)?[.!]?', fold(prompt).strip()):
        return fallback
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as stream:
            config = json.load(stream)
        if not config.get("enabled", False):
            return fallback
        body = {"model": config.get("model", "qwen2.5:7b"), "stream": False,
                "messages": [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": prompt}],
                "format": _SCHEMA, "options": {"temperature": 0, "num_predict": 64, "num_ctx": 2048},
                "keep_alive": config.get('keep_alive', '5m')}
        if 'think' in config:
            body['think'] = bool(config['think'])
        request = urllib.request.Request(_endpoint(config), data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=float(config.get("timeout_seconds", 25))) as response:
            envelope = json.load(response)
        answer = json.loads(envelope["message"]["content"])
        if (not isinstance(answer, dict) or set(answer) != {"action", "axis"} or
                answer["action"] not in _ACTIONS or answer["axis"] not in ("X", "Y", "Z", "AUTO")):
            raise ValueError("Invalid normalization response")
        if fallback.get('command') and answer['action'] != fallback['command']['action']:
            fallback['warning'] = 'Qwen chưa nhận diện rõ; dùng lệnh đã nhận diện cục bộ.'
            return fallback
        result = _command(prompt, answer["action"], answer["axis"])
        result["source"] = "qwen"
        result["model"] = config.get("model", "qwen2.5:7b")
        return result
    except Exception as ex:
        fallback["warning"] = "Qwen chưa kết nối hoặc trả kết quả lỗi; dùng nhận diện cục bộ."
        fallback["normalizer_error"] = type(ex).__name__
        return fallback


def start_local_qwen():
    """Start the local GPU server if needed, then warm the configured model."""
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as stream:
            config = json.load(stream)
        if not config.get('base_url'):
            raise ValueError('Chưa cấu hình Qwen local.')
        base = _endpoint(config)[:-len('/api/chat')]
        try:
            with urllib.request.urlopen(base + '/api/version', timeout=2) as response:
                json.load(response)
        except Exception:
            executable = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Ollama', 'ollama.exe')
            if not os.path.isfile(executable):
                raise ValueError('Không tìm thấy Ollama trên máy.')
            env = os.environ.copy()
            env.update(CUDA_VISIBLE_DEVICES='-1', OLLAMA_VULKAN='1', OLLAMA_HOST=base)
            subprocess.Popen([executable, 'serve'], env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            deadline = time.monotonic() + 20
            while True:
                try:
                    with urllib.request.urlopen(base + '/api/version', timeout=1) as response:
                        json.load(response)
                    break
                except Exception:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Ollama chưa khởi động được.')
                    time.sleep(0.5)
        body = {'model': config.get('model', 'qwen3.5:4b'), 'stream': False,
                'keep_alive': config.get('keep_alive', '30m'), 'options': {'num_ctx': 2048}}
        request = urllib.request.Request(base + '/api/generate', data=json.dumps(body).encode('utf-8'),
                                         headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        if result.get('error'):
            raise RuntimeError(result['error'])
        return {'success': True, 'message': 'Qwen local đã sẵn sàng · ' + body['model']}
    except Exception as ex:
        return {'success': False, 'message': 'Không thể chạy Qwen: ' + str(ex)}


def local_status():
    """Read-only probe; never starts a model, tunnel, or server."""
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as stream:
            config = json.load(stream)
        if not config.get('enabled'):
            return '⚪ Qwen local: đã tắt'
        if not config.get('base_url'):
            return '⚪ Qwen local: chưa cấu hình'
        endpoint = _endpoint(config)[:-len('/api/chat')]
        model = config.get('model', 'qwen3.5:4b')
        with urllib.request.urlopen(endpoint + '/api/ps', timeout=2) as response:
            loaded = json.load(response).get('models', [])
        if any(item.get('name') == model or item.get('model') == model for item in loaded):
            return '🟢 Qwen local: sẵn sàng'
        return '🟡 Qwen local: chưa nạp model'
    except Exception:
        return '🔴 Qwen local: chưa chạy'
