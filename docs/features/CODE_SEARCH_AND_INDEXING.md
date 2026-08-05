# Code Search & Indexing Engine

TestPilot AI features a high-performance **3-Layer Hybrid Code Search Engine** powered by vector embeddings, relational database indexes, and direct disk scanning.

---

## 3-Layer Search Architecture

When a user submits a code search query (e.g. `mockStreamResponse`), TestPilot AI evaluates three complementary retrieval layers in parallel to ensure 100% recall accuracy:

```
                          ┌───────────────────────────┐
                          │   User Search Request     │
                          └─────────────┬─────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
       ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
       │     Layer 1      │   │     Layer 2      │   │     Layer 3      │
       │ Vector Search    │   │ Relational ILIKE │   │ Disk File Scanner│
       │ (Qdrant 384-dim) │   │  (PostgreSQL DB) │   │ (/tmp/repos/...) │
       └─────────┬────────┘   └─────────┬────────┘   └─────────┬────────┘
                 │                      │                      │
                 └──────────────────────┼──────────────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │ Combined & Scored Results │
                          └───────────────────────────┘
```

### Layer 1: Qdrant Vector DB Search
- **Collections**: `code_symbols` and `repository_chunks`.
- **Dimensions**: 384-dimensional dense vectors.
- **Embedding Generation**: Uses local SentenceTransformers (`all-MiniLM-L6-v2`) with a deterministic 384-dimensional hash vector fallback to ensure zero downtime.

### Layer 2: PostgreSQL `RepositoryFile` Search
- Performs fast ILIKE text matching over `path`, `functions`, `classes`, and `exports` columns.
- Retains function and class metadata even if vector indices are rebuilding.

### Layer 3: Local Disk Scanner
- Directly scans `/tmp/repos/<repo_id>` or `/tmp/repos/<repo_name>` using keyword matching.
- Guarantees exact symbol hits (e.g. specific function names or variable declarations) are returned even for newly added files.

---

##  Repository Scoping & Selector
- Users can scope search queries strictly to a selected repository (e.g., `Shikhaar/Portfolio2.0`).
- The frontend dynamically loads user connected repositories via `/api/v1/repositories`.
