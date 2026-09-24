# T115 Student Risk and Intervention Briefing

- The project README and all documentation live in `docs/` (start at `docs/README.md`), not the repo root.
- The application is in `student_attrition_risk_app/` (see its `README.md`); specs are in `specs/`, the constitution in `.specify/`.

## Setup and tests

Run from `student_attrition_risk_app/`:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

Copy `.env.example` to `.env` for local runs only. Never print or commit `DATABRICKS_TOKEN`.
