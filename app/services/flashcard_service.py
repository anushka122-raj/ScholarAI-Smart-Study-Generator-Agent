"""
services/flashcard_service.py
------------------------------
Generates question-and-answer flashcards from plain text.

Current implementation
~~~~~~~~~~~~~~~~~~~~~~
Rule-based extraction pipeline:
  1. Split text into sentences.
  2. Filter to sentences with enough information density
     (minimum word count and at least one recognised "key term").
  3. For each qualifying sentence, detect the most salient term (first
     capitalised multi-word phrase, or the top-frequency keyword).
  4. Construct a *question* by blanking the term, and use the full sentence
     as the *answer*.

IBM Granite integration path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Replace the body of ``_llm_generate`` with a real model call.  The public
``generate`` method signature and the ``Flashcard`` dataclass are stable.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from app.utils.text_utils import extract_keywords

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class Flashcard:
    """
    A single question-answer flashcard.

    Attributes
    ----------
    question : str
        The question or cloze-deletion prompt shown to the learner.
    answer : str
        The full answer or the original sentence for context.
    hint : str
        An optional hint (defaults to empty string).
    source_sentence : str
        The original sentence the card was derived from.
    """

    question: str
    answer: str
    hint: str = ""
    source_sentence: str = ""

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "question": self.question,
            "answer": self.answer,
            "hint": self.hint,
            "source_sentence": self.source_sentence,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

# Matches a capitalised proper noun or technical phrase (2–5 words)
_PROPER_PHRASE = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,4})\b")

# Minimum number of words a sentence must have to be card-worthy
_MIN_SENTENCE_WORDS = 8

# Extended stopword set used when picking the salient term
_STOPWORDS: set[str] = {
    "the", "a", "an", "and", "or", "of", "in", "to", "is", "are", "was",
    "were", "for", "with", "on", "at", "by", "this", "that", "it", "be",
    "as", "from", "we", "our", "their", "has", "have", "which", "also",
    "but", "not", "can", "such", "into", "than", "more", "its", "been",
    "about", "these", "those", "they", "them", "will", "may", "when",
}


class FlashcardService:
    """
    Generate question-answer flashcards from input text.

    Parameters
    ----------
    max_cards : int
        Upper bound on the number of flashcards returned per call
        (default: 10).  The actual count may be lower if the text does not
        contain enough information-rich sentences.
    """

    def __init__(self, max_cards: int = 10) -> None:
        self._max_cards = max(1, max_cards)

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    def generate(self, text: str, max_cards: Optional[int] = None) -> List[Flashcard]:
        """
        Generate flashcards from *text*.

        Parameters
        ----------
        text : str
            Source text (e.g. a textbook paragraph or paper abstract).
        max_cards : int, optional
            Override the instance-level ``max_cards`` for this call.

        Returns
        -------
        List[Flashcard]
            Ordered list of generated flashcards (may be empty if the text
            is too short or featureless).
        """
        text = text.strip()
        if not text:
            logger.warning("FlashcardService received empty text")
            return []

        limit = max_cards if max_cards is not None else self._max_cards
        logger.info("Generating up to %d flashcard(s)", limit)

        sentences = self._split_sentences(text)
        global_keywords = extract_keywords(text, top_n=20)

        cards: List[Flashcard] = []
        for sentence in sentences:
            if len(cards) >= limit:
                break
            card = self._sentence_to_card(sentence, global_keywords)
            if card is not None:
                cards.append(card)

        logger.info("Generated %d flashcard(s)", len(cards))
        return cards

    # ------------------------------------------------------------------ #
    # Granite integration stub
    # ------------------------------------------------------------------ #

    def _llm_generate(self, prompt: str) -> str:  # noqa: ARG002
        """
        Placeholder for IBM Granite model inference.

        When wired up, this method should accept the formatted *prompt* and
        return the raw model output (a JSON array of {question, answer}
        objects is recommended for easy parsing).  The calling method
        ``generate`` will then delegate to ``_llm_generate`` instead of the
        rule-based pipeline.
        """
        return ""

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split *text* into individual sentences."""
        raw = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        return [s.strip() for s in raw if s.strip()]

    def _sentence_to_card(
        self, sentence: str, global_keywords: list[str]
    ) -> Optional[Flashcard]:
        """
        Attempt to derive a single flashcard from *sentence*.

        Returns ``None`` if the sentence does not meet the quality bar.
        """
        words = sentence.split()
        if len(words) < _MIN_SENTENCE_WORDS:
            return None

        term = self._extract_salient_term(sentence, global_keywords)
        if not term:
            return None

        # Build a cloze-deletion question
        question = self._make_question(sentence, term)
        return Flashcard(
            question=question,
            answer=term,
            hint=f'Found in: "{self._short_context(sentence, term)}"',
            source_sentence=sentence,
        )

    @staticmethod
    def _extract_salient_term(sentence: str, global_keywords: list[str]) -> str:
        """
        Pick the most salient term in *sentence*.

        Priority order:
        1. First capitalised multi-word proper phrase (≥ 2 words).
        2. First match from the global keyword list present in the sentence.
        3. First single capitalised word (excluding sentence-start).
        """
        # 1. Proper multi-word phrase
        for match in _PROPER_PHRASE.finditer(sentence):
            phrase = match.group(1)
            if len(phrase.split()) >= 2:
                return phrase

        # 2. Global keyword present in sentence
        sentence_lower = sentence.lower()
        for kw in global_keywords:
            if kw in sentence_lower and kw not in _STOPWORDS:
                return kw

        # 3. First capitalised single word that is not the sentence opener
        words = sentence.split()
        for word in words[1:]:
            clean = re.sub(r"[^\w]", "", word)
            if clean and clean[0].isupper() and len(clean) > 2:
                return clean

        return ""

    @staticmethod
    def _make_question(sentence: str, term: str) -> str:
        """Replace the first occurrence of *term* with a blank."""
        blanked = sentence.replace(term, "______", 1)
        if blanked == sentence:
            # Case-insensitive fallback
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            blanked = pattern.sub("______", sentence, count=1)
        return f"Fill in the blank: {blanked}"

    @staticmethod
    def _short_context(sentence: str, term: str) -> str:
        """Return a short excerpt around *term* for use as a hint."""
        idx = sentence.lower().find(term.lower())
        if idx == -1:
            return sentence[:60]
        start = max(0, idx - 20)
        end = min(len(sentence), idx + len(term) + 20)
        return ("…" if start > 0 else "") + sentence[start:end] + ("…" if end < len(sentence) else "")
