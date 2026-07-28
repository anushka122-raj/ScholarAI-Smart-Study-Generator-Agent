# ScholarAI

> An AI-powered academic paper discovery and summarisation tool.

ScholarAI lets you search, explore, and summarise academic literature using
natural language queries — backed by the Semantic Scholar API and OpenAI.

---

## Features

- **Paper search** — query millions of academic papers via Semantic Scholar
- **Smart summaries** — OpenAI-powered abstracts and Q&A over papers
- **Keyword extraction** — automatically surfaces key topics in any paper
- **Clean data model** — typed `Paper` dataclass with round-trip dict support
- **Configurable** — all settings driven by environment variables

---

## Project Structure

```
ScholarAI/
├── app/
│   ├── __init__.py          # Package marker
│   ├── config.py            # Env-var driven configuration
│   ├── main.py              # Entry point / CLI bootstrap
│   ├── models/
│   │   ├── __init__.py
│   │   └── paper.py         # Paper dataclass
│   ├── services/
│   │   ├── __init__.py
│   │   └── search_service.py  # Semantic Scholar integration
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py    # Text cleaning helpers
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Unit tests (pytest)
├── .env.example             # Environment variable template
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Dev / test dependencies
└── README.md
```

---

## Quick Start

### 1. Clone & enter the project

```bash
git clone https://github.com/your-org/ScholarAI.git
cd ScholarAI
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Activate — macOS/Linux
source .venv/bin/activate

# Activate — Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in OPENAI_API_KEY, etc.
```

### 5. Run the demo

```bash
python -m app.main
```

---

## Running Tests

Install dev dependencies first:

```bash
pip install -r requirements-dev.txt
```

Then run:

```bash
# All tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required for AI features)* | OpenAI secret key |
| `SEMANTIC_SCHOLAR_API_KEY` | *(optional)* | Higher rate limits |
| `DEFAULT_RESULT_LIMIT` | `10` | Max papers per search |
| `DEFAULT_LANGUAGE` | `en` | Result language filter |
| `DEBUG` | `false` | Verbose debug logging |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Contributing

1. Fork the repo and create a feature branch.
2. Run `ruff check .` and `mypy app/` before opening a PR.
3. Add or update tests for any changed behaviour.

---

## License

MIT — see `LICENSE` for details.
