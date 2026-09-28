"""LLMChain fallback behaviour, with provider HTTP calls mocked out (no real
network, no quota spend)."""
from __future__ import annotations

import pytest

import extraction.llm_client as llm
from extraction.llm_client import LLMCallRecord, LLMChain, LLMError


@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")


def _provider_stub(monkeypatch, behaviour: dict):
    """behaviour: model -> 'ok' | 'quota' | 'error'. Records call order."""
    calls = []

    def fake(model, prompt, api_key, timeout):
        calls.append(model)
        outcome = behaviour.get(model, "ok")
        if outcome == "quota":
            raise LLMError("HTTP 429", quota=True)
        if outcome == "error":
            raise LLMError("network: boom")
        return '{"ok": true}', LLMCallRecord(model=model, input_tokens=1000, output_tokens=500)

    monkeypatch.setitem(llm._PROVIDERS, "gemini", (fake, "GEMINI_API_KEY"))
    monkeypatch.setitem(llm._PROVIDERS, "mistral", (fake, "MISTRAL_API_KEY"))
    monkeypatch.setitem(llm._PROVIDERS, "groq", (fake, "GROQ_API_KEY"))
    return calls


def test_first_model_answers_when_healthy(keys, monkeypatch):
    calls = _provider_stub(monkeypatch, {})
    text, rec = LLMChain().complete("p")
    assert rec.model == "gemini-2.5-flash"
    assert calls == ["gemini-2.5-flash"]
    assert rec.cost_usd > 0  # list-price cost is reported, not a placeholder


def test_falls_through_in_priority_order(keys, monkeypatch):
    calls = _provider_stub(monkeypatch, {"gemini-2.5-flash": "quota", "mistral-small-latest": "error"})
    _, rec = LLMChain().complete("p")
    assert rec.model == "ministral-8b-latest"
    assert calls == ["gemini-2.5-flash", "mistral-small-latest", "ministral-8b-latest"]


def test_quota_hit_benches_model_for_later_requests(keys, monkeypatch):
    calls = _provider_stub(monkeypatch, {"gemini-2.5-flash": "quota"})
    chain = LLMChain()
    chain.complete("p")
    calls.clear()
    _, rec = chain.complete("p")
    assert calls == ["mistral-small-latest"]  # benched model not retried
    assert rec.model == "mistral-small-latest"


def test_all_fail_raises_so_extractor_goes_deterministic(keys, monkeypatch):
    _provider_stub(monkeypatch, {m.split(":")[1]: "error" for m in llm.DEFAULT_CHAIN})
    with pytest.raises(LLMError):
        LLMChain().complete("p")


def test_skips_providers_without_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    calls = _provider_stub(monkeypatch, {})
    _, rec = LLMChain().complete("p")
    assert rec.model == "mistral-small-latest"
    assert calls == ["mistral-small-latest"]


def test_time_budget_stops_the_chain(keys, monkeypatch):
    _provider_stub(monkeypatch, {m.split(":")[1]: "error" for m in llm.DEFAULT_CHAIN})
    chain = LLMChain(total_budget_s=0.5)  # < 1 s left before the first call
    with pytest.raises(LLMError, match="time budget"):
        chain.complete("p")


def test_from_env_disabled_in_tests():
    assert LLMChain.from_env() is None  # conftest sets FIXFLOW_DISABLE_LLM=1


def test_extractor_uses_llm_output_and_variations(monkeypatch):
    from extraction.extractor import StructureExtractor

    llm_json = """{
      "query_variations": ["a one", "b two", "c three"],
      "goal": "Follow these steps to perform this Blank Screen Troubleshooting",
      "title": "Blank screen issue",
      "score": 0.0,
      "actions": [{
        "actionName": "Force a Restart",
        "description": "It will clear temporary glitches",
        "category": "critical",
        "stepGroups": [{"steps": ["Press and hold the Power and Volume down buttons."],
                        "actionableDeeplink": null, "validationDeeplink": null}]
      }]
    }"""

    class FakeChain:
        def complete(self, prompt):
            return llm_json, LLMCallRecord(model="gemini-3.5-flash-lite", input_tokens=2000, output_tokens=400)

        def __call__(self, prompt):
            return self.complete(prompt)[0]

    out = StructureExtractor(llm_callable=FakeChain()).extract_full(
        "My Galaxy screen is completely black", "Blank display", "Press and hold the Power and Volume down buttons."
    )
    assert out.llm_used and out.model == "gemini-3.5-flash-lite" and out.cost_usd > 0
    assert out.goal.actions[0].actionName == "Force a Restart"
    assert out.query_variations[:3] == ["a one", "b two", "c three"]
    assert 8 <= len(out.query_variations) <= 10  # padded to the FAQ minimum


def test_hedge_races_next_model_when_first_is_slow(keys, monkeypatch):
    import time as _time

    def fake(model, prompt, api_key, timeout):
        if model == "gemini-2.5-flash":
            _time.sleep(1.0)
        return '{"ok": true}', LLMCallRecord(model=model, input_tokens=10, output_tokens=5)

    monkeypatch.setitem(llm._PROVIDERS, "gemini", (fake, "GEMINI_API_KEY"))
    monkeypatch.setitem(llm._PROVIDERS, "mistral", (fake, "MISTRAL_API_KEY"))
    monkeypatch.setitem(llm._PROVIDERS, "groq", (fake, "GROQ_API_KEY"))
    start = _time.monotonic()
    _, rec = LLMChain(hedge_s=0.1).complete("p")
    assert rec.model == "mistral-small-latest"
    assert _time.monotonic() - start < 0.8


def test_groq_is_last_resort(keys, monkeypatch):
    calls = _provider_stub(
        monkeypatch,
        {"gemini-2.5-flash": "error", "mistral-small-latest": "quota", "ministral-8b-latest": "error"},
    )
    _, rec = LLMChain().complete("p")
    assert rec.model == "openai/gpt-oss-120b"
    assert calls[-1] == "openai/gpt-oss-120b"
