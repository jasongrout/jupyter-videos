"""Time cached GGUF chat models on the question of the AI shot, with the settings of local_llm_server.py.

Usage: python bench_models.py <out.json> [name ...]

Each model answers a short warm-up message, then the question of the take. The script records the time to the first
token, the generation rate and the answer, and the CPU steal time during each answer (0 where the hypervisor does not report it).
"""

import json
import sys
import time
from pathlib import Path

from huggingface_hub import hf_hub_download
from llama_cpp import Llama

# Hugging Face repositories and files; hf_hub_download reads them from the local cache when they are there.
MODELS = {
    "gemma-4-E4B": ("ggml-org/gemma-4-E4B-it-GGUF", "gemma-4-E4B-it-Q4_0.gguf"),
    "gemma-4-E2B": ("ggml-org/gemma-4-E2B-it-GGUF", "gemma-4-E2B-it-Q4_0.gguf"),
    "Qwen3-4B": ("Qwen/Qwen3-4B-GGUF", "Qwen3-4B-Q4_K_M.gguf"),
    "Ministral-3-3B": ("mistralai/Ministral-3-3B-Instruct-2512-GGUF", "Ministral-3-3B-Instruct-2512-Q4_K_M.gguf"),
    "granite-4.1-3b": ("ibm-granite/granite-4.1-3b-GGUF", "granite-4.1-3b-Q4_0.gguf"),
    "SmolLM3-3B": ("ggml-org/SmolLM3-3B-GGUF", "SmolLM3-Q4_K_M.gguf"),
    "MiniCPM5-2B": ("openbmb/MiniCPM5-2B-GGUF", "MiniCPM5-2B-Q4_K_M.gguf"),
    "Qwen3-1.7B": ("ggml-org/Qwen3-1.7B-GGUF", "Qwen3-1.7B-Q4_K_M.gguf"),
    "LFM2.5-1.2B": ("LiquidAI/LFM2.5-1.2B-Instruct-GGUF", "LFM2.5-1.2B-Instruct-Q8_0.gguf"),
    "Qwen3.5-0.8B": ("ggml-org/Qwen3.5-0.8B-GGUF", "Qwen3.5-0.8B-Q4_0.gguf"),
}
# These models think before they answer unless the system prompt turns it off.
NO_THINK = {"Qwen3-4B", "SmolLM3-3B", "Qwen3-1.7B", "Qwen3.5-0.8B"}
SYSTEM = ("You are Jupyternaut, an AI assistant in JupyterLab. No tools are available: answer in plain text, "
          "briefly, with a short code example when it helps.")
QUESTION = "Briefly, how do I read a CSV file with comment lines in pandas?"
OPTIONS = {"max_tokens": 400, "temperature": 0.7}


def cpu_times():
    fields = [int(v) for v in Path("/proc/stat").read_text().split("\n")[0].split()[1:]]
    return sum(fields), fields[7]


def ask(llm, messages, max_tokens=OPTIONS["max_tokens"]):
    start = time.perf_counter()
    first = None
    text = ""
    for chunk in llm.create_chat_completion(messages=messages, stream=True, **{**OPTIONS, "max_tokens": max_tokens}):
        piece = chunk["choices"][0]["delta"].get("content") or ""
        if piece and first is None:
            first = time.perf_counter()
        text += piece
    end = time.perf_counter()
    return text, start, first or end, end


def main():
    out = Path(sys.argv[1])
    names = sys.argv[2:] or list(MODELS)
    results = json.loads(out.read_text()) if out.exists() else []
    for name in names:
        system = SYSTEM + (" /no_think" if name in NO_THINK else "")
        messages = [{"role": "system", "content": system}, {"role": "user", "content": QUESTION}]
        try:
            t0 = time.perf_counter()
            llm = Llama(model_path=hf_hub_download(*MODELS[name]), n_ctx=8192, n_threads=6, seed=0, verbose=False)
            load = time.perf_counter() - t0
            ask(llm, [{"role": "system", "content": system}, {"role": "user", "content": "Hi!"}], max_tokens=8)
            total0, steal0 = cpu_times()
            text, start, first, end = ask(llm, messages)
            total1, steal1 = cpu_times()
        except Exception as error:  # a model that this llama.cpp build cannot load
            print(f"{name}: {type(error).__name__}: {error}", flush=True)
            results.append({"name": name, "error": str(error)})
            continue
        tokens = len(llm.tokenize(text.encode(), add_bos=False, special=True))
        row = {
            "name": name,
            "file_gb": round(Path(hf_hub_download(*MODELS[name])).stat().st_size / 1e9, 2),
            "load_s": round(load, 2),
            "first_token_s": round(first - start, 2),
            "generate_s": round(end - first, 2),
            "total_s": round(end - start, 2),
            "tokens": tokens,
            "tokens_per_s": round(tokens / max(end - first, 1e-6), 1),
            "steal_pct": round(100 * (steal1 - steal0) / max(total1 - total0, 1), 1),
            "answer": text,
        }
        results.append(row)
        print(f"{name}: {row['total_s']} s, {tokens} tokens, {row['tokens_per_s']} tokens/s, first token {row['first_token_s']} s, steal {row['steal_pct']} %", flush=True)
        out.write_text(json.dumps(results, indent=1))
        del llm


main()
