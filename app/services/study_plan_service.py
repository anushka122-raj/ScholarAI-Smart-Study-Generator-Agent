"""
services/study_plan_service.py
--------------------------------
Generates a personalised, day-wise study schedule.

Current implementation
~~~~~~~~~~~~~~~~~~~~~~
Deterministic scheduler:
  1. Validate inputs (exam_date must be in the future, topics non-empty).
  2. Compute the number of available study days (today → exam_date - 1).
  3. Reserve the final day before the exam as a full-revision day.
  4. Distribute the remaining topics across the remaining days using a
     round-robin assignment weighted by ``hours_per_day``.
  5. Attach a short "focus tip" to each day slot based on the topics
     assigned to it.

IBM Granite integration path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Replace ``_llm_generate`` with a real model call to produce a richer,
narrative-style study plan.  The public ``generate`` signature and the
``StudyPlan`` / ``DaySlot`` dataclasses remain unchanged.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class DaySlot:
    """
    Represents a single day in the study schedule.

    Attributes
    ----------
    date : date
        The calendar date for this study session.
    topics : List[str]
        Topics to cover on this day.
    hours : float
        Recommended study hours for this day.
    session_label : str
        Human-readable label, e.g. "Day 1" or "Revision Day".
    tip : str
        A short study tip tailored to the day's topics.
    """

    date: date
    topics: List[str]
    hours: float
    session_label: str = ""
    tip: str = ""

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "date": self.date.isoformat(),
            "topics": self.topics,
            "hours": self.hours,
            "session_label": self.session_label,
            "tip": self.tip,
        }


@dataclass
class StudyPlan:
    """
    A complete study schedule from today until the exam.

    Attributes
    ----------
    exam_date : date
        The target exam date.
    total_study_days : int
        Total days available for study (excluding the exam day itself).
    total_study_hours : float
        Cumulative hours across all scheduled days.
    topics : List[str]
        The full list of topics provided by the caller.
    schedule : List[DaySlot]
        Ordered day-by-day study schedule.
    warnings : List[str]
        Non-fatal advisory messages (e.g. "Only 2 days available for 10 topics").
    """

    exam_date: date
    total_study_days: int
    total_study_hours: float
    topics: List[str]
    schedule: List[DaySlot] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "exam_date": self.exam_date.isoformat(),
            "total_study_days": self.total_study_days,
            "total_study_hours": self.total_study_hours,
            "topics": self.topics,
            "schedule": [slot.to_dict() for slot in self.schedule],
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class StudyPlanService:
    """
    Generate a day-wise study plan given an exam date and topics.

    Parameters
    ----------
    min_hours_per_session : float
        Minimum hours to allocate to any single day (default: 1.0).
    max_topics_per_day : int
        Upper limit on the number of topics assigned to a single day
        (default: 3).  Keeps daily workload manageable.
    """

    def __init__(
        self,
        min_hours_per_session: float = 1.0,
        max_topics_per_day: int = 3,
    ) -> None:
        self._min_hours = max(0.5, min_hours_per_session)
        self._max_topics_per_day = max(1, max_topics_per_day)

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    def generate(
        self,
        exam_date: date,
        hours_per_day: float,
        topics: List[str],
        start_date: date | None = None,
    ) -> StudyPlan:
        """
        Generate a study plan.

        Parameters
        ----------
        exam_date : date
            The date of the exam.  Must be strictly after *start_date*.
        hours_per_day : float
            Number of study hours available each day.
        topics : List[str]
            Ordered list of topics to cover (earlier = higher priority).
        start_date : date, optional
            First day of study.  Defaults to today if not provided.

        Returns
        -------
        StudyPlan
            A complete schedule with one ``DaySlot`` per available day.

        Raises
        ------
        ValueError
            If *exam_date* is not after *start_date*, or *topics* is empty.
        """
        today = start_date or date.today()
        topics = [t.strip() for t in topics if t.strip()]

        # ---- Input validation -------------------------------------------
        if not topics:
            raise ValueError("topics must contain at least one non-empty string.")
        if exam_date <= today:
            raise ValueError(
                f"exam_date ({exam_date}) must be strictly after start_date ({today})."
            )
        if hours_per_day < self._min_hours:
            raise ValueError(
                f"hours_per_day ({hours_per_day}) must be ≥ {self._min_hours}."
            )

        available_days = (exam_date - today).days  # e.g. 7 if exam is in a week
        logger.info(
            "Building study plan: %d topic(s) over %d day(s) @ %.1f h/day",
            len(topics),
            available_days,
            hours_per_day,
        )

        warnings: List[str] = []
        plan = self._build_schedule(
            today=today,
            exam_date=exam_date,
            hours_per_day=hours_per_day,
            topics=topics,
            available_days=available_days,
            warnings=warnings,
        )
        return plan

    # ------------------------------------------------------------------ #
    # Granite integration stub
    # ------------------------------------------------------------------ #

    def _llm_generate(self, prompt: str) -> str:  # noqa: ARG002
        """
        Placeholder for IBM Granite model inference.

        The expected output is a JSON array of DaySlot-compatible dicts.
        When this is wired up, ``generate`` should call ``_llm_generate``,
        parse the JSON result, and construct ``DaySlot`` objects from it
        instead of running ``_build_schedule``.
        """
        return ""

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _build_schedule(
        self,
        today: date,
        exam_date: date,
        hours_per_day: float,
        topics: List[str],
        available_days: int,
        warnings: List[str],
    ) -> StudyPlan:
        """Core scheduling algorithm."""
        schedule: List[DaySlot] = []

        # Edge case: only one day available — cram everything
        if available_days == 1:
            warnings.append(
                "Only 1 day before the exam. All topics assigned to a single revision session."
            )
            slot = DaySlot(
                date=today,
                topics=list(topics),
                hours=hours_per_day,
                session_label="Day 1 — Full Revision",
                tip=self._tip_for_topics(topics, is_revision=True),
            )
            schedule.append(slot)
            return StudyPlan(
                exam_date=exam_date,
                total_study_days=1,
                total_study_hours=hours_per_day,
                topics=list(topics),
                schedule=schedule,
                warnings=warnings,
            )

        # Reserve the last day before the exam for revision
        revision_date = exam_date - timedelta(days=1)
        study_days = available_days - 1  # days available for new-topic study

        if study_days < 1:
            # Available_days == 1 case is already handled above, so this
            # branch is theoretically unreachable, but guard it anyway.
            study_days = 1

        # Warn if topics outnumber study days significantly
        topics_per_day_ideal = len(topics) / study_days
        if topics_per_day_ideal > self._max_topics_per_day:
            warnings.append(
                f"You have {len(topics)} topic(s) for {study_days} study day(s). "
                f"Consider spreading over more days or reducing topics "
                f"({topics_per_day_ideal:.1f} topics/day required)."
            )

        # Distribute topics round-robin across study days
        topic_chunks = self._distribute_topics(topics, study_days)

        total_hours = 0.0
        current_date = today

        for day_index, chunk in enumerate(topic_chunks, start=1):
            if current_date >= revision_date:
                current_date = revision_date - timedelta(days=study_days - day_index + 1)

            slot = DaySlot(
                date=current_date,
                topics=chunk,
                hours=hours_per_day,
                session_label=f"Day {day_index}",
                tip=self._tip_for_topics(chunk, is_revision=False),
            )
            schedule.append(slot)
            total_hours += hours_per_day
            current_date += timedelta(days=1)

        # Revision day slot
        revision_slot = DaySlot(
            date=revision_date,
            topics=list(topics),
            hours=hours_per_day,
            session_label="Revision Day",
            tip=(
                "Review all topics using your flashcards and quiz yourself. "
                "Focus extra time on any areas that felt unclear during earlier sessions."
            ),
        )
        schedule.append(revision_slot)
        total_hours += hours_per_day

        return StudyPlan(
            exam_date=exam_date,
            total_study_days=available_days,
            total_study_hours=round(total_hours, 2),
            topics=list(topics),
            schedule=schedule,
            warnings=warnings,
        )

    def _distribute_topics(
        self, topics: List[str], num_days: int
    ) -> list[list[str]]:
        """
        Divide *topics* into *num_days* approximately equal chunks.

        Each chunk contains at most ``_max_topics_per_day`` topics.
        If there are more topics than ``num_days * max_topics_per_day``,
        the excess topics are appended to the last day (and a warning
        is already raised by the caller).
        """
        chunk_size = math.ceil(len(topics) / num_days)
        chunk_size = min(chunk_size, self._max_topics_per_day)

        chunks: list[list[str]] = []
        for i in range(0, len(topics), chunk_size):
            chunks.append(topics[i : i + chunk_size])

        # Pad with empty chunks if we have fewer chunks than days
        while len(chunks) < num_days:
            chunks.append([])

        # Trim extra chunks back onto the last real chunk
        while len(chunks) > num_days:
            overflow = chunks.pop()
            chunks[-1].extend(overflow)

        return chunks[:num_days]

    @staticmethod
    def _tip_for_topics(topics: List[str], *, is_revision: bool) -> str:
        """Return a short, context-aware study tip for the given topics."""
        if is_revision:
            joined = ", ".join(topics[:3])
            suffix = " and more" if len(topics) > 3 else ""
            return (
                f"Revise {joined}{suffix}. Use active recall — close your notes "
                "and try to write down everything you remember before checking."
            )

        if not topics:
            return "Use this session for catch-up or extra practice."

        primary = topics[0]
        if len(topics) == 1:
            return (
                f"Deep-dive into '{primary}'. Aim to produce a one-page summary "
                "or a mind-map by the end of the session."
            )

        secondary = topics[1] if len(topics) > 1 else ""
        return (
            f"Start with '{primary}' (spend ~60% of your time), "
            f"then move to '{secondary}'. End with a quick self-test."
        )
