"""Unit tests for SIIS knowledge base auto-retriever."""
from pathlib import Path
import pytest

from resolution.siis_retriever import SIISRetriever


@pytest.fixture
def retriever():
    return SIISRetriever.default()


class TestSIISRetriever:
    def test_default_loader_loads_articles(self, retriever):
        assert len(retriever.articles) >= 11
        assert retriever._bm25 is not None
        assert retriever._tfidf_matrix is not None

    def test_retrieve_camera_issue(self, retriever):
        match = retriever.retrieve("My camera video flickers when shooting indoors")
        assert match is not None
        assert "Camera" in match.title
        assert match.score > 0.4
        assert match.cosine_score > 0.1

    def test_retrieve_screen_rotation_issue(self, retriever):
        match = retriever.retrieve("Screen won't rotate when I turn my Galaxy phone")
        assert match is not None
        assert "rotate" in match.title.lower()

    def test_retrieve_email_connection_issue(self, retriever):
        match = retriever.retrieve("Cannot connect to email server on Samsung tablet")
        assert match is not None
        assert "Email" in match.title

    def test_retrieve_smart_switch_issue(self, retriever):
        match = retriever.retrieve("Transferring secure folder data to my new phone with Smart Switch")
        assert match is not None
        assert "Smart Switch" in match.title or "Secure folder" in match.title

    def test_retrieve_black_screen_issue(self, retriever):
        match = retriever.retrieve("Phone display is completely black and won't turn on")
        assert match is not None
        assert "Blank or black" in match.title or "Access your Galaxy" in match.title

    def test_out_of_domain_query_returns_none(self, retriever):
        # Irrelevant or nonsensical queries must not match any article
        assert retriever.retrieve("How to make chocolate chip pancakes") is None
        assert retriever.retrieve("Tell me a funny joke about dogs") is None
        assert retriever.retrieve("Who won the soccer world cup in 1994") is None

    def test_empty_or_whitespace_query_returns_none(self, retriever):
        assert retriever.retrieve("") is None
        assert retriever.retrieve("   ") is None
        assert retriever.retrieve("??? !!!") is None
