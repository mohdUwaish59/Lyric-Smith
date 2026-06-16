"""
llm.py — LLM clients (feature 7, real backends).

All clients are callables with the signature expected by generation.py:

    client(prompt: str, n: int) -> list[str]

returning up to n candidate lines. Two open-source/local backends are
provided plus a mock for offline testing:

  - OllamaClient : talks to a local Ollama server (default :11434).
  - VLLMClient   : talks to a vLLM OpenAI-compatible server (default :8000).
  - MockLLM      : deterministic, no network (used by tests).

Only the Python standard library is used (urllib) — no 'requests' needed.
"""

import json
import re
import urllib.error
import urllib.request

__all__ = ["OllamaClient", "VLLMClient", "HuggingFaceClient", "MockLLM", "clean_lines"]


# --------------------------------------------------------------------------
# Response parsing
# --------------------------------------------------------------------------

_NUM_PREFIX = re.compile(r"^\s*\d+[\.\)\:]\s*")
_BULLET_PREFIX = re.compile(r"^\s*[-*•]\s*")


def clean_lines(text, n=None):
    """Turn a raw model completion into a clean list of candidate lines.

    Strips numbering ('1. '), bullets ('- '), surrounding quotes, and blank
    lines. Returns at most n lines if n is given.
    """
    out = []
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        s = _NUM_PREFIX.sub("", s)
        s = _BULLET_PREFIX.sub("", s)
        s = s.strip().strip('"').strip("'").strip()
        # drop obvious non-lyric lines the model sometimes adds
        if not s or s.lower().startswith(("here are", "sure,", "option")):
            continue
        out.append(s)
    return out[:n] if n else out


def _post_json(url, payload, timeout=120):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --------------------------------------------------------------------------
# Ollama  (https://ollama.com)  ->  ollama serve ; ollama pull llama3.1
# --------------------------------------------------------------------------

class OllamaClient:
    """Client for a local Ollama server.

    Example:
        from lyricsmith.llm import OllamaClient
        llm = OllamaClient(model="llama3.1")           # must be pulled first
        lines = llm("Write 4 distinct 8-syllable lines...", 4)
    """

    def __init__(self, model="llama3.1", host="http://localhost:11434",
                 temperature=0.9, timeout=120, num_predict=256):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout
        self.num_predict = num_predict
        self._attempt_count = 0

    def __call__(self, prompt, n=1):
        # Increase temperature slightly for later attempts to get more variety
        self._attempt_count += 1
        temp = min(self.temperature + (self._attempt_count // 3) * 0.05, 1.2)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": self.num_predict,
                "top_p": 0.95,  # Add nucleus sampling for better quality
            },
        }
        try:
            data = _post_json(f"{self.host}/api/generate", payload, self.timeout)
        except (urllib.error.URLError, TimeoutError) as e:
            raise RuntimeError(
                f"Ollama request failed ({e}). Is 'ollama serve' running and "
                f"model '{self.model}' pulled?") from e
        return clean_lines(data.get("response", ""), n)


# --------------------------------------------------------------------------
# vLLM  (OpenAI-compatible server)
#   python -m vllm.entrypoints.openai.api_server --model <hf-model>
# --------------------------------------------------------------------------

class VLLMClient:
    """Client for a vLLM OpenAI-compatible server (also works for any
    OpenAI-compatible endpoint: text-generation-inference, LM Studio, etc.).

    Example:
        from lyricsmith.llm import VLLMClient
        llm = VLLMClient(model="meta-llama/Meta-Llama-3.1-8B-Instruct")
        lines = llm(prompt, 4)
    """

    def __init__(self, model, host="http://localhost:8000",
                 temperature=0.8, timeout=120, max_tokens=256, api_key="EMPTY"):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.api_key = api_key

    def __call__(self, prompt, n=1):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        url = f"{self.host}/v1/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as e:
            raise RuntimeError(
                f"vLLM request failed ({e}). Is the vLLM OpenAI server running "
                f"on {self.host} with model '{self.model}'?") from e
        content = body["choices"][0]["message"]["content"]
        return clean_lines(content, n)


# --------------------------------------------------------------------------
# HuggingFace Inference API (https://huggingface.co/inference-api)
# Free tier available, good for testing without local models
# --------------------------------------------------------------------------

class HuggingFaceClient:
    """Client for HuggingFace Inference API.
    
    Get your free API token from: https://huggingface.co/settings/tokens
    
    Example:
        from lyricsmith.llm import HuggingFaceClient
        llm = HuggingFaceClient(
            model="meta-llama/Llama-3.1-8B-Instruct",
            api_token="hf_..."  # Your token
        )
        lines = llm("Write 4 distinct 8-syllable lines...", 4)
    
    Popular models (free tier):
        - meta-llama/Llama-3.1-8B-Instruct
        - meta-llama/Llama-3.2-3B-Instruct
        - Qwen/Qwen2.5-7B-Instruct
        - mistralai/Mistral-7B-Instruct-v0.3
    """
    
    def __init__(self, model, api_token, temperature=0.9, timeout=120, max_new_tokens=256):
        self.model = model
        self.api_token = api_token
        self.temperature = temperature
        self.timeout = timeout
        self.max_new_tokens = max_new_tokens
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"
        self._attempt_count = 0
    
    def __call__(self, prompt, n=1):
        # Increase temperature slightly for later attempts
        self._attempt_count += 1
        temp = min(self.temperature + (self._attempt_count // 3) * 0.05, 1.2)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_new_tokens,
                "temperature": temp,
                "top_p": 0.95,
                "return_full_text": False,
            },
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            if e.code == 401:
                raise RuntimeError(
                    f"HuggingFace API authentication failed. "
                    f"Check your API token at https://huggingface.co/settings/tokens"
                ) from e
            elif e.code == 503:
                raise RuntimeError(
                    f"Model '{self.model}' is currently loading. Try again in a minute, "
                    f"or use a different model."
                ) from e
            else:
                raise RuntimeError(
                    f"HuggingFace API request failed ({e.code}): {error_body}"
                ) from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise RuntimeError(
                f"HuggingFace API request failed: {e}. Check your internet connection."
            ) from e
        
        # Parse response - can be list or single dict
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            text = result.get("generated_text", "")
        else:
            text = ""
        
        return clean_lines(text, n)


# --------------------------------------------------------------------------
# Mock (offline, deterministic) — used by tests and the offline demo
# --------------------------------------------------------------------------

class MockLLM:
    """Deterministic stand-in. Routes on keywords in the prompt's meaning so
    the offline demo is reproducible. Real clients ignore all of this."""

    def __init__(self, pool=None):
        self.pool = pool or {
            "opener": [
                "A boy alone",
                "The little boy asleep at night",
                "The quiet boy is sound asleep",
            ],
            "image": [
                "Quiet shadows everywhere",
                "Moonlight cold and silver bright",
                "Stars are shining in the sky",
            ],
        }

    def _slot(self, prompt):
        p = prompt.lower()
        if "rhyme with" in p or "image" in p:
            return "image"
        return "opener"

    def __call__(self, prompt, n=1):
        return self.pool.get(self._slot(prompt), ["la la la la"])[:n]
