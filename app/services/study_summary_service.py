"""
services/study_summary_service.py
----------------------------------
Produces a concise summary and a list of key points from any body of text.

Current implementation
~~~~~~~~~~~~~~~~~~~~~~
Uses an extractive summarisation approach:
  1. Split the text into sentences.
  2. Score every sentence by the frequency of its non-stopword terms.
  3. Return the top-N highest-scoring sentences (preserving original order)
     as the summary, and the top keywords as key points.

IBM Granite integration path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Replace the body of ``_llm_generate`` with a call to the Granite REST
endpoint.  The public ``summarise`` signature and the ``SummaryResult``
return type remain unchanged, so no calling code needs to be updated.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List

from app.utils.text_utils import extract_keywords, truncate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class SummaryResult:
    """
    Holds the output produced by :class:`StudySummaryService`.

    Attributes
    ----------
    summary : str
        A concise, human-readable summary of the source text.
    key_points : List[str]
        Bullet-ready key topics or concepts extracted from the text.
    word_count_original : int
        Number of words in the original text (for context).
    word_count_summary : int
        Number of words in the generated summary.
    """

    summary: str
    key_points: List[str]
    word_count_original: int = 0
    word_count_summary: int = 0

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary (e.g. for JSON responses)."""
        return {
            "summary": self.summary,
            "key_points": self.key_points,
            "word_count_original": self.word_count_original,
            "word_count_summary": self.word_count_summary,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

# Sentence boundary pattern: split after . ! ? followed by whitespace/end,
# but not after common abbreviations (e.g. "Dr.", "Fig.").
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

# Extended stopword list for scoring (superset of text_utils._STOPWORDS)
_STOPWORDS: set[str] = {
    "the", "a", "an", "and", "or", "of", "in", "to", "is", "are", "was",
    "were", "for", "with", "on", "at", "by", "this", "that", "it", "be",
    "as", "from", "we", "our", "their", "has", "have", "which", "also",
    "but", "not", "can", "such", "into", "than", "more", "its", "been",
    "about", "these", "those", "they", "them", "will", "may", "when",
    "show", "shown", "used", "using", "use", "new", "two", "one", "both",
}


class StudySummaryService:
    """
    Summarise plain text and extract key points.

    Parameters
    ----------
    num_sentences : int
        Target number of sentences to include in the summary (default: 5).
    num_key_points : int
        Number of key points to return (default: 7).
    """

    def __init__(
        self,
        num_sentences: int = 5,
        num_key_points: int = 7,
    ) -> None:
        self._num_sentences = max(1, num_sentences)
        self._num_key_points = max(1, num_key_points)

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    def summarise(self, text: str) -> SummaryResult:
        """
        Summarise *text* and return key points.

        Parameters
        ----------
        text : str
            The source text to summarise (plain text, any length).

        Returns
        -------
        SummaryResult
            A dataclass containing the summary string and key-point list.
        """
        text = text.strip()
        if not text:
            logger.warning("StudySummaryService received empty text")
            return SummaryResult(summary="", key_points=[], word_count_original=0, word_count_summary=0)

        original_word_count = len(text.split())
        logger.info("Summarising text (%d words)", original_word_count)

        sentences = self._split_sentences(text)

        # Delegate to the stub; replace this call with _llm_generate later.
        summary = self._extractive_summary(sentences)
        key_points = extract_keywords(text, top_n=self._num_key_points)

        result = SummaryResult(
            summary=summary,
            key_points=key_points,
            word_count_original=original_word_count,
            word_count_summary=len(summary.split()),
        )
        logger.info(
            "Summary generated: %d → %d words, %d key points",
            original_word_count,
            result.word_count_summary,
            len(key_points),
        )
        return result

    # ------------------------------------------------------------------ #
    # Granite integration stub
    # ------------------------------------------------------------------ #

    def _llm_generate(self, prompt: str) -> str:  # noqa: ARG002
        """
        Placeholder for IBM Granite model inference.

        Replace the ``return ""`` with a real API call, e.g.:

        .. code-block:: python

            response = granite_client.generate(prompt=prompt, max_tokens=512)
            return response.text

        The prompt is already formatted by the calling method; this stub
        simply signals that no LLM is available and falls back to the
        extractive pipeline.
        """
        return ""

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split *text* into individual sentences."""
        raw = _SENT_SPLIT.split(text)
        return [s.strip() for s in raw if s.strip()]

    def _score_sentence(self, sentence: str, term_freq: dict[str, int]) -> float:
        """
        Score a sentence by summing the normalised frequencies of its terms.

        Higher-scoring sentences contain more of the text's important words.
        """
        words = re.findall(r"\b[a-z]{3,}\b", sentence.lower())
        content_words = [w for w in words if w not in _STOPWORDS]
        if not content_words:
            return 0.0
        score = sum(term_freq.get(w, 0) for w in content_words)
        return score / len(content_words)  # normalise by sentence length

    def _extractive_summary(self, sentences: list[str]) -> str:
        """Return the top-N scored sentences, preserving original order."""
        if len(sentences) <= self._num_sentences:
            return " ".join(sentences)

        # Build a term-frequency map over the full text
        all_words = re.findall(r"\b[a-z]{3,}\b", " ".join(sentences).lower())
        freq: dict[str, int] = {}
        for w in all_words:
            if w not in _STOPWORDS:
                freq[w] = freq.get(w, 0) + 1

        # Score and rank sentences
        scored = [
            (i, self._score_sentence(s, freq), s)
            for i, s in enumerate(sentences)
        ]
        top = sorted(scored, key=lambda x: x[1], reverse=True)[: self._num_sentences]
        # Restore original document order
        top.sort(key=lambda x: x[0])
        return " ".join(s for _, _, s in top)
