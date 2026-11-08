# MemoryX

Phase 0: SQLite storage, chunking, keyword search, CLI, and a baseline eval.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Use

```bash
python -m app.cli add demo "User lives in San Francisco."
python -m app.cli add demo "User prefers TypeScript and dark mode."
python -m app.cli ls demo
python -m app.cli search demo "san francisco"
python -m app.cli reset demo
```

## Test and evaluate

```bash
pytest
python -m evals.run --mode keyword
```

Reports are written to `evals/reports/`.
