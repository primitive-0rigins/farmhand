# AGENTS.md - Farmhand

Coding agent instructions for this repository.

## Product Rules

- Build the daily operating surface first, not a marketing page.
- The first screen is "Today": do today, watch for, weather risk, this week.
- Farmers are not assumed to be technical. UI language must be plain and direct.
- Every generated task needs a reason the farmer can inspect.
- Every generated task should be editable into a reusable farm playbook.
- Deterministic rules come before AI. AI may assist later, but should not hide
  why a task appeared.

## Technical Stack

- Backend: Python 3.12+, FastAPI, Postgres
- Frontend: React + TypeScript
- Database migrations: Alembic when database models are introduced
- Tests: pytest for backend domain logic
- Runtime config: environment variables only, no secrets in repo

## Privacy And Data Rules

- Never commit farm addresses, customer data, API keys, tokens, or credentials.
- Use placeholder farms and public city-level examples in docs and tests.
- Do not commit generated local stores, database dumps, or logs.
- Weather, pest, and disease providers must be abstracted behind adapters.

## Engineering Rules

- Keep rules explainable and testable.
- Prefer explicit data flow over hidden automation.
- Add tests for new public domain logic.
- Avoid speculative abstractions. Build the next farm workflow.
- Keep UI dense, legible, and task-oriented.

## Verification

Before committing backend logic:

```bash
cd backend
python3 -m pytest
```

Before committing frontend logic, run the local package checks once dependencies
exist:

```bash
cd frontend
npm run build
```
