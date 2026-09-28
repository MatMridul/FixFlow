"""Ordered multi-provider LLM chain (Gemini -> Mistral) with quota-aware fallback.

The hackathon FAQ gives bonus points for Gemini and Mistral, and ships no API
keys (bring your own, via env vars / .env, never committed). Free tiers are
tight — the strongest Gemini model allows only ~20 requests/day — so the chain
tries models strongest-first and falls through on quota/errors:

    gemini-2.5-flash -> mistral-small-latest -> ministral-8b-latest -> groq gpt-oss-120b

Requests are hedged: if the current model hasn't answered within `hedge_s`,
the next one starts in parallel and the first valid answer wins. Free-tier
Gemini often answers 503 only after several seconds; without hedging that
alone could spend the cold-path budget.

A model that returns a quota/rate-limit error is benched for a cool-down window
so later requests don't pay its latency just to fail again. If every model
fails, the caller (StructureExtractor) falls back to deterministic extraction,
so the API never goes down during judging for lack of an LLM.

Uses stdlib urllib only — no provider SDKs to install or pin.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Ordered by measured quality/latency on the free tiers (2026-09-28): gemini-3.x
# flash models returned 503 "high demand" (sometimes after 5-7 s, which eats the
# cold-path budget) and mistral-medium/small returned 429 on the free key, so the
# default leads with the models that actually answer. Override with LLM_CHAIN.
DEFAULT_CHAIN = [
    "gemini:gemini-2.5-flash",
    "mistral:mistral-small-latest",
    "mistral:ministral-8b-latest",
    "groq:openai/gpt-oss-120b",
]

# USD per 1M tokens (input, output). Free tier bills $0, but meta.cost_usd
# reports list-price cost so the brief's "cost per query" metric is honest
# about what the query would cost on a paid tier.
_PRICE_PER_M = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-3.8-flash": (0.30, 2.50),
    "ministral-8b-latest": (0.10, 0.10),
    "openai/gpt-oss-120b": (0.15, 0.60),
    "gemini-3.5-flash-lite": (0.10, 0.40),
    "mistral-medium-latest": (0.40, 2.00),
    "mistral-small-latest": (0.10, 0.30),
}

logger = logging.getLogger("fixflow.llm")

_QUOTA_COOLDOWN_S = 15 * 60
_ERROR_COOLDOWN_S = 60
_OVERLOAD_COOLDOWN_S = 20


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
        self.cooldown_s: Optional[float] = None  # overrides the default bench window


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
        headers={"Content-Type": "application/json", "User-Agent": "fixflow/1.0", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        # 429 = rate limit / daily quota; 404 = model id not available on this key.
        err = LLMError(f"HTTP {e.code}: {detail}", quota=e.code in (429, 403, 404))
        if e.code == 503:
            err.cooldown_s = _OVERLOAD_COOLDOWN_S  # "high demand" spikes pass quickly
        raise err from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        err = LLMError(f"network: {e}")
        if isinstance(e, TimeoutError) or "timed out" in str(e):
            err.cooldown_s = 0.0  # we cut it off to protect the latency budget; not the model's fault
        raise err from e


def _gemini_thinking(model: str) -> dict:
    """Extraction is a formatting task: thinking only adds latency (2.5-flash
    took 9-25 s with default thinking vs the 8 s cold-path budget)."""
    if model.startswith("gemini-2.5"):
        return {"thinkingBudget": 0}
    return {"thinkingLevel": "low"}


def _call_gemini(model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "thinkingConfig": _gemini_thinking(model),
        },
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


def _call_openai_compatible(url: str, model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    if model.startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"  # reasoning model; low keeps it ~1.5 s
    data = _post_json(url, body, {"Authorization": f"Bearer {api_key}"}, timeout)
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"unexpected response shape: {str(data)[:200]}") from e
    usage = data.get("usage", {})
    rec = LLMCallRecord(
        model=model,
        input_tokens=int(usage.get("prompt_tokens", 0)),
        output_tokens=int(usage.get("completion_tokens", 0)),
    )
    return text, rec


def _call_mistral(model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    return _call_openai_compatible("https://api.mistral.ai/v1/chat/completions", model, prompt, api_key, timeout)


def _call_groq(model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    # Last-resort fallback when both Gemini and Mistral are down or rate-limited.
    return _call_openai_compatible("https://api.groq.com/openai/v1/chat/completions", model, prompt, api_key, timeout)


# Losing hedged calls finish in the background; the pool just bounds threads.
_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="llm")


def _timed_call(fn, model: str, prompt: str, api_key: str, timeout: float) -> tuple[str, LLMCallRecord]:
    start = time.perf_counter()
    text, record = fn(model, prompt, api_key, timeout)
    record.latency_ms = (time.perf_counter() - start) * 1000.0
    return text, record


_PROVIDERS = {
    "gemini": (_call_gemini, "GEMINI_API_KEY"),
    "groq": (_call_groq, "GROQ_API_KEY"),
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
    timeout_s: float = 7.0
    # Whole-chain budget: the scorer wants cold-path P95 <= 8 s (FAQ A3), so
    # falling through 4 models at 6 s each can't be allowed. Each attempt gets
    # at most what's left; past the budget the extractor goes deterministic.
    total_budget_s: float = 7.3
    # Start the next model in parallel if the current one is still silent.
    hedge_s: float = 2.5
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
            timeout_s=float(os.environ.get("LLM_TIMEOUT_S", "7")),
            total_budget_s=float(os.environ.get("LLM_TOTAL_BUDGET_S", "7.3")),
            hedge_s=float(os.environ.get("LLM_HEDGE_S", "2.5")),
        )

    def active_models(self) -> List[str]:
        now = time.monotonic()
        return [c for c in self.chain if self._benched_until.get(c, 0.0) <= now]

    def __call__(self, prompt: str) -> str:
        return self.complete(prompt)[0]

    def complete(self, prompt: str) -> tuple[str, LLMCallRecord]:
        errors: List[str] = []
        deadline = time.monotonic() + self.total_budget_s
        queue = list(self.chain)
        pending: Dict = {}

        def launch_next() -> None:
            while queue:
                entry = queue.pop(0)
                with self._lock:
                    if self._benched_until.get(entry, 0.0) > time.monotonic():
                        continue
                provider, model = entry.split(":", 1)
                fn, key_env = _PROVIDERS[provider]
                api_key = os.environ.get(key_env)
                if not api_key:
                    continue
                remaining = deadline - time.monotonic()
                if remaining < 1.0:
                    errors.append(f"{entry}: skipped, time budget exhausted")
                    queue.clear()
                    return
                timeout = min(self.timeout_s, remaining)
                pending[_POOL.submit(_timed_call, fn, model, prompt, api_key, timeout)] = entry
                return

        launch_next()
        while pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                errors.append("time budget exhausted")
                break
            done, _ = wait(list(pending), timeout=min(self.hedge_s, remaining), return_when=FIRST_COMPLETED)
            if not done:
                launch_next()  # hedge: current model is slow, race the next one
                continue
            for fut in done:
                entry = pending.pop(fut)
                try:
                    return fut.result()
                except LLMError as e:
                    errors.append(f"{entry}: {e}")
                    logger.warning("LLM %s failed (quota=%s): %s", entry, e.quota, str(e)[:160])
                    cooldown = e.cooldown_s
                    if cooldown is None:
                        cooldown = _QUOTA_COOLDOWN_S if e.quota else _ERROR_COOLDOWN_S
                    if cooldown > 0:
                        with self._lock:
                            self._benched_until[entry] = time.monotonic() + cooldown
                except Exception as e:  # never let a provider bug escape the chain
                    errors.append(f"{entry}: {type(e).__name__}: {e}")
            launch_next()  # failure: move straight to the next model
        raise LLMError("all LLM providers failed: " + " | ".join(errors))
