"""
models/paper.py
---------------
Defines the core `Paper` data model used throughout ScholarAI.

Using a dataclass keeps the model lightweight while still providing
type annotations, a generated __repr__, and easy dict conversion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Paper:
    """Represents a single academic paper returned by a search or fetch."""

    # ------------------------------------------------------------------ #
    # Required fields
    # ------------------------------------------------------------------ #
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: str

    # ------------------------------------------------------------------ #
    # Optional / enriched fields
    # ------------------------------------------------------------------ #
    paper_id: str = ""
    doi: str = ""
    url: str = ""
    venue: str = ""
    citation_count: int = 0
    keywords: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Helper methods
    # ------------------------------------------------------------------ #

    def short_abstract(self, max_chars: int = 160) -> str:
        """Return a truncated abstract suitable for list views."""
        if len(self.abstract) <= max_chars:
            return self.abstract
        return self.abstract[:max_chars].rsplit(" ", 1)[0] + "…"

    def to_dict(self) -> dict:
        """Serialise the paper to a plain dictionary (e.g. for JSON output)."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "doi": self.doi,
            "url": self.url,
            "venue": self.venue,
            "citation_count": self.citation_count,
            "keywords": self.keywords,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        """Construct a Paper from a dictionary (e.g. from an API response)."""
        return cls(
            paper_id=data.get("paper_id", ""),
            title=data.get("title", "Untitled"),
            authors=data.get("authors", []),
            year=data.get("year"),
            abstract=data.get("abstract", ""),
            doi=data.get("doi", ""),
            url=data.get("url", ""),
            venue=data.get("venue", ""),
            citation_count=data.get("citation_count", 0),
            keywords=data.get("keywords", []),
        )
