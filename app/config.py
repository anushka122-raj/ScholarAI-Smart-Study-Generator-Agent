"""
config.py
---------
Centralised configuration for ScholarAI.

All runtime settings are sourced from environment variables so that no
secrets are ever hard-coded.  Copy `.env.example` to `.env` and fill in
your values; python-dotenv will load them automatically when the app starts.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file if one exists (ignored in production where
# real env vars are injected by the host/container).
load_dotenv()


class Config:
    """Application-wide configuration object."""

    # ------------------------------------------------------------------ #
    # API credentials
    # ------------------------------------------------------------------ #
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    # ------------------------------------------------------------------ #
    # Search defaults
    # ------------------------------------------------------------------ #
    DEFAULT_RESULT_LIMIT: int = int(os.getenv("DEFAULT_RESULT_LIMIT", "10"))
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")

    # ------------------------------------------------------------------ #
    # Application behaviour
    # ------------------------------------------------------------------ #
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


# Singleton instance used across the app
config = Config()
