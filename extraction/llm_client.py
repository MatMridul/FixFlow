"""Ordered multi-provider LLM chain (Gemini -> Mistral) with quota-aware fallback.

The hackathon FAQ gives bonus points for Gemini and Mistral, and ships no API
keys (bring your own, via env vars / .env, never committed). Free tiers are
tight — the strongest Gemini model allows only ~20 requests/day — so the chain
tries models strongest-first and falls through on quota/errors:

    gemini-3.8-flash -> gemini-3.5-flash-lite -> mistral-medium-latest -> mistral-small-latest

A model that returns a quota/rate-limit error is benched for a cool-down window
so later requests don't pay its latency just to fail again. If every model
fails, the caller (StructureExtractor) falls back to deterministic extraction,
so the API never goes down during judging for lack of an LLM.

Uses stdlib urllib only — no provider SDKs to install or pin.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CHAIN = [
    "gemini:gemini-3.8-flash",
    "gemini:gemini-3.5-flash-lite",
    "mistral:mistral-medium-latest",
    "mistral:mistral-small-latest",
]

# USD per 1M tokens (input, output). Free tier bills $0, but meta.cost_usd
# reports list-price cost so the brief's "cost per query" metric is honest
# about what the query would cost on a paid tier.
_PRICE_PER_M = {
    "gemini-3.8-flash": (0.30, 2.50),
    "gemini-3.5-flash-lite": (0.10, 0.40),
    "mistral-medium-latest": (0.40, 2.00),
    "mistral-small-latest": (0.10, 0.30),
}

_QUOTA_COOLDOWN_S = 15 * 60
_ERROR_COOLDOWN_S = 60


def load_dotenv(path: Path = _REPO_ROOT / ".env") -> None:
    """Minimal .env loader (KEY=VALUE lines). Real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class LLMError(Exception):
    def __init__(self, message: str, quota: bool = False):
        super().__init__(message)
        self.quota = quota


@dataclass
class LLMCallRecord:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    @property
    def cost_usd(self) -> float:
        price_in, price_out = _PRICE_PER_M.get(self.model, (0.0, 0.0))
        return (self.input_tokens * price_in + self.output_tokens * price_out) / 1_000_000


def _post_json(url: str, body: dict, headers: Dict[str, str], timeout: float) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        # 429 = rate limit / daily quota; 404 = model id not available on this key.
        raise LLMError(f"HTTP {e.code}: {detail}", quota=e.code in (429, 403, 404)) from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LLMError(f"network: {e}") from e


def _call_gemini(model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    data = _post_json(url, body, {"x-goog-api-key": api_key}, timeout)
    try:
        text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"unexpected gemini response shape: {str(data)[:200]}") from e
    usage = data.get("usageMetadata", {})
    rec = LLMCallRecord(
        model=model,
        input_tokens=int(usage.get("promptTokenCount", 0)),
        output_tokens=int(usage.get("candidatesTokenCount", 0)),
    )
    return text, rec


def _call_mistral(model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    data = _post_json(
        "https://api.mistral.ai/v1/chat/completions",
        body,
        {"Authorization": f"Bearer {api_key}"},
        timeout,
    )
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"unexpected mistral response shape: {str(data)[:200]}") from e
    usage = data.get("usage", {})
    rec = LLMCallRecord(
        model=model,
        input_tokens=int(usage.get("prompt_tokens", 0)),
        output_tokens=int(usage.get("completion_tokens", 0)),
    )
    return text, rec


_PROVIDERS = {
    "gemini": (_call_gemini, "GEMINI_API_KEY"),
    "mistral": (_call_mistral, "MISTRAL_API_KEY"),
}


@dataclass
class LLMChain:
    """Tries each configured model in order.

    `complete(prompt)` returns `(text, record)` — the record says which model
    actually answered and its token usage. Per-call return values (not shared
    instance state) because FastAPI runs sync endpoints in a thread pool, so
    concurrent requests share one chain. `__call__` keeps the plain
    `prompt -> str` shape StructureExtractor's `llm_callable` expects.
    """

    chain: List[str] = field(default_factory=lambda: list(DEFAULT_CHAIN))
    timeout_s: float = 6.0
    # Whole-chain budget: the scorer wants cold-path P95 <= 8 s (FAQ A3), so
    # falling through 4 models at 6 s each can't be allowed. Each attempt gets
    # at most what's left; past the budget the extractor goes deterministic.
    total_budget_s: float = 6.5
    _benched_until: Dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def from_env(cls) -> Optional["LLMChain"]:
        """Build a chain from env / .env. Returns None when no provider key is
        configured, so callers fall back to deterministic extraction."""
        load_dotenv()
        if os.environ.get("FIXFLOW_DISABLE_LLM") == "1":
            return None  # tests set this so they never spend real quota
        raw = os.environ.get("LLM_CHAIN")
        chain = [c.strip() for c in raw.split(",") if c.strip()] if raw else list(DEFAULT_CHAIN)
        available = [c for c in chain if os.environ.get(_PROVIDERS.get(c.split(":", 1)[0], (None, ""))[1])]
        if not available:
            return None
        return cls(
            chain=available,
            timeout_s=float(os.environ.get("LLM_TIMEOUT_S", "6")),
            total_budget_s=float(os.environ.get("LLM_TOTAL_BUDGET_S", "6.5")),
        )

    def active_models(self) -> List[str]:
        now = time.monotonic()
        return [c for c in self.chain if self._benched_until.get(c, 0.0) <= now]

    def __call__(self, prompt: str) -> str:
        return self.complete(prompt)[0]

    def complete(self, prompt: str) -> tuple[str, LLMCallRecord]:
        errors: List[str] = []
        chain_start = time.monotonic()
        for entry in self.chain:
            remaining = self.total_budget_s - (time.monotonic() - chain_start)
            if remaining < 1.0:
                errors.append(f"{entry}: skipped, time budget exhausted")
                break
            with self._lock:
                if self._benched_until.get(entry, 0.0) > time.monotonic():
                    continue
            provider, model = entry.split(":", 1)
            fn, key_env = _PROVIDERS[provider]
            api_key = os.environ.get(key_env)
            if not api_key:
                continue
            start = time.perf_counter()
            try:
                text, record = fn(model, prompt, api_key, min(self.timeout_s, remaining))
            except LLMError as e:
                errors.append(f"{entry}: {e}")
                with self._lock:
                    self._benched_until[entry] = time.monotonic() + (
                        _QUOTA_COOLDOWN_S if e.quota else _ERROR_COOLDOWN_S
                    )
                continue
            record.latency_ms = (time.perf_counter() - start) * 1000.0
            return text, record
        raise LLMError("all LLM providers failed: " + " | ".join(errors))
