"""
utils/text_utils.py
-------------------
Shared text-processing helpers used across ScholarAI.

Keeping these in a single module avoids duplication and makes it easy to
swap in more sophisticated NLP later (e.g. spaCy, NLTK) without touching
service or model code.
"""

from __future__ import annotations

import re
import unicodedata


def sanitise_query(query: str) -> str:
    """
    Clean a raw user query before sending it to an external API.

    Steps:
    1. Strip leading/trailing whitespace.
    2. Normalise Unicode to NFC (handles accented characters correctly).
    3. Collapse consecutive whitespace to a single space.
    4. Remove characters that are neither word chars, spaces, nor common
       punctuation used in academic queries (hyphens, colons, quotes).

    Returns
    -------
    str
        The cleaned query string.
    """
    if not query:
        return ""

    query = query.strip()
    query = unicodedata.normalize("NFC", query)
    query = re.sub(r"\s+", " ", query)
    query = re.sub(r"[^\w\s\-:\"'.,]", "", query)
    return query.strip()


def truncate(text: str, max_words: int = 50) -> str:
    """
    Truncate *text* to at most *max_words* words, appending "…" if cut.

    Useful for generating short previews of long abstracts.
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    """
    Naïve keyword extractor: returns the *top_n* most frequent non-stopwords.

    For a production system replace this with a TF-IDF or KeyBERT approach.
    """
    _STOPWORDS = {
        "the", "a", "an", "and", "or", "of", "in", "to", "is", "are",
        "was", "were", "for", "with", "on", "at", "by", "this", "that",
        "it", "be", "as", "from", "we", "our", "their", "has", "have",
    }
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    freq: dict[str, int] = {}
    for word in words:
        if word not in _STOPWORDS:
            freq[word] = freq.get(word, 0) + 1
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    return sorted_words[:top_n]
