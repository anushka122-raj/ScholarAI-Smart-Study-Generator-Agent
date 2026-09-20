# 🔬 ScholarAI

<p align="center">
  <h3 align="center">🧠 AI-Powered Academic Research Assistant</h3>
</p>

<p align="center">
  <b>Search • Discover • Understand • Summarise • Research</b>
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-Powered-412991?style=for-the-badge\&logo=openai\&logoColor=white)
![Semantic Scholar](https://img.shields.io/badge/Semantic%20Scholar-API-4285F4?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Testing-Pytest-0A9EDC?style=for-the-badge\&logo=pytest\&logoColor=white)

</p>

---

## 🌟 Overview

**ScholarAI** is an AI-powered academic research assistant that helps users **discover, explore, and understand research papers using natural-language queries**.

It combines:

* 🔎 **Semantic Scholar API** for academic paper discovery
* 🤖 **OpenAI** for intelligent paper analysis
* 🧹 **Text processing** for preparing academic content
* 💬 **AI-powered Q&A** for interacting with papers
* 📝 **Summarisation** for quickly understanding research

Instead of manually going through large amounts of academic literature, ScholarAI aims to provide a more intelligent research workflow.

---

# 🚀 Core Features

```mermaid
mindmap
  root((🔬 ScholarAI))
    🔎 Discovery
      Natural Language Search
      Academic Paper Search
      Semantic Scholar API
    🧠 AI Analysis
      Summarisation
      Keyword Extraction
      Paper Q&A
    📚 Research
      Paper Exploration
      Research Insights
      Academic Understanding
    ⚙️ Engineering
      Python
      Modular Architecture
      Environment Configuration
      Unit Testing
```

---

# 🏗️ System Architecture

The complete ScholarAI pipeline:

```mermaid
flowchart TD

    U["👤 User<br/>Research Query"]

    S["🔎 Search Service<br/>Natural Language Processing"]

    API["📚 Semantic Scholar API<br/>Academic Paper Discovery"]

    P["📄 Relevant Research Papers"]

    T["🧹 Text Processing<br/>Cleaning & Preparation"]

    AI["🤖 OpenAI<br/>AI Analysis"]

    SUM["📝 Summaries"]
    KEY["🏷️ Keywords"]
    QA["💬 Paper Q&A"]
    INS["💡 Research Insights"]

    U --> S
    S --> API
    API --> P
    P --> T
    T --> AI

    AI --> SUM
    AI --> KEY
    AI --> QA
    AI --> INS

    classDef user fill:#FFE4F1,stroke:#E91E63,stroke-width:2px,color:#222;
    classDef search fill:#E3F2FD,stroke:#2196F3,stroke-width:2px,color:#222;
    classDef api fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#222;
    classDef paper fill:#FFF3E0,stroke:#FF9800,stroke-width:2px,color:#222;
    classDef ai fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#222;
    classDef output fill:#E0F7FA,stroke:#00ACC1,stroke-width:2px,color:#222;

    class U user;
    class S search;
    class API api;
    class P,T paper;
    class AI ai;
    class SUM,KEY,QA,INS output;
```

---

# 🧠 How ScholarAI Works

```mermaid
flowchart LR

    A["💭 User asks:<br/>How are LLMs used in healthcare?"]
    
    B["🔎 Search"]
    
    C["📚 Semantic Scholar"]
    
    D["📄 Papers"]
    
    E["🧹 Clean Text"]
    
    F["🤖 AI Processing"]
    
    G["📝 Summary"]
    
    H["🏷️ Keywords"]
    
    I["💬 Q&A"]

    A --> B --> C --> D --> E --> F
    F --> G
    F --> H
    F --> I

    classDef query fill:#FFF0F6,stroke:#E91E63,stroke-width:2px,color:#222;
    classDef discovery fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#222;
    classDef processing fill:#FFF8E1,stroke:#FFB300,stroke-width:2px,color:#222;
    classDef ai fill:#F3E5F5,stroke:#8E24AA,stroke-width:2px,color:#222;
    classDef result fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#222;

    class A query;
    class B,C,D discovery;
    class E processing;
    class F ai;
    class G,H,I result;
```

---

# 🔄 AI Research Pipeline

ScholarAI can be viewed as a sequence of research-processing stages:

```mermaid
flowchart TD

    A["👤 Researcher"]

    B["💭 Natural Language Query"]

    C["🔎 Paper Retrieval"]

    D["📚 Academic Literature"]

    E["🧹 Text Cleaning"]

    F["✂️ Text Preparation"]

    G["🧠 LLM Processing"]

    H["📊 Information Extraction"]

    I["📝 Summary"]
    J["🏷️ Keywords"]
    K["💬 Question Answering"]

    L["💡 Research Understanding"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H

    H --> I
    H --> J
    H --> K

    I --> L
    J --> L
    K --> L

    classDef actor fill:#FCE4EC,stroke:#D81B60,stroke-width:2px,color:#222;
    classDef input fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px,color:#222;
    classDef data fill:#FFF3E0,stroke:#FB8C00,stroke-width:2px,color:#222;
    classDef processing fill:#F3E5F5,stroke:#8E24AA,stroke-width:2px,color:#222;
    classDef output fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#222;
    classDef final fill:#E0F7FA,stroke:#00838F,stroke-width:3px,color:#222;

    class A actor;
    class B,C input;
    class D,E,F data;
    class G,H processing;
    class I,J,K output;
    class L final;
```

---

# 🧩 Application Architecture

```mermaid
flowchart TB

    subgraph USER["👤 User Layer"]
        UI["💻 ScholarAI Interface"]
        QUERY["🔎 Research Query"]
    end

    subgraph APP["⚙️ Application Layer"]
        MAIN["🚀 Application Entry Point"]
        CONFIG["⚙️ Configuration"]
        SEARCH["🔎 Search Service"]
        TEXT["🧹 Text Utilities"]
    end

    subgraph EXTERNAL["🌐 External Services"]
        S2["📚 Semantic Scholar API"]
        OPENAI["🤖 OpenAI API"]
    end

    subgraph OUTPUT["✨ AI Results"]
        SUMMARY["📝 Summary"]
        KEYWORDS["🏷️ Keywords"]
        ANSWERS["💬 Answers"]
    end

    UI --> QUERY
    QUERY --> MAIN

    MAIN --> CONFIG
    MAIN --> SEARCH
    SEARCH --> S2

    S2 --> TEXT
    TEXT --> OPENAI

    OPENAI --> SUMMARY
    OPENAI --> KEYWORDS
    OPENAI --> ANSWERS

    classDef user fill:#FCE4EC,stroke:#E91E63,stroke-width:2px,color:#222;
    classDef app fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#222;
    classDef external fill:#FFF3E0,stroke:#FB8C00,stroke-width:2px,color:#222;
    classDef output fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#222;

    class UI,QUERY user;
    class MAIN,CONFIG,SEARCH,TEXT app;
    class S2,OPENAI external;
    class SUMMARY,KEYWORDS,ANSWERS output;
```

---

# 📁 Project Structure

```text
ScholarAI/
│
├── 📦 app/
│   │
│   ├── __init__.py
│   ├── ⚙️ config.py
│   ├── 🚀 main.py
│   │
│   ├── 📚 models/
│   │   ├── __init__.py
│   │   └── 📄 paper.py
│   │
│   ├── 🔧 services/
│   │   ├── __init__.py
│   │   └── 🔎 search_service.py
│   │
│   └── 🛠️ utils/
│       ├── __init__.py
│       └── 🧹 text_utils.py
│
├── 🧪 tests/
│   ├── __init__.py
│   └── test_main.py
│
├── 🔐 .env.example
├── 📦 requirements.txt
├── 🧪 requirements-dev.txt
└── 📖 README.md
```

---

# 🧱 Component Responsibilities

```mermaid
flowchart LR

    M["📄 Paper Model"]
    C["⚙️ Config"]
    S["🔎 Search Service"]
    T["🧹 Text Utils"]
    MAIN["🚀 Main"]
    TEST["🧪 Tests"]

    C --> MAIN
    MAIN --> S
    S --> M
    S --> T
    T --> MAIN

    TEST -. validates .-> MAIN
    TEST -. validates .-> S
    TEST -. validates .-> T

    classDef component fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#222;
    classDef testing fill:#FCE4EC,stroke:#D81B60,stroke-width:2px,color:#222;

    class M,C,S,T,MAIN component;
    class TEST testing;
```

---

# 🛠️ Tech Stack

```mermaid
flowchart TD

    TECH["ScholarAI Technology Stack"]

    PY["Python - Core Application"]
    OPEN["OpenAI - AI Processing"]
    SEM["Semantic Scholar - Paper Discovery"]
    TEST["Pytest - Testing"]
    ENV["Environment Variables - Configuration"]

    TECH --> PY
    TECH --> OPEN
    TECH --> SEM
    TECH --> TEST
    TECH --> ENV

    classDef root fill:#E1BEE7,stroke:#8E24AA,stroke-width:3px,color:#222;
    classDef tech fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#222;

    class TECH root;
    class PY,OPEN,SEM,TEST,ENV tech;


----------------------------------------------------------------------------------------------

## Contributing

1. Fork the repo and create a feature branch.
2. Run `ruff check .` and `mypy app/` before opening a PR.
3. Add or update tests for any changed behaviour.

---

## License

MIT — see `LICENSE` for details.
