# CodeAtlas

> AI-powered codebase intelligence for understanding unfamiliar software repositories.

CodeAtlas is a developer tool that combines **static code analysis, AST parsing, dependency graphs, semantic retrieval, and LLM reasoning** to help developers understand large and unfamiliar codebases.

Instead of treating a repository as a collection of text files, CodeAtlas builds a structured representation of the codebase and uses it to provide **evidence-backed explanations, dependency exploration, execution-flow tracing, and change-impact analysis**.

---

## Why CodeAtlas?

Understanding an unfamiliar codebase is often harder than writing new code.

Developers usually have to:

- Search through hundreds of files
- Follow imports manually
- Trace function calls
- Understand unfamiliar abstractions
- Figure out where a feature actually starts and ends
- Determine what might break after changing a component

Traditional code search is useful, but it doesn't understand the relationships between different parts of a codebase.

CodeAtlas aims to provide a higher-level layer of understanding.

```mermaid
flowchart TD
    A[Codebase] --> B[Static Analysis]
    B --> C[AST Data]
    B --> D[Code Graph]
    C --> E[Hybrid Retrieval]
    D --> E
    E --> F[LLM Reasoning]
    F --> G[Evidence-backed Answer]

    classDef input fill:#1e1b4b,stroke:#4f46e5,color:#fff
    classDef core fill:#064e3b,stroke:#10b981,color:#fff
    class A input
    class B,C,D,E,F,G core
```

---

## Core Features

### Codebase Understanding

Analyze a repository and extract:

- Files
- Classes
- Functions
- Methods
- Imports
- Calls
- Inheritance relationships
- Dependencies

### AI-Powered Code Search

Ask natural-language questions about a repository.

Example:

> Where is user authentication handled?

CodeAtlas retrieves relevant code using a combination of:

- Semantic similarity
- Symbol relationships
- Dependency information
- Static analysis

### Dependency Graph

Build a graph representing relationships between components.

Example:

```mermaid
flowchart TD
    OC[OrderController] --> OS[OrderService]
    OS --> PS[PaymentService]
    OS --> OR[OrderRepository]
    OR --> DB[(PostgreSQL)]
```

### Execution Flow Analysis

Trace important paths through a codebase.

Example:

```mermaid
flowchart TD
    A([HTTP Request]) --> B[Controller]
    B --> C[Service]
    C --> D[Repository]
    D --> E[(Database)]
```

### Change Impact Analysis

Ask:

> If I modify this function, what could be affected?

CodeAtlas uses the dependency graph and static analysis to identify potentially affected components and uses the LLM to explain why they are relevant.

### Architecture Exploration

Generate a high-level representation of a repository so developers can understand the architecture without reading the entire codebase first.

---

## Technical Approach

CodeAtlas intentionally avoids relying on a heavyweight framework such as LangChain for its core AI pipeline.

The retrieval and reasoning pipeline is implemented directly so the system has explicit control over:

- Code parsing
- Code-aware chunking
- Embeddings
- Graph traversal
- Retrieval
- Reranking
- Context construction
- LLM generation
- Structured outputs
- Evaluation

### High-Level Architecture

```mermaid
flowchart TD
    FE["Frontend<br/>Next.js"] --> API["FastAPI API"]

    API --> ING[Repository Ingestion]
    API --> RET[Retrieval Engine]
    API --> LLM[LLM Reasoning]

    ING --> TS[Tree-sitter]
    TS --> CS[Code Structure]

    RET --> VS[Vector Search]
    RET --> GS[Graph Search]

    CS --> CE
    VS --> CE
    GS --> CE
    LLM --> CE

    CE["Context + Evidence"] --> ANS["Answer + Citations"]

    classDef ui fill:#1e1b4b,stroke:#4f46e5,color:#fff
    classDef core fill:#064e3b,stroke:#10b981,color:#fff
    class FE,API ui
    class ING,RET,LLM core
```

---

## Tech Stack

### Backend

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- asyncpg
- Alembic

### Code Intelligence

- Tree-sitter
- AST analysis
- Static dependency analysis
- Custom code graph

### AI / Retrieval

- LLM API
- Embeddings
- pgvector
- Hybrid retrieval
- Custom reranking

### Database

- PostgreSQL
- pgvector

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Monaco Editor
- React Flow

### Development

- uv
- Ruff
- Pyright
- Pytest
- Docker

---

## Project Structure

```text
codeatlas/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── graph/
│   │   ├── ingestion/
│   │   ├── llm/
│   │   ├── parser/
│   │   ├── retrieval/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   │   ├── api/
│   │   ├── database/
│   │   ├── graph/
│   │   ├── ingestion/
│   │   ├── parser/
│   │   └── services/
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
├── docs/
├── evaluation/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── LICENSE
├── Makefile
└── README.md
```

---

## Development Roadmap

CodeAtlas is being developed incrementally.

```mermaid
flowchart LR
    P1[1. Backend Foundation] --> P2[2. Ingestion] --> P3[3. Code Intelligence] --> P4[4. Code Graph]
    P4 --> P5[5. Semantic Retrieval] --> P6[6. LLM Reasoning] --> P7[7. Frontend] --> P8[8. Evaluation]

    style P1 fill:#064e3b,stroke:#10b981,color:#fff
    style P2 fill:#1e1b4b,stroke:#4f46e5,color:#fff
    style P3 fill:#1e1b4b,stroke:#4f46e5,color:#fff
    style P4 fill:#1e1b4b,stroke:#4f46e5,color:#fff
    style P5 fill:#1e1b4b,stroke:#4f46e5,color:#fff
    style P6 fill:#1e1b4b,stroke:#4f46e5,color:#fff
    style P7 fill:#1e1b4b,stroke:#4f46e5,color:#fff
    style P8 fill:#1e1b4b,stroke:#4f46e5,color:#fff
```

### Phase 1 — Backend Foundation

- [x] Project structure
- [x] FastAPI application
- [x] Health endpoint
- [x] Application configuration
- [x] PostgreSQL setup
- [x] SQLAlchemy async database layer
- [x] Alembic migrations

### Phase 2 — Repository Ingestion

- [x] Git repository ingestion
- [x] Repository creation API (POST /api/v1/repositories)
- [x] Repository file discovery
- [x] File filtering
- [x] Repository metadata
- [x] File hashing and incremental indexing
- [x] Detect and store repository file language metadata
- [x] Database migration for file-language metadata
- [x] Automated ingestion and API tests

### Phase 3 — Code Intelligence

- [x] Tree-sitter integration
- [x] Python, JavaScript, and TypeScript parsing
- [x] AST extraction
- [x] Symbol extraction for supported syntax
- [x] Import extraction
- [x] Function and class relationships extraction
- [x] Symbol persistence in PostgreSQL
- [x] Replace symbols when source files change
- [x] Preserve symbols for unchanged files
- [x] Remove symbols when source files are deleted
- [x] Automated parser, repository, and indexing tests  

### Phase 4 — Code Graph

- [ ] Dependency graph construction
- [ ] Symbol relationships
- [ ] Graph traversal
- [ ] Impact analysis primitives

### Phase 5 — Semantic Retrieval

- [ ] Code-aware chunking
- [ ] Embedding generation
- [ ] pgvector storage
- [ ] Vector search
- [ ] Graph search
- [ ] Hybrid retrieval
- [ ] Reranking

### Phase 6 — LLM Reasoning

- [ ] LLM integration
- [ ] Structured outputs
- [ ] Evidence-backed answers
- [ ] Code citations
- [ ] Architecture explanations
- [ ] Flow tracing
- [ ] Change-impact explanations

### Phase 7 — Frontend

- [ ] Repository dashboard
- [ ] File explorer
- [ ] Code viewer
- [ ] AI chat
- [ ] Dependency graph visualization
- [ ] Architecture explorer
- [ ] Impact analysis interface

### Phase 8 — Evaluation

- [ ] Evaluation dataset
- [ ] Retrieval metrics
- [ ] Answer quality evaluation
- [ ] Citation accuracy
- [ ] End-to-end benchmarks

---

## Local Development

### Prerequisites

- Python 3.13
- uv
- Docker
- Node.js

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## Environment Variables

Create a local `.env` file based on `.env.example`.

Example:

```env
DATABASE_URL=postgresql+asyncpg://codeatlas:password@localhost:5432/codeatlas

LLM_API_KEY=
EMBEDDING_API_KEY=
```

Never commit `.env` or API keys to the repository.

---

## Design Principles

### 1. Deterministic analysis before LLM reasoning

CodeAtlas should not ask an LLM to determine facts that can be established through static analysis.

For example:

> Which functions does `OrderService.create()` call?

This should come from parsed code and the dependency graph.

The LLM should instead answer:

> Why are these functions involved in creating an order?

### 2. Evidence-backed generation

AI responses should be grounded in actual repository evidence.

Answers should be able to reference locations such as:

```text
src/orders/service.py:42-67
src/payments/service.py:18-31
src/orders/repository.py:12-29
```

rather than generating unsupported explanations.

### 3. Hybrid retrieval

Neither vector search nor graph traversal is sufficient on its own.

CodeAtlas combines:

```mermaid
flowchart LR
    S[Semantic Search] --> H((Hybrid<br/>Context))
    T[Structural Search] --> H
    D[Dependency Relationships] --> H
    H --> L[LLM]
```

to construct better context for the LLM.

### 4. Explicit AI pipeline

The AI pipeline is intentionally implemented without a heavyweight orchestration framework.

```mermaid
flowchart TD
    Q[Question] --> QU[Query Understanding]
    QU --> VR[Vector Retrieval]
    QU --> GR[Graph Retrieval]
    VR --> RF[Result Fusion]
    GR --> RF
    RF --> RR[Reranking]
    RR --> CC[Context Construction]
    CC --> LLM[LLM]
    LLM --> SR[Structured Response]
    SR --> EV[Evidence Validation]
```

---

## Current Status

> 🚧 **Early development — Phase 2 implemented**

CodeAtlas currently supports repository ingestion, incremental file indexing, and AST-based code analysis for Python, JavaScript, and TypeScript.

The parser extracts symbols, imports, and supported code relationships. Extracted symbols are persisted in PostgreSQL and synchronized when files are added, changed, or deleted.

**Next milestone:** Phase 3 — Code Graph construction, including dependency relationships, graph traversal, and impact-analysis primitives.

Semantic retrieval, LLM reasoning, and the frontend remain future milestones.

---

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.