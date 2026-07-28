"""
main.py
-------
Entry point for ScholarAI.

Run from the project root with:
    python -m app.main

Or, if you add a CLI wrapper later:
    scholarai search "transformer architectures"
"""

import logging
from datetime import date, timedelta

from app.config import config
from app.services.search_service import SearchService
from app.services.study_summary_service import StudySummaryService
from app.services.flashcard_service import FlashcardService
from app.services.quiz_service import QuizService
from app.services.study_plan_service import StudyPlanService

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback sample text used when the user provides no input
# ---------------------------------------------------------------------------
_SAMPLE_TEXT = (
    "Machine learning is a subset of artificial intelligence that enables systems to learn "
    "from data and improve their performance without being explicitly programmed. "
    "Deep learning is a specialised branch of machine learning that uses neural networks "
    "with many layers to model complex patterns in large datasets. "
    "Neural networks are computational models inspired by the structure of the human brain, "
    "consisting of interconnected nodes organised into layers. "
    "Natural language processing, or NLP, is a field of AI focused on enabling machines to "
    "understand, interpret, and generate human language. "
    "Transformer models have revolutionised NLP by replacing recurrent architectures with "
    "self-attention mechanisms that capture long-range dependencies more effectively. "
    "Transfer learning allows a model pre-trained on a large corpus to be fine-tuned on a "
    "smaller, task-specific dataset, dramatically reducing the need for labelled data. "
    "Reinforcement learning trains an agent to take actions in an environment by maximising "
    "a cumulative reward signal, and has achieved superhuman performance in games like Go and Chess."
)

# Width of the printed rule lines
_W = 60


# ---------------------------------------------------------------------------
# Private demo helpers
# ---------------------------------------------------------------------------

def _rule(char: str = "─") -> str:
    """Return a full-width rule string."""
    return char * _W


def _header(title: str) -> None:
    """Print a prominent section header."""
    print(f"\n{_rule('═')}")
    print(f"  {title}")
    print(_rule("═"))


def _subheader(title: str) -> None:
    """Print a lightweight sub-section header."""
    print(f"\n  {_rule('·')}")
    print(f"  {title}")
    print(f"  {_rule('·')}")


def _demo_summary(text: str) -> None:
    """Run StudySummaryService and print the result."""
    _header("1 / 4  ·  STUDY SUMMARY")
    svc = StudySummaryService(num_sentences=4, num_key_points=6)
    result = svc.summarise(text)

    _subheader("Summary")
    # Wrap long summary text at word boundaries for readability
    words = result.summary.split()
    line, lines = [], []
    for word in words:
        line.append(word)
        if len(" ".join(line)) >= 56:
            lines.append("  " + " ".join(line))
            line = []
    if line:
        lines.append("  " + " ".join(line))
    print("\n".join(lines))
    print(f"\n  ({result.word_count_original} words → {result.word_count_summary} words)")

    _subheader("Key Points")
    for i, point in enumerate(result.key_points, start=1):
        print(f"  {i}. {point}")


def _demo_flashcards(text: str) -> None:
    """Run FlashcardService and print at least three flashcards."""
    _header("2 / 4  ·  FLASHCARDS")
    svc = FlashcardService(max_cards=5)
    cards = svc.generate(text)

    display = cards[:max(3, len(cards))]
    if not display:
        print("  (No flashcards could be generated for the provided text.)")
        return

    for i, card in enumerate(display, start=1):
        print(f"\n  ┌─ Card {i} {'─' * (_W - 10)}")
        print(f"  │  Q: {card.question}")
        print(f"  │  A: {card.answer}")
        if card.hint:
            print(f"  │  💡 {card.hint}")
        print(f"  └{'─' * (_W - 3)}")


def _demo_quiz(text: str) -> None:
    """Run QuizService and print MCQ + short-answer questions."""
    _header("3 / 4  ·  QUIZ QUESTIONS")
    svc = QuizService(num_mcq=3, num_short=2, seed=1)
    questions = svc.generate(text)

    mcqs   = [q for q in questions if q.kind == "mcq"]
    shorts = [q for q in questions if q.kind == "short_answer"]

    _subheader("Multiple-Choice Questions")
    if not mcqs:
        print("  (No MCQ questions generated.)")
    for i, q in enumerate(mcqs, start=1):
        print(f"\n  Q{i}. {q.question}")
        for letter, choice in zip("ABCD", q.choices):
            marker = "✓" if choice == q.correct_answer else " "
            print(f"       {letter}) {choice}  {marker}")
        print(f"       ↳ Source: {q.explanation[:80]}…" if len(q.explanation) > 80
              else f"       ↳ Source: {q.explanation}")

    _subheader("Short-Answer Questions")
    if not shorts:
        print("  (No short-answer questions generated.)")
    for i, q in enumerate(shorts, start=1):
        print(f"\n  Q{i}. {q.question}")
        print(f"       Model answer: {q.correct_answer[:100]}…" if len(q.correct_answer) > 100
              else f"       Model answer: {q.correct_answer}")


def _demo_study_plan() -> None:
    """Run StudyPlanService with fixed demo parameters and print the schedule."""
    _header("4 / 4  ·  STUDY PLAN")

    exam_date    = date.today() + timedelta(days=30)
    hours_per_day = 3.0
    topics = [
        "Machine Learning",
        "Deep Learning",
        "Neural Networks",
        "NLP",
    ]

    print(f"\n  Exam date    : {exam_date.strftime('%d %b %Y')}  ({30} days from today)")
    print(f"  Hours / day  : {hours_per_day:.0f} h")
    print(f"  Topics       : {', '.join(topics)}")

    svc  = StudyPlanService()
    plan = svc.generate(exam_date, hours_per_day=hours_per_day, topics=topics)

    if plan.warnings:
        print()
        for w in plan.warnings:
            print(f"  ⚠  {w}")

    _subheader(
        f"Schedule  ({plan.total_study_days} days · "
        f"{plan.total_study_hours:.0f} h total)"
    )

    # Column widths
    col_date    = 12
    col_label   = 16
    col_topics  = 26
    col_hours   =  6

    header_row = (
        f"  {'Date':<{col_date}} {'Session':<{col_label}} "
        f"{'Topics':<{col_topics}} {'Hours':>{col_hours}}"
    )
    print(f"\n{header_row}")
    print(f"  {'─' * col_date} {'─' * col_label} {'─' * col_topics} {'─' * col_hours}")

    for slot in plan.schedule:
        topics_str = ", ".join(slot.topics)
        if len(topics_str) > col_topics:
            topics_str = topics_str[: col_topics - 1] + "…"
        print(
            f"  {slot.date.strftime('%d %b %Y'):<{col_date}} "
            f"{slot.session_label:<{col_label}} "
            f"{topics_str:<{col_topics}} "
            f"{slot.hours:>{col_hours}.1f}"
        )

    print(f"\n  Tip for Revision Day: {plan.schedule[-1].tip[:120]}")


def _run_smart_study_demo() -> None:
    """
    Interactive Smart Study Generator demonstration.

    Prompts the user to paste study notes.  If the user presses Enter
    immediately (empty input), falls back to the built-in sample text.
    Then runs all four study services in sequence.
    """
    print(f"\n\n{'═' * _W}")
    print("  SMART STUDY GENERATOR  —  Interactive Demo")
    print(f"{'═' * _W}")
    print(
        "\n  Paste your study notes below and press Enter twice when done."
        "\n  (Press Enter immediately to use the built-in sample text.)\n"
    )

    lines = []
    blank_count = 0
    try:
        while True:
            line = input()
            if line == "":
                blank_count += 1
                # First blank line on an empty session → use fallback
                if blank_count == 1 and not lines:
                    break
                # Two consecutive blanks → end of multi-line input
                if blank_count >= 2:
                    break
            else:
                blank_count = 0
                lines.append(line)
    except EOFError:
        pass  # non-interactive environment (e.g. piped input)

    text = " ".join(lines).strip() or _SAMPLE_TEXT

    if text == _SAMPLE_TEXT:
        print("\n  ℹ  No input detected — using built-in sample text.\n")
    else:
        word_count = len(text.split())
        print(f"\n  ✓  Received {word_count} word(s) of study notes.\n")

    _demo_summary(text)
    _demo_flashcards(text)
    _demo_quiz(text)
    _demo_study_plan()

    print(f"\n{_rule('═')}")
    print("  Smart Study Generator demo complete.")
    print(f"{_rule('═')}\n")


def main() -> None:
    """Bootstrap the application and run a demo search."""
    logger.info("ScholarAI starting up…")

    if config.DEBUG:
        logger.debug("Debug mode is ON")

    # --- Demo: search for papers ----------------------------------------
    query = "large language models survey"
    logger.info("Running demo search: %r", query)

    service = SearchService()
    results = service.search(query, limit=config.DEFAULT_RESULT_LIMIT)

    if not results:
        logger.warning("No results returned for query: %r", query)
        print(f"\n{'─' * 60}")
        print("  No paper results found. Continuing to the demo…")
        print(f"{'─' * 60}\n")

    print(f"\n{'─' * 60}")
    print(f"  Top {len(results)} results for: {query!r}")
    print(f"{'─' * 60}")
    for i, paper in enumerate(results, start=1):
        print(f"\n[{i}] {paper.title}")
        print(f"    Authors : {', '.join(paper.authors)}")
        print(f"    Year    : {paper.year}")
        print(f"    Abstract: {paper.short_abstract()}")
    print(f"\n{'─' * 60}\n")

    _run_smart_study_demo()


if __name__ == "__main__":
    main()
