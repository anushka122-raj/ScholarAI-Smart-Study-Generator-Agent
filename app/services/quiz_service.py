"""
services/quiz_service.py
-------------------------
Generates multiple-choice (MCQ) and short-answer questions from plain text.

Current implementation
~~~~~~~~~~~~~~~~~~~~~~
Rule-based question generation pipeline:

MCQ
  1. Select information-dense sentences (verb + content-word density).
  2. For each sentence, pick the most salient term as the correct answer.
  3. Blank the term in the sentence to form the question stem.
  4. Build three distractor options by sampling other top keywords from
     the text that are NOT the correct answer.
  5. Shuffle the four choices before returning.

Short-answer
  1. Select sentences that begin (or contain a clause beginning) with a
     subject-verb structure.
  2. Convert each to a "What is X?" or "Explain Y." prompt.

IBM Granite integration path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Replace the body of ``_llm_generate`` with a real model call.  Public
method signatures and the ``QuizQuestion`` dataclass are stable.
"""

from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from app.utils.text_utils import extract_keywords

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

QuestionKind = Literal["mcq", "short_answer"]


@dataclass
class QuizQuestion:
    """
    A single quiz question — either multiple-choice or short-answer.

    Attributes
    ----------
    kind : QuestionKind
        ``"mcq"`` for multiple-choice, ``"short_answer"`` for open-ended.
    question : str
        The question stem shown to the learner.
    correct_answer : str
        The model (correct) answer.
    choices : List[str]
        For MCQ: four shuffled options including the correct answer.
        For short-answer: an empty list.
    explanation : str
        A brief explanation or the source sentence for reference.
    """

    kind: QuestionKind
    question: str
    correct_answer: str
    choices: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "kind": self.kind,
            "question": self.question,
            "correct_answer": self.correct_answer,
            "choices": self.choices,
            "explanation": self.explanation,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

_STOPWORDS: set[str] = {
    "the", "a", "an", "and", "or", "of", "in", "to", "is", "are", "was",
    "were", "for", "with", "on", "at", "by", "this", "that", "it", "be",
    "as", "from", "we", "our", "their", "has", "have", "which", "also",
    "but", "not", "can", "such", "into", "than", "more", "its", "been",
    "about", "these", "those", "they", "them", "will", "may", "when",
    "show", "shown", "used", "using", "use", "new", "two", "one", "both",
}

# Verbs that signal a definition-like sentence, useful for short-answer
_DEFINITION_VERBS = re.compile(
    r"\b(is|are|was|were|refers to|defined as|means|describes|represents)\b",
    re.IGNORECASE,
)

_MIN_SENTENCE_WORDS = 8
_NUM_MCQ_DISTRACTORS = 3   # correct + 3 distractors = 4 choices total


class QuizService:
    """
    Generate MCQ and short-answer questions from input text.

    Parameters
    ----------
    num_mcq : int
        Number of multiple-choice questions to generate (default: 5).
    num_short : int
        Number of short-answer questions to generate (default: 3).
    seed : int or None
        Random seed for reproducible distractor shuffling.  Pass ``None``
        (the default) for non-deterministic output.
    """

    def __init__(
        self,
        num_mcq: int = 5,
        num_short: int = 3,
        seed: Optional[int] = None,
    ) -> None:
        self._num_mcq = max(0, num_mcq)
        self._num_short = max(0, num_short)
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    def generate(
        self,
        text: str,
        num_mcq: Optional[int] = None,
        num_short: Optional[int] = None,
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions from *text*.

        Parameters
        ----------
        text : str
            Source text to derive questions from.
        num_mcq : int, optional
            Override instance-level MCQ count for this call.
        num_short : int, optional
            Override instance-level short-answer count for this call.

        Returns
        -------
        List[QuizQuestion]
            MCQ questions first, short-answer questions second.
        """
        text = text.strip()
        if not text:
            logger.warning("QuizService received empty text")
            return []

        mcq_limit = num_mcq if num_mcq is not None else self._num_mcq
        short_limit = num_short if num_short is not None else self._num_short

        logger.info("Generating %d MCQ + %d short-answer question(s)", mcq_limit, short_limit)

        sentences = self._split_sentences(text)
        keywords = extract_keywords(text, top_n=30)

        questions: List[QuizQuestion] = []
        questions.extend(self._build_mcq(sentences, keywords, mcq_limit))
        questions.extend(self._build_short_answer(sentences, keywords, short_limit))

        logger.info("Generated %d question(s) total", len(questions))
        return questions

    # ------------------------------------------------------------------ #
    # Granite integration stub
    # ------------------------------------------------------------------ #

    def _llm_generate(self, prompt: str) -> str:  # noqa: ARG002
        """
        Placeholder for IBM Granite model inference.

        The expected output format is a JSON array of objects with keys
        ``kind``, ``question``, ``correct_answer``, ``choices``, and
        ``explanation``.  Parse the JSON inside ``generate`` and skip the
        rule-based pipeline entirely once this is wired up.
        """
        return ""

    # ------------------------------------------------------------------ #
    # Private — MCQ helpers
    # ------------------------------------------------------------------ #

    def _build_mcq(
        self, sentences: list[str], keywords: list[str], limit: int
    ) -> list[QuizQuestion]:
        """Generate up to *limit* MCQ questions."""
        questions: list[QuizQuestion] = []
        for sentence in sentences:
            if len(questions) >= limit:
                break
            q = self._sentence_to_mcq(sentence, keywords)
            if q is not None:
                questions.append(q)
        return questions

    def _sentence_to_mcq(
        self, sentence: str, keywords: list[str]
    ) -> Optional[QuizQuestion]:
        """Derive one MCQ from *sentence*, or return ``None``."""
        if len(sentence.split()) < _MIN_SENTENCE_WORDS:
            return None

        term = self._pick_term(sentence, keywords)
        if not term:
            return None

        distractors = self._pick_distractors(term, keywords)
        if not distractors:
            return None

        # Blank the term in the sentence to form the stem
        stem = self._blank_term(sentence, term)
        choices = [term] + distractors
        self._rng.shuffle(choices)

        return QuizQuestion(
            kind="mcq",
            question=f"Which term correctly completes the following?\n\n\"{stem}\"",
            correct_answer=term,
            choices=choices,
            explanation=sentence,
        )

    def _pick_distractors(self, correct: str, keywords: list[str]) -> list[str]:
        """
        Choose *_NUM_MCQ_DISTRACTORS* distractor terms from *keywords*.

        Distractors must differ from *correct* and from each other.
        """
        pool = [
            kw for kw in keywords
            if kw.lower() != correct.lower() and kw not in _STOPWORDS
        ]
        if len(pool) < _NUM_MCQ_DISTRACTORS:
            return []
        return self._rng.sample(pool, _NUM_MCQ_DISTRACTORS)

    # ------------------------------------------------------------------ #
    # Private — short-answer helpers
    # ------------------------------------------------------------------ #

    def _build_short_answer(
        self, sentences: list[str], keywords: list[str], limit: int
    ) -> list[QuizQuestion]:
        """Generate up to *limit* short-answer questions."""
        questions: list[QuizQuestion] = []
        # Prefer sentences that contain a definition-style verb
        definition_sentences = [s for s in sentences if _DEFINITION_VERBS.search(s)]
        # Fall back to any sufficiently long sentence
        fallback = [s for s in sentences if s not in definition_sentences]
        candidates = definition_sentences + fallback

        for sentence in candidates:
            if len(questions) >= limit:
                break
            q = self._sentence_to_short_answer(sentence, keywords)
            if q is not None:
                questions.append(q)
        return questions

    def _sentence_to_short_answer(
        self, sentence: str, keywords: list[str]
    ) -> Optional[QuizQuestion]:
        """Derive one short-answer question from *sentence*, or return ``None``."""
        if len(sentence.split()) < _MIN_SENTENCE_WORDS:
            return None

        term = self._pick_term(sentence, keywords)
        if not term:
            return None

        question_text = self._formulate_short_question(sentence, term)
        return QuizQuestion(
            kind="short_answer",
            question=question_text,
            correct_answer=sentence,  # full sentence is the model answer
            choices=[],
            explanation=f"Refer to the source material discussing '{term}'.",
        )

    @staticmethod
    def _formulate_short_question(sentence: str, term: str) -> str:
        """
        Convert *sentence* into a short-answer prompt about *term*.

        Heuristic: if the sentence contains a definition verb, ask
        "What is <term>?"; otherwise ask the learner to explain it.
        """
        if _DEFINITION_VERBS.search(sentence):
            return f"What is {term}? Explain in your own words."
        return f"Explain the concept of '{term}' as described in the text."

    # ------------------------------------------------------------------ #
    # Shared private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split *text* into sentences."""
        raw = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        return [s.strip() for s in raw if s.strip()]

    @staticmethod
    def _pick_term(sentence: str, keywords: list[str]) -> str:
        """
        Select the highest-priority keyword present in *sentence*.

        Checks global keywords first (ordered by frequency), then falls
        back to the first capitalised word that is not the sentence opener.
        """
        sentence_lower = sentence.lower()
        for kw in keywords:
            if kw.lower() in sentence_lower and kw not in _STOPWORDS:
                return kw

        # Capitalised-word fallback (skip first word — it's always capitalised)
        words = sentence.split()
        for word in words[1:]:
            clean = re.sub(r"[^\w]", "", word)
            if clean and clean[0].isupper() and len(clean) > 2:
                return clean

        return ""

    @staticmethod
    def _blank_term(sentence: str, term: str) -> str:
        """Replace the first occurrence of *term* in *sentence* with ______."""
        blanked = sentence.replace(term, "______", 1)
        if blanked == sentence:
            blanked = re.sub(re.escape(term), "______", sentence, count=1, flags=re.IGNORECASE)
        return blanked
