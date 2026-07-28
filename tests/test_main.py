"""
tests/test_main.py
------------------
Basic unit tests for core ScholarAI components.

Run with:
    pytest tests/ -v
"""

import pytest
from app.models.paper import Paper
from app.utils.text_utils import sanitise_query, truncate, extract_keywords


# ---------------------------------------------------------------------------
# Paper model tests
# ---------------------------------------------------------------------------

class TestPaper:
    """Tests for the Paper dataclass."""

    def _make_paper(self, **kwargs) -> Paper:
        defaults = dict(
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer"],
            year=2017,
            abstract="We propose a new simple network architecture, the Transformer. " * 5,
        )
        defaults.update(kwargs)
        return Paper(**defaults)

    def test_short_abstract_truncates(self):
        paper = self._make_paper()
        result = paper.short_abstract(max_chars=30)
        assert len(result) <= 33  # 30 chars + possible "…"
        assert result.endswith("…")

    def test_short_abstract_no_truncation_needed(self):
        paper = self._make_paper(abstract="Short abstract.")
        assert paper.short_abstract() == "Short abstract."

    def test_to_dict_round_trip(self):
        paper = self._make_paper(doi="10.1234/test", citation_count=42)
        d = paper.to_dict()
        restored = Paper.from_dict(d)
        assert restored.title == paper.title
        assert restored.doi == paper.doi
        assert restored.citation_count == paper.citation_count

    def test_from_dict_missing_fields_use_defaults(self):
        paper = Paper.from_dict({"title": "Minimal Paper"})
        assert paper.authors == []
        assert paper.year is None
        assert paper.abstract == ""


# ---------------------------------------------------------------------------
# text_utils tests
# ---------------------------------------------------------------------------

class TestSanitiseQuery:
    def test_strips_whitespace(self):
        assert sanitise_query("  hello  ") == "hello"

    def test_collapses_internal_spaces(self):
        assert sanitise_query("large   language  models") == "large language models"

    def test_empty_string(self):
        assert sanitise_query("") == ""

    def test_removes_special_chars(self):
        result = sanitise_query("transformers! @ 2023?")
        assert "!" not in result
        assert "@" not in result


class TestTruncate:
    def test_does_not_truncate_short_text(self):
        assert truncate("hello world", max_words=5) == "hello world"

    def test_truncates_long_text(self):
        text = " ".join(["word"] * 20)
        result = truncate(text, max_words=10)
        assert result.endswith("…")
        # "…" is appended directly to the 10th word — split() gives exactly 10 tokens
        assert len(result.split()) == 10


class TestExtractKeywords:
    def test_returns_list(self):
        kws = extract_keywords("deep learning models for natural language processing")
        assert isinstance(kws, list)

    def test_respects_top_n(self):
        text = "neural networks deep learning models " * 10
        kws = extract_keywords(text, top_n=3)
        assert len(kws) <= 3
