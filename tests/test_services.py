"""
tests/test_services.py
-----------------------
Unit tests for the four new ScholarAI study services:
  - StudySummaryService
  - FlashcardService
  - QuizService
  - StudyPlanService

Run with:
    pytest tests/test_services.py -v
"""

from __future__ import annotations

import pytest
from datetime import date, timedelta

from app.services.study_summary_service import StudySummaryService, SummaryResult
from app.services.flashcard_service import FlashcardService, Flashcard
from app.services.quiz_service import QuizService, QuizQuestion
from app.services.study_plan_service import StudyPlanService, StudyPlan, DaySlot

# ---------------------------------------------------------------------------
# Shared fixture text — long enough to exercise all services
# ---------------------------------------------------------------------------

SAMPLE_TEXT = (
    "The Transformer architecture was introduced by Vaswani et al. in 2017. "
    "It relies entirely on attention mechanisms to draw global dependencies between input and output. "
    "Self-attention allows the model to consider all positions in the sequence simultaneously. "
    "This parallelism makes training significantly faster than recurrent approaches. "
    "BERT is a bidirectional model pre-trained using masked language modelling. "
    "GPT models are autoregressive and predict the next token given all previous tokens. "
    "Fine-tuning a pre-trained model on downstream tasks requires far less labelled data. "
    "Positional encoding is added to the input embeddings to retain sequence order information. "
    "The encoder maps an input sequence to a continuous representation. "
    "The decoder generates an output sequence from the encoder representation one token at a time."
)

SHORT_TEXT = "AI is great."  # too short for most services to produce output


# ===========================================================================
# StudySummaryService
# ===========================================================================

class TestStudySummaryService:

    def setup_method(self):
        self.svc = StudySummaryService(num_sentences=3, num_key_points=5)

    def test_returns_summary_result(self):
        result = self.svc.summarise(SAMPLE_TEXT)
        assert isinstance(result, SummaryResult)

    def test_summary_is_shorter_than_original(self):
        result = self.svc.summarise(SAMPLE_TEXT)
        assert result.word_count_summary < result.word_count_original

    def test_key_points_count(self):
        result = self.svc.summarise(SAMPLE_TEXT)
        assert len(result.key_points) <= 5

    def test_key_points_are_strings(self):
        result = self.svc.summarise(SAMPLE_TEXT)
        assert all(isinstance(kp, str) for kp in result.key_points)

    def test_word_counts_are_positive(self):
        result = self.svc.summarise(SAMPLE_TEXT)
        assert result.word_count_original > 0
        assert result.word_count_summary > 0

    def test_empty_text_returns_empty_result(self):
        result = self.svc.summarise("")
        assert result.summary == ""
        assert result.key_points == []
        assert result.word_count_original == 0

    def test_to_dict_keys(self):
        result = self.svc.summarise(SAMPLE_TEXT)
        d = result.to_dict()
        assert set(d.keys()) == {"summary", "key_points", "word_count_original", "word_count_summary"}

    def test_single_sentence_text(self):
        result = self.svc.summarise("Neural networks learn representations from data.")
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0


# ===========================================================================
# FlashcardService
# ===========================================================================

class TestFlashcardService:

    def setup_method(self):
        self.svc = FlashcardService(max_cards=5)

    def test_returns_list(self):
        cards = self.svc.generate(SAMPLE_TEXT)
        assert isinstance(cards, list)

    def test_cards_are_flashcard_instances(self):
        cards = self.svc.generate(SAMPLE_TEXT)
        assert all(isinstance(c, Flashcard) for c in cards)

    def test_max_cards_respected(self):
        cards = self.svc.generate(SAMPLE_TEXT, max_cards=3)
        assert len(cards) <= 3

    def test_question_contains_blank(self):
        cards = self.svc.generate(SAMPLE_TEXT)
        for card in cards:
            assert "______" in card.question

    def test_answer_is_non_empty(self):
        cards = self.svc.generate(SAMPLE_TEXT)
        for card in cards:
            assert card.answer.strip() != ""

    def test_empty_text_returns_empty_list(self):
        assert self.svc.generate("") == []

    def test_to_dict_keys(self):
        cards = self.svc.generate(SAMPLE_TEXT, max_cards=1)
        if cards:
            d = cards[0].to_dict()
            assert set(d.keys()) == {"question", "answer", "hint", "source_sentence"}

    def test_override_max_cards_per_call(self):
        # Instance default is 5; override to 1 for this call
        cards = self.svc.generate(SAMPLE_TEXT, max_cards=1)
        assert len(cards) <= 1


# ===========================================================================
# QuizService
# ===========================================================================

class TestQuizService:

    def setup_method(self):
        # Fixed seed for reproducible distractor selection
        self.svc = QuizService(num_mcq=3, num_short=2, seed=42)

    def test_returns_list(self):
        questions = self.svc.generate(SAMPLE_TEXT)
        assert isinstance(questions, list)

    def test_question_instances(self):
        questions = self.svc.generate(SAMPLE_TEXT)
        assert all(isinstance(q, QuizQuestion) for q in questions)

    def test_mcq_has_four_choices(self):
        questions = self.svc.generate(SAMPLE_TEXT)
        mcqs = [q for q in questions if q.kind == "mcq"]
        for q in mcqs:
            assert len(q.choices) == 4

    def test_correct_answer_in_mcq_choices(self):
        questions = self.svc.generate(SAMPLE_TEXT)
        for q in [q for q in questions if q.kind == "mcq"]:
            assert q.correct_answer in q.choices

    def test_short_answer_has_empty_choices(self):
        questions = self.svc.generate(SAMPLE_TEXT)
        for q in [q for q in questions if q.kind == "short_answer"]:
            assert q.choices == []

    def test_kinds_are_valid(self):
        questions = self.svc.generate(SAMPLE_TEXT)
        for q in questions:
            assert q.kind in ("mcq", "short_answer")

    def test_override_counts_per_call(self):
        questions = self.svc.generate(SAMPLE_TEXT, num_mcq=1, num_short=1)
        assert len([q for q in questions if q.kind == "mcq"]) <= 1
        assert len([q for q in questions if q.kind == "short_answer"]) <= 1

    def test_empty_text_returns_empty_list(self):
        assert self.svc.generate("") == []

    def test_to_dict_keys(self):
        questions = self.svc.generate(SAMPLE_TEXT, num_mcq=1, num_short=0)
        if questions:
            d = questions[0].to_dict()
            assert set(d.keys()) == {"kind", "question", "correct_answer", "choices", "explanation"}


# ===========================================================================
# StudyPlanService
# ===========================================================================

class TestStudyPlanService:

    def setup_method(self):
        self.svc = StudyPlanService()
        self.topics = [
            "Transformers", "Attention Mechanisms", "BERT", "GPT",
            "Fine-tuning", "Positional Encoding",
        ]
        self.exam_date = date.today() + timedelta(days=7)

    def test_returns_study_plan(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        assert isinstance(plan, StudyPlan)

    def test_schedule_contains_day_slots(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        assert all(isinstance(s, DaySlot) for s in plan.schedule)

    def test_revision_day_last_before_exam(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        last_slot = plan.schedule[-1]
        assert last_slot.date == self.exam_date - timedelta(days=1)
        assert "Revision" in last_slot.session_label

    def test_all_topics_appear_in_revision_day(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        revision_slot = plan.schedule[-1]
        for topic in self.topics:
            assert topic in revision_slot.topics

    def test_total_hours_positive(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        assert plan.total_study_hours > 0

    def test_exam_date_stored_correctly(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        assert plan.exam_date == self.exam_date

    def test_raises_for_past_exam_date(self):
        with pytest.raises(ValueError, match="must be strictly after"):
            self.svc.generate(date.today(), hours_per_day=2.0, topics=self.topics)

    def test_raises_for_empty_topics(self):
        with pytest.raises(ValueError, match="topics must contain"):
            self.svc.generate(self.exam_date, hours_per_day=2.0, topics=[])

    def test_to_dict_keys(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        d = plan.to_dict()
        assert set(d.keys()) == {
            "exam_date", "total_study_days", "total_study_hours",
            "topics", "schedule", "warnings",
        }

    def test_day_slot_to_dict_keys(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=2.0, topics=self.topics)
        d = plan.schedule[0].to_dict()
        assert set(d.keys()) == {"date", "topics", "hours", "session_label", "tip"}

    def test_single_topic(self):
        plan = self.svc.generate(self.exam_date, hours_per_day=1.5, topics=["Deep Learning"])
        assert isinstance(plan, StudyPlan)
        assert len(plan.schedule) >= 1

    def test_one_day_before_exam(self):
        tomorrow = date.today() + timedelta(days=1)
        plan = self.svc.generate(tomorrow, hours_per_day=3.0, topics=self.topics)
        # Only one day slot should be generated
        assert len(plan.schedule) == 1
        assert "Revision" in plan.schedule[0].session_label
        assert len(plan.warnings) > 0
