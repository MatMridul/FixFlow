"""Paraphrase cache paths added after the benchmark measured a 7% paraphrase
hit rate (FAQ A3 needs >= 80%): same-article lookup and pre-warmed variations."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from cache import CacheStore, CompositionalCache

ARTICLE = {
    "title": "Black screen on Galaxy tablet",
    "content": (
        "If your tablet screen goes black, try these steps.\n\nForce restart\n"
        "Press and hold the Side key and Volume down key for 10 seconds.\n\n"
        "Check the display settings\nOpen Settings, tap Display, and turn off Dark mode."
    ),
}
QUERY = "My Samsung tablet screen goes completely black when I open Gmail and won't come back"


@pytest.fixture
def client_and_cache():
    cache = CompositionalCache(store=CacheStore(db_path=str(Path(tempfile.mkdtemp()) / "c.db")))
    return TestClient(create_app(cache=cache)), cache


def test_same_article_paraphrase_hits(client_and_cache):
    client, _ = client_and_cache
    cold = client.post("/v1/troubleshoot", json={"query": QUERY, "siis_response": ARTICLE}).json()
    assert cold["meta"]["cache_hit"] is False
    para = client.post("/v1/troubleshoot", json={
        "query": "Why does my tablet display turn black whenever Gmail opens?", "siis_response": ARTICLE,
    }).json()
    assert para["meta"]["cache_hit"] is True
    assert para["meta"]["model"] == "cache-article-v1"
    assert para["response"]["contexts"] == cold["response"]["contexts"]


def test_same_article_opposite_command_is_a_miss(client_and_cache):
    client, _ = client_and_cache
    client.post("/v1/troubleshoot", json={"query": "How do I turn on Dark mode", "siis_response": ARTICLE})
    other = client.post("/v1/troubleshoot", json={"query": "How do I turn off Dark mode", "siis_response": ARTICLE}).json()
    assert other["meta"]["cache_hit"] is False


def test_no_article_paraphrase_hits_prewarmed_variations(client_and_cache):
    client, _ = client_and_cache
    client.post("/v1/troubleshoot", json={"query": QUERY, "siis_response": ARTICLE})
    para = client.post("/v1/troubleshoot", json={"query": "samsung tablet screen went black after opening gmail"}).json()
    assert para["meta"]["cache_hit"] is True
    assert para["response"]["contexts"]


def test_no_article_different_setting_is_a_miss(client_and_cache):
    _, cache = client_and_cache
    from schema import Action, Goal, StepGroup
    goal = Goal(goal="Follow these steps to perform this Brightness Configuration", title="Screen brightness",
                score=0.9, actions=[Action(actionName="Adjust Brightness", description="It will make the screen readable",
                                           stepGroups=[StepGroup(steps=["Open Settings.", "Tap Display."])])])
    cache.put_article("fp", "How to adjust screen brightness", [goal], variations=["change screen brightness level"])
    assert cache.get_by_variants("How to change screen timeout duration").hit is False


def test_clear_empties_paraphrase_indexes(client_and_cache):
    client, cache = client_and_cache
    client.post("/v1/troubleshoot", json={"query": QUERY, "siis_response": ARTICLE})
    cache.clear()
    fp = cache.article_fingerprint(ARTICLE["title"], ARTICLE["content"])
    assert cache.get_by_article(QUERY, fp).hit is False
    assert cache.get_by_variants(QUERY).hit is False
