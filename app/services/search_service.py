"""
services/search_service.py
--------------------------
SearchService encapsulates all paper-search logic for ScholarAI.

Currently backed by the free Semantic Scholar API (no key required for
basic usage).  Swap the `_fetch` method to integrate a different source
(PubMed, arXiv, OpenAlex, etc.) without changing any calling code.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import requests

from app.config import config
from app.models.paper import Paper
from app.utils.text_utils import sanitise_query

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,authors,year,abstract,externalIds,url,venue,citationCount"


class SearchService:
    """Fetch and return academic papers matching a natural-language query."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or config.SEMANTIC_SCHOLAR_API_KEY
        self._session = requests.Session()
        if self._api_key:
            self._session.headers.update({"x-api-key": self._api_key})

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    def search(self, query: str, limit: int = 10) -> List[Paper]:
        """
        Search for papers by keyword/natural-language query.

        Parameters
        ----------
        query : str
            The search string (e.g. "attention mechanisms transformers").
        limit : int
            Maximum number of results to return (default: 10, max: 100).

        Returns
        -------
        List[Paper]
            A list of Paper objects ordered by relevance.
        """
        clean_query = sanitise_query(query)
        if not clean_query:
            logger.warning("Empty query after sanitisation — returning []")
            return []

        logger.info("Searching Semantic Scholar for %r (limit=%d)", clean_query, limit)
        raw = self._fetch(clean_query, limit)
        papers = [self._parse_paper(item) for item in raw]
        logger.info("Found %d paper(s)", len(papers))
        return papers

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _fetch(self, query: str, limit: int) -> list:
        """Call the Semantic Scholar search endpoint and return raw JSON."""
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": _FIELDS,
        }
        try:
            response = self._session.get(
                f"{_BASE_URL}/paper/search",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.RequestException as exc:
            logger.error("Semantic Scholar request failed: %s", exc)
            return []

    @staticmethod
    def _parse_paper(item: dict) -> Paper:
        """Map a raw API response dict to a Paper dataclass instance."""
        authors = [a.get("name", "") for a in item.get("authors", [])]
        external_ids = item.get("externalIds") or {}
        return Paper(
            paper_id=item.get("paperId", ""),
            title=item.get("title", "Untitled"),
            authors=authors,
            year=item.get("year"),
            abstract=item.get("abstract") or "",
            doi=external_ids.get("DOI", ""),
            url=item.get("url", ""),
            venue=item.get("venue", ""),
            citation_count=item.get("citationCount", 0),
        )
