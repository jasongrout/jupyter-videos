"""A small OpenAI-compatible chat server for a local GGUF model, for the AI shot of the release video.

Usage: python local_llm_server.py <model.gguf> <model id> [port]

It serves GET /v1/models and POST /v1/chat/completions (streamed or not) with llama-cpp-python, and answers
CORS preflights, so a JupyterLab page on another localhost port can call it. A request with tool definitions
gets a short system prompt without them, so the model answers in text.
"""

import json
import os
import sys
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from llama_cpp import Llama

MODEL_PATH, MODEL_ID = sys.argv[1], sys.argv[2]
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8080
# A recording runs Chromium and its screencast next to the model, so fewer threads can be faster then.
llm = Llama(model_path=MODEL_PATH, n_ctx=8192, n_threads=int(os.environ.get("LLM_THREADS", 6)), seed=0, verbose=False)
lock = threading.Lock()
NO_TOOLS = ("You are Jupyternaut, an AI assistant in JupyterLab. No tools are available: answer in plain text, "
            "in one or two sentences, with a short code example when it helps.")


class Handler(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            body = json.dumps({"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "local"}]}).encode()
            self.send_response(200)
            self.cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.cors()
            self.end_headers()

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            self.send_response(404)
            self.cors()
            self.end_headers()
            return
        received = time.time()
        request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        messages = [m for m in request.get("messages", []) if m.get("role") in ("system", "user", "assistant") and isinstance(m.get("content"), str)]
        if request.get("tools"):
            # This server cannot run tools: a system prompt that offers them makes the model write tool calls as text.
            messages = [m for m in messages if m["role"] != "system"]
            messages.insert(0, {"role": "system", "content": NO_TOOLS})
        prompt_chars = sum(len(m["content"]) for m in messages)
        print(f"request: {len(messages)} messages, {prompt_chars} characters, stream={request.get('stream')}", flush=True)
        # Keep each request, to replay its system prompt and warm the cache before a recording.
        log = Path(os.environ.get("LLM_REQUEST_LOG", Path(os.environ.get("RV_BASE", Path(__file__).resolve().parents[1] / "work/runtime")) / "llm-requests"))
        log.mkdir(parents=True, exist_ok=True)
        number = len([f for f in log.iterdir() if not f.name.endswith(".timing.json")])
        (log / f"{number:03d}.json").write_text(json.dumps(request))
        # A fixed seed gives the same answer to the same question in every take.
        options = {"max_tokens": min(int(request.get("max_tokens") or 400), 400), "temperature": float(request.get("temperature", 0.3)), "seed": 0}
        with lock:
            if request.get("stream"):
                self.send_response(200)
                self.cors()
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                first = None
                for chunk in llm.create_chat_completion(messages=messages, stream=True, **options):
                    chunk["model"] = MODEL_ID
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                    self.wfile.flush()
                    if first is None and chunk["choices"][0]["delta"].get("content"):
                        first = time.time()
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                # Wall-clock times, to set the speed of the answer in the cut to that of a run without the recorder.
                (log / f"{number:03d}.timing.json").write_text(json.dumps({"received": received, "first": first, "done": time.time()}))
            else:
                result = llm.create_chat_completion(messages=messages, **options)
                result["model"] = MODEL_ID
                body = json.dumps(result).encode()
                self.send_response(200)
                self.cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

    def log_message(self, *args):
        pass


print(f"serving {MODEL_ID} on http://localhost:{PORT}/v1", flush=True)
ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
