#!/usr/bin/env python3
"""
RIZEN OFFLINE AI - local chat server.

Serves the web interface on this computer and runs the Qwen3-8B model through
llama-cpp-python. While the app runs, nothing is sent to the internet.

Developed by Anunay Srivastava. Released under the MIT License (see LICENSE).
"""

import json
import logging
import os
import re
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

APP_NAME = "RIZEN OFFLINE AI"
VERSION = "1.1.0"
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CHAT_DIR = BASE_DIR / "data" / "chats"
BRAIN_FILE = BASE_DIR / "brain.md"
CONFIG_FILE = BASE_DIR / "config.json"

SYSTEM_START = "<!-- SYSTEM_PROMPT:START -->"
SYSTEM_END = "<!-- SYSTEM_PROMPT:END -->"
FALLBACK_PROMPT = (
    "You are RIZEN OFFLINE AI, a helpful assistant that runs entirely on the user's "
    "computer. Be accurate and clear. If you are not sure, say so."
)

DEFAULT_CONFIG = {
    "model_name": "Qwen3-8B",
    "model_path": "models/Qwen3-8B-Q4_K_M.gguf",
    "host": "127.0.0.1",
    "port": 7860,
    "context_size": 4096,
    "thinking_tokens": 1536,
    "threads": 0,
    "gpu_layers": 0,
    "open_browser": True,
}

THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"
EMPTY_THINK = "<think>\n\n</think>\n\n"  # what Qwen3 writes when thinking is off
FORCED_CLOSE = "\n</think>\n\n"           # used when the user skips the thinking
STOP_TOKENS = ["<|im_end|>", "<|endoftext|>"]
THINK_RE = re.compile(r"<think>.*?(</think>|$)", re.DOTALL)
CHAT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def load_config():
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            config.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[warning] config.json could not be read, using defaults: {exc}")
    return config


CONFIG = load_config()


def load_system_prompt():
    """Read the system prompt from brain.md. Editing brain.md changes the assistant."""
    try:
        text = BRAIN_FILE.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_PROMPT
    match = re.search(re.escape(SYSTEM_START) + r"(.*?)" + re.escape(SYSTEM_END), text, re.DOTALL)
    prompt = match.group(1).strip() if match else ""
    return prompt or FALLBACK_PROMPT


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def clamp(value, low, high):
    return max(low, min(high, value))


def safe_text(text):
    """Stop typed text from pretending to be a Qwen control token such as <|im_start|>."""
    return str(text).replace("<|", "<\u200b|")


def trim_history(history, budget):
    """Keep the newest turns that fit the budget. Old reasoning is never sent back."""
    kept = []
    used = 0
    for message in reversed(history):
        role = message.get("role")
        content = str(message.get("content", ""))
        if role == "assistant":
            content = THINK_RE.sub("", content)
        content = content.strip()
        if role not in ("user", "assistant") or not content:
            continue
        if kept and used + len(content) > budget:
            break
        used += len(content)
        kept.append({"role": role, "content": content})
    kept.reverse()
    if not kept or kept[-1]["role"] != "user":
        raise ValueError("The last message must come from you.")
    return kept


def build_prompt(system, history, thinking, ctx, max_tokens):
    """Write the Qwen3 ChatML prompt ourselves, so the thinking block can be closed on demand."""
    budget = max(2000, (ctx - max_tokens) * 3) - len(system)  # rough character budget
    kept = trim_history(history, budget)
    parts = [f"<|im_start|>system\n{safe_text(system)}<|im_end|>\n"]
    for message in kept:
        parts.append(f"<|im_start|>{message['role']}\n{safe_text(message['content'])}<|im_end|>\n")
    parts.append("<|im_start|>assistant\n")
    if not thinking:
        parts.append(EMPTY_THINK)  # answer directly, no reasoning
    return "".join(parts)


class ModelEngine:
    """Loads the GGUF model once and streams replies. One reply runs at a time."""

    def __init__(self, config):
        self.config = config
        self.path = resolve_path(config["model_path"])
        self.llm = None
        self.status = "idle"
        self.error = ""
        self.phase = "idle"  # idle | thinking | answering
        self.last_stopped = False
        self._busy = threading.Lock()
        self._stop = threading.Event()
        self._skip = threading.Event()

    def load_async(self):
        threading.Thread(target=self._load, name="model-loader", daemon=True).start()

    def _load(self):
        if not self.path.is_file():
            self.status = "missing"
            self.error = f"The model file is missing: {self.path.name}. Run start.bat once to download it."
            return
        try:
            from llama_cpp import Llama
        except ImportError:
            self.status = "error"
            self.error = "The Qwen engine (llama-cpp-python) is not installed. Run start.bat to finish setup."
            return
        self.status = "loading"
        print(f"Loading {self.config['model_name']} ({self.path.name}). This can take a minute...")
        threads = int(self.config.get("threads") or max(1, (os.cpu_count() or 2) - 1))
        try:
            self.llm = Llama(
                model_path=str(self.path),
                n_ctx=int(self.config["context_size"]),
                n_threads=threads,
                n_gpu_layers=int(self.config.get("gpu_layers", 0)),
                verbose=False,
            )
        except Exception as exc:  # any load failure is shown in the interface
            self.status = "error"
            self.error = f"The model could not be loaded: {exc}"
            return
        self.status = "ready"
        print("Model ready. RIZEN OFFLINE AI is running on this computer.")

    def request_stop(self):
        self._stop.set()

    def request_skip(self):
        """Ask the model to stop thinking and answer now. Only meaningful while it is thinking."""
        if self.phase != "thinking":
            return False
        self._skip.set()
        return True

    def _phase(self, name, **extra):
        self.phase = name
        return {"type": "phase", "phase": name, **extra}

    def _stream(self, prompt_text, max_tokens, temperature, top_p):
        """Run one completion on a raw prompt and yield its text pieces."""
        tokens = self.llm.tokenize(prompt_text.encode("utf-8"), add_bos=False, special=True)
        stream = self.llm.create_completion(
            tokens,
            stream=True,
            stop=STOP_TOKENS,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=20,
            repeat_penalty=1.05,
        )
        for chunk in stream:
            piece = chunk["choices"][0].get("text") or ""
            if piece:
                yield piece

    def generate(self, messages, options):
        """Yields event dicts: phase changes and text tokens."""
        if self.status != "ready" or self.llm is None:
            raise RuntimeError(self.error or "The model is not ready yet.")
        if not self._busy.acquire(blocking=False):
            raise RuntimeError("RIZEN is already writing a reply. Press Stop or wait for it to finish.")
        try:
            self._stop.clear()
            self._skip.clear()
            self.last_stopped = False
            ctx = int(self.config["context_size"])
            temperature = clamp(float(options.get("temperature", 0.7)), 0.0, 2.0)
            top_p = clamp(float(options.get("top_p", 0.8)), 0.05, 1.0)
            max_tokens = int(clamp(int(options.get("max_tokens", 1024)), 16, ctx - 256))
            thinking_budget = int(clamp(int(self.config.get("thinking_tokens", 1536)), 64, ctx // 2))
            thinking = bool(options.get("thinking", False))
            system = str(options.get("system") or load_system_prompt())
            prompt = build_prompt(system, messages, thinking, ctx, max_tokens)
            yield from self._run(prompt, thinking, thinking_budget, max_tokens, temperature, top_p)
        finally:
            self.phase = "idle"
            self._skip.clear()
            self._busy.release()

    def _run(self, prompt, thinking, thinking_budget, max_tokens, temperature, top_p):
        if not thinking:
            yield self._phase("answering")
            for piece in self._stream(prompt, max_tokens, temperature, top_p):
                if self._stop.is_set():
                    self.last_stopped = True
                    return
                yield {"type": "token", "text": piece}
            return

        # Step 1: the model reasons inside <think>...</think>, then answers in the same stream.
        yield self._phase("thinking")
        text = ""
        think_tokens = 0
        closed = False
        for piece in self._stream(prompt, thinking_budget + max_tokens, temperature, top_p):
            if self._stop.is_set():
                self.last_stopped = True
                return
            if not closed:
                # Skip requested, or the thinking budget is used up: stop reasoning here.
                if self._skip.is_set() or think_tokens >= thinking_budget:
                    break
                think_tokens += 1
            text += piece
            yield {"type": "token", "text": piece}
            if not closed and THINK_CLOSE in text[-(len(piece) + len(THINK_CLOSE)):]:
                closed = True
                yield self._phase("answering")

        if closed:
            return  # the model finished thinking on its own, and the answer streamed normally

        # Step 2: close the thinking here and continue straight into the answer.
        yield self._phase("answering", forced=True)
        text += FORCED_CLOSE
        yield {"type": "token", "text": FORCED_CLOSE}
        for piece in self._stream(prompt + text, max_tokens, temperature, top_p):
            if self._stop.is_set():
                self.last_stopped = True
                return
            yield {"type": "token", "text": piece}


ENGINE = ModelEngine(CONFIG)
CHAT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
logging.getLogger("werkzeug").setLevel(logging.WARNING)


def sse(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def chat_file(chat_id):
    if not CHAT_ID_RE.match(chat_id):
        return None
    return CHAT_DIR / f"{chat_id}.json"


def read_chat(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def clean_message(message):
    if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
        return None
    cleaned = {"role": message["role"], "content": str(message.get("content") or "")}
    if message.get("error"):
        cleaned["error"] = str(message["error"])[:2000]
    if message.get("stopped"):
        cleaned["stopped"] = True
    if message.get("skipped"):
        cleaned["skipped"] = True
    return cleaned


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/status")
def api_status():
    return jsonify(
        status=ENGINE.status,
        error=ENGINE.error,
        app_name=APP_NAME,
        version=VERSION,
        model_name=CONFIG["model_name"],
        context_size=CONFIG["context_size"],
    )


@app.get("/api/config")
def api_config():
    return jsonify(
        app_name=APP_NAME,
        version=VERSION,
        model_name=CONFIG["model_name"],
        system_prompt=load_system_prompt(),
    )


@app.get("/api/chats")
def list_chats():
    items = []
    for path in CHAT_DIR.glob("*.json"):
        chat = read_chat(path)
        if chat is None:
            continue
        items.append({
            "id": chat.get("id", path.stem),
            "title": chat.get("title") or "New chat",
            "updated": chat.get("updated", 0),
            "count": len(chat.get("messages", [])),
        })
    items.sort(key=lambda item: item["updated"], reverse=True)
    return jsonify(items)


@app.get("/api/chats/<chat_id>")
def get_chat(chat_id):
    path = chat_file(chat_id)
    if path is None or not path.exists():
        return jsonify(error="Chat not found."), 404
    return jsonify(read_chat(path) or {})


@app.put("/api/chats/<chat_id>")
def save_chat(chat_id):
    path = chat_file(chat_id)
    if path is None:
        return jsonify(error="Invalid chat id."), 400
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        return jsonify(error="Chat data is missing or invalid."), 400
    now = int(time.time() * 1000)
    messages = [m for m in (clean_message(item) for item in data["messages"]) if m]
    chat = {
        "id": chat_id,
        "title": str(data.get("title") or "New chat").strip()[:120] or "New chat",
        "created": data["created"] if isinstance(data.get("created"), int) else now,
        "updated": now,
        "messages": messages,
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return jsonify(chat)


@app.delete("/api/chats/<chat_id>")
def delete_chat(chat_id):
    path = chat_file(chat_id)
    if path is None or not path.exists():
        return jsonify(error="Chat not found."), 404
    path.unlink()
    return jsonify(ok=True)


@app.post("/api/chat/stream")
def chat_stream():
    body = request.get_json(silent=True) or {}
    messages = body.get("messages")
    options = body.get("options") if isinstance(body.get("options"), dict) else {}
    if (
        not isinstance(messages, list)
        or not messages
        or not isinstance(messages[-1], dict)
        or messages[-1].get("role") != "user"
    ):
        return jsonify(error="Send the chat history, ending with your message."), 400
    if ENGINE.status != "ready":
        return jsonify(error=ENGINE.error or "The model is not ready yet."), 503

    def generate():
        yield sse({"type": "start"})
        try:
            for event in ENGINE.generate(messages, options):
                yield sse(event)
            yield sse({"type": "done", "stopped": ENGINE.last_stopped})
        except Exception as exc:  # shown to the person in the chat
            yield sse({"type": "error", "message": str(exc) or "Generation failed."})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/chat/skip")
def chat_skip():
    accepted = ENGINE.request_skip()
    return jsonify(ok=accepted, phase=ENGINE.phase)


@app.post("/api/chat/stop")
def chat_stop():
    ENGINE.request_stop()
    return jsonify(ok=True)


def main():
    host = CONFIG["host"]
    port = int(CONFIG["port"])
    url = f"http://{host}:{port}"
    print("=" * 56)
    print(f"  {APP_NAME} v{VERSION}")
    print(f"  Open this in your browser: {url}")
    print("  Press Ctrl+C in this window to stop.")
    print("=" * 56)
    ENGINE.load_async()
    # open-rizen.bat sets RIZEN_NO_BROWSER so that it can open the link itself.
    if CONFIG.get("open_browser", True) and not os.environ.get("RIZEN_NO_BROWSER"):
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    try:
        app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
    except OSError as exc:
        print(f"Could not start the server on {url}: {exc}")
        print('Another program may be using this port. Change "port" in config.json.')
        raise SystemExit(1)


if __name__ == "__main__":
    main()
